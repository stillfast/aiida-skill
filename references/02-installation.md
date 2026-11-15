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
