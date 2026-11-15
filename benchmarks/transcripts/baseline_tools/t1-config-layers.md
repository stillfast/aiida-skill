## 一句话总览
四者是「层级容器 + 执行器」关系：Profile ⊃ Computer ⊃ Code，Daemon 是跑在某个 Profile 之上的后台执行引擎。
Profile = 一个隔离的 AiiDA 实例（数据库+仓库+broker）；Computer = 一台算力机器；Code = 某台机器上的某个可执行程序；Daemon = 替你把 Process 异步跑完的后台进程组。

## 1. Profile（配置档）
- 本质：一套「存储后端 + 进程控制后端 + 元信息」的注册信息。
- 内容：storage backend（core.psql_dos：PostgreSQL 库 + 文件仓库）、process_control（core.rabbitmq）、profile UUID、default_user_email、options（caching 开关）。
- 存在形式：~/.aiida/config.json（本机已有 profile：aiida_profile，core.psql_dos + core.rabbitmq）。
- 关键点：隔离性。不同 profile 的 Node/Computer/Code 完全互不可见。
- 常用：verdi profile list/show/setdefault；verdi profile setup core.psql_dos。

## 2. Computer（计算资源）
- 描述「一台机器/一个集群」，是 profile 数据库里的一条记录，不绑定具体程序。
- 字段：label、hostname、transport（local / core.ssh）、scheduler（direct / core.slurm / core.pbspro …）、workdir、mpirun 命令、默认队列/资源。
- 两段式：computer setup → computer configure core.ssh → computer test。

## 3. Code（可执行程序）
- 描述「某台 computer 上的某个可执行文件」+「用哪个输入插件解释它」。
- 字段：label、computer（必填）、remote_abs_path、input_plugin（abacus.abacus、quantumespresso.pw）、prepend/append、是否 local。
- 同一程序在不同机器上要各建一个 Code；一个 computer 可挂多个 Code。
- 常用：verdi code create core.code.installed --computer --remote-abs-path --input-plugin。

## 4. 三者关系（运行时调用链）
1. submit 一个 CalcJob 并指定 code；2. 由 code 拿到 computer；3. 由 transport 连机器、在 workdir 建沙盒、上传输入；4. 用 scheduler 提交；5. 结束后 retrieve，用 code 指定的 input_plugin 解析，结果存回当时那个 profile。
所以：Code 必须挂在 Computer 上，Computer 与 Code 都活在某个 Profile 里。verdi status 是排障第一站。

## 5. Daemon
- 是什么：verdi daemon start 拉起的后台进程组（1 主 + N worker），只在某个 profile 下工作。
- 负责：通过 RabbitMQ 接收 submit 的 Process 并驱动状态机；对 CalcJob 建目录/上传/提交/轮询/retrieve/parse/存库；对 WorkChain 自动触发下一步、处理分支与上下文、失败重试、pause/play/kill；多 worker 并行。
- 边界：verdi run / run() 前台同步执行不需要 daemon；submit() 必须有 daemon。

## 6. 易错点
- 混淆 computer 与 code；换机器/换路径不重建 code；忘记 computer configure；daemon 或 broker 没起导致 process 停在 created/waiting；插件选错 → 解析失败。
