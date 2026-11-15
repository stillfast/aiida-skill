诊断完成（已在本机 aiida_profile 上实证）。结论：不是 ABACUS 或集群的问题，是这次重提交把 SLURM 分区丢了——子 CalcJob 的 metadata.options 里没有 queue_name。

## 证据
1. yeesuan 上没有系统默认分区：scontrol show config 无 DefaultQueue，sinfo 只有 q_ysuan / q_ysuan_384 / d2_ys。sbatch 不带 -p 必然报这句。
2. 574627 的 _aiidasubmit.sh 只有 --nodes=1 --ntasks-per-node=1 --mem=48828：没有 --partition，没有 --time，且 mpirun -np 1。
3. 同集群正常任务（574427/574455/575112 …）是 queue=d2_ys, 1×56 ranks, 86400 s；574627 是 queue=None, 1 rank, wallclock=None——就是 AiiDA 默认值。

## 根因链
574443 AbacusDefectsWorkChain（label "defects resubmit of 574069"）→ 574543 AbacusBaseWorkChain → 574627。
- 574443 由 temporary/resubmit_574069.py 生成：它用 get_incoming() 只复制 link；原来的调度选项是以 base__abacus__metadata__options 形式传的 metadata（不是 link），因此被静默丢掉。
- AbacusDefectsWorkChain._child_options() 只认 base.abacus.metadata.options 和 options 端口，两者都空 → 不给子 CalcJob 写 options → 子任务按 AiiDA 默认（1 rank、无 queue、无 wallclock）出去。
- execmanager.submit_calculation 抛 SchedulerError 后走 exponential_backoff_retry，5 次后 PAUSED。

## 修复步骤
1. 别再动 574627/574543/574443（节点不可变，且已被 KILL），直接重提交。
2. 重提交时显式给 options，推荐用 options 端口（REGULAR input，get_builder_restart() 不会丢）：
   inputs["options"] = Dict(dict={"queue_name": "d2_ys", "resources": {"num_machines": 1, "num_mpiprocs_per_machine": 56}, "max_wallclock_seconds": 86400, "max_memory_kb": 1572864000, "withmpi": True})
   等价写法：inputs["base"]["abacus"]["metadata"] = {"options": {...}}（能提交但 resubmit 会再丢）。
3. 代码层 fail-fast 已存在但未提交：require_partition()。请把 workflows/defects/abacus.py、input_builders/defects/abacus.py 等改动 commit。
4. 验证：新 calcjob 提交后 30 s 内 ssh 远端 grep -E "partition|ntasks|--time" _aiidasubmit.sh 应看到 #SBATCH --partition=...、--ntasks-per-node=56、mpirun -np 56。
5. 防复发：任何直接 submit 到 yeesuan 的 CalcJob 都必须带 queue_name；优先用 static/metadata.yml 的 preset。

## 另外
- 574627 是 1 个 MPI rank；只补 queue 不补 resources，432 原子 LCAO 也跑不动，必须同时给 56 ranks。
- 现在有两个 19:29/19:30 创建的 AbacusCalculation 575184/575188（"diamond Si SCF (test)"）同样缺 queue_name（8 ranks/3600 s），一旦 submit 会立刻复现同一错误。
- AiiDA 的 hash 里 queue_name/max_wallclock_seconds/max_memory_kb 是 ignored，补这些不破坏缓存；但 resources 参与 hash。
