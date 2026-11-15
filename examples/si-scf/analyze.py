#!/usr/bin/env python
"""Read one finished calculation: status, energy, volume, SCF steps.

    python analyze.py <pk>
    python analyze.py <pk> --json
"""
from __future__ import annotations

import argparse
import json
import re
import sys


def summarize(pk: int) -> dict:
    import aiida
    from aiida.orm import load_node

    aiida.load_profile()
    node = load_node(pk)

    out = {
        "pk": node.pk,
        "uuid": str(node.uuid),
        "state": node.process_state.value,
        "exit_status": node.exit_status,
        "exit_message": node.exit_message,
    }

    # energy / structure, when the process produced them
    try:
        out["total_energy_ev"] = node.outputs.misc.get_dict().get("total_energy")
    except Exception:  # noqa: BLE001
        out["total_energy_ev"] = None
    try:
        structure = node.outputs.structure
        out["volume_A3"] = structure.get_cell_volume()
        out["formula"] = structure.get_formula()
    except Exception:  # noqa: BLE001
        pass

    # SCF iteration count from the retrieved log
    try:
        log = node.outputs.retrieved.get_object_content("OUT.aiida/running_scf.log")
        steps = re.findall(r"^\s*(?:GE|CG|DA)\s*\d+", log, re.M)
        out["scf_steps"] = len(steps)
    except Exception:  # noqa: BLE001
        pass
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pk", type=int)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = summarize(args.pk)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for key, value in result.items():
            print(f"{key:>16}: {value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
