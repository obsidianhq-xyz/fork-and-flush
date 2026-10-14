# fork-and-flush

[![skills.sh](https://skills.sh/b/obsidianhq-xyz/skills)](https://skills.sh/obsidianhq-xyz/skills)

A portable Agent Skill for bounded research and optimization. Explore in separate
workspaces with fresh agent conversations, evaluate the candidates, and continue
the best verified lineage.

An independent skill implementation of Microsoft Research's Fork-and-Flush method,
described in [Fork-and-Flush: Escaping Idea Basins in Autoresearch
Agents](https://arxiv.org/html/2610.07447v1) by Cai et al. No affiliation with or
endorsement by Microsoft Research or the authors is implied. This package does not
claim the paper's benchmark gains.

## Install

Install from [obsidianhq-xyz/skills](https://github.com/obsidianhq-xyz/skills):

```sh
npx skills add obsidianhq-xyz/skills --skill fork-and-flush
```

Choose your agent in the installer's prompt, or specify supported targets:

```sh
npx skills add obsidianhq-xyz/skills --skill fork-and-flush \
  -a codex -a claude-code
```

For local testing from this checkout:

```sh
npx skills add . --skill fork-and-flush
```

Alternatively, copy `skills/fork-and-flush` into your host's skill directory. Keep
the references and helper script with `SKILL.md`. See the
[installer documentation](https://github.com/vercel-labs/skills) for supported hosts.

## Use

For plugin installation in OpenAI, Claude Code, or Grok Build, see [plugin packages](https://github.com/obsidianhq-xyz/skills/blob/main/docs/plugins.md).
All hosts use this same portable skill; no MCP server is required.

For Claude Code, install this plugin from the catalog:

```text
/plugin install fork-and-flush --marketplace obsidianhq-xyz/skills
```

Ask the agent to use the skill and supply a measurable task, evaluator, allowed
workspace, and budget. For example:

> Use fork-and-flush to improve the bin-packing example. Start from its incumbent,
> use two fresh branches capped at 90 seconds each, then continue the winner for
> at most 60 seconds. Score with the unchanged evaluator, preserve the original
> files, and report the winning artifact and actual resource use.

In Codex, you can explicitly invoke `$fork-and-flush`. Other hosts use their own
skill invocation syntax. The skill uses available runtime tools; installing it
does not create an agent scheduler or grant additional permissions.

Use it for competing implementations, algorithm tuning, or other scored research.
Routine edits and tasks with no meaningful evaluator are poor fits.

## How it works

1. Fix the task, evaluator, budget, and schedule.
2. Snapshot the current workspace and preserve the best verified result.
3. Start independent branches with fresh conversations and identical task contracts.
4. Evaluate candidates after the workers stop; retain a valid incumbent on failure.
5. Continue the winner's session and repeat when the schedule calls for it.

The [skill](skills/fork-and-flush/SKILL.md) contains the execution instructions.
[Method notes](skills/fork-and-flush/references/method.md) explain the reference
schedule and adaptations. The optional planner prints allocations without running
agents:

```sh
python3 skills/fork-and-flush/scripts/plan.py --budget 100 --branches 4
```

## Portability

The core follows the [Agent Skills format](https://agentskills.io/specification)
and contains no required vendor-specific frontmatter or tools. Runtime references
cover [Codex](skills/fork-and-flush/references/codex.md),
[Claude Code](skills/fork-and-flush/references/claude-code.md),
[Grok Build](skills/fork-and-flush/references/grok-build.md), and a
[common contract](skills/fork-and-flush/references/runtime-contract.md) for other hosts.

Execution requires fresh conversations, independent writable workspaces, reliable
evaluation, and externally enforced limits. Git branches and conversation resets
solve different parts of that requirement. If the host lacks a required operation,
the skill explains the gap rather than pretending to run the method.

## Development

From the repository root, Python 3.10+ is sufficient for the planner, example, and deterministic tests:

```sh
python3 -m unittest discover -s tests -v
python3 examples/bin-packing/evaluate.py examples/bin-packing/candidate.py
```

Optional format validation uses Python 3.11+ and the pinned validator in
`requirements-dev.txt`: install it in an isolated environment, then run
`skills-ref validate plugins/fork-and-flush/skills/fork-and-flush`.

Original package content is [MIT licensed](https://github.com/obsidianhq-xyz/skills/blob/main/LICENSE).
See [attribution](NOTICE.md) for the research source.

Published by Obsidian Labs. [Support](https://github.com/obsidianhq-xyz/skills/blob/main/SUPPORT.md) · [Privacy](https://github.com/obsidianhq-xyz/skills/blob/main/PRIVACY.md).

## Network and permissions

The installed skill and optional planner call no network endpoints, collect no
telemetry, and require no plugin credentials. There are no MCP servers, hooks,
agents, or install scripts. The host provides its own model connection, login,
tools, and approval policy. Experiments use only the files and actions authorized
by the user; the skill does not grant permissions. Repository acceptance tests
are opt-in developer tools and consume the tester's existing model account usage.
