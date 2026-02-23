#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COMPOSE_CANDIDATES = [
    "compose.yml",
    "compose.yaml",
    "docker-compose.yml",
    "docker-compose.yaml",
]


def fail(msg: str, errors: list[str]) -> None:
    errors.append(msg)


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def main() -> int:
    errors: list[str] = []

    exposure = ROOT / "ops" / "exposure.yml"
    if not exposure.exists():
        fail("Missing ops/exposure.yml", errors)

    env_example = ROOT / ".env.example"
    if not env_example.exists():
        fail("Missing .env.example", errors)

    compose_path = None
    for name in DEFAULT_COMPOSE_CANDIDATES:
        cand = ROOT / name
        if cand.exists():
            compose_path = cand
            break

    if compose_path is not None:
        data = load_yaml(compose_path)
        services = data.get("services", {}) if isinstance(data, dict) else {}
        for svc, cfg in services.items():
            if isinstance(cfg, dict) and cfg.get("ports"):
                fail(f"Default compose publishes host ports on service '{svc}'", errors)

        networks = data.get("networks", {}) if isinstance(data, dict) else {}
        has_lane_reference = False
        if isinstance(networks, dict):
            for _, cfg in networks.items():
                if not isinstance(cfg, dict):
                    continue
                if cfg.get("external"):
                    n = str(cfg.get("name", ""))
                    if "LAMBIC_LANE_NETWORK" in n or n in {"edge_dev", "edge_int", "edge_prod"}:
                        has_lane_reference = True
                        break
        if not has_lane_reference:
            fail("Default compose has no external lane network reference", errors)
    else:
        print("No default compose file found; compose-specific checks skipped.")

    if errors:
        print("Lambic edge contract lint failed:\n")
        for err in errors:
            print(f"- {err}")
        return 1

    print("Lambic edge contract lint passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
