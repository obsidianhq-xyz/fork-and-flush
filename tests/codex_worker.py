#!/usr/bin/env python3
"""Run one bounded Codex invocation for the opt-in acceptance test (POSIX)."""

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import time


def run(workspace, logs, prompt, timeout, resume=None):
    workspace, logs = Path(workspace).resolve(), Path(logs).resolve()
    if not workspace.is_dir() or not 0 < timeout <= 300:
        raise ValueError("existing workspace and timeout in (0, 300] required")
    if logs == workspace or workspace in logs.parents:
        raise ValueError("logs must live outside the worker workspace")
    logs.mkdir(parents=True, exist_ok=False)
    command = ["codex", "exec", "--sandbox", "workspace-write", "-C", str(workspace)]
    if resume:
        command += ["resume", resume]
    command += ["--skip-git-repo-check", "--json", "--output-last-message", str(logs / "final.txt"), "-"]
    started = time.monotonic()
    timed_out = False
    with (logs / "events.jsonl").open("w") as stdout, (logs / "stderr.txt").open("w") as stderr:
        process = subprocess.Popen(command, cwd=workspace, stdin=subprocess.PIPE,
                                   stdout=stdout, stderr=stderr, text=True, start_new_session=True)
        try:
            process.communicate(prompt, timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
        finally:
            # Also stop any surviving descendants after the CLI exits.
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                pass
            # The parent can exit while a descendant ignores SIGTERM.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
    elapsed = time.monotonic() - started
    events = []
    for line in (logs / "events.jsonl").read_text().splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    sessions = [e["thread_id"] for e in events if e.get("type") == "thread.started"]
    usage = [e["usage"] for e in events if e.get("type") == "turn.completed" and "usage" in e]
    result = {"workspace": str(workspace), "command": command, "resume": resume,
              "session_ids": sessions, "usage": usage, "allocated_seconds": timeout,
              "elapsed_seconds": elapsed, "timed_out": timed_out, "returncode": process.returncode,
              "turn_completed": any(e.get("type") == "turn.completed" for e in events)}
    (logs / "run.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--logs", type=Path, required=True)
    parser.add_argument("--prompt-file", type=Path, required=True)
    parser.add_argument("--timeout", type=float, required=True)
    parser.add_argument("--resume")
    args = parser.parse_args()
    print(json.dumps(run(args.workspace, args.logs, args.prompt_file.read_text(), args.timeout, args.resume)))
