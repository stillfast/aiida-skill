# Prompts used in the pilot (identical across arms)

The control sentence appended to the **baseline** prompts (see README):

> （评估要求：仅凭你自己的知识回答，不要读取本地文件、不要运行命令，也不要使用任何预置 skill。）

The **skill** arm gets the same task text without that sentence, so the only
difference is whether the `aiida` skill is installed and may be used.

## t1-config-layers

AiiDA 里 profile、computer、code 分别是什么？三者是什么关系？daemon 负责什么？用中文给要点。

## t2-build-builder

用 AiiDA 的 aiida-abacus 插件写一段 Python：为 diamond Si（a=5.43 Å）构建一个单点 SCF 的 builder，不提交。给出代码和必要说明。

## t3-diagnose-partition

下面是一个 AiiDA 进程的状态和日志，请判断问题并给出修复步骤：

574627 AbacusCalculation ⏸ Waiting — Pausing after failed transport task: submit_calculation failed 5 times consecutively

verdi process report 574627 末尾：
aiida.schedulers.scheduler.SchedulerError: Error during submission, retval=1
stdout=
stderr=sbatch: error: Batch job submission failed: No partition specified or system default partition

## t4-diagnose-scf302

一个 ABACUS SCF 作业：跑满 50 个电子步，DRHO 从 0.17 起在 0.03–0.45 之间震荡，最后打印 CONVERGENCE HAS NOT BEEN ACHIEVED，CalcJob exit 302。请解释原因并给出调参方案。

## t5-batch-procedure

我要用 AiiDA 批量跑 20 个结构的 VASP 结构弛豫，怎么组织？给出流程和脚本结构。
