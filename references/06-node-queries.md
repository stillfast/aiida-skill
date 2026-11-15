---
verified: 2026-11
applies_to: "aiida-core>=2.6,<3"
---

# 5. 读取结果与排障的查询手册

WorkChain 跑完之后，日常最常用的不是再看输入，而是**从节点里把数据捞出来**。
以下片段都在 aiida-core 2.8 上跑过。

## 6.1 状态：先看这几个属性

| 属性 | 含义 |
|---|---|
| `process_state` | `created/waiting/running/finished/exited/killed` |
| `exit_status` | `0` 成功；`None` 未结束；非 0 由插件定义 |
| `exit_message` | 与 exit code 对应的说明 |
| `is_finished_ok` | `Finished` 且 `exit_status == 0` ← **脚本里判成功用它** |
| `is_failed` | `Finished` 且 `exit_status != 0` |
| `is_killed` / `is_excepted` / `is_terminated` | 其它终态判断 |

```python
for node in nodes:
    if not node.is_finished_ok:
        print(node.pk, node.process_state, node.exit_status, node.exit_message)
```

## 6.2 端口与链接

```python
node = load_node(pk)
print(list(node.inputs))       # 直接输入端口名
print(list(node.outputs))      # 直接输出端口名
print(node.inputs.structure)   # 取具体节点
```

```python
from aiida.orm import CalcJobNode

# 上游（谁生成了它）
for link in node.base.links.get_incoming().all():
    print(link.link_label, "<-", link.node.pk)

# 下游（它生成了谁）
for link in node.base.links.get_outgoing().all():
    print(link.link_label, "->", link.node.pk, link.node.node_type)

# 只看计算子节点（WorkChain 排障最有用）
for link in node.base.links.get_outgoing(node_class=CalcJobNode).all():
    print("calc:", link.node.pk, link.node.process_label)
```

## 6.3 按 label / extras 查节点（幂等去重的基础）

```python
from aiida.orm import Node, QueryBuilder

qb = QueryBuilder()
qb.append(Node, filters={"label": {"==": "my-label"}})
nodes = qb.all(flat=True)

# extras 过滤 + 只看成功/在跑的
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

打标签用 `node.base.extras.set_many({...})`（或 `node.set_extra(k, v)`），
之后按 `extras.<key>` 过滤即可实现"同一结构不重复提交"。

## 6.4 读取回的文件

```python
retrieved = node.outputs.retrieved
print(retrieved.list_object_names())
with retrieved.open("OUT.aiida/running_scf.log") as handle:
    text = handle.read()

# 整目录拷到本地（保留结构）
retrieved.copy_tree("/tmp/run-123")
```

日志里抽电子步数（ABACUS 的 `ELEC=` 行）：

```python
import re
match = re.findall(r"ELEC=\s+(\d+)", text)
print("electronic steps:", int(match[-1]) if match else None)
```

## 6.5 misc / 结构化输出

```python
node.outputs.misc.get_dict()          # {'total_energy': ..., 'final_forces': ...}
node.outputs.output_parameters.get_dict()
node.outputs.structure.get_cell_volume()
node.outputs.structure.get_formula()
```

## 6.6 trajectory（ABACUS 等会输出）

```python
traj = node.outputs.trajectory
print(traj.get_arraynames())          # ['cells', 'positions', 'forces', 'stress', ...]
forces = traj.get_array("forces")
```

`node.get_remote_path()`（RemoteData）给出集群上的原始目录；本地看文件用
`verdi calcjob gotocomputer <pk>`。

## 6.7 归档

```python
from aiida.tools.archive import create_archive

create_archive(
    entities=[node], filename="results.aiida",
    overwrite=True, include_comments=True, include_logs=True,
)
```

> 注意：`call_calc_backward` / `call_work_backward` / `create_backward` 这些参数是
> AiiDA 1.x 的，2.x 的 `create_archive` 已没有；2.x 用
> `entities=` + 上面这几个参数就够了（`inspect.signature(create_archive)` 为准）。

## 6.8 调试

```bash
verdi daemon logshow                             # 实时看 daemon 日志
verdi config set logging.aiida_loglevel DEBUG    # 提高日志级别（影响新起的进程）
verdi config unset logging.aiida_loglevel        # 恢复
verdi process report <pk>                        # 单进程日志（最快）
verdi daemon status                              # worker 数 / 是否在跑
```

## 6.9 Jupyter 里直接用 verdi

```python
%load_ext aiida          # aiida 包自带 load_ipython_extension（2.x 可用）
%verdi status
%verdi process list -a
```

> 旧文档里的 `%load_ext aiida.ipython` 已不存在；模块名就是 `aiida`。

## 6.10 探插件端口（写脚本前必做）

```python
from aiida.plugins import CalculationFactory

spec = CalculationFactory("abacus.abacus").spec()
print(list(spec.outputs))        # 有哪些输出端口
print(list(spec.inputs))         # 有哪些输入端口
```

```bash
verdi plugin list aiida.calculations abacus.abacus
verdi plugin list aiida.workflows abacus.base
```
