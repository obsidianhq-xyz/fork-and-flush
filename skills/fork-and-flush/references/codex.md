# Codex runtime

Use the actual capabilities exposed by your Codex surface. CLI execution and
in-session subagents are alternatives; the core skill does not depend on either.

## CLI

After preparing independent workspaces, start each branch with a new `codex exec`:

```sh
codex exec -C "$branch_dir" --sandbox workspace-write --json \
  --output-last-message "$log_dir/final.txt" - < "$prompt_file"
```

Use a caller-supplied directory and prompt. Keep logs outside the branch snapshot.
The command alone does not impose a time/token limit: run it under a supervisor
with a deadline and process-tree cancellation. Respect configured approvals and
report a blocked run rather than weakening them. CLI flags vary; inspect `--help`.

Capture `thread.started.thread_id` and `turn.completed.usage` from JSONL events.
Use a new invocation without `resume` or `fork` for each flush. To exploit a winner,
resume its exact session ID from its workspace, not an ambiguous `--last`:

```sh
cd "$winning_dir"
codex exec resume "$winning_session_id" --json - < "$continuation_prompt"
```

An ephemeral session is useful for a one-off test, but not for a branch you need to
resume. Usage is reported after a turn; that is measurement, not a hard token cap.
Use an external deadline when that is the available enforceable unit.

## In-session agents

If the host exposes a delegation tool with an explicit no-history option, use it
for a flush. Confirm the option's semantics from the live tool contract. Some
subagents inherit the entire parent conversation, and some share its filesystem.
Assign a different workspace to each and verify write isolation. A thread-fork
operation commonly preserves history and is unsuitable for flushing.

Retain the same model/settings across branches unless the user asks otherwise.
Do not create user-visible sidebar chats merely as worker slots. Use the host's
worker mechanism or the CLI when available and authorized.

[Official non-interactive documentation](https://learn.chatgpt.com/docs/non-interactive-mode)
and [skill documentation](https://developers.openai.com/codex/skills).

