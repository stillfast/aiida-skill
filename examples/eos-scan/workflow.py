#!/usr/bin/env python
"""Layer 1 (workflow): describe an equation-of-state scan. Submits nothing.

This file only *describes* the calculation: structure, backend, protocol, how
many volume points, which code-dependent overrides. ``submit.py`` imports the
same function, so what you validate is exactly what you submit.

    python workflow.py --dry-run                          # bcc U, QE, fast
    python workflow.py --dry-run --element Si             # needs a Si family
    python workflow.py --dry-run --code vaspstd@mycluster

Backends come from aiida-common-workflows (``common_workflows.relax.<code>``);
``verdi plugin list aiida.workflows | grep common_workflows.relax`` lists the
installed ones. ABACUS is not a common-workflows backend: use abacus.relax
directly (see ``../si-scf``).
"""
from __future__ import annotations

import argparse
import json

PROTOCOLS = ("fast", "moderate", "precise")

#: element -> (crystal structure, lattice constant in Å)
STRUCTURES = {
    "U": ("bcc", 3.45),
    "Si": ("diamond", 5.43),
    "Al": ("fcc", 4.05),
}


def make_builder(code_label: str, protocol: str, element: str,
                 scale_count: int, scale_increment: float,
                 relax_type: str = "none", sub_process: dict | None = None):
    """Return (workchain class, builder) for an equation-of-state scan."""
    import aiida
    from aiida import orm
    from aiida.plugins import WorkflowFactory
    from aiida_common_workflows.common import ElectronicType, RelaxType, SpinType
    from aiida_common_workflows.plugins import (
        get_entry_point_name_from_class,
        load_workflow_entry_point,
    )

    aiida.load_profile()

    backend = _backend_from_code_type(code_label.split("@")[0])
    relax_workchain = load_workflow_entry_point("relax", backend)
    sub_process_class = get_entry_point_name_from_class(relax_workchain).name

    code = orm.load_code(code_label)
    options = {
        "resources": {"num_machines": 1},
        "max_wallclock_seconds": 3600,
        "withmpi": True,
    }
    generator_inputs = {
        "engines": {"relax": {"code": code, "options": options}},
        "protocol": protocol,
        "relax_type": getattr(RelaxType, relax_type.upper()),
        "electronic_type": ElectronicType.METAL,
        "spin_type": SpinType.NONE,
    }

    WorkChain = WorkflowFactory("common_workflows.eos")
    builder = WorkChain.get_builder()
    builder.structure = _structure(element)
    builder.generator_inputs = generator_inputs
    builder.sub_process_class = sub_process_class
    builder.scale_count = scale_count
    builder.scale_increment = scale_increment
    if sub_process:
        # Code-dependent overrides are handed to the relax WorkChain, e.g.
        # QE pseudos/cutoffs or ABACUS-family-like settings. Keep whatever
        # the user passed: this is the only code-specific knob here.
        builder.sub_process = sub_process
    return WorkChain, builder


def _backend_from_code_type(code_type: str) -> str:
    mapping = {
        "qe": "quantum_espresso", "pw": "quantum_espresso",
        "vasp": "vasp", "vaspstd": "vasp", "vaspncl": "vasp",
        "fleur": "fleur", "cp2k": "cp2k", "siesta": "siesta",
    }
    if code_type not in mapping:
        raise SystemExit(
            f"cannot map code '{code_type}' to a common-workflows backend; "
            f"known: {sorted(mapping)}"
        )
    return mapping[code_type]


def _structure(element: str):
    from aiida import orm
    from ase.build import bulk

    if element not in STRUCTURES:
        raise SystemExit(f"element must be one of {sorted(STRUCTURES)}")
    crystal, a = STRUCTURES[element]
    return orm.StructureData(ase=bulk(element, crystal, a))


def validate(builder) -> None:
    """Validate ports and print what will actually run."""
    error = builder._process_class.spec().inputs.validate(builder._inputs(prune=True))
    if error is not None:
        raise SystemExit(f"validation failed: {error}")

    generator_inputs = dict(builder.generator_inputs)
    print(f"structure         : {builder.structure.get_formula()}")
    print(f"backend           : {builder.sub_process_class}")
    print(f"protocol          : {generator_inputs.get('protocol')}")
    print(f"relax_type        : {generator_inputs.get('relax_type')}")
    for name, engine in (generator_inputs.get("engines") or {}).items():
        print(f"engine '{name}'      : {engine['code']}")
        print(f"  scheduler options: {engine.get('options')}")
    print(f"scale_count       : {_value(builder.scale_count)}")
    print(f"scale_increment   : {_value(builder.scale_increment)}")


def _value(node):
    """Builder values may be Data nodes before submission."""
    return getattr(node, "value", node)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", default="qe@yeesuan")
    parser.add_argument("--protocol", default="fast", choices=PROTOCOLS)
    parser.add_argument("--element", default="U", choices=sorted(STRUCTURES))
    parser.add_argument("--scale-count", type=int, default=5)
    parser.add_argument("--scale-increment", type=float, default=0.02)
    parser.add_argument("--relax-type", default="none",
                        help="none | positions | cell | positions_cell")
    parser.add_argument("--sub-process", default=None,
                        help="JSON dict with code-dependent overrides")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    sub_process = json.loads(args.sub_process) if args.sub_process else None
    _, builder = make_builder(
        args.code, args.protocol, args.element, args.scale_count,
        args.scale_increment, args.relax_type, sub_process,
    )
    validate(builder)
    if args.dry_run:
        print("\ndry run: nothing submitted (see submit.py)")
    else:
        print("\nuse submit.py to submit these inputs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
