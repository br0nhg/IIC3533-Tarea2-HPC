#!/usr/bin/env bash
# setup.sh - Instala dependencias y crea el entorno Python (macOS o Ubuntu).
set -euo pipefail
cd "$(dirname "$0")"

if [[ "$(uname -s)" == "Darwin" ]]; then
    brew list libomp >/dev/null 2>&1 || brew install libomp
else
    sudo apt-get update
    sudo apt-get install -y build-essential python3-venv python3-pip
fi

[[ -d .venv ]] || python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt

make
echo "Setup OK. Siguiente paso: ./run_all.sh <etiqueta> --quick"
