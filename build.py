#!/usr/bin/env python3
"""Minimal reproducible builder for the Focus Break Timer NVDA add-on."""
from __future__ import annotations

from pathlib import Path
import re
import shutil
import zipfile

ROOT = Path(__file__).resolve().parent
ADDON = ROOT / "addon"
DIST = ROOT / "dist"


def manifest_value(name: str) -> str:
    text = (ADDON / "manifest.ini").read_text(encoding="utf-8")
    match = re.search(rf"^{re.escape(name)}\s*=\s*(?:\"([^\"]*)\"|([^\r\n]+))\s*$", text, re.M)
    if not match:
        raise RuntimeError(f"Missing manifest value: {name}")
    return (match.group(1) or match.group(2)).strip()


def build() -> Path:
    version = manifest_value("version")
    name = manifest_value("name")
    DIST.mkdir(exist_ok=True)
    output = DIST / f"{name}-{version}.nvda-addon"
    if output.exists():
        output.unlink()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(ADDON.rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
                continue
            archive.write(path, path.relative_to(ADDON).as_posix())
    return output


if __name__ == "__main__":
    print(build())
