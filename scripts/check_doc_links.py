#!/usr/bin/env python3
"""Check local Markdown links in README/CONTRIBUTING files."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
REF_PATTERN = re.compile(r"^\[([^\]]+)\]:\s*(\S+)")
EXTERNAL_PREFIXES = (
    "http://",
    "https://",
    "mailto:",
    "tel:",
    "ftp://",
    "ftps://",
    "data:",
)


def extract_targets(text: str) -> list[str]:
    targets: list[str] = []
    for match in LINK_PATTERN.finditer(text):
        raw = match.group(1).strip()
        targets.append(raw)
    for line in text.splitlines():
        ref_match = REF_PATTERN.match(line.strip())
        if ref_match:
            targets.append(ref_match.group(2).strip())
    return targets


def normalize_target(raw: str) -> str:
    target = raw.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    if " " in target:
        target = target.split(" ", 1)[0]
    return target


def is_external(target: str) -> bool:
    lower = target.lower()
    return lower.startswith(EXTERNAL_PREFIXES)


def resolve_target(base_dir: Path, repo_root: Path, target: str) -> Path | None:
    if target.startswith("#"):
        return None
    path_part = target.split("#", 1)[0]
    if not path_part:
        return None
    if path_part.startswith("/"):
        return repo_root / path_part.lstrip("/")
    return base_dir / path_part


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate local Markdown links.")
    parser.add_argument(
        "files",
        nargs="*",
        default=["README.md", "CONTRIBUTING.md"],
        help="Markdown files to check.",
    )
    parser.add_argument(
        "--root",
        default=Path.cwd(),
        type=Path,
        help="Repository root used for absolute paths.",
    )
    args = parser.parse_args()

    repo_root = args.root.resolve()
    failures: list[str] = []

    for file_name in args.files:
        file_path = Path(file_name)
        if not file_path.exists():
            failures.append(f"Missing file: {file_name}")
            continue
        text = file_path.read_text(encoding="utf-8")
        base_dir = file_path.parent.resolve()
        for raw_target in extract_targets(text):
            target = normalize_target(raw_target)
            if not target or is_external(target):
                continue
            resolved = resolve_target(base_dir, repo_root, target)
            if resolved is None:
                continue
            if not resolved.exists():
                failures.append(f"{file_name}: '{target}' not found at {resolved}")

    if failures:
        print("Broken documentation links detected:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Documentation links look good.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
