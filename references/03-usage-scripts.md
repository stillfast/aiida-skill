---
verified: 2026-11
applies_to: "aiida-core>=2.6,<3"
---

# 3B. 使用（二）：再写 scripts

workflow 跑通一次之后，scripts 层负责**成批地跑**和**把结果变成表/图**。
分层参考 `acwf-verification-scripts`（`aiidateam/acwf-verification-scripts`）：

```
2-submit/    批量提交（SubmissionController）
3-analyze/   提取 → 拟合 → 出图/JSON
4-export/    归档（AiiDA archive）
```

> 注意：上游那套脚本 pin 的是 `aiida-core==1.6`。**借用它的结构，不要直接装它。**

## 4.1 批量提交：SubmissionController

核心是把"每个任务"描述成一个可去重的键（extras），控制器负责并发上限、
断点续跑、去重：

```python
from aiida import orm
from aiida.engine import submit
from aiida_submission_controller import FromGroupSubmissionController


class EosSubmission(FromGroupSubmissionController):
    def __init__(self, code_label, **kwargs):
        super().__init__(**kwargs)
        self._code = orm.load_code(code_label)

    def get_extra_unique_keys(self):
        return ('element', 'configuration')      # 每个任务的唯一键

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

自己写一个 for 循环也能提交，但要自己处理：并发、失败重试、重复提交、
中断后续跑。任务超过 10 个时，用控制器。

## 4.2 结果提取

只读 outputs，不碰数据库内部：

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

统一成 `pandas.DataFrame` → CSV/JSON，后面拟合和画图都基于它。

## 4.3 分析：EOS 拟合示例

```python
import numpy as np
from scipy.optimize import curve_fit

def birch_murnaghan(V, E0, V0, B0, Bp):
    eta = (V0 / V) ** (2 / 3)
    return E0 + 9 * V0 * B0 / 16 * ((eta - 1) ** 3 * Bp
            + (eta - 1) ** 2 * (6 - 4 * eta))

popt, _ = curve_fit(birch_murnaghan, data.volume, data.energy, p0=[data.energy.min(), data.volume.min(), 0.5, 4])
```

## 4.4 导出与归档

```bash
verdi archive create results.aiida --groups <group-label>
verdi archive import results.aiida        # 在另一台机器复现
```

归档是"可移交的溯源图"，比 CSV 更适合给合作者或投稿附件。

## 4.4bis 本仓库的可运行例子

`examples/eos-scan/` 把这一节的两层拆开演示：

```bash
python workflow.py --dry-run                    # 只构建 + 校验（打印真正生效的设置）
python submit.py --code qe@mycluster --element U
python analyze.py <pk> --json eos.json          # 读 structures/total_energies，拟合 BM
```

读结果时用 `node.base.links.get_outgoing(link_type=LinkType.RETURN).nested()`，
输出是 `structures` / `total_energies` 两个嵌套命名空间（按同一 index 对应）；
官方 CLI 也能直接画图：`aiida-common-workflows plot eos <pk>`。

## 4.5 scripts 层的一些原则

- **只消费 outputs**，不修改节点；
- 每个脚本有 `--dry-run` / `--limit`，大批量前先小批量验证；
- 失败要**分类记录**（exit code + pk），而不是 `except: pass`；
- 分析脚本要能在"部分失败"的数据上跑（跳过失败项并报告数量）；
- 所有中间结果落 CSV/JSON，图从数据重新生成，保证可复现。
