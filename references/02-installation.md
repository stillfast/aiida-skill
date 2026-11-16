---
verified: 2026-11
applies_to: "aiida-core>=2.6,<3"
---

# 2. Installation and Configuration

Three-step setup: **profile → computer → code**, then install pseudopotentials and start the daemon.
Every command has a corresponding script under `install/`, and the parameters are centralized in `install/config.env`.

> Reference implementations: `scripts/aiida/aiida-config/teaching/teaching.ipynb` (original tutorial),
> `aiida-ubuntu-quickstart` (one-click script). This repository parameterizes them.

## 2.1 Environment

```bash
conda create -n aiida python=3.10 -y
conda activate aiida
pip install aiida-core==2.8.*
pip install aiida-abacus aiida-vasp aiida-quantumespresso aiida-fleur
pip install aiida-common-workflows aiida-pseudo aiida-submission-controller
```

You may add `aiida-phonopy`, `ase`, `pymatgen`. Check the entry points:

```bash
verdi status          # no profile yet at this point; it will prompt you to create one
reentry scan -r aiida # needed for older versions; generally unnecessary on 2.x
```

## 2.2 profile: where the data lives

Two backends:

```bash
# A. SQLite + zmq (single machine, zero dependencies, good for practice/teaching)
verdi profile setup core.sqlite_dos -n \
  -p profile_<name> --no-set-as-default \
  --email you@example.com --first-name <first> --last-name <last> \
  --institution <inst> --broker zmq \
  --filepath "$HOME/data/aiida_profile/profile_<name>"

# B. PostgreSQL + RabbitMQ (production)
verdi profile setup core.psql_dos -n \
  --profile-name <name> --set-as-default \
  --email you@example.com --first-name <first> --last-name <last> \
  --institution <inst> --use-rabbitmq \
  --database-username aiida_user --database-password <pw> \
  --database-name aiida_db --database-engine postgresql_psycopg \
  --database-hostname 127.0.0.1 --database-port 5432 \
  --repository-uri "file:///path/to/repository"
```

Start the message broker (the psql backend requires RabbitMQ):

```bash
# rabbitmq-server in the conda environment can be used directly, or use the system service
rabbitmq-server -detached
verdi profile list
verdi profile setdefault <name>     # switch when needed
```

## 2.2bis When there is no system service: conda's own PostgreSQL + RabbitMQ

On a laptop / container / Windows without root, you can use the conda packages directly (this is also many people's first environment):

```bash
conda install -c conda-forge postgresql
conda install -c conda-forge rabbitmq-server=3.8.3   # version must be compatible with aiida-core, see wiki

# initialize a database directory (under the user home)
mkdir -p ~/data/aiida_profile/pgdata
initdb -D ~/data/aiida_profile/pgdata

# start on a non-default port (5433 is often used to avoid the system postgres)
pg_ctl -D ~/data/aiida_profile/pgdata -o "-p 5433" -l ~/data/aiida_profile/pg.log start
psql -h 127.0.0.1 -p 5433 -d postgres

# in psql, create the database and user, and pin the time zone (AiiDA timestamps are displayed in the database time zone)
CREATE USER aiida_user WITH PASSWORD 'change-me';
CREATE DATABASE aiida_db OWNER aiida_user;
ALTER DATABASE aiida_db SET timezone TO 'Asia/Shanghai';   -- or 'Etc/GMT-8'
GRANT ALL PRIVILEGES ON DATABASE aiida_db TO aiida_user;
\l    -- list databases
\du   -- list users
\q

rabbitmq-server -detached
```

In the profile, write the port as 5433:

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

**Connection latency** (test it first with multi-machine/remote DSN; don't wait for an AiiDA timeout to discover the network is wrong):

```bash
time psql -h 127.0.0.1 -p 5433 -U aiida_user -d aiida_db -c "\q"
```

**Start on boot/activation**: put the three commands into conda's `activate.d`, so they run automatically on `conda activate aiida`:

```bash
mkdir -p "$CONDA_PREFIX/etc/conda/activate.d"
cat > "$CONDA_PREFIX/etc/conda/activate.d/aiida.sh" <<'SH'
pg_ctl -D "$HOME/data/aiida_profile/pgdata" -l "$HOME/data/aiida_profile/pg.log" start 2>/dev/null || true
rabbitmq-server -detached 2>/dev/null || true
verdi daemon status >/dev/null 2>&1 || verdi daemon start 2>/dev/null || true
SH
```

> Time zone: only after the database time zone is set to `Asia/Shanghai` (or `Etc/GMT-8`) do
> the ctime/mtime in `verdi process list` match local time; otherwise the default is UTC, and it is easy to mistake "8 hours late" for a fault.

## 2.3 computer: where to submit

First confirm that ssh works:

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

verdi computer test <cluster>   # must be all green
```

Key points:

- `work-dir` is AiiDA's scratch directory on the cluster and must be writable;
- `{tot_num_mpiprocs}` in `mpirun-command` is determined by the `resources` of each submission;
- login nodes have limited resources, so `computer test` only tests ssh and file read/write, not computation.

## 2.4 code: which executable to run

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

- `--default-calc-job-plugin` decides which plugin's CalcJob this code is handed to;
- put `module load` / `source spack` in `--prepend-text`; it runs at the start of every job;
- `--with-mpi` works together with `mpirun-command`; for a single-core job just set `resources` to 1.

**Note**: on a machine with a scheduler, `metadata.options` must carry `queue_name`,
otherwise `sbatch` reports `No partition specified or system default partition`.

## 2.5 Pseudopotentials / orbitals

```bash
# general: SSSP
aiida-pseudo install sssp -v 1.3 -x PBE -p precision

# ABACUS: UPF + numerical atomic orbital families
aiida-pseudo install family /path/to/upf/*.UPF <family-name> -x PBE
aiida-pseudo install family /path/to/orbital/*.orb <family-name> -x PBE
```

## 2.6 daemon

```bash
verdi daemon start
verdi daemon status
verdi status           # all green: version / config / profile / storage / broker / daemon
```

After changing the source of an installed plugin you must run `verdi daemon restart` (the daemon holds the old modules).

## 2.7 Self-check

```bash
python install/06-doctor.py            # human-readable report
python install/06-doctor.py --json     # machine-readable
python install/06-doctor.py --strict   # non-zero exit code if the environment falls outside the range supported by versions.yaml
```
