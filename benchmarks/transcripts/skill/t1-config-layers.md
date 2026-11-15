【一句话】profile = 数据存哪（一整套库）；computer = 算在哪台机器、怎么排队；code = 调哪个可执行文件。daemon = 把 submit() 出去的进程真正跑起来/盯完/取回结果并解析的后台服务。

【层次关系】profile ⊃ computer ⊃ code，严格一对多嵌套：
- profile 是顶层容器：storage 后端（PostgreSQL/SQLite）+ repository 文件库 + broker（RabbitMQ/zmq）+ 用户信息。computer、code、所有 Node 都归属某个 profile。
- computer 描述"机器"：hostname、transport（core.ssh/core.local）、scheduler（core.slurm/core.direct）、work-dir、mpirun 命令、默认核数/内存、ssh 认证。
- code 描述"程序"：可执行文件绝对路径 + 所属 computer + default_calc_job_plugin + prepend/append text（module load）+ 是否 with_mpi。code 是 Node（InstalledCode），所以 CalcJob 会与它连一条输入边 —— 追溯时能查到当时用的哪个二进制。同一可执行文件在两台机器上必须建两条 code 记录；一台机器可挂多个 code。另有 core.code.abstract（不绑机器，运行时才解析），可移植工作流用。
- 一次 CalcJob 的输入 = code + structure + parameters/kpoints/pseudos + metadata.options（queue_name、resources、walltime）；computer 由 code 自动推出。

【daemon 负责什么】不是它算，是它执行与转运：
1) 从存储里捞 status=CREATED 的进程并启动（submit 只写库，没 daemon 会一直卡在 CREATED；run() 前台同步执行不需要 daemon）；
2) 建远端 work-dir、上传输入文件、渲染提交脚本并交给调度器；
3) 定期轮询调度器作业状态；
4) 结束后 retrieve 输出文件回本地 repository；
5) 调 parser 解析 → 生成输出节点与 ExitCode；
6) 驱动 WorkChain：等待子进程、按 handler 重试/转移。
要点：每个 profile 一个 daemon；daemon 挂了不影响已提交的作业，但轮询与 retrieve 暂停；改过插件源码必须 restart。

【排错对应层】profile → "Could not determine the current profile"；computer → Computer test 失败/sbatch: command not found；code → Code not found/缺 module；"sbatch: No partition specified" 属 metadata.options.queue_name 没传到；进程长期 created = daemon 没起。

备注：当前 shell 里 verdi 不在 PATH，要先把对应 conda 环境 activate 才能跑 verdi status 自查。详细依据见 skill 仓库 /home/liguozhou/.cache/dsh/skills/aiida/references/02-installation.md 与 SUMMARY.md。
