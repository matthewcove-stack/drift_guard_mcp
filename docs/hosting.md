# Hosting

## Lane hostnames
- `dev`: `drift-guard-mcp.localhost`
- `integration`: `int.drift-guard-mcp.lambiclabs.com`
- `prod`: `drift-guard-mcp.lambiclabs.com`

## Exposure policy
- Any internet-reachable hostname is protected by default (Cloudflare Access preferred).
- Public exposure must be explicit and documented.

## Compose policy
- Do not publish host ports by default in the primary compose file.
- Use a dev override file for local convenience port mappings when needed.

## Lane network
- Default external lane network is `${LAMBIC_LANE_NETWORK:-edge_dev}`.
- Canonical lane network names: `edge_dev`, `edge_int`, `edge_prod`.
