# Grok Build runtime

Grok Build loads the canonical skill through the existing Claude-format plugin
manifest. Verify discovery with `grok plugin validate /path/to/plugin` and
`grok inspect --json` in the intended task workspace. A valid manifest alone does
not prove session isolation, tool access, or successful execution.

## Fresh exploration and continuation

Launch each branch as a new `grok -p` process in its own writable workspace.
Give every branch the same task contract and no parent transcript or reasoning
summary. Omit `--resume` and `--continue` for these fresh sessions; an optional
`--session-id` must be a new UUID. Keep session stores outside workspace snapshots.

Record the native `streaming-json` final `end.sessionId` before selecting a leader.
Resume the winner with `grok --resume <exact-session-id> -p ...` from its workspace.
Do not use `--fork-session` for a flush: it preserves the resumed conversation.
Avoid bare `--continue`, which can select a different recent session.

## Permissions and limits

Use the host's existing approval and sandbox policy. In headless runs, `--tools`
uses raw names such as `read_file` and `search_replace`; permission rules use
aliases such as `Read` and `Edit(/absolute/path/candidate.py)`. Inspect actual
tool events: missing tools or denied writes are failures, not completed branches.
Disable subagent, shell, web, MCP, and unrelated plugin capabilities when they are
not required by the experiment. Do not weaken permissions to recover a test.

An external supervisor must enforce each time limit, stop the entire process
group, wait for writes to cease, and independently evaluate immutable checkpoints.
`--max-turns` is an additional turn limit, not a time or spend cap. Sum elapsed
worker time across parallel branches and continuation; report setup, evaluation,
failed probes, and skill-decision checks separately. A POSIX process-group cap is
not a hostile-code sandbox. Record the actual model reported by the run, including
any automatic fallback from the configured model.

For isolated testing, use a dedicated `GROK_HOME` and its own plugin configuration;
do not change the user's normal configuration. Any copied login file is a secret:
keep it private, exclude it from artifacts, and remove the temporary copy afterward.

If process execution, fresh sessions, workspace isolation, cancellation, or a
measurable budget is unavailable, explain the missing capability and stop at a
plan. Loading this skill does not provide a scheduler or additional permissions.

References: [headless scripting](https://docs.x.ai/build/cli/headless-scripting),
[sessions](https://docs.x.ai/build/features/sessions),
[permissions](https://docs.x.ai/build/features/permissions), and
[plugins](https://docs.x.ai/build/features/skills-plugins-marketplaces).
