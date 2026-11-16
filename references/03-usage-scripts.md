---
verified: 2026-11
applies_to: "aiida-core>=2.6,<3"
---

# 3B. Usage (2): then write scripts

Once the workflow has run through once, the scripts layer is responsible for **running in batches** and **turning results into tables/plots**.
For the layering, see `acwf-verification-scripts` (`aiidateam/acwf-verification-scripts`):

```
2-submit/    batch submission (SubmissionController)
3-analyze/   extract → fit → plots/JSON
4-export/    archive (AiiDA archive)
```

> Note: that upstream set of scripts pins `aiida-core==1.6`. **Borrow its structure; do not install it directly.**

## 4.1 Batch submission: SubmissionController

The core idea is to describe "each task" as a deduplicable key (extras); the controller handles the concurrency limit,
resume after interruption, and deduplication:

```python
from aiida import orm
from aiida.engine import submit
from aiida_submission_controller import FromGroupSubmissionController


class EosSubmission(FromGroupSubmissionController):
    def __init__(self, code_label, **kwargs):
        super().__init__(**kwargs)
        self._code = orm.load_code(code_label)

    def get_extra_unique_keys(self):
        return ('element', 'configuration')      # unique key of each task

    def get_inputs_and_processclass_from_extras(self, extras_values):
        structure = self.get_parent_node_from_extras(extras_values)
        builder = self._builder_for(structure)
        return builder, None


controller = EosSubmission(
    code_label='abacus_lts@<cluster>',
    parent_group_label='structures',
    unique_extra_keys=('element', 'configuration'),
    query_types=('structure',),
    max_concurrent=8,
)
controller.submit_new_batch(verbose=True)
```

Writing your own for loop can also submit, but you must handle: concurrency, retries on failure, duplicate submission, and
resuming after interruption. Use the controller once there are more than 10 tasks.

## 4.2 Result extraction

Read outputs only; never touch the database internals:

```python
from aiida.orm import load_node

for pk in pks:
    n = load_node(pk)
    if n.exit_status != 0:
        errors.append((pk, n.exit_status, n.exit_message))
        continue
    misc = n.outputs.misc.get_dict()
    rows.append({'pk': pk,
                 'energy': misc['total_energy'],
                 'volume': n.outputs.structure.get_cell_volume()})
```

Normalize everything into a `pandas.DataFrame` → CSV/JSON; fitting and plotting afterwards are all based on it.

## 4.3 Analysis: EOS fitting example

```python
import numpy as np
from scipy.optimize import curve_fit

def birch_murnaghan(V, E0, V0, B0, Bp):
    eta = (V0 / V) ** (2 / 3)
    return E0 + 9 * V0 * B0 / 16 * ((eta - 1) ** 3 * Bp
            + (eta - 1) ** 2 * (6 - 4 * eta))

popt, _ = curve_fit(birch_murnaghan, data.volume, data.energy, p0=[data.energy.min(), data.volume.min(), 0.5, 4])
```

## 4.4 Export and archiving

```bash
verdi archive create results.aiida --groups <group-label>
verdi archive import results.aiida        # reproduce on another machine
```

An archive is a "transferable provenance graph", better suited than CSV for handing to collaborators or attaching to a submission.

## 4.4bis Runnable examples in this repository

`examples/eos-scan/` demonstrates the two layers of this section separately:

```bash
python workflow.py --dry-run                    # build + validate only (print the settings that actually take effect)
python submit.py --code qe@mycluster --element U
python analyze.py <pk> --json eos.json          # read structures/total_energies and fit BM
```

When reading results use `node.base.links.get_outgoing(link_type=LinkType.RETURN).nested()`;
the output holds two nested namespaces, `structures` / `total_energies` (matched by the same index);
the official CLI can also plot directly: `aiida-common-workflows plot eos <pk>`.

## 4.5 Some principles for the scripts layer

- **Consume outputs only**; do not modify nodes;
- every script has `--dry-run` / `--limit`; validate on a small batch before a large one;
- record failures **by category** (exit code + pk) rather than with `except: pass`;
- analysis scripts must be able to run on "partially failed" data (skip the failed entries and report how many);
- all intermediate results land in CSV/JSON, and figures are regenerated from the data so everything stays reproducible.
