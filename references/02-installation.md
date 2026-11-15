---
verified: 2026-11
applies_to: "aiida-core>=2.6,<3"
---

# 2. 安装与配置

三步配置：**profile → computer → code**，最后装赝势并启动 daemon。
所有命令都能在 `install/` 里找到对应脚本，参数集中在 `install/config.env`。

> 参考实现：`scripts/aiida/aiida-config/teaching/teaching.ipynb`（原版教程）、
> `aiida-ubuntu-quickstart`（一键脚本）。本仓库把它们参数化。

## 2.1 环境

```bash
conda create -n aiida python=3.10 -y
conda activate aiida
pip install aiida-core==2.8.*
pip install aiida-abacus aiida-vasp aiida-quantumespresso aiida-fleur
pip install aiida-common-workflows aiida-pseudo aiida-submission-controller
```

可加 `aiida-phonopy`、`ase`、`pymatgen`。检查入口点：

```bash
verdi status          # 此时还没有 profile，会提示创建
reentry scan -r aiida # 旧版需要；2.x 一般不必
```

## 2.2 profile：数据存哪

两种后端：

```bash
# A. SQLite + zmq（单机、零依赖，适合练手/教学）
verdi profile setup core.sqlite_dos -n \
  -p profile_<name> --no-set-as-default \
  --email you@example.com --first-name <first> --last-name <last> \
  --institution <inst> --broker zmq \
  --filepath "$HOME/data/aiida_profile/profile_<name>"

# B. PostgreSQL + RabbitMQ（生产）
verdi profile setup core.psql_dos -n \
  --profile-name <name> --set-as-default \
  --email you@example.com --first-name <first> --last-name <last> \
  --institution <inst> --use-rabbitmq \
  --database-username aiida_user --database-password <pw> \
  --database-name aiida_db --database-engine postgresql_psycopg \
  --database-hostname 127.0.0.1 --database-port 5432 \
  --repository-uri "file:///path/to/repository"
```

启动消息代理（psql 后端必须有 RabbitMQ）：

```bash
# conda 环境里的 rabbitmq-server 可直接用，或系统服务
rabbitmq-server -detached
verdi profile list
verdi profile setdefault <name>     # 需要时可切换
```

## 2.2bis 没有系统服务时：conda 自带 PostgreSQL + RabbitMQ

笔记本 / 容器 / Windows 上没有 root 时，可以直接用 conda 包（这也是很多人的第一套环境）：

```bash
conda install -c conda-forge postgresql
conda install -c conda-forge rabbitmq-server=3.8.3   # 版本要和 aiida-core 兼容，见 wiki

# 初始化一个数据库目录（放在用户目录下）
mkdir -p ~/data/aiida_profile/pgdata
initdb -D ~/data/aiida_profile/pgdata

# 用非默认端口起（5433 常用来避开系统里的 postgres）
pg_ctl -D ~/data/aiida_profile/pgdata -o "-p 5433" -l ~/data/aiida_profile/pg.log start
psql -h 127.0.0.1 -p 5433 -d postgres

# psql 里建库建用户，并固定时区（AiiDA 的时间戳按库时区显示）
CREATE USER aiida_user WITH PASSWORD 'change-me';
CREATE DATABASE aiida_db OWNER aiida_user;
ALTER DATABASE aiida_db SET timezone TO 'Asia/Shanghai';   -- 或 'Etc/GMT-8'
GRANT ALL PRIVILEGES ON DATABASE aiida_db TO aiida_user;
\l    -- 列库
\du   -- 列用户
\q

rabbitmq-server -detached
```

profile 里把端口写成 5433：

```bash
verdi profile setup core.psql_dos -n \
  --profile-name aiida --set-as-default \
  --email you@example.com --first-name F --last-name L --institution INST \
  --use-rabbitmq \
  --database-username aiida_user --database-password change-me \
  --database-name aiida_db --database-engine postgresql_psycopg \
  --database-hostname 127.0.0.1 --database-port 5433 \
  --repository-uri "file://$HOME/data/aiida_profile/repository"
```

