#!/usr/bin/env bash
# Create (or reuse) the conda environment with aiida-core and the plugins.
set -euo pipefail

ENV_NAME="${ENV_NAME:-aiida}"
PYTHON_VERSION="${PYTHON_VERSION:-3.10}"

command -v conda >/dev/null || { echo "conda not found" >&2; exit 1; }

if conda env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
  echo "[01-env] environment '$ENV_NAME' already exists"
else
  conda create -y -n "$ENV_NAME" "python=$PYTHON_VERSION"
fi

eval "$(conda shell.bash hook)"
conda activate "$ENV_NAME"

python -m pip install --upgrade pip
# Keep the versions in sync with ../versions.yaml
python -m pip install \
  "aiida-core==2.8.*" \
  aiida-abacus aiida-vasp aiida-quantumespresso aiida-fleur \
  aiida-common-workflows aiida-pseudo aiida-submission-controller

verdi --version
echo "[01-env] done. Activate with: conda activate $ENV_NAME"
