【AiiDA 574627 诊断结论】

一、定性：ABACUS 根本没启动。故障在 AiiDA CalcJob 的 submit 阶段：sbatch 被调度器拒绝，连续失败 5 次后进程被 pause，所以是 ⏸ Waiting 而不是 Failed。

二、根因：报错 "No partition specified or system default partition" 表示
1) _aiidasubmit.sh 里没有 "#SBATCH --partition=..."；
2) 该 Slurm 集群没有配置默认分区。
core.slurm 只有在 metadata.options.queue_name 非空时才写 --partition。

三、先诊断（不动任何东西）
1. sinfo -s / scontrol show config | grep -i DefaultPartition
2. scontrol show partition <name>
3. verdi calcjob gotocomputer 574627 看 _aiidasubmit.sh 头部
4. verdi process show 574627 → metadata.options → verdi node attributes
5. verdi computer show / computer test；daemon logshow
6. 手工复现：sbatch --no-requeue _aiidasubmit.sh

四、修复（二选一）
方案 A（集群侧）：slurm.conf 增加 DefaultPartition=<真实分区名>，scontrol reconfigure；然后 verdi process play 574627（复用已生成的脚本）。
方案 B（用户侧）：builder.metadata.options.queue_name = 'cpu'；resources / walltime / account。已暂停的 574627 用 play 拿不到新选项——提交脚本/选项在暂停时已固定。所以要么按 A 修默认分区后 play，要么 verdi process kill 574627 后用修正选项重新 submit（更干净）。不建议手工改远端 _aiidasubmit.sh。

五、验证：squeue -u $USER；verdi process list；verdi calcjob outputcat；daemon logshow。

六、防复发：集群固定 DefaultPartition；AiiDA 侧把 queue_name 固化；定期 sinfo 核对与 computer test。

（以上全部基于通用 AiiDA/Slurm 知识作答，未读本地文件、未执行命令、未调用预置 skill。）
