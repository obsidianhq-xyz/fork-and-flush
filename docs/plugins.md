# Plugin installation and packaging

Obsidian Labs publishes each plugin from its own folder under `plugins/<name>/`.
Fork-and-flush lives in `plugins/fork-and-flush/`; its OpenAI and Claude manifests
use the same canonical skill directory. Plugin version 0.1.5 packages skill
version 0.1.2.

## Agent Skills installation

```sh
npx skills add obsidianhq-xyz/skills --skill fork-and-flush
```

Select your host in the installer, or use `-a codex -a claude-code`.

## Claude Code

```text
/plugin marketplace add obsidianhq-xyz/skills
/plugin install fork-and-flush@obsidianhq-skills
```

For a local session, load only the selected plugin folder:

```sh
claude --plugin-dir /absolute/path/to/skills/plugins/fork-and-flush
```

Invoke `/fork-and-flush:fork-and-flush` with your task, evaluator, permitted
workspace, and explicit budget.

## Grok Build

Install the selected plugin subdirectory:

```sh
grok plugin install https://github.com/obsidianhq-xyz/skills.git#plugins/fork-and-flush
```

Ask Grok to use fork-and-flush and supply the task, evaluator, workspace, and
budget. See the [Grok runtime guide](../plugins/fork-and-flush/skills/fork-and-flush/references/grok-build.md).

## OpenAI plugin package

The OpenAI ZIP uses the root Agent Plugins 1.0 manifest described in the
[packaging guide](https://developers.openai.com/plugins/build/plugins).
Publisher verification, directory review, and publication are separate from
repository installation. See the [submission guide](https://developers.openai.com/plugins/deploy/submission).

## Build packages

From the repository root, build all plugins or select one:

```sh
python3 scripts/package_plugins.py --output /absolute/path/outside-this-repo
python3 scripts/package_plugins.py --plugin fork-and-flush --output /absolute/path/outside-this-repo
```

The builder emits one OpenAI ZIP and one Claude ZIP per plugin, plus a JSON
manifest with archive and file SHA-256 hashes. Packages include the selected
plugin's skill files, README, manifests, license, attribution, and publisher policy
pages. Development tests and experiment logs are excluded.

## Runtime requirements

Fork-and-flush requires fresh conversations, separate writable workspaces, a fixed
evaluator, and externally enforced limits. Installation provides instructions and
a schedule planner; the host supplies execution tools and permissions. The skill
explains missing capabilities when the host cannot execute the workflow.
