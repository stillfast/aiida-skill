---
verified: 2026-11
applies_to: "aiida-core>=2.6,<3"
---

# verdi quick reference

## Environment

```bash
verdi status                     # version/config/profile/storage/broker/daemon
verdi profile list
verdi profile setdefault <name>
verdi daemon start|stop|restart|status
verdi daemon incr 2              # add a worker
```

## Configuration

```bash
verdi computer setup --label ... --hostname ...
verdi computer configure core.ssh_async <label> -n --host <host>
verdi computer test <label>
verdi computer list

verdi code create core.code.installed --label ... --computer ...
verdi code show <label>
verdi code list
```

## Plugins

```bash
verdi plugin list aiida.workflows
verdi plugin list aiida.workflows <entry_point>     # ports
verdi plugin list aiida.calculations
verdi plugin list aiida.calculations <entry_point>
verdi plugin list aiida.parsers
```

## Processes

```bash
verdi process list -a
verdi process list -a -p <pk>
verdi process show <pk>
verdi process status <pk>
verdi process report <pk>
verdi process kill <pk>
verdi process play <paused-pk>     # only if the inputs are already fixed
```

## Nodes and data

```bash
verdi node show <pk>
verdi node graph generate <pk>
verdi node repo ls <pk>
verdi calcjob gotocomputer <pk>
```

## Data management

```bash
verdi archive create out.aiida --groups <group>
verdi archive import out.aiida
verdi group list
verdi group show <group>
```

## A few common lines in Python

```python
from aiida import load_profile
load_profile('aiida_profile')

from aiida.orm import load_node, load_code, StructureData, Dict, KpointsData, List, Float, Str
from aiida.plugins import WorkflowFactory, CalculationFactory
from aiida.engine import submit, run_get_node
```

## Command differences between 2.x and old docs (following old tutorials will fail)

| Old form (1.x) | Current (2.x) |
|---|---|
| `verdi code setup` | `verdi code create core.code.installed ...` |
| `verdi profile set-default X` | `verdi profile setdefault X` |
| `verdi calcjobs gotocomputer` | `verdi calcjob gotocomputer` |
| `reentry scan` | Usually unnecessary (2.x discovers entry points automatically) |
| `verdi computer setup` (interactive) | `verdi computer setup --non-interactive ...` |
| `%load_ext aiida.ipython` | `%load_ext aiida` (the module name is simply `aiida`) |

## Stuck / zombie processes

```bash
verdi daemon stop
verdi process repair          # mark active processes with no task in the broker as failed
verdi daemon start
```

## Debugging and logs

```bash
verdi daemon logshow
verdi config set logging.aiida_loglevel DEBUG     # takes effect for new processes
verdi config unset logging.aiida_loglevel
```

## Caching

```bash
verdi config set caching.default_enabled True     # calculations with identical inputs are reused directly
verdi process show <pk>                           # check cached_from
```

## Jupyter

```python
%load_ext aiida
%verdi status
%verdi process list -a
%verdi process report <pk>
```

## Archiving Python API (2.x signature)

```python
from aiida.tools.archive import create_archive
create_archive(entities=[node], filename="out.aiida", overwrite=True,
               include_comments=True, include_logs=True)
```
