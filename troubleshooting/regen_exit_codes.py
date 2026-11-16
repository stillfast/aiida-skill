#!/usr/bin/env python
"""Regenerate ``exit-codes.md`` from the installed plugin sources.

The *numbers, names and messages* are extracted from the plugin classes, so
they never go stale; the human-written "typical cause / fix" text lives in
``exit-codes.notes.yaml`` and is merged in by code.

    python troubleshooting/regen_exit_codes.py           # rewrite exit-codes.md
    python troubleshooting/regen_exit_codes.py --check   # exit 1 if out of date
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "exit-codes.md"
NOTES = HERE / "exit-codes.notes.yaml"

#: entry points rendered in the table, in this order
CLASSES = [
    ("abacus.abacus", "aiida.calculations", "ABACUS CalcJob"),
    ("abacus.base", "aiida.workflows", "ABACUS base WorkChain"),
    ("abacus.relax", "aiida.workflows", "ABACUS relax WorkChain"),
    ("abacus.band", "aiida.workflows", "ABACUS band WorkChain"),
    ("vasp.vasp", "aiida.calculations", "VASP CalcJob"),
    ("vasp.v2.vasp", "aiida.workflows", "VASP v2 WorkChain"),
    ("vasp.v2.relax", "aiida.workflows", "VASP v2 relax WorkChain"),
]

HEADER = """---
generated: true
generated_by: troubleshooting/regen_exit_codes.py
---

# Exit-code reference

> The "code / name / message" columns are generated from the installed plugin
> sources; the "typical cause / fix" column comes from the hand-written
> `exit-codes.notes.yaml`. Re-run `python troubleshooting/regen_exit_codes.py`
> after upgrading a plugin.

Read the exit code together with `verdi process show <pk>`: the same number means
different things in different plugins (e.g. 700 in the VASP CalcJob vs the VASP
WorkChain), and a WorkChain exit code usually just points at a failed child.
"""


def collect() -> dict[str, list[dict]]:
    from aiida.plugins import CalculationFactory, WorkflowFactory

    rows: dict[str, list[dict]] = {}
    for entry_point, group, title in CLASSES:
        factory = CalculationFactory if group == "aiida.calculations" else WorkflowFactory
        try:
            cls = factory(entry_point)
        except Exception as exc:  # noqa: BLE001 - plugin not installed
            rows[title] = [{"code": "—", "name": "not installed", "message": str(exc)}]
            continue
        spec = cls.spec()
        codes = getattr(spec, "exit_codes", {}) or {}
        entries = []
        for name, exit_code in sorted(codes.items(), key=lambda item: int(item[1].status)):
            entries.append(
                {
                    "code": str(exit_code.status),
                    "name": name,
                    "message": (exit_code.message or "").strip().split("\n")[0],
                }
            )
        rows[title] = entries
    return rows


def load_notes() -> dict:
    try:
        import yaml
    except ImportError:  # pragma: no cover
        return {}
    if not NOTES.exists():
        return {}
    with NOTES.open() as handle:
        return yaml.safe_load(handle) or {}


def render(rows: dict[str, list[dict]], notes: dict) -> str:
    lines = [HEADER]
    for title, entries in rows.items():
        lines.append(f"\n## {title}\n")
        lines.append("| code | name | message | typical cause / fix |")
        lines.append("| --- | --- | --- | --- |")
        for entry in entries:
            note = (notes.get(title) or {}).get(entry["code"]) or {}
            cause = note.get("cause", "")
            fix = note.get("fix", "")
            cell = "；".join(part for part in (cause, fix) if part) or "—"
            lines.append(
                f"| {entry['code']} | `{entry['name']}` | {entry['message']} | {cell} |"
            )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="do not write; exit 1 if the file is out of date")
    args = parser.parse_args()

    try:
        import aiida

        aiida.load_profile()
    except Exception:  # noqa: BLE001 - exit codes do not need a profile
        pass

    rendered = render(collect(), load_notes())
    if args.check:
        current = OUTPUT.read_text() if OUTPUT.exists() else ""
        if current.strip() != rendered.strip():
            print(f"{OUTPUT} is out of date; run python troubleshooting/regen_exit_codes.py")
            return 1
        return 0
    OUTPUT.write_text(rendered)
    print(f"wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
