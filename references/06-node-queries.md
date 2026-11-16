---
verified: 2026-11
applies_to: "aiida-core>=2.6,<3"
---

# 5. Query cookbook for reading results and troubleshooting

Once a WorkChain has run, the everyday task is usually not looking at the inputs again but **pulling data out of the nodes**. All snippets below were run on aiida-core 2.8.

## 6.1 Status: check these attributes first

| Attribute | Meaning |
|---|---|
| `process_state` | `created/waiting/running/finished/exited/killed` |
| `exit_status` | `0` success; `None` not finished; non-zero is defined by the plugin |
| `exit_message` | Message corresponding to the exit code |
| `is_finished_ok` | `Finished` and `exit_status == 0` ← **use this to test success in scripts** |
| `is_failed` | `Finished` and `exit_status != 0` |
| `is_killed` / `is_excepted` / `is_terminated` | Other terminal-state checks |

```python
for node in nodes:
    if not node.is_finished_ok:
        print(node.pk, node.process_state, node.exit_status, node.exit_message)
```

## 6.2 Ports and links

```python
node = load_node(pk)
print(list(node.inputs))       # direct input port names
print(list(node.outputs))      # direct output port names
print(node.inputs.structure)   # fetch the specific node
```

```python
from aiida.orm import CalcJobNode

# upstream (who created it)
for link in node.base.links.get_incoming().all():
    print(link.link_label, "<-", link.node.pk)

# downstream (what it created)
for link in node.base.links.get_outgoing().all():
    print(link.link_label, "->", link.node.pk, link.node.node_type)

# calculation children only (most useful for WorkChain troubleshooting)
for link in node.base.links.get_outgoing(node_class=CalcJobNode).all():
    print("calc:", link.node.pk, link.node.process_label)
```

## 6.3 Query nodes by label / extras (the basis for idempotent deduplication)

```python
from aiida.orm import Node, QueryBuilder

qb = QueryBuilder()
qb.append(Node, filters={"label": {"==": "my-label"}})
nodes = qb.all(flat=True)

# extras filter + only successful/running ones
qb = QueryBuilder()
qb.append(Node, tag="n")
qb.add_filter("n", {"extras.batch": "relax20"})
qb.add_filter("n", {"or": [
    {"attributes.exit_status": 0},
    {"attributes.process_state": "created"},
    {"attributes.process_state": "running"},
    {"attributes.process_state": "waiting"},
]})
```

Tag nodes with `node.base.extras.set_many({...})` (or `node.set_extra(k, v)`); afterwards, filtering by `extras.<key>` is enough to implement "never submit the same structure twice".

## 6.4 The retrieved files

```python
retrieved = node.outputs.retrieved
print(retrieved.list_object_names())
with retrieved.open("OUT.aiida/running_scf.log") as handle:
    text = handle.read()

# copy the whole directory locally (structure preserved)
retrieved.copy_tree("/tmp/run-123")
```

Extracting the number of electronic steps from the log (ABACUS `ELEC=` lines):

```python
import re
match = re.findall(r"ELEC=\s+(\d+)", text)
print("electronic steps:", int(match[-1]) if match else None)
```

## 6.5 misc / structured outputs

```python
node.outputs.misc.get_dict()          # {'total_energy': ..., 'final_forces': ...}
node.outputs.output_parameters.get_dict()
node.outputs.structure.get_cell_volume()
node.outputs.structure.get_formula()
```

## 6.6 trajectory (output by ABACUS and others)

```python
traj = node.outputs.trajectory
print(traj.get_arraynames())          # ['cells', 'positions', 'forces', 'stress', ...]
forces = traj.get_array("forces")
```

`node.get_remote_path()` (RemoteData) gives the original directory on the cluster; to inspect the files locally use
`verdi calcjob gotocomputer <pk>`.

## 6.7 Archiving

```python
from aiida.tools.archive import create_archive

create_archive(
    entities=[node], filename="results.aiida",
    overwrite=True, include_comments=True, include_logs=True,
)
```

> Note: the parameters `call_calc_backward` / `call_work_backward` / `create_backward` belong to
> AiiDA 1.x and no longer exist in the 2.x `create_archive`; in 2.x,
> `entities=` plus the parameters above is enough (defer to `inspect.signature(create_archive)`).

## 6.8 Debugging

```bash
verdi daemon logshow                             # watch the daemon log live
verdi config set logging.aiida_loglevel DEBUG    # raise the log level (affects newly started processes)
verdi config unset logging.aiida_loglevel        # restore
verdi process report <pk>                        # single-process log (fastest)
verdi daemon status                              # worker count / whether it is running
```

## 6.9 Using verdi directly in Jupyter

```python
%load_ext aiida          # the aiida package ships load_ipython_extension (available in 2.x)
%verdi status
%verdi process list -a
```

> `%load_ext aiida.ipython` from old docs no longer exists; the module name is simply `aiida`.

## 6.10 Probe plugin ports (mandatory before writing a script)

```python
from aiida.plugins import CalculationFactory

spec = CalculationFactory("abacus.abacus").spec()
print(list(spec.outputs))        # which output ports exist
print(list(spec.inputs))         # which input ports exist
```

```bash
verdi plugin list aiida.calculations abacus.abacus
verdi plugin list aiida.workflows abacus.base
```
