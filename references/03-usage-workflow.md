---
verified: 2026-11
applies_to: "aiida-core>=2.6,<3"
---

# 3A. Usage (1): write the workflow first

The workflow layer answers one question: **"What steps does a single calculation consist of, and what happens if they fail?"**
This layer does not require you to write code — the plugin has already written the WorkChain; what you need to do is
**pick the right WorkChain, fill in the inputs correctly, and dry-run before submitting**.

## 3.1 Find an available WorkChain

```bash
verdi plugin list aiida.workflows              # which workflows are registered
verdi plugin list aiida.workflows abacus.relax # inspect its input/output ports
verdi plugin list aiida.calculations           # the underlying CalcJob
```

Common entry points:

| Requirement | Single-code WorkChain | Unified interface (common-workflows) |
|---|---|---|
| Single-point SCF | `abacus.base` / `vasp.v2.vasp` | — |
| Structure relaxation | `abacus.relax` / `vasp.v2.relax` | `common_workflows.relax` |
| Equation of state | — | `common_workflows.eos` |
| Band/DOS | built into the plugin | — |

## 3.2 Build inputs with the builder

`builder` is AiiDA's input container; port names come from the plugin spec, so you cannot misspell them:

```python
from aiida.plugins import WorkflowFactory
from aiida.engine import submit
from aiida.orm import StructureData, Dict, load_code
from ase.build import bulk

WorkChain = WorkflowFactory('abacus.base')
builder = WorkChain.get_builder()
builder.structure = StructureData(ase=bulk('Si', 'diamond', 5.43))
builder.abacus.code = load_code('abacus_lts@<cluster>')
builder.abacus.parameters = Dict({'input': {'ecutwfc': 100, 'scf_thr': 1e-6,
                                            'basis_type': 'lcao'}})
builder.kpoints_distance = 0.3
builder.pseudo_family = 'sgbrv'
builder.metadata.options = {
    'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 56},
    'queue_name': 'q_ysuan',
    'max_wallclock_seconds': 7200,
    'withmpi': True,
}
```

**Do not** hand-write the `inputs` dict: port names, nested namespaces and the placement of metadata are all easy to get wrong,
and different mistakes show up in different ways (some fail at submit time, others are only discovered once the job is running).

## 3.3 Save effort with protocol levels

Plugins provide `get_builder_from_protocol(...)`, whose three presets `fast / moderate / precise`
replace filling in parameters one by one:

```python
builder = WorkChain.get_builder_from_protocol(
    code=load_code('abacus_lts@<cluster>'),
    structure=structure,
    protocol='fast',
    overrides={'abacus': {'parameters': {'input': {'ecutwfc': 100}}}},
)
```

The common-workflows interface works the same way, and you can switch codes:

```python
from aiida_common_workflows.plugins import load_workflow_entry_point
from aiida_common_workflows.common import RelaxType, ElectronicType

WorkChain = load_workflow_entry_point('relax', 'vasp')     # or quantum_espresso / fleur ...
builder = WorkChain.get_input_generator().get_builder(
    structure, engines={'relax': {'code': code, 'options': options}},
    protocol='fast', relax_type=RelaxType.POSITIONS_CELL,
    electronic_type=ElectronicType.METAL,
)
```

Switching backends with the same set of parameters changes only one string — this is the basis for "validating different codes".

> Currently the relax backends registered by aiida-common-workflows are abinit / bigdft / castep / cp2k /
> fleur / gaussian / gpaw / nwchem / orca / quantum_espresso / siesta / vasp / wien2k,
> with **no ABACUS**. For ABACUS use plugin-native WorkChains such as `abacus.base` / `abacus.relax`.
> Use `verdi plugin list aiida.workflows | grep common_workflows` to confirm what is actually registered on this machine.

## 3.4 Checks you must do before submitting

```python
# 1) validate the ports
err = builder._process_class.spec().inputs.validate(builder._inputs(prune=True))
assert err is None, err

# 2) print the scheduler parameters that will actually take effect
opts = builder.metadata.options
print(opts.get('queue_name'), opts.get('max_wallclock_seconds'), opts.get('resources'))

# 3) print the physical parameters that will actually take effect (protocol levels override your defaults)
print(builder.abacus.parameters.get_dict())
```

Step 2 is a lesson from experience: **lost scheduler parameters are the most frequent "silent failure"**, showing up as
`No partition specified` at submit time, or as a job that runs for 20 hours on 1 core.

## 3.5 Submit, track, retrieve results

```python
node = submit(builder)
print(node.pk, node.uuid)
```

```bash
verdi process list -a                 # all processes
verdi process show <pk>               # inputs, outputs, exit status
verdi process status <pk>             # process tree
verdi process report <pk>             # log (including how handlers acted)
verdi process kill <pk>               # stop it (including child processes)
```

Reading results:

```python
node = load_node(pk)
node.outputs.misc.get_dict()['total_energy']   # energy
node.outputs.structure                          # relaxed structure
node.exit_status, node.exit_message             # 0 + None = success
node.outputs.retrieved.open('OUT.aiida/running_scf.log')  # raw log
```

## 3.6 When to write your own WorkChain

Write one only when "the existing workflows cannot be combined", for example: custom criteria between individual steps,
a need to compare across codes, or a need to generate sub-jobs in batches. Follow three rules when writing:

1. `spec.outline` clearly delineates the stages, each of which is re-entrant;
2. express the failure policy with `exit_code` + `@process_handler` rather than a `try/except` catch-all;
3. use standard Data types for outputs (`Dict`, `StructureData`) so downstream scripts can consume them easily.

## 3.7 Common pitfalls

| Symptom | Cause | Action |
|---|---|---|
| `Unexpected ports` | the plugin does not support a certain metadata key | check `verdi plugin list aiida.calculations <name>` |
| job runs on 1 core | `metadata.options` were not passed to the child CalcJob | dry-run and print options, see 3.4 |
| the daemon still runs old code | an editable install changed the source | `verdi daemon restart` |
| port names do not match | the plugin version changed | trust `verdi plugin list`, not memory |
