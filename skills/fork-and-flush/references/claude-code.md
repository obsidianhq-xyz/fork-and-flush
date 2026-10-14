# Claude Code runtime

Documentation-based guidance. This package's v0.1.0 Claude Code execution path
has not been runtime-tested. Do not infer support from installation alone.

For each isolated branch directory, a new `claude -p` invocation can start a fresh
conversation. Pass only the task contract and branch location, not the coordinator
transcript. Example command shape:

```sh
cd "$branch_dir"
claude -p --output-format json < "$prompt_file"
```

Do not use `--continue`, `--resume`, or a history-preserving fork for flushes. To
exploit the winner, use its recorded session ID with the CLI's supported resume
option from its workspace. Check the installed CLI help for available flags.

The JSON result exposes session identity and usage/cost information. Use the host's
budget controls or an external deadline, and account for all branches. Resumed
session cost reports may be cumulative; use deltas to avoid counting earlier spend
again. Keep permissions scoped to the authorized workspace and operations.

Local instructions, skills, hooks, and memory can be loaded even for a fresh
conversation. Keep task artifacts but avoid reinjecting a parent transcript through
those channels. If using native subagents, verify their context inheritance and
working directory behavior rather than assuming every subagent is a flush.

Use the agent's supported skill installation mechanism for `SKILL.md`; omit any
Codex-only metadata. [Skills](https://code.claude.com/docs/en/skills) and
[programmatic execution](https://code.claude.com/docs/en/headless) documentation.

