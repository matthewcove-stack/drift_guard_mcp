# Drift Guard MCP (Python)

A minimal MCP server that exposes 3 tools to your agent (Codex/VS Code):

- `repo.contract_validate()` — verifies required repo files exist (Matthew Cove AI-First Engineering v2 contract)
- `drift.check()` — deterministic drift checks (e.g., code changed but `docs/current_state.md` not updated)
- `verify.run(profile="default")` — runs verification commands (parsed from `AGENTS.md`)

## Install (recommended: uv)
```bash
uv venv
uv pip install -e ".[dev]"  # or: uv pip install -e .
```

Or with pip:
```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

## Run (stdio transport for VS Code)
```bash
drift-guard-mcp
```

## VS Code MCP config (example)
Create (or edit) `.vscode/mcp.json` in the repo you want to guard:

```json
{
  "servers": {
    "drift-guard": {
      "command": "drift-guard-mcp",
      "args": []
    }
  }
}
```

VS Code docs on MCP server config: see Microsoft's "Use MCP servers in VS Code".

## Docker (OS-independent)
See `README_DOCKER.md` for running this MCP server via Docker so your setup is independent of host OS.
