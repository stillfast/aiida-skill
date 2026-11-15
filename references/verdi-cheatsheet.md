---
verified: 2026-11
applies_to: "aiida-core>=2.6,<3"
---

# verdi 速查

## 环境

```bash
verdi status                     # version/config/profile/storage/broker/daemon
verdi profile list
verdi profile setdefault <name>
verdi daemon start|stop|restart|status
verdi daemon incr 2              # 增加 worker
```

## 配置

```bash
verdi computer setup --label ... --hostname ...
verdi computer configure core.ssh_async <label> -n --host <host>
verdi computer test <label>
verdi computer list

verdi code create core.code.installed --label ... --computer ...
verdi code show <label>
verdi code list
```

## 插件

```bash
verdi plugin list aiida.workflows
verdi plugin list aiida.workflows <entry_point>     # 端口
verdi plugin list aiida.calculations
verdi plugin list aiida.calculations <entry_point>
verdi plugin list aiida.parsers
```

## 进程

```bash
verdi process list -a
verdi process list -a -p <pk>
verdi process show <pk>
verdi process status <pk>
verdi process report <pk>
verdi process kill <pk>
verdi process play <paused-pk>     # 仅当输入已修好
```

## 节点与数据

```bash
verdi node show <pk>
verdi node graph generate <pk>
verdi node repo ls <pk>
verdi calcjob gotocomputer <pk>
```

## 数据管理

```bash
verdi archive create out.aiida --groups <group>
verdi archive import out.aiida
verdi group list
verdi group show <group>
```

## Python 里常用的几行

```python
from aiida import load_profile
load_profile('aiida_profile')

from aiida.orm import load_node, load_code, StructureData, Dict, KpointsData, List, Float, Str
from aiida.plugins import WorkflowFactory, CalculationFactory
from aiida.engine import submit, run_get_node
```
