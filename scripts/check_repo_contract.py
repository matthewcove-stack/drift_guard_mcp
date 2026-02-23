#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
CANONICAL_PHASE_DIR = ROOT / "docs/phases"
CANONICAL_PROMPT_DIR = ROOT / "docs/prompts"
ROOT_ALLOWED_MD = {"README.md", "AGENTS.md"}
IGNORED_DIRS = {
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "dist",
    "build",
    ".next",
    "target",
}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def is_under(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def main() -> int:
    violations: list[str] = []
    md_files = [
        p
        for p in ROOT.rglob("*.md")
        if not any(part in IGNORED_DIRS for part in p.parts)
    ]

    for path in md_files:
        path_rel = rel(path)
        in_docs = is_under(path, DOCS_DIR)
        allowed_root = path.parent == ROOT and path.name in ROOT_ALLOWED_MD
        if not in_docs and not allowed_root:
            violations.append(
                f"Markdown file outside docs/: {path_rel} "
                "(allowed root files: README.md, AGENTS.md)"
            )

        name_lower = path.name.lower()
        if "phase_" in name_lower and not is_under(path, CANONICAL_PHASE_DIR):
            violations.append(
                f"Phase doc filename must be under docs/phases: {path_rel}"
            )

        if path.name.startswith("PROMPT_") and not is_under(path, CANONICAL_PROMPT_DIR):
            violations.append(
                f"Prompt doc must be under docs/prompts: {path_rel}"
            )

    if violations:
        print("Repository documentation contract check failed:\n")
        for item in violations:
            print(f"- {item}")
        return 1

    print("Repository documentation contract check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
