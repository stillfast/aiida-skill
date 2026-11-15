#!/usr/bin/env python
"""Layer 2 (scripts): submit exactly what ``workflow.py`` built.

    python submit.py --code qe@yeesuan --element U --scale-count 5
"""
from __future__ import annotations

import argparse
import json

from workflow import PROTOCOLS, STRUCTURES, make_builder, validate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", default="qe@yeesuan")
    parser.add_argument("--protocol", default="fast", choices=PROTOCOLS)
    parser.add_argument("--element", default="U", choices=sorted(STRUCTURES))
    parser.add_argument("--scale-count", type=int, default=5)
    parser.add_argument("--scale-increment", type=float, default=0.02)
    parser.add_argument("--relax-type", default="none")
    parser.add_argument("--sub-process", default=None)
    args = parser.parse_args()

    sub_process = json.loads(args.sub_process) if args.sub_process else None
    _, builder = make_builder(
        args.code, args.protocol, args.element, args.scale_count,
        args.scale_increment, args.relax_type, sub_process,
    )
    validate(builder)

    from aiida.engine import submit

    node = submit(builder)
    print(f"\nsubmitted: pk={node.pk} uuid={node.uuid}")
    print("track with: verdi process status", node.pk)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
