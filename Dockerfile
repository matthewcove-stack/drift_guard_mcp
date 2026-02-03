# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Keep Python output unbuffered so MCP stdio behaves nicely
ENV PYTHONUNBUFFERED=1         PIP_DISABLE_PIP_VERSION_CHECK=1         PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install the package (editable install not needed inside container)
COPY pyproject.toml README.md /app/
COPY src /app/src
COPY docs /app/docs

# Install using pip (simple + compatible). If you prefer uv, swap this.
RUN pip install --upgrade pip && pip install .

# MCP runs over stdio; VS Code will pipe stdin/stdout to this container
ENTRYPOINT ["drift-guard-mcp"]
