#!/usr/bin/env bash
# Register ABACUS and VASP as installed codes on the computer.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$HERE/config.env"

create_code() {
  local label="$1" plugin="$2" executable="$3" prepend="$4"
  verdi -p "$PROFILE_NAME" code show "$label" &>/dev/null && {
    echo "[04-code] code '$label' already exists"; return 0; }
  verdi -p "$PROFILE_NAME" code create core.code.installed \
    --label "$label" \
    --description "$label on $COMPUTER_LABEL" \
    --default-calc-job-plugin "$plugin" \
    --computer "$COMPUTER_LABEL" \
    --filepath-executable "$executable" \
    --prepend-text "$prepend" \
    --use-double-quotes --with-mpi --non-interactive
}

[ -n "${ABACUS_EXECUTABLE:-}" ] && create_code "$CODE_ABACUS_LABEL" abacus.abacus "$ABACUS_EXECUTABLE" "$ABACUS_PREPEND"
[ -n "${VASP_EXECUTABLE:-}" ] && create_code "$CODE_VASP_LABEL" vasp.vasp "$VASP_EXECUTABLE" "$VASP_PREPEND"
verdi -p "$PROFILE_NAME" code list
