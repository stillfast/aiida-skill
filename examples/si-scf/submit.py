#!/usr/bin/env python
"""Minimal AiiDA submission: one ABACUS SCF for diamond Si.

The point of this example is the *workflow layer*: build a builder from the
plugin, validate it, print the scheduler options that will actually be used,
and only then submit.

    python submit.py --dry-run                 # build + validate, do not submit
    python submit.py --submit --queue q_ysuan  # submit and print the pk
    python submit.py --submit --protocol fast  # use the plugin protocol instead

It needs a configured ``abacus`` code, e.g. ``abacus_lts@yeesuan``.
"""
from __future__ import annotations

import argparse
import sys

from ase.build import bulk


def build(code_label: str, protocol: str | None, queue: str | None,
          wallclock: int, mpiprocs: int, pseudo: str):
    import aiida
    from aiida import orm
    from aiida.plugins import WorkflowFactory

    aiida.load_profile()

    structure = orm.StructureData(ase=bulk("Si", "diamond", 5.43))
    code = orm.load_code(code_label)

    options = {
        "resources": {"num_machines": 1, "num_mpiprocs_per_machine": mpiprocs},
        "max_wallclock_seconds": wallclock,
        "withmpi": True,
    }
    if queue:
        options["queue_name"] = queue

    WorkChain = WorkflowFactory("abacus.base")
    if protocol:
        builder = WorkChain.get_builder_from_protocol(
            code=code, structure=structure, protocol=protocol,
            overrides={"pseudo_family": pseudo},
        )
    else:
        builder = WorkChain.get_builder()
        builder.abacus.structure = structure
        builder.abacus.code = code
        builder.abacus.parameters = orm.Dict(
            {"input": {"calculation": "scf", "basis_type": "lcao",
                       "ecutwfc": 100, "scf_thr": 1e-6, "scf_nmax": 100,
                       "smearing_method": "mp", "smearing_sigma": 0.01,
                       "nspin": 1}}
        )
        builder.kpoints_distance = orm.Float(0.25)
        builder.pseudo_family = orm.Str(pseudo)
    # WorkChains expose the CalcJob metadata through the nested namespace:
    # for ``abacus.base`` that is ``builder.abacus.metadata.options``.
    builder.abacus.metadata.options = options
    return builder


def validate(builder) -> None:
    """Validate ports and print what will actually be used."""
    inputs = builder._inputs(prune=True)
    error = builder._process_class.spec().inputs.validate(inputs)
    if error is not None:
        print(f"validation failed: {error}", file=sys.stderr)
        raise SystemExit(1)

    options = dict(getattr(builder.abacus.metadata, "options", {}) or {})
    print("scheduler options :", {
        "queue_name": options.get("queue_name"),
        "max_wallclock_seconds": options.get("max_wallclock_seconds"),
        "resources": options.get("resources"),
    })
    if options.get("queue_name") is None:
        print("WARNING: no queue_name — a SLURM submission will fail with "
              "'No partition specified'. Pass --queue.", file=sys.stderr)

    def parameters_of(node):
        try:
            return node["parameters"].get_dict()
        except Exception:  # noqa: BLE001
            return node.get("parameters", {})

    print("abacus parameters :", parameters_of(inputs.get("abacus", {})))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", default="abacus_lts@yeesuan")
    parser.add_argument("--protocol", default=None,
                        help="fast/moderate/precise (plugin protocol); "
                             "omit to use the explicit parameters below")
    parser.add_argument("--queue", default=None, help="SLURM partition")
    parser.add_argument("--wallclock", type=int, default=1800)
    parser.add_argument("--mpiprocs", type=int, default=8)
    parser.add_argument("--pseudo", default="sg15_dzp",
                        help="ABACUS atomic-orbital family (UPF + orbitals)")
    parser.add_argument("--dry-run", action="store_true", help="build and validate only")
    parser.add_argument("--submit", action="store_true", help="actually submit")
    args = parser.parse_args()

    builder = build(args.code, args.protocol, args.queue, args.wallclock,
                    args.mpiprocs, args.pseudo)
    validate(builder)

    if not args.submit:
        print("\ndry run: nothing submitted (use --submit)")
        return 0
    if args.dry_run:
        print("\n--dry-run and --submit are mutually exclusive", file=sys.stderr)
        return 1

    from aiida.engine import submit

    node = submit(builder)
    print(f"\nsubmitted: pk={node.pk} uuid={node.uuid}")
    print("track with: verdi process status", node.pk)
    return 0


if __name__ == "__main__":
    sys.exit(main())
