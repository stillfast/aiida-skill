#!/usr/bin/env python
"""Compare versions.yaml with the latest releases on PyPI.

Used by the ``drift`` workflow and runnable locally:

    python install/07-check-upstream.py            # human report
    python install/07-check-upstream.py --json     # machine-readable
    python install/07-check-upstream.py --fail-on-drift   # exit 1 if anything moved

Exit codes: 0 = in sync, 1 = drift detected (with --fail-on-drift), 2 = error.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYPI = "https://pypi.org/pypi/{name}/json"


def latest_on_pypi(name: str) -> str | None:
    try:
        with urllib.request.urlopen(PYPI.format(name=name), timeout=20) as response:
            payload = json.load(response)
    except Exception:  # noqa: BLE001 - network problems must not crash CI
        return None
    info = payload.get("info") or {}
    return info.get("version")


def tracked_packages(versions: dict) -> dict[str, str | None]:
    packages: dict[str, str | None] = {}
    core = versions.get("aiida-core") or {}
    packages["aiida-core"] = core.get("latest_known") or core.get("supported")
    for name, spec in (versions.get("plugins") or {}).items():
        packages[name] = spec.get("latest_known") or spec.get("supported")
    return packages


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-on-drift", action="store_true")
    parser.add_argument("--versions", default=str(REPO_ROOT / "versions.yaml"))
    args = parser.parse_args()

    try:
        import yaml
    except ImportError:
        print("PyYAML is required", file=sys.stderr)
        return 2
    with open(args.versions) as handle:
        versions = yaml.safe_load(handle) or {}

    try:
        from packaging.version import Version
    except ImportError:  # pragma: no cover
        Version = None

    drift = []
    for name, pinned in tracked_packages(versions).items():
        latest = latest_on_pypi(name)
        state = "unknown"
        if latest is not None and pinned is not None:
            if Version is None:
                state = "drift" if latest != pinned else "ok"
            else:
                state = ("drift" if Version(latest) > Version(pinned)
                         else "ahead" if Version(latest) < Version(pinned) else "ok")
        drift.append({"package": name, "pinned": pinned, "pypi": latest, "state": state})

    if args.json:
        print(json.dumps(drift, indent=2))
    else:
        for row in drift:
            flag = {"drift": "DRIFT", "ahead": "ahead", "ok": "ok   "}.get(row["state"], "?    ")
            print(f"[{flag}] {row['package']:<26} pinned={row['pinned']} pypi={row['pypi']}")

    if args.fail_on_drift and any(row["state"] == "drift" for row in drift):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
