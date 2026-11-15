#!/usr/bin/env bash
# Register the SLURM computer (transport: ssh) and test the connection.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$HERE/config.env"

verdi -p "$PROFILE_NAME" computer show "$COMPUTER_LABEL" &>/dev/null && {
  echo "[03-computer] '$COMPUTER_LABEL' already exists"; exit 0; }

verdi -p "$PROFILE_NAME" computer setup \
  --label "$COMPUTER_LABEL" \
  --hostname "$COMPUTER_HOST" \
  --description "SLURM cluster ($COMPUTER_HOST)" \
  --transport core.ssh_async \
  --scheduler core.slurm \
  --shebang '#!/bin/bash' \
  --work-dir "$COMPUTER_WORKDIR" \
  --mpirun-command "$COMPUTER_MPIRUN" \
  --mpiprocs-per-machine "$COMPUTER_MPIPROCS_PER_MACHINE" \
  --default-memory-per-machine "$COMPUTER_MEMORY_KB" \
  --non-interactive

# --host reads from ~/.ssh/config; adjust if you connect by IP.
verdi -p "$PROFILE_NAME" computer configure core.ssh_async "$COMPUTER_LABEL" -n \
  --host "$COMPUTER_HOST" --backend asyncssh --safe-interval 5.0 \
  --no-use-login-shell --max-io-allowed 8

verdi -p "$PROFILE_NAME" computer test "$COMPUTER_LABEL"