**连接延迟**（多机/远程 DSN 时先测，别等 AiiDA 超时才发现网络不对）：

```bash
time psql -h 127.0.0.1 -p 5433 -U aiida_user -d aiida_db -c "\q"
```

**开机/激活即起**：把三条命令写进 conda 的 `activate.d`，`conda activate aiida` 时自动执行：

```bash
mkdir -p "$CONDA_PREFIX/etc/conda/activate.d"
cat > "$CONDA_PREFIX/etc/conda/activate.d/aiida.sh" <<'SH'
pg_ctl -D "$HOME/data/aiida_profile/pgdata" -l "$HOME/data/aiida_profile/pg.log" start 2>/dev/null || true
rabbitmq-server -detached 2>/dev/null || true
verdi daemon status >/dev/null 2>&1 || verdi daemon start 2>/dev/null || true
SH
```

> 时区：库时区设成 `Asia/Shanghai`（或 `Etc/GMT-8`）后，`verdi process list` 的
> ctime/mtime 才和本地一致；不改的话默认 UTC，容易把"晚了 8 小时"当成故障。

## 2.3 computer：提交到哪

先确认 ssh 能通：

```bash
ssh <host> whoami
```

```bash
verdi computer setup \
  --label <cluster> --hostname <ip-or-host> \
  --description "SLURM cluster" \
  --transport core.ssh_async --scheduler core.slurm \
  --shebang '#!/bin/bash' \
  --work-dir "/path/on/cluster/aiida_work" \
  --mpirun-command "mpirun -np {tot_num_mpiprocs}" \
  --mpiprocs-per-machine 56 \
  --default-memory-per-machine 50000000 \
  --non-interactive

verdi computer configure core.ssh_async <cluster> -n \
  --host <host> --backend asyncssh --safe-interval 5.0 \
  --no-use-login-shell --max-io-allowed 8

verdi computer test <cluster>   # 必须全绿
```

要点：

- `work-dir` 是集群上 AiiDA 的临时目录，要可写；
- `mpirun-command` 里的 `{tot_num_mpiprocs}` 由每次提交的 `resources` 决定；
- 登录节点资源有限，`computer test` 只测 ssh 和文件读写，不测计算。

## 2.4 code：跑哪个可执行文件

```bash
verdi code create core.code.installed \
  --label abacus_lts --description "ABACUS 3.10 on <cluster>" \
  --default-calc-job-plugin abacus.abacus \
  --computer <cluster> \
  --filepath-executable /path/to/abacus \
  --prepend-text '
module purge
module load gcc/12.1.0
' --use-double-quotes --with-mpi --non-interactive
```

- `--default-calc-job-plugin` 决定这个 code 交给哪个插件的 CalcJob；
- `--prepend-text` 里放 `module load` / `source spack`，每个作业开头执行；
- `--with-mpi` 与 `mpirun-command` 配合；单核作业把 `resources` 设成 1 即可。

**注意**：scheduler 机器上，`metadata.options` 必须带 `queue_name`，
否则 `sbatch` 报 `No partition specified or system default partition`。

## 2.5 赝势 / 轨道

```bash
# 通用：SSSP
aiida-pseudo install sssp -v 1.3 -x PBE -p precision

# ABACUS：UPF + 数值原子轨道家族
aiida-pseudo install family /path/to/upf/*.UPF <family-name> -x PBE
aiida-pseudo install family /path/to/orbital/*.orb <family-name> -x PBE
```

## 2.6 daemon

```bash
verdi daemon start
verdi daemon status
verdi status           # 全绿：version / config / profile / storage / broker / daemon
```

改了已安装插件的源码后必须 `verdi daemon restart`（daemon 持有旧模块）。

## 2.7 自检

```bash
python install/06-doctor.py            # 人读报告
python install/06-doctor.py --json     # 机器可读
python install/06-doctor.py --strict   # 环境不在 versions.yaml 支持范围时退出码非 0
```
