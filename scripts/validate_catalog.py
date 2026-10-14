#!/usr/bin/env python3
"""Validate every catalog skill and build all plugin packages in a temporary directory."""

import subprocess
import tempfile

from package_plugins import build_catalog, plugins


def main():
    names = set()
    catalog = plugins()
    for plugin in catalog.values():
        for skill in sorted((plugin / "skills").glob("*/SKILL.md")):
            if skill.parent.name in names:
                raise ValueError(f"Duplicate skill name: {skill.parent.name}")
            names.add(skill.parent.name)
            subprocess.run(["skills-ref", "validate", str(skill.parent)], check=True)
    with tempfile.TemporaryDirectory() as output:
        build_catalog(output)
    print(f"Catalog valid: {len(catalog)} plugins, {len(names)} skills")


if __name__ == "__main__":
    main()
