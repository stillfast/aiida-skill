---
verified: 2026-11
applies_to: "aiida-core>=2.6,<3"
---

# 4. 测试与故障分析

故障按"从外到内"三层排查。**先排除配置，再怀疑插件，最后才是 DFT 代码**。

```
① 配置层（profile / computer / code / metadata.options）
        ↓ 排除
② 插件层（aiida-core、aiida-abacus、aiida-vasp …）
        ↓ 排除
③ DFT 代码层（ABACUS / VASP / QE 及其 exit code）
```

## 4.1 第一层：参数配置错误

典型症状：**根本没提交上去**，或**提交上去但参数全错**。

| 症状 | 定位 | 修复 |
|---|---|---|
| `sbatch: No partition specified or system default partition` | 子 CalcJob 的 `metadata.options` 里没有 `queue_name` | 检查 options 是否真的传到子作业；见 4.5 |
| `Pausing after failed transport task: submit_calculation failed 5 times` | 上一行的后续：连续 5 次提交失败后暂停 | 修好分区/连接后 `verdi process kill` 并**重提**（暂停态 play 会用同样的坏输入） |
| `Computer test` 失败 | ssh/工作目录/调度器命令 | `verdi computer configure`、检查 `work-dir` 权限 |
| `Code not found` / 运行时 `command not found` | code 的路径或 `prepend-text` | `verdi code show <label>`，在集群上手动跑一次路径 |
| `Could not determine the current profile` | 脚本里没 `load_profile()` | 显式 `load_profile('aiida_profile')` |
| 作业 1 核跑、极慢 | `resources` 没生效 | 打印 `metadata.options['resources']` |

系统的第一步永远是：

```bash
verdi status
verdi process show <pk>
verdi process report <pk>          # 真正的异常栈在这里
verdi computer test <label>
verdi code show <label>
```

### 特别常见：metadata.options 静默丢失

**现象**：Resubmit 一个 WorkChain（`get_builder_restart()`）后，子作业没有分区。

**原因**：调度参数如果放在某个 **dynamic 命名空间** 里（例如
`base.abacus.metadata.options`），AiiDA 既不会把它存成 input link，也不会写进
`metadata_inputs`；`get_builder_restart()` 只从这两处重建，于是参数丢失，
子作业带着 AiiDA 默认值（1 核、无队列）提交。

**修复**：把 options 放在一个**普通输入端口**（如 `options` Dict）里，由
WorkChain 在 `submit` 时合并进子作业的 `metadata.options`；并加 fail-fast：
没有 `queue_name` 时直接报错，而不是等 sbatch 失败 5 次。

**验证**：

```python
load_node(orig_pk).get_builder_restart().base['abacus']   # 看 metadata 还在不在
```

## 4.2 第二层：上游仓库的 bug

判断标准：**最小复现**能在干净环境里重现，且与你的集群/参数无关。

1. 写最小脚本（一个结构、一个 WorkChain、默认协议）；
2. 在 `aiida-core` / 插件仓库的 main 分支上确认是否已修；
3. 是 bug → 开 issue（附最小脚本、版本、traceback）→ 提 PR（带回归测试）；
4. 临时绕过：用 `overrides` 改参数、或改用另一个 WorkChain，**不要**直接改
   `site-packages`（重装即丢；本地 patch 要写进 issue 里说明）。

常见的上游问题形态：

| 形态 | 例子 | 修法 |
|---|---|---|
| parser 字段缺失/列数变化 | vasprun 的 `<partial>` 列数变了 | 换解析路径（如 DOSCAR）、或修 parser |
| WorkChain 端口不一致 | 插件新版改了 namespace | 适配层兼容新旧；`verdi plugin list` 为准 |
| handler 不处理某 exit code | 被墙钟杀死（301）不触发收敛处理器 | 补 handler 或调大墙钟 |
| 默认参数不合理 | `mixing_beta=0.8` 导致电荷震荡 | 在协议/preset 里覆盖，并向上游提 issue |

## 4.3 第三层：DFT 代码本身

作业**真的跑过**，AiiDA 只是如实记录。这时看 exit code 和原始日志。
完整对照表见 [`troubleshooting/exit-codes.md`](../troubleshooting/exit-codes.md)。

快速判断：

| 现象 | 先看 | 常见原因 |
|---|---|---|
| ABACUS 301 | `_scheduler-stderr.txt`、`running_scf.log` 尾部 | 墙钟被杀、OOM、MPI/UCX 超时 |
| ABACUS 302 | `running_scf.log` 的 DRHO 列 | SCF 电荷震荡（mixing_beta 太大） |
| ABACUS 303/401 | ionic 步数、`relax_nmax` | 离子步不够 / 重试耗尽 |
| VASP 700 | `OUTCAR`、`vasp.out` | 未跑完（ZBRENT、电子步失败） |
| `Signal 9` | sacct / stderr | 内存超限被杀 |
| `DUE TO TIME LIMIT` | stderr | 墙钟不够 |

调参的经验（来自真实案例）：

- **电荷震荡**：`mixing_type=broyden, mixing_beta=0.2, mixing_ndim=20~24,
  mixing_gg0=1.5` 往往能让金属/5f 体系收敛；
- **时间不够**：先算一步 SCF 的耗时 × 预估步数，再定墙钟；LCAO 约 100 s/步、
  PW 可达 300–1300 s/步；
- **离子步跑满**：`relax_nmax` / `max_ionic_steps` 调大，或让 WorkChain
  从最新结构续算（plugin 的 handler 通常支持）。

## 4.4 诊断的固定动作

```bash
verdi process show <pk>            # state / exit_status / 输入输出
verdi process report <pk>          # 日志与 handler 处置
verdi process status <pk>          # 子进程树，定位是哪一层失败
verdi calcjob gotocomputer <pk>    # 打印集群上的 remote 目录
```

```python
node = load_node(pk)
node.outputs.retrieved.open('...') # 本地取回的文件
node.base.attributes.all           # 实际生效的 queue/resources/wallclock
```

## 4.5 复盘：把坑写下来

每个诊断完的故障写成一条 `troubleshooting/cases/NNN-<slug>.yaml`
（模板 `_template.yaml`），字段包括：症状、错误签名正则、定位步骤、根因、
修复、受影响的版本、证据（真实 pk）。这样下次遇到同样的日志可以直接匹配，
也方便在版本升级后把 `status` 改成 `fixed-upstream`。
