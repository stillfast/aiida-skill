## 结论
不是 ABACUS / 集群问题，是 AiiDA 提交参数丢失：574627 的 metadata.options 落成了 AiiDA 默认值（没有 queue_name，num_mpiprocs_per_machine=1），生成的 _aiidasubmit.sh 里没有 #SBATCH --partition，而 yeesuan 的 slurm 没有默认分区 → sbatch 立即 retval=1。AiiDA 对 transport task（submit）做指数退避重试，连续 5 次后把进程 pause。verdi process play 救不回来，脚本是 upload 阶段一次性生成并上传的。

## 核实证据（profile aiida_profile，AiiDA 2.8.0）
1. 574627：computer yeesuan（core.slurm），code abacus_lts。当前状态已是 KILLED，不是 Waiting。
2. get_metadata_inputs()['metadata']['options'] = {'withmpi': True, 'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 1}, 'parser_name': 'abacus.abacus', ...} —— 无 queue_name，rank 掉到 1。
3. _aiidasubmit.sh：#SBATCH --nodes=1 / --ntasks-per-node=1 / --mem=48828，没有 --partition。对照正常作业 575160：--partition=d2_ys / --ntasks-per-node=56 / --time=1-00:00:00 / --mem=1536000。
4. 调用链：574069 → 574443（label='defects resubmit of 574069'，get_builder_restart）→ 574543（host）→ 574627。574443 和 574069 的 inputs 里都没有 base.abacus.metadata（查 link labels 确认）：options 只活在 dynamic base 命名空间的 builder 里，get_builder_restart() 不持久化它 → 重提交时整体丢失。
5. 原跑 574069 的子作业 574150 是 queue=d2_ys、56 ranks、86400 s → 首跑正常，只有 restart 路径坏。
6. 时间线：五次 SchedulerError 后 pause；16:41 workflows/defects/abacus.py 被改（新增 options 端口 + require_partition）；18:07 daemon 重启；之后 575036 这批子作业都带 queue_name 了。

## 修复步骤
A. 收尾：verdi process list -a --paused；清远端 verdi calcjob cleanworkdir 574627；不要 verdi process play 574627。
B. 重提交用普通 input 端口 options：
   b = orig.get_builder_restart(); b.options = orm.Dict(dict={"queue_name": "d2_ys", "max_wallclock_seconds": 86400, "max_memory_kb": 1572864000, "resources": {"num_machines": 1, "num_mpiprocs_per_machine": 56}}); submit(b)
C. 或走 CLI：defects 提交加 --metadata yeesuan_ys_24h。
D. 现在有 fail-fast：require_partition() 在两个 leg 之前检查，漏 options 会直接 ValueError。
E. 提交后验收：verdi calcjob inputcat <new_pk> _aiidasubmit.sh | grep -E 'partition|ntasks-per-node|mem'；squeue -u $USER。
F. 兜底（不建议默认开）：computer prepend_text 加 "#SBATCH --partition=..."；集群侧正解是加 Default=YES。
G. 同链路坑：574069 的 diag4-2-2 当初是 defect relax 腿 exit 301 → 401/402 才 SKIPPED；当前 575036 已在重算 diag4-2-2，若只是补这个 cell，574627 这条链不必再提交。

## 未决
是否把 options 端口/require_partition 那批未提交改动 commit + 跑 tests；是否需要实际重提交某条链（会真实占队列，未执行）。
