#!/usr/bin/env python3
"""Opt-in Claude workflow + packaged-skill decision check; uses account usage."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import zipfile


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


def run(workspace, logs, plugin, prompt, seconds, resume=None, readonly=False):
    logs.mkdir(parents=True)
    (logs / "prompt.txt").write_text(prompt)
    candidate = workspace / "candidate.py"
    allowed = ["Read", "Skill"]
    if not readonly:
        # Claude uses // for absolute paths; Edit rules cover Write as well.
        allowed += [f"Edit(/{candidate})"]
    command = ["claude", "-p", "--output-format", "stream-json", "--verbose",
               "--debug-file", str(logs / "debug.txt"),
               "--plugin-dir", str(plugin), "--setting-sources", "",
               "--settings", '{"disableAllHooks":true}', "--strict-mcp-config",
               "--permission-mode", "dontAsk", "--tools", "Read,Edit,Write,Skill",
               "--allowedTools", ",".join(allowed)]
    if resume:
        command += ["--resume", resume]
    started = time.monotonic()
    timed_out = False
    with (logs / "events.jsonl").open("w") as out, (logs / "stderr.txt").open("w") as err:
        child = subprocess.Popen(command, cwd=workspace, stdin=subprocess.PIPE,
                                 stdout=out, stderr=err, text=True, start_new_session=True)
        try:
            child.communicate(prompt, timeout=seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
        finally:
            try:
                os.killpg(child.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                child.wait(timeout=2)
            except subprocess.TimeoutExpired:
                pass
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            child.wait()
    elapsed = time.monotonic() - started
    events = []
    for line in (logs / "events.jsonl").read_text().splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    init = next((e for e in events if e.get("type") == "system" and e.get("subtype") == "init"), {})
    result = next((e for e in reversed(events) if e.get("type") == "result"), {})
    record = {"allocated_seconds": seconds, "elapsed_seconds": elapsed,
              "timed_out": timed_out, "returncode": child.returncode,
              "session_id": result.get("session_id", init.get("session_id")),
              "resume": resume, "model": init.get("model"), "plugins": init.get("plugins"),
              "skills": init.get("skills"), "result_subtype": result.get("subtype"),
              "is_error": result.get("is_error"), "usage": result.get("usage"),
              "reported_total_cost_usd": result.get("total_cost_usd"),
              "permission_denials": result.get("permission_denials", [])}
    save(logs / "run.json", record)
    (logs / "final.txt").write_text(result.get("result", ""))
    save(logs / "command.json", command)
    print(json.dumps({k: record[k] for k in ("elapsed_seconds", "timed_out", "returncode",
          "session_id", "resume", "is_error", "reported_total_cost_usd")}), flush=True)
    return record


def main(run_dir, plugin_zip):
    root = Path(__file__).resolve().parents[1]
    run_dir = run_dir.resolve()
    run_dir.mkdir(parents=True, exist_ok=False)
    plugin = run_dir / "plugin"
    with zipfile.ZipFile(plugin_zip) as bundle:
        bundle.extractall(plugin)
    plugin_before = {str(p.relative_to(plugin)): digest(p) for p in plugin.rglob("*") if p.is_file()}
    fixture = root / "examples/bin-packing"
    source_before = {p.name: digest(p) for p in fixture.glob("*") if p.is_file()}
    fixed = run_dir / "fixed"
    shutil.copytree(fixture, fixed, ignore=shutil.ignore_patterns("__pycache__"))
    checkpoints = run_dir / "checkpoints"
    checkpoints.mkdir()
    def evaluate(name, candidate):
        checkpoint = checkpoints / (name + ".py")
        shutil.copyfile(candidate, checkpoint)
        checkpoint.chmod(0o444)
        result = subprocess.run([sys.executable, str(fixed / "evaluate.py"), str(checkpoint)],
                                capture_output=True, text=True, timeout=10, check=True)
        value = json.loads(result.stdout)
        save(checkpoints / (name + ".json"), value)
        return value
    start = time.monotonic()
    baseline = evaluate("incumbent", fixed / "candidate.py")
    branches = []
    for name in ("a", "b"):
        workspace = run_dir / name
        shutil.copytree(fixed, workspace, ignore=shutil.ignore_patterns("__pycache__"))
        branches.append(workspace)
    isolated = all((branches[0] / n).stat().st_ino != (branches[1] / n).stat().st_ino
                   for n in source_before)
    prompt = """You are one independent worker in a bounded bin-packing experiment.
