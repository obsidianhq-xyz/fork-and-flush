#!/usr/bin/env python3
"""Build independent plugin ZIPs from the catalog's canonical plugin folders."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def plugins(root=ROOT):
    catalog = json.loads((root / ".claude-plugin/marketplace.json").read_text())
    found = {}
    for entry in catalog["plugins"]:
        name = entry["name"]
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
            raise ValueError(f"Invalid plugin name: {name}")
        path = root / "plugins" / name
        if name in found or entry["source"] != f"./plugins/{name}":
            raise ValueError(f"Invalid or duplicate catalog entry: {name}")
        if path.is_symlink() or not path.is_dir():
            raise ValueError(f"Missing canonical plugin directory: {name}")
        found[name] = path
    actual = {p.name for p in (root / "plugins").iterdir() if p.is_dir()}
    if not found or actual != set(found):
        raise ValueError("Catalog must list every plugin directory exactly once")
    return found


def build(output, name="fork-and-flush", root=ROOT):
    plugin = plugins(root)[name]
    portable = json.loads((plugin / "plugin.json").read_text())
    claude = json.loads((plugin / ".claude-plugin/plugin.json").read_text())
    if portable["name"] != name:
        raise ValueError("Plugin name must match its catalog entry and directory")
    if {k: v for k, v in portable.items() if k not in ("$schema", "extensions")} != claude:
        raise ValueError("Plugin metadata must agree across both manifests")
    shared = {p: (plugin / p if (plugin / p).is_file() else root / p)
              for p in ("LICENSE", "NOTICE.md", "PRIVACY.md", "SUPPORT.md", "README.md")}
    shared.update({p.relative_to(plugin).as_posix(): p
                   for p in sorted((plugin / "skills").rglob("*")) if p.is_file()
                   and "__pycache__" not in p.parts and p.suffix != ".pyc"
                   and p.name != ".DS_Store"})
    if not any(p.endswith("/SKILL.md") for p in shared):
        raise ValueError(f"Plugin has no skills: {name}")
    output = Path(output).resolve()
    if output == root or root in output.parents:
        raise ValueError("Output must be outside the source repository")
    output.mkdir(parents=True, exist_ok=True)
    report = {"name": name, "version": portable["version"], "packages": {}}
    for target, manifest in (("openai", "plugin.json"), ("claude", ".claude-plugin/plugin.json")):
        archive = output / f"{name}-{target}-{portable['version']}.zip"
        files = {manifest: plugin / manifest, **shared}
        if target == "openai":
            files.update({p.relative_to(plugin).as_posix(): p
                          for p in sorted((plugin / "assets").rglob("*")) if p.is_file()})
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            for relative, path in files.items():
                if path.is_symlink():
                    raise ValueError(f"Symlinks are not distributable: {path}")
                info = zipfile.ZipInfo(relative, (2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                bundle.writestr(info, path.read_bytes())
        with zipfile.ZipFile(archive) as bundle:
            assert bundle.testzip() is None
            for relative, path in files.items():
                assert bundle.read(relative) == path.read_bytes()
        report["packages"][target] = {
            "file": archive.name,
            "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
            "files": {relative: hashlib.sha256(path.read_bytes()).hexdigest()
                      for relative, path in files.items()},
        }
    return report


def build_catalog(output, names=None, root=ROOT):
    selected = list(plugins(root)) if names is None else names
    report = {"plugins": {name: build(output, name, root) for name in selected}}
    (Path(output) / "plugin-packages.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--plugin", action="append", help="Build selected plugins; default: all")
    args = parser.parse_args()
    print(json.dumps(build_catalog(args.output, args.plugin), indent=2))
