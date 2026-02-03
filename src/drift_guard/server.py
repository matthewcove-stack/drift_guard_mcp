from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from mcp.server.fastmcp import FastMCP


mcp = FastMCP("Drift Guard")


# -------------------------
# Helpers
# -------------------------

def _repo_root() -> Path:
    # Prefer VS Code workspace cwd; otherwise current working dir
    return Path(os.getcwd()).resolve()

def _load_contract(repo: Path) -> Dict[str, Any]:
    contract_path = repo / "docs" / "v2_contract.json"
    if contract_path.exists():
        return json.loads(contract_path.read_text(encoding="utf-8"))
    # Fallback to embedded default
    return {
        "required_files": [
            "AGENTS.md",
            "docs/intent.md",
            "docs/current_state.md",
            "docs/phases.md",
            "docs/phase_execution_prompt.md",
        ],
        "authoritative": "docs/current_state.md",
    }

def _run(cmd: List[str], repo: Path, timeout_s: int = 120) -> Tuple[int, str, str]:
    p = subprocess.run(
        cmd,
        cwd=str(repo),
        capture_output=True,
        text=True,
        timeout=timeout_s,
    )
    return p.returncode, p.stdout, p.stderr

def _is_git_repo(repo: Path) -> bool:
    return (repo / ".git").exists()

def _git_changed_files(repo: Path) -> List[str]:
    if not _is_git_repo(repo):
        return []
    # include staged + unstaged changes
    code, out, err = _run(["git", "diff", "--name-only"], repo)
    if code != 0:
        return []
    unstaged = [x.strip() for x in out.splitlines() if x.strip()]
    code, out, err = _run(["git", "diff", "--name-only", "--staged"], repo)
    staged = [x.strip() for x in out.splitlines() if x.strip()] if code == 0 else []
    return sorted(set(unstaged + staged))

def _looks_like_code_file(path: str) -> bool:
    # Treat docs/ + markdown as non-code by default
    if path.startswith("docs/"):
        return False
    if path.endswith(".md") or path.endswith(".txt") or path.endswith(".rst"):
        return False
    return True

def _parse_verification_commands(agents_md: Path) -> List[str]:
    if not agents_md.exists():
        return []
    text = agents_md.read_text(encoding="utf-8", errors="ignore")

    # Very small convention:
    # In AGENTS.md, under a heading "## Verification Commands", list commands as bullet points or fenced code.
    section_re = re.compile(r"^##\s+Verification Commands\s*$", re.MULTILINE)
    m = section_re.search(text)
    if not m:
        return []

    tail = text[m.end():]
    # stop at next "## " heading
    stop = re.search(r"^##\s+", tail, re.MULTILINE)
    section = tail[: stop.start()] if stop else tail

    cmds: List[str] = []

    # bullets like "- pytest"
    for line in section.splitlines():
        line = line.strip()
        if line.startswith("- "):
            cmds.append(line[2:].strip())
    # fenced code blocks (take lines inside)
    for block in re.findall(r"```(?:bash|sh)?\n(.*?)\n```", section, flags=re.DOTALL):
        for line in block.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                cmds.append(line)

    # de-dupe while preserving order
    seen = set()
    out: List[str] = []
    for c in cmds:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


# -------------------------
# Tools
# -------------------------

@mcp.tool()
def repo_contract_validate() -> Dict[str, Any]:
    """Validate the Matthew Cove AI-First Engineering v2 repo contract."""
    repo = _repo_root()
    contract = _load_contract(repo)
    required = contract.get("required_files", [])
    missing = [p for p in required if not (repo / p).exists()]

    ok = len(missing) == 0
    return {
        "ok": ok,
        "repo_root": str(repo),
        "missing": missing,
        "required_files": required,
        "authoritative": contract.get("authoritative", "docs/current_state.md"),
    }

@mcp.tool()
def drift_check() -> Dict[str, Any]:
    """Run deterministic drift checks (minimal but high-signal)."""
    repo = _repo_root()
    changed = _git_changed_files(repo)

    # Rule 1: If any code-like files changed, docs/current_state.md must change too.
    code_changed = [p for p in changed if _looks_like_code_file(p)]
    current_state_path = "docs/current_state.md"
    current_state_changed = current_state_path in changed

    failures: List[Dict[str, Any]] = []

    if code_changed and not current_state_changed:
        failures.append({
            "rule": "current_state_updated",
            "message": "Code changed but docs/current_state.md was not updated (drift).",
            "evidence": {"code_changed_files": code_changed[:50], "count": len(code_changed)},
        })

    # Rule 2: Required repo contract must hold (fast-fail)
    contract_res = repo_contract_validate()
    if not contract_res.get("ok"):
        failures.append({
            "rule": "repo_contract",
            "message": "Repo contract is not satisfied (missing required files).",
            "evidence": {"missing": contract_res.get("missing", [])},
        })

    # Rule 3 (optional minimal): if docs/intent.md changed, current_state should usually change too.
    if "docs/intent.md" in changed and not current_state_changed:
        failures.append({
            "rule": "intent_requires_current_state_alignment",
            "message": "docs/intent.md changed but docs/current_state.md did not. Verify alignment (potential drift).",
            "evidence": {},
        })

    ok = len(failures) == 0
    return {
        "ok": ok,
        "repo_root": str(repo),
        "changed_files": changed,
        "failures": failures,
    }

@mcp.tool()
def verify_run(profile: str = "default") -> Dict[str, Any]:
    """Run verification commands parsed from AGENTS.md (best-effort)."""
    repo = _repo_root()
    agents_md = repo / "AGENTS.md"
    cmds = _parse_verification_commands(agents_md)

    results: List[Dict[str, Any]] = []

    if not cmds:
        return {
            "ok": False,
            "repo_root": str(repo),
            "profile": profile,
            "commands": [],
            "results": [],
            "message": "No verification commands found in AGENTS.md under '## Verification Commands'.",
        }

    ok = True
    for cmd in cmds:
        # Run in shell to support compound commands; keep timeouts modest
        try:
            p = subprocess.run(
                cmd,
                cwd=str(repo),
                shell=True,
                capture_output=True,
                text=True,
                timeout=600,
            )
            res = {
                "command": cmd,
                "exit_code": p.returncode,
                "stdout": p.stdout[-8000:],  # tail for safety
                "stderr": p.stderr[-8000:],
            }
            results.append(res)
            if p.returncode != 0:
                ok = False
        except Exception as e:
            ok = False
            results.append({
                "command": cmd,
                "exit_code": None,
                "stdout": "",
                "stderr": f"{type(e).__name__}: {e}",
            })

    return {
        "ok": ok,
        "repo_root": str(repo),
        "profile": profile,
        "commands": cmds,
        "results": results,
    }


def main() -> None:
    # stdio transport is what VS Code expects for local servers
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
