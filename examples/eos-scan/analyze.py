#!/usr/bin/env python
"""Layer 2 (scripts): read a finished EOS WorkChain and fit it.

    python analyze.py <pk>              # Birch-Murnaghan fit + table
    python analyze.py <pk> --json out.json
    python analyze.py <pk> --csv out.csv

Reads only outputs (never touches the database internals), so it works on any
``common_workflows.eos`` node regardless of the backend that produced it.
"""
from __future__ import annotations

import argparse
import json
import math
import sys


def read_eos(pk: int) -> dict:
    import aiida
    from aiida.orm import load_node

    aiida.load_profile()
    node = load_node(pk)

    # The EOS WorkChain exposes `structures` and `total_energies` as nested
    # output namespaces keyed by the same index (see `aiida-common-workflows
    # plot eos <pk>`).
    from aiida.common.links import LinkType

    outputs = node.base.links.get_outgoing(link_type=LinkType.RETURN).nested()
    volumes, energies = [], []
    for index, structure in sorted(outputs["structures"].items()):
        volumes.append(structure.get_cell_volume())
        energies.append(float(outputs["total_energies"][index].value))

    # Sort by volume (the EOS workchain output order is not guaranteed).
    pairs = sorted(zip(volumes, energies))
    volumes = [volume for volume, _ in pairs]
    energies = [energy for _, energy in pairs]
    return {"pk": node.pk, "count": len(energies), "volumes": volumes,
            "energies": energies}


def birch_murnaghan(volume, e0, v0, b0, b_prime):
    eta = (v0 / volume) ** (2 / 3)
    return e0 + 9 * v0 * b0 / 16 * (
        (eta - 1) ** 3 * b_prime + (eta - 1) ** 2 * (6 - 4 * eta)
    )


def fit(volumes, energies) -> dict | None:
    try:
        from scipy.optimize import curve_fit
    except ImportError:
        return None
    try:
        params, covariance = curve_fit(
            birch_murnaghan, volumes, energies,
            p0=[min(energies), volumes[energies.index(min(energies))], 0.5, 4.0],
        )
    except Exception as exc:  # noqa: BLE001 - poor scan range / too few points
        return {"error": str(exc)}
    errors = [math.sqrt(covariance[i][i]) for i in range(4)]
    return {"e0_ev": params[0], "v0_a3": params[1], "b0_ev_a3": params[2],
            "b_prime": params[3], "errors": errors,
            "b0_gpa": params[2] * 160.2176634}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pk", type=int)
    parser.add_argument("--json", default=None, help="write the data + fit here")
    parser.add_argument("--csv", default=None, help="write volume,energy here")
    args = parser.parse_args()

    data = read_eos(args.pk)
    if not data["count"]:
        print(f"node {args.pk} has no EOS outputs yet (still running?)",
              file=sys.stderr)
        return 1

    data["fit"] = fit(data["volumes"], data["energies"])

    print(f"pk={data['pk']}  points={data['count']}")
    for volume, energy in zip(data["volumes"], data["energies"]):
        print(f"  V={volume:10.3f} A^3   E={energy:.6f} eV")
    if data["fit"] is None:
        print("\n(scipy not available: no fit)")
    elif "error" in data["fit"]:
        print(f"\nfit failed: {data['fit']['error']}")
    else:
        result = data["fit"]
        print(f"\nBirch-Murnaghan: V0={result['v0_a3']:.3f} A^3  "
              f"B0={result['b0_gpa']:.1f} GPa  B'={result['b_prime']:.2f}  "
              f"E0={result['e0_ev']:.6f} eV")

    if args.json:
        with open(args.json, "w") as handle:
            json.dump(data, handle, indent=2)
        print(f"wrote {args.json}")
    if args.csv:
        with open(args.csv, "w") as handle:
            handle.write("volume,energy\n")
            for volume, energy in zip(data["volumes"], data["energies"]):
                handle.write(f"{volume},{energy}\n")
        print(f"wrote {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
