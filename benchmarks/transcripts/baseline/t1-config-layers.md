【AiiDA 概念要点，纯知识作答，未读任何本地文件】

1) Profile（配置档/档案）
- AiiDA 的环境隔离单元：一个 profile = 一整套 存储后端（PostgreSQL 数据库）+ 文件仓库（repository，存原始输入/输出文件）+ 消息代理（RabbitMQ broker）的绑定，外加默认用户邮箱等配置。
- 存在 ~/.aiida/config.json；用 verdi profile list/switch/setup 管理（新版 verdi profile setup core.psql_dos）。
- 一套安装可有多套 profile（不同项目、生产/测试、不同数据库），数据完全隔离。
- 所有 Computer、Code、Node 都归属某个 profile；换 profile = 换整套数据。verdi status 显示 profile/storage/repository/daemon 状态。

2) Computer（计算资源）
- 对"一台能跑计算的机器/集群"的抽象，回答"怎么连上去、怎么排队提交"。
- 属性：hostname、transport 插件（local/ssh，决定登录与传文件）、scheduler 插件（direct/slurm/pbspro/sge/lsf）、work directory 模板、mpirun 命令、prepend/append、默认 MPI 进程数、shebang。
- 流程：verdi computer setup → configure（SSH/认证）→ test（连通性与目录可写验证）。localhost 是代表本机的特殊一台，建 profile 时通常顺带创建。
- 它只知道"机器"，不知道机器上装了什么软件。

3) Code（代码/可执行程序）
- 对"某个具体可执行程序 + 怎么调用"的抽象，回答"哪个程序、装在哪、用哪个插件解析"。
- 属性：所属 Computer、远程绝对路径（如 /opt/abacus/bin/abacus）、default_calc_job_plugin（对应 CalcJob 入口点，如 quantumespresso.pw、abacus.abacus，决定输入生成与输出解析）、是否 mpirun、默认参数。
- AiiDA 2.x：AbstractCode 基类下有 InstalledCode（传统型，绑 computer + 绝对路径）与较新版本引入的 PortableCode（容器化/可移植，可不绑 computer）。
- 同一程序装两台机器 = 两个 Code；同机两个版本 = 两个 Code。命令：verdi code create/list/show。

4) 三者关系
- 容器关系：Profile ⊃ {Computer, Code, Node}，Profile 是数据与配置边界。
- Computer ↔ Code 是一对多：一个 Computer 可注册多个 Code；每个 InstalledCode 必须指向一个 Computer（code.computer 必填），Computer 不反向引用 Code，所以先建 Computer 再建 Code。
- 提交时串联：CalcJob 指定 code → 引擎从 code.computer 取 transport+scheduler → 上传输入到 workdir → 调度器提交；CalcJobNode 同时记录 code 与 computer 引用，保证 provenance 可追溯。
- 一句话：Profile 是"哪套数据库/仓库"，Computer 是"哪台机器、怎么连"，Code 是"那台机器上的哪个程序、怎么跑"。

5) Daemon
- verdi daemon start/stop/status/logshow；后台常驻进程（主进程 + N 个 worker，circus + RabbitMQ），worker 数可调。
- 核心职责：异步执行引擎。submit() 只把 CalcJob 写库标为 created；真正远程动作由 daemon 完成：(1) 轮询 DB/broker 取 created/waiting 任务；(2) 上传输入文件到目标 Computer 并按 scheduler 提交；(3) 定期 poll 调度器状态 waiting→running→done；(4) 结束后 retrieve 输出、调 parser 解析、输出 Data 存进 profile、状态推进为 finished/failed/excepted；(5) 驱动 WorkChain/WorkGraph 状态机（子步骤、重试、清理、异常处理）。
- 与 profile 绑定：daemon 一次只服务一个 profile，须能访问该 profile 的 DB+broker 及各 Computer 的 transport（通常跑在有 SSH 权限的机器上）；verdi daemon status 看当前 profile worker 情况。
- 不做的事：不亲自算科学问题（真正计算在 Computer 调度器下），只做编排、传输、拉取、解析、记账。
- 不用 daemon 也能跑：run() 为阻塞式本地同步执行，适合调试；远程、长时间、工作流任务必须靠 daemon。

补充说明：本任务明确要求"仅凭自有知识、不读文件、不跑命令、不用 skill"，故未做任何本地核查；以上为通用知识性回答，未涉及当前 bcc_uranium 目录的任何具体配置。
