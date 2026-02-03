# Running Drift Guard MCP in Docker (OS-independent)

This MCP server uses **stdio transport**. VS Code (or any MCP client) must be able to
spawn the server and pipe stdin/stdout.

## Build the image
From this folder:

```bash
docker build -t drift-guard-mcp:local .
```

(Optional) via compose:
```bash
docker compose build
```

## How VS Code should run it (recommended)

In the **repo you want to guard**, create `.vscode/mcp.json` like this (example):

```json
{
  "servers": {
    "drift-guard": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-v",
        "${workspaceFolder}:/workspace",
        "-w",
        "/workspace",
        "drift-guard-mcp:local"
      ]
    }
  }
}
```

Notes:
- `-i` keeps stdin open (required for stdio MCP).
- The workspace is mounted at `/workspace` and set as working directory so drift checks run against the repo.
- This is OS-independent (Windows/macOS/Linux) as long as Docker Desktop is installed.

## Quick manual smoke test
You can sanity-check the container starts:

```bash
docker run --rm -i drift-guard-mcp:local
```

It will wait for MCP messages on stdin (so it may appear to “hang” — that’s expected).