Read TASK.md and candidate.py in your current workspace. Improve only candidate.py.
Use the standard library and satisfy arbitrary valid inputs; do not specialize to
fixed evaluator cases. You have at most 90 seconds including startup. The external
supervisor will score and checkpoint your artifact with the unchanged evaluator
once you stop. There is no shell tool in this worker; do not try to run evaluation
or request extra permissions. Do not spawn agents, read sibling runs, or modify
anything outside candidate.py. Save a valid improvement promptly, then finish.
"""
    with ThreadPoolExecutor(max_workers=2) as pool:
        runs = list(pool.map(lambda w: run(w, run_dir / "logs" / w.name, plugin, prompt, 90), branches))
    if any(r["is_error"] or r["returncode"] != 0 or r["result_subtype"] != "success"
           or r["permission_denials"] for r in runs):
        save(run_dir / "outcome.json", {"status": "incomplete", "branches": runs,
             "reason": "A fresh worker did not complete successfully; no continuation attempted"})
        raise RuntimeError("Fresh worker failure; inspect raw logs before retrying")
    evaluations = [evaluate(w.name, w / "candidate.py") for w in branches]
    viable = [i for i, r in enumerate(runs) if r["session_id"] and evaluations[i]["valid"]]
    if not viable:
        raise RuntimeError("No valid resumable branch; inspect raw logs")
    winner = min(viable, key=lambda i: (evaluations[i]["score"], i))
    chosen = branches[winner]
    if baseline["score"] <= evaluations[winner]["score"]:
        shutil.copyfile(checkpoints / "incumbent.py", chosen / "candidate.py")
    continuation = run(chosen, run_dir / "logs/resume", plugin,
        "Continue this same bin-packing task within 60 seconds. The supervisor restored "
        "the best verified checkpoint if necessary. Improve only candidate.py; keep "
        "the same constraints. External scoring happens after you stop. Save and finish.",
        60, resume=runs[winner]["session_id"])
    if (continuation["is_error"] or continuation["returncode"] != 0
            or continuation["result_subtype"] != "success" or continuation["permission_denials"]):
        save(run_dir / "outcome.json", {"status": "incomplete", "branches": runs,
             "continuation": continuation, "reason": "Continuation did not complete successfully"})
        raise RuntimeError("Continuation failure; inspect raw logs")
    continued = evaluate("continued", chosen / "candidate.py")
    artifacts = [("incumbent", baseline), ("a", evaluations[0]), ("b", evaluations[1]),
                 ("continued", continued)]
    best = min((x for x in artifacts if x[1]["valid"]), key=lambda x: x[1]["score"])
    final = evaluate("final", checkpoints / (best[0] + ".py"))
    measured = sum(r["elapsed_seconds"] for r in [*runs, continuation])
    source_after = {p.name: digest(p) for p in fixture.glob("*") if p.is_file()}
    plugin_after = {str(p.relative_to(plugin)): digest(p) for p in plugin.rglob("*") if p.is_file()}
    worker_inputs_unchanged = all(digest(w / n) == source_before[n]
                                  for w in branches for n in ("TASK.md", "evaluate.py"))
    outcome = {"claude_version": subprocess.check_output(["claude", "--version"], text=True).strip(),
               "plugin_zip_sha256": digest(plugin_zip), "plugin_files": plugin_before,
               "baseline": baseline, "branches": runs, "evaluations": evaluations,
               "selected_branch": chosen.name, "continuation": continuation,
               "continuation_evaluation": continued, "final": final,
               "best_checkpoint": best[0], "allocated_worker_seconds": 240,
               "measured_aggregate_worker_seconds": measured,
               "workflow_wall_seconds": time.monotonic() - start,
               "source_unchanged": source_before == source_after,
               "worker_inputs_unchanged": worker_inputs_unchanged,
               "plugin_unchanged": plugin_before == plugin_after,
               "independent_inodes": isolated,
               "fresh_session_ids_distinct": runs[0]["session_id"] != runs[1]["session_id"],
               "exact_session_resumed": continuation["session_id"] == runs[winner]["session_id"]}
    save(run_dir / "outcome.json", outcome)
    decision_workspace = run_dir / "decisions"
    decision_workspace.mkdir()
    decisions = run(decision_workspace, run_dir / "logs/decisions", plugin,
        """Use the installed fork-and-flush:fork-and-flush skill via the Skill tool.
This is a read-only decision test: do not launch workers or change files.
Explain the action for each case:
1. Minimize score: incumbent 10, valid fresh A best checkpoint 8 then latest 12,
valid fresh B 8. Stable branch order A then B. Which artifact and session continue?
2. Incumbent 10 and both valid fresh branches 10, order A then B. What continues?
3. Only this conversation and one writable directory exist. User asks for four
branches but gives no numerical budget or evaluator. What do you do?
4. Minimize latency: incumbent repeats [10,10,10], A [1,30,30], invalid B reports 0.
No noise comparison rule was declared. What do you select and report?
""", 90, readonly=True)
    save(run_dir / "decision-result.json", decisions)
    assert decisions["returncode"] == 0 and not decisions["is_error"] and decisions["result_subtype"] == "success"
    assert all(outcome[k] for k in ("source_unchanged", "worker_inputs_unchanged", "plugin_unchanged",
                                   "independent_inodes", "fresh_session_ids_distinct", "exact_session_resumed"))
    assert final["valid"] and final["score"] <= baseline["score"]
    print("Workflow invariants passed. Manually review logs/decisions/final.txt and Skill events.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--plugin-zip", type=Path, required=True)
    args = parser.parse_args()
    main(args.run_dir, args.plugin_zip.resolve())
