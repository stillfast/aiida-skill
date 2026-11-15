#!/usr/bin/env bash
# Install the SSSP pseudopotential library. ABACUS UPF/orbital families are
# installed from local files (see references/02-installation.md §2.5).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$HERE/config.env"

aiida-pseudo install sssp -v "$SSSP_VERSION" -x "$SSSP_FUNCTIONAL" -p "$SSSP_PRECISION"
aiida-pseudo list
