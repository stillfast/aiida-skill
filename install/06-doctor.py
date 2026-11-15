#!/usr/bin/env python
"""Environment doctor for the aiida-skill repository.

Checks the pieces that every AiiDA failure story starts with: the installed
versions (against ``versions.yaml``), the profile, the daemon, the computers,
the codes and the pseudopotential families.

Usage
-----
    python install/06-doctor.py            # human-readable report
    python install/06-doctor.py --json     # machine-readable
    python install/06-doctor.py --strict   # exit 1 unless everything is in
                                           # the supported version window

Exit codes: 0 = ok, 1 = problems found, 2 = environment outside versions.yaml.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from importlib import metadata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OK, WARN, FAIL, INFO = "ok", "warn", "fail", "info"


def _dist_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def _major_minor(version: str) -> tuple[int, int]:
    parts = version.split(".")
    digits = []
    for part in parts[:2]:
        num = ""
        for char in part:
            if char.isdigit():
                num += char
            else:
                break
        digits.append(int(num or 0))
    return digits[0], digits[1]


def _classify(installed: str, minimum: str, supported: str) -> str:
    """supported / newer-than-tested / unsupported."""
    if installed is None:
        return "missing"
    if _major_minor(installed) < _major_minor(minimum):
        return "unsupported"
    if _major_minor(installed) > _major_minor(supported):
        return "newer-than-tested"
    return "supported"


def load_versions(path: Path) -> dict:
    try:
        import yaml
    except ImportError:  # pragma: no cover - yaml ships with aiida-core
        return {}
    with path.open() as handle:
        return yaml.safe_load(handle) or {}


class Report:
    def __init__(self) -> None:
        self.rows: list[dict] = []
        self.unsupported = False

    def add(self, section: str, name: str, status: str, detail: str = "") -> None:
        self.rows.append(
            {"section": section, "name": name, "status": status, "detail": detail}
        )
        if status == "unsupported":
            self.unsupported = True

    def worst(self) -> str:
        order = [FAIL, "unsupported", WARN, INFO, OK]
        for status in order:
            if any(row["status"] == status for row in self.rows):
                return status
        return OK

    def as_dict(self) -> dict:
        return {"worst": self.worst(), "rows": self.rows}


def check_versions(report: Report, versions: dict) -> None:
    version = versions.get("aiida-core", {})
    installed = _dist_version("aiida-core")
    status = _classify(installed, version.get("minimum", "0"), version.get("supported", "0"))
    report.add("version", "aiida-core", status, f"installed={installed} supported={version.get('supported')}")

    for name, spec in (versions.get("plugins") or {}).items():
        installed = _dist_version(name)
        if installed is None:
            report.add("version", name, INFO, "not installed")
            continue
        status = _classify(installed, spec.get("minimum", "0"), spec.get("supported", "0"))
        report.add("version", name, status, f"installed={installed} supported={spec.get('supported')}")


def check_environment(report: Report) -> None:
    try:
        import aiida
    except ImportError:
        report.add("environment", "aiida-core import", FAIL, "cannot import aiida")
        return

    profile = os.environ.get("AIIDA_PROFILE") or os.environ.get("AIIDA_PROFILE_NAME")
    try:
        aiida.load_profile(profile)
    except Exception as exc:  # noqa: BLE001
        report.add("environment", "profile", FAIL, f"cannot load profile: {exc}")
        return

    from aiida.manage import get_manager

    current = get_manager().get_profile()
    report.add("environment", "profile", OK, current.name)

    try:
        from aiida.engine.daemon.client import get_daemon_client

        running = get_daemon_client().is_daemon_running
        report.add("environment", "daemon", OK if running else FAIL,
                   "running" if running else "NOT running: verdi daemon start")
    except Exception as exc:  # noqa: BLE001
        report.add("environment", "daemon", WARN, f"cannot determine: {exc}")


def check_computers_and_codes(report: Report) -> None:
    try:
        from aiida import orm
    except ImportError:
        return

    try:
        computers = list(orm.Computer.collection.all())
    except Exception as exc:  # noqa: BLE001
        report.add("computers", "query", FAIL, str(exc))
        return
    if not computers:
        report.add("computers", "any", FAIL, "no computer configured")
    for computer in computers:
        report.add(
            "computers", computer.label, INFO,
            f"{computer.scheduler_type} {computer.hostname}",
        )

    try:
        codes = list(orm.InstalledCode.collection.all())
    except Exception as exc:  # noqa: BLE001
        report.add("codes", "query", FAIL, str(exc))
        return
    if not codes:
        report.add("codes", "any", FAIL, "no code configured")
    for code in codes:
        computer_label = code.computer.label
        report.add(
            "codes", code.label, INFO,
            f"{code.default_calc_job_plugin} @ {computer_label}",
        )


def check_pseudos(report: Report) -> None:
    try:
        from aiida import orm

        query = orm.QueryBuilder()
        query.append(
            orm.Group,
            filters={"type_string": {"like": "pseudo.family%"}},
            project=["label"],
        )
        families = query.all(flat=True)
    except Exception as exc:  # noqa: BLE001
        report.add("pseudos", "query", WARN, f"cannot list families: {exc}")
        return
    if not families:
        report.add("pseudos", "any", WARN, "no pseudopotential family installed")
    for family in families:
        report.add("pseudos", family, INFO, "")


def print_human(report: Report) -> None:
    icons = {OK: "[ok]  ", WARN: "[warn]", FAIL: "[FAIL]", INFO: "[info]",
             "supported": "[ok]  ", "newer-than-tested": "[warn]",
             "unsupported": "[FAIL]", "missing": "[FAIL]"}
    section = None
    for row in report.rows:
        if row["section"] != section:
            section = row["section"]
            print(f"\n== {section} ==")
        print(f"  {icons.get(row['status'], '[?]   ')} {row['name']:<34} {row['detail']}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--strict", action="store_true",
                        help="exit 2 if the environment is outside versions.yaml")
    parser.add_argument("--versions", default=str(REPO_ROOT / "versions.yaml"))
    args = parser.parse_args()

    report = Report()
    versions = load_versions(Path(args.versions))
    if not versions:
        report.add("version", "versions.yaml", WARN, f"missing or empty: {args.versions}")
    else:
        check_versions(report, versions)
    check_environment(report)
    check_computers_and_codes(report)
    check_pseudos(report)

    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
    else:
        print_human(report)

    if report.unsupported and args.strict:
        return 2
    if report.worst() in (FAIL, "unsupported"):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
