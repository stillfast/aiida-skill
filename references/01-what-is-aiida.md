---
verified: 2026-11
applies_to: "aiida-core>=2.6,<3"
---

# 1. AiiDA 是什么，配合什么使用

## 1.1 定义

AiiDA 是一个**面向计算科学的工作流引擎 + 溯源数据库**。它不做 DFT，做的是：

| 能力 | 传统做法 | AiiDA 的做法 |
|---|---|---|
| 提交 | 手写 sbatch / 输入文件 | 描述 inputs，由插件生成文件并提交 |
| 追溯 | 翻目录、看 `history` | 每个输入/输出都是带 UUID 的节点，连成图 |
| 重试 | 人工发现失败再重来 | WorkChain 里的 handler 按 exit code 自动处理 |
| 批量 | for 循环写 shell | process 输入是数据节点，可以程序化生成 |

设计上的三个关键词：

- **Provenance（溯源）**：任何结果都能回答"它由哪些输入、哪个 code、哪次运行产生"。
- **Reproducibility（可复现）**：节点不可变；换参数 = 新节点，旧记录保留。
- **Workflow（工作流）**：把"SCF → 弛豫 → 收敛检查 → 重启"这类流程写成可重入的 Process。

## 1.2 组成

```
aiida-core           引擎（Process 接口、Node 模型、verdi CLI）+ 存储后端
  ├── PostgreSQL     主数据库（节点元数据、链接）——生产用
  ├── SQLite         轻量后端（单机练手）
  ├── RabbitMQ       进程间通信，daemon 依赖它
  ├── 文件仓库       大对象（结构、取回的文件）落盘，数据库只存哈希
  └── daemon         后台 worker，真正执行和轮询调度器的进程
插件（entry points）  每个代码一个：CalcJob（输入生成 + parser）+ WorkChain（流程）
  ├── aiida-abacus
  ├── aiida-vasp
  ├── aiida-quantumespresso
  └── aiida-fleur
aiida-common-workflows 跨代码的统一接口（relax / eos / bands … + 协议档）
脚本层（如 acwf-verification-scripts）批量提交 + 结果分析
```

`verdi` 是命令行入口；所有操作最终都落到 "Process" 和 "Node" 两种对象上。

## 1.3 数据模型（够用就行）

| 类型 | 例子 | 说明 |
|---|---|---|
| **Data** | `StructureData`、`Dict`、`Int`、`FolderData` | 计算的输入/输出，store 之后不可变 |
| **CalcJob** | `AbacusCalculation`、`VaspCalculation` | 一次真实的外部程序调用；有 `retrieved`（本地文件）、`remote_folder`（集群路径）、`exit_status` |
| **WorkChain** | `abacus.relax`、`vasp.v2.relax` | 编排多个 CalcJob，可重试、可分支 |
| **ProcessNode 的 outputs** | `output_parameters`、`misc`、`structure` | 供下游读取 |

链接（link）把节点连成图。`verdi process show <pk>` 看直接输入输出，
`verdi node graph generate <pk>`（或 `Graph()`）可以画整张图。

## 1.4 进程状态与 exit code

- `ProcessState`：`created → waiting → running → finished`（另有 `exited`、`killed`）。
- `exit_status`：`0` 成功；`None` 还没结束；非 0 的**含义由插件定义**，不是一个统一编号。
  因此排查时"看 exit code"必须结合**是哪个插件**（见 `04-troubleshooting.md`）。
- `verdi process report <pk>` 输出该进程的日志；`verdi process status <pk>` 输出子进程树。

## 1.5 什么时候不该用 AiiDA

- 一次性的、参数固定的单点计算：直接写 sbatch 更快。
- 需要极低延迟的交互式调试：AiiDA 有 daemon 轮询开销。
- 团队里没有人愿意维护 profile/computer/code 这套配置。

但只要出现"多结构 × 多参数"、"要追溯"、"失败要自动重试"中的任意一条，
AiiDA 的收益就远大于配置成本。

## 1.6 生态里的相邻工具

| 工具 | 作用 |
|---|---|
| ASE / pymatgen | 结构构造与转换（`StructureData(ase=atoms)`） |
| aiida-pseudo | 赝势家族管理（SSSP 等） |
| aiida-phonopy | 声子后处理 |
| aiida-common-workflows | 跨代码统一接口，做验证/对比 |
| aiida-submission-controller | 批量提交控制器（本仓库 `03-usage-scripts.md` 用到） |
