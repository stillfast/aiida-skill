# 平时怎么用这个 skill

三种用法，按你需要介入的程度排序。

## 1. 直接说需求（最常用）

skill 已经装进 DSH（`$DSH_HOME/skills/aiida` → 本仓库），**不需要任何命令**。
在对话里自然描述任务即可，agent 会自己加载它：

| 你说 | agent 会做什么 |
|---|---|
| "用 ABACUS 给这个 α-U 结构做个 SCF" | 先 `verdi status` + `06-doctor.py` 探环境 → 查 `abacus.base` 实际端口 → 构建 builder → 打印 queue/墙钟/核数 → dry-run 校验 → 你确认后提交 |
| "564954 这个作业为什么失败" | `verdi process show/report` → 看 exit code 属于哪一层 → 查 `troubleshooting/exit-codes.md` 与 cases → 给结论和下一步 |
| "帮我把 defects 的两个卡住的作业重提" | 先定位卡住原因（如 `No partition specified`）→ 修输入 → kill → 重提 → 核对子作业的 `queue_name` |
| "我想批量跑 20 个结构的 relax" | 建议先跑通单个（workflow 层），再给 SubmissionController 的 scripts 层模板 |
| "AiiDA 里 profile/computer/code 是什么关系" | 直接读 `SUMMARY.md` 里的心智模型回答 |

**提需求时最好附上**：`pk`/`uuid`、完整报错原文、exit code、集群与队列名。
agent 会用这些去查节点，而不是猜。

## 2. 显式点名 skill

如果想让 agent 一定按这套流程走（比如怕它凭记忆瞎写端口）：

> 用 **aiida** skill 来做：……

或者开头就要求：

> 先跑 `install/06-doctor.py`，再按 skill 的 SOP 走。

## 3. 人自己用（不经过 agent）

```bash
cd ~/work/aiida-skill
less SUMMARY.md                 # 10 分钟看懂 AiiDA
python install/06-doctor.py     # 环境自检
less references/02-installation.md
```

装新环境时：抄 `install/config.env.yeesuan.example` → 改路径/队列 → 依次跑 `install/0*.sh`。

## 怎么知道它有没有用

`benchmarks/` 里放着一次对照实验（同样的 5 个问题，分别在不给 skill、只给工具、给 skill 三种条件下回答）：
纯知识 0.62 → 允许查环境 0.89 → 加 skill 0.91。复现方法和局限见
[`benchmarks/results/pilot-2026-11-15.md`](benchmarks/results/pilot-2026-11-15.md)。

## 它怎么"自己更新"

- skill 目录是指向 `~/work/aiida-skill` 的符号链接，`git pull` 之后 DSH 的文件监听会重新读取，**不用重装、不用重启**；
- 环境变了先跑 `06-doctor.py`：版本超出 `versions.yaml` 支持范围会明确告诉你，而不是照着旧文档瞎跑；
- 你每踩一个新坑，就让 agent 把它写成 `troubleshooting/cases/NNN-*.yaml` 提交——仓库就是这么长起来的。

## 什么时候不需要它

- 单纯问 DFT 物理参数（INCAR 里 `ISMEAR` 怎么选、k 网格多少）——这是计算物理问题，不是 AiiDA 问题；
- 已经在跑、只想看进度：`verdi process list` 就够了。

## 一句提醒

skill 的价值是**流程**（先探环境 → 再查端口 → 先 dry-run → 再按三层排查），
不是"背答案"。所以它永远让你先看当前环境，而不是相信文档里的旧版本号。
