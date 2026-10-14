---
name: fork-and-flush
description: Explore competing solutions to a measurable research or engineering problem using isolated agent branches, fresh conversations, and objective selection. Use for bounded optimization experiments or when the user requests fork-and-flush. Ordinary edits and tasks without an evaluator do not need this workflow.
license: MIT
metadata:
  version: "0.1.2"
---

# Fork-and-flush

Preserve accumulated work while periodically restarting exploration in fresh
agent conversations. Continue the best verified lineage within the user's budget.
This is an independent adaptation of [Cai et al.](https://arxiv.org/html/2610.07447v1),
not a reproduction of their benchmark results.

Requires fresh agent sessions, isolated writable workspaces, an evaluator, and
externally enforced limits. The optional schedule helper needs Python 3.10+.

## Establish the experiment

Use the user's existing decisions. Resolve missing essentials before launching:

- Task, permitted files and actions, and immutable evaluation inputs.
- Evaluator, score direction, validity rules, and treatment of noisy scores.
- Total budget, its unit, per-branch limits, concurrency, and stopping condition.
- Starting workspace and an existing scored incumbent, if any.

Prefer a programmatic evaluator. If a rubric or model judge is necessary, fix it
before exploration and label the result as judged rather than objectively optimal.
For noisy metrics, use the same seeds/repeats and a predetermined comparison rule.
Do not let a branch change its own tests, evaluator, or acceptance threshold.

Choose a budget the runtime can actually enforce. Sum consumption across workers;
parallel elapsed time is not total compute. Include failed branches and retries.
Reserve evaluation and final verification costs when they use the same resource.
Evaluation-call limits do not bound model spend; wall-clock limits do not reproduce
the paper's credit budget. Report the unit and any adaptation explicitly.

## Check the host

Read the relevant runtime reference:

- [Codex](references/codex.md)
- [Claude Code](references/claude-code.md)
- [Grok Build](references/grok-build.md)
- [Other agents and the common contract](references/runtime-contract.md)

Confirm fresh conversations, separate writable copies, stopping/cancellation, and
an observable budget before executing. Use the host's existing permissions. This
skill does not authorize publication, deployment, new paid services, or bypassing
sandbox/approval rules.

If a capability is unavailable, explain the specific gap and provide an experiment
plan. Do not claim that asking the current agent to forget, compacting its history,
or creating a Git branch flushes conversation context. Sequential fresh sessions
can be an explicitly disclosed adaptation; serial brainstorming in one chat is not.

## Choose a schedule

Use a fixed schedule so small score improvements cannot indefinitely postpone
exploration. The paper's reference schedule and a budget-accounting example are in
[method.md](references/method.md). An optional deterministic planner is available:

```sh
python3 <skill-dir>/scripts/plan.py --budget 100 --branches 4
```

Treat its output as allocations, not a scheduler or budget enforcer. It leaves
execution and metering to the host. Adjust branch count and schedule to the actual
concurrency and budget; disclose changes. A parent occupying a worker slot reduces
available parallelism. Do not quietly queue four branches and call them four-way
parallel execution.

An existing experiment can start from its current incumbent. A short requested
intervention may use one fork round; identify it as a reduced schedule.

## Run a fork round

1. Stop writes to the current leader before taking a snapshot. Preserve the full
   authorized workspace: source, relevant uncommitted/untracked work, data, tests,
   and experiment artifacts. A worktree from HEAD alone misses dirty files. Keep
   runtime session stores and coordinator transcripts outside the snapshot.
2. Save the best verified artifact and its score independently of the leader's
   latest edits. Record a content hash or equivalent immutable artifact identifier.
3. Create one writable workspace per branch from the same snapshot. Confirm that
   shared paths, symlinks, or external state cannot make workers overwrite each
   other. Preserve the user's original checkout.
4. Launch fresh conversations with the same task, constraints, evaluator contract,
   workspace location, and branch limit. Do not pass the parent's chat, a recap of
   its reasoning, or a preferred solution. Preserve ordinary task instructions and
   workspace artifacts; the flush concerns conversational history, not amnesia.
   Do not assign specialist roles or force different approaches by default.
   Require immutable artifact-and-score checkpoints whenever a candidate is
   evaluated, in both exploration and exploitation. The supervisor should preserve
   them outside mutable worker files. Include the inherited incumbent checkpoint
   in each branch's best-so-far record so later edits cannot erase a better result.
5. Keep branches independent until their allocated horizon closes. If a worker
   finishes early, continue that worker within its remaining allocation when useful.
   Stop every worker at its cap and wait for writes to cease before evaluation.
6. Evaluate saved candidates with the unchanged evaluator. Record validity, score,
   artifact hash, workspace, session identity, resource usage, and failures outside
   worker workspaces. Use measured results rather than a worker's claimed score.

## Select and continue

Rank each branch by its best valid, comparable, reproducible checkpoint, including
the inherited incumbent. An invalid or unverified artifact must not replace the
incumbent. A timeout may leave a usable checkpoint: evaluate it independently and
confirm the session is resumable before using it as the next leader.

Separate artifact preservation from session selection. Choose a viable fresh branch
among those sharing the best score using a stable branch order. Retain the incumbent
artifact only when it also shares that best score; tied improvements must still
replace a worse incumbent. Do not automatically resume the old parent's conversation
on a plateau; that would undo the flush. If no branch can continue, preserve the
incumbent and report that the round did not produce a usable new leader.

For noisy or statistically indistinguishable scores, apply the predefined rule
rather than selecting a lucky extreme. If no rule was fixed, treat the comparison
as exploratory, define the rule prospectively, and re-evaluate saved candidates
with matched repeats within remaining budget before replacing the incumbent.

Adopt the winning lineage and preserve its best artifact. Restore its best verified
checkpoint if the latest candidate regressed, and tell the worker which checkpoint
was restored without importing another session's reasoning. Continue the winner's
existing session for serial exploitation; fresh contexts are introduced at fork
rounds. If the host cannot resume the winner, disclose the extra reset. Do not merge
losing solutions into the winner by default: that changes the experiment.

Repeat at the next scheduled trigger while budget remains. Stop if the budget,
user-defined target, or validity constraints require it. If every new candidate
fails, retain the incumbent and report the failures; do not relaunch indefinitely.
Retain logs and results until the user can inspect them. Clean up only run-owned
resources whose evidence has been preserved.

## Deliver evidence

Re-evaluate the final artifact from its saved location. Report:

- Baseline and final score, direction, validity, and evaluator identity.
- Winning artifact path/hash and a per-branch results table.
- Budget unit, allocated and measured usage, and any unmetered overhead.
- Actual session/workspace isolation, schedule changes, and failed branches.
- Whether this was workflow validation or a repeated, matched-budget effectiveness
  study. One successful run does not establish improvement over a single agent.

Return the best verified result found anywhere in the run, even if later work regressed.
