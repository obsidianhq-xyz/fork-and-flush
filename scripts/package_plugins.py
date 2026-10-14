#!/usr/bin/env python3
"""Build both plugin ZIPs from the single canonical skills directory."""

import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def build(output):
    root = Path(__file__).resolve().parents[1]
    portable = json.loads((root / "plugin.json").read_text())
    claude = json.loads((root / ".claude-plugin/plugin.json").read_text())
    if {k: v for k, v in portable.items() if k != "$schema"} != claude:
        raise ValueError("Plugin metadata must agree across both manifests")
    shared = [root / "LICENSE", root / "NOTICE.md"]
    shared += sorted(p for p in (root / "skills").rglob("*") if p.is_file()
                     and "__pycache__" not in p.parts and p.suffix != ".pyc"
                     and p.name != ".DS_Store")
    output = Path(output).resolve()
    if output == root / "skills" or root / "skills" in output.parents:
        raise ValueError("Output must be outside the canonical skills directory")
    output.mkdir(parents=True, exist_ok=True)
    report = {"version": portable["version"], "packages": {}}
    for target, manifest in (("openai", "plugin.json"), ("claude", ".claude-plugin/plugin.json")):
        archive = output / f"fork-and-flush-{target}-{portable['version']}.zip"
        files = [root / manifest, *shared]
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            for path in files:
                if path.is_symlink():
                    raise ValueError(f"Symlinks are not distributable: {path}")
                info = zipfile.ZipInfo(path.relative_to(root).as_posix(), (2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                bundle.writestr(info, path.read_bytes())
        with zipfile.ZipFile(archive) as bundle:
            assert bundle.testzip() is None
            for path in shared:
                assert bundle.read(path.relative_to(root).as_posix()) == path.read_bytes()
        report["packages"][target] = {
            "file": archive.name,
            "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
            "files": {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in files},
        }
    (output / "plugin-packages.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    print(json.dumps(build(parser.parse_args().output), indent=2))
