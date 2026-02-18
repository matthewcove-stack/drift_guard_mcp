# Codex Rules (Dev Edge Standard)

Non-negotiables:
- Do NOT add host port mappings (`ports:`) for dev web/API services.
- Dev access is via the shared edge proxy on :8080 using *.localtest.me.
- Do NOT hardcode localhost:PORT; always use DEV_BASE_URL.
- Do NOT modify production deployment files, prod compose, or ingress/tunnel config unless explicitly asked.
