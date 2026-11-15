---
verified: 2026-11
applies_to: "aiida-core>=2.6,<3"
---

# 3A. 使用（一）：先写 workflow

workflow 层回答一个问题：**"一次计算由哪些步骤组成，失败了怎么办？"**
这一层不需要你写代码——插件已经把 WorkChain 写好了；你要做的是
**选对 WorkChain、填对输入、先 dry-run 再提交**。

## 3.1 找到可用的 WorkChain

```bash
verdi plugin list aiida.workflows              # 列出了哪些工作流
verdi plugin list aiida.workflows abacus.relax # 看它的输入/输出端口
verdi plugin list aiida.calculations           # 底层 CalcJob
```

常见入口：

| 需求 | 单代码 WorkChain | 统一接口（common-workflows） |
|---|---|---|
| 单点 SCF | `abacus.base` / `vasp.v2.vasp` | — |
| 结构弛豫 | `abacus.relax` / `vasp.v2.relax` | `common_workflows.relax` |
| 状态方程 | — | `common_workflows.eos` |
| 能带/DOS | 插件自带 | — |

## 3.2 用 builder 构建输入

`builder` 是 AiiDA 的输入容器，端口名从插件 spec 来，不会拼错：

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

**不要**手写 `inputs` 字典：端口名、嵌套命名空间、metadata 的位置都容易错，
而且错的位置不同表现各异（有的是 submit 时报错，有的是作业跑起来才发现）。

## 3.3 用协议档（protocol）省事

插件提供 `get_builder_from_protocol(...)`，用 `fast / moderate / precise`
三档预设替代逐项填参：

```python
builder = WorkChain.get_builder_from_protocol(
    code=load_code('abacus_lts@<cluster>'),
    structure=structure,
    protocol='fast',
    overrides={'abacus': {'parameters': {'input': {'ecutwfc': 100}}}},
)
```

common-workflows 的接口同理，且可以跨代码切换：

```python
from aiida_common_workflows.plugins import load_workflow_entry_point
from aiida_common_workflows.common import RelaxType, ElectronicType

WorkChain = load_workflow_entry_point('relax', 'vasp')     # 或 quantum_espresso / fleur ...
builder = WorkChain.get_input_generator().get_builder(
    structure, engines={'relax': {'code': code, 'options': options}},
    protocol='fast', relax_type=RelaxType.POSITIONS_CELL,
    electronic_type=ElectronicType.METAL,
)
```

同一组参数换后端只改一个字符串，这就是"验证不同代码"的基础。

> 目前 aiida-common-workflows 注册的 relax 后端是 abinit / bigdft / castep / cp2k /
> fleur / gaussian / gpaw / nwchem / orca / quantum_espresso / siesta / vasp / wien2k，
> **没有 ABACUS**。ABACUS 请直接用 `abacus.base` / `abacus.relax` 这类插件原生 WorkChain。
> 用 `verdi plugin list aiida.workflows | grep common_workflows` 确认本机实际注册了哪些。

## 3.4 提交前必须做的检查

```python
# 1) 校验端口
err = builder._process_class.spec().inputs.validate(builder._inputs(prune=True))
assert err is None, err

# 2) 打印真正会生效的调度参数
opts = builder.metadata.options
print(opts.get('queue_name'), opts.get('max_wallclock_seconds'), opts.get('resources'))

# 3) 打印真正会生效的物理参数（协议档会覆盖你的默认值）
print(builder.abacus.parameters.get_dict())
```

第 2 步是经验之谈：**调度参数丢失是最高频的"静默失败"**，表现是提交时
`No partition specified`，或者作业用 1 核跑了 20 小时。

## 3.5 提交、跟踪、取结果

```python
node = submit(builder)
print(node.pk, node.uuid)
```

```bash
verdi process list -a                 # 所有进程
verdi process show <pk>               # 输入、输出、exit status
verdi process status <pk>             # 子进程树
verdi process report <pk>             # 日志（含 handler 的处置）
verdi process kill <pk>               # 停掉（子进程一起）
```

结果读取：

```python
node = load_node(pk)
node.outputs.misc.get_dict()['total_energy']   # 能量
node.outputs.structure                          # 弛豫后的结构
node.exit_status, node.exit_message             # 0 + None = 成功
node.outputs.retrieved.open('OUT.aiida/running_scf.log')  # 原始日志
```

## 3.6 什么时候该自己写 WorkChain

只有在"现成工作流组合不起来"时才写，例如：多步之间有自定义判据、
需要跨代码比较、需要批量生成子作业。写的时候遵守三条：

1. `spec.outline` 明确分段，每段可重入；
2. 用 `exit_code` + `@process_handler` 表达失败策略，而不是 `try/except` 兜底；
3. 输出用标准 Data 类型（`Dict`、`StructureData`），方便下游脚本消费。

## 3.7 常见坑

| 现象 | 原因 | 处置 |
|---|---|---|
| `Unexpected ports` | 该插件不支持某个 metadata 键 | 查 `verdi plugin list aiida.calculations <name>` |
| 作业 1 核跑 | `metadata.options` 没传到子 CalcJob | dry-run 打印 options，见 3.4 |
| daemon 里还是旧代码 | editable 安装改了源码 | `verdi daemon restart` |
| 端口名对不上 | 插件版本变化 | `verdi plugin list` 为准，不要凭记忆 |
