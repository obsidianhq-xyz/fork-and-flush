# Obsidian Labs skills

A catalog of portable agent skills published by Obsidian Labs. Each plugin
has its own canonical skill files, version, and installable packages.

| Skill | Purpose |
| --- | --- |
| [fork-and-flush](plugins/fork-and-flush/README.md) | Explore measurable research and optimization tasks in fresh sessions and continue the best verified lineage within a fixed budget. |

## Install

Install a specific skill:

```sh
npx skills add obsidianhq-xyz/skills --skill fork-and-flush
```

List available skills without installing:

```sh
npx skills add obsidianhq-xyz/skills --list
```

For Claude Code:

```text
/plugin marketplace add obsidianhq-xyz/skills
/plugin install fork-and-flush@obsidianhq-skills
```

See [plugin installation and packaging](docs/plugins.md) for Grok Build and other
hosts. Installing a skill provides instructions; the host supplies its own tools,
permissions, and runtime capabilities.

## Development

```sh
python3 -m pip install -r requirements-dev.txt
python3 scripts/validate_catalog.py
python3 -m unittest discover -s tests -v
python3 scripts/package_plugins.py --output /absolute/path/outside-this-repo
```

Add each plugin under `plugins/<name>/`, with its manifests, README, attribution,
and `skills/<name>/SKILL.md`. Add one entry to `.claude-plugin/marketplace.json`.
Builds and validation discover the catalog; skills are maintained in one location.
Use per-plugin release tags such as `fork-and-flush-v0.1.5`. Existing `v0.1.0` and
`v0.1.1` releases remain historical fork-and-flush releases.

[MIT license](LICENSE) · [Support](SUPPORT.md) · [Privacy](PRIVACY.md)
