#!/usr/bin/env bash
# run_all.sh - Ejecuta todos los experimentos de la Tarea 2 y guarda CSVs.
#
# Uso:
#   ./run_all.sh <etiqueta-maquina> [--quick]
#   ej: ./run_all.sh pc1-mac      ./run_all.sh pc2-ubuntu
#
# Variables opcionales: REPS (default 5), REPS_BIG (N=4096, default 3),
#                       NLEAF (n elegido para el Alg. 2, default 128).
set -euo pipefail
cd "$(dirname "$0")"

LABEL="${1:?Uso: ./run_all.sh <etiqueta-maquina> [--quick]}"
QUICK=0; [[ "${2:-}" == "--quick" ]] && QUICK=1

REPS="${REPS:-5}"
REPS_BIG="${REPS_BIG:-3}"
NLEAF="${NLEAF:-128}"
PS=(1 2 4 8)
N_MAIN=2048
N_WEAK=(1024 2048 4096)
NS_LEAF=(2048 1024 512 256 128 64 32)
PY=.venv/bin/python

if (( QUICK )); then
    REPS=1; REPS_BIG=1; N_MAIN=512; N_WEAK=(256 512); NS_LEAF=(512 256 128 64 32); NLEAF=64
    LABEL="${LABEL}-quick"
fi

OUT="results/${LABEL}"
mkdir -p "$OUT"
CSV="$OUT/times.csv"
echo "version,N,n,p,rep,time_s,checksum" > "$CSV"

# En Linux se fija la afinidad (un thread por core fisico). macOS no la soporta.
if [[ "$(uname -s)" == "Linux" ]]; then
    export OMP_PROC_BIND=close OMP_PLACES=cores
fi

make -s

# ---------------------------------------------------------------- maquina
{
    echo "label: $LABEL"
    echo "date: $(date -Iseconds 2>/dev/null || date)"
    echo "os: $(uname -srm)"
    echo "compiler: $(c++ --version 2>/dev/null | head -1) / $(g++ --version 2>/dev/null | head -1)"
    echo "python: $($PY --version 2>&1)  numba: $($PY -c 'import numba;print(numba.__version__)')"
    if [[ "$(uname -s)" == "Darwin" ]]; then
        echo "cpu: $(sysctl -n machdep.cpu.brand_string)"
        echo "physical_cores: $(sysctl -n hw.physicalcpu)"
        echo "logical_cores: $(sysctl -n hw.logicalcpu)"
        echo "perf_cores: $(sysctl -n hw.perflevel0.physicalcpu 2>/dev/null || echo -)"
        echo "eff_cores: $(sysctl -n hw.perflevel1.physicalcpu 2>/dev/null || echo -)"
        echo "l1d_bytes(P): $(sysctl -n hw.perflevel0.l1dcachesize 2>/dev/null || echo -)"
        echo "l2_bytes(P): $(sysctl -n hw.perflevel0.l2cachesize 2>/dev/null || echo -)"
        echo "l1d_bytes(E): $(sysctl -n hw.perflevel1.l1dcachesize 2>/dev/null || echo -)"
        echo "l2_bytes(E): $(sysctl -n hw.perflevel1.l2cachesize 2>/dev/null || echo -)"
        echo "mem_bytes: $(sysctl -n hw.memsize)"
        echo "clock: Apple no expone la frecuencia via sysctl; buscar la especificacion del chip"
    else
        lscpu
        echo "physical_cores: $(lscpu -p=CORE,SOCKET | grep -v '^#' | sort -u | wc -l)"
        echo "logical_cores: $(nproc --all)"
        grep -m1 'MHz' /proc/cpuinfo || true
        echo "max_mhz: $(cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq 2>/dev/null || echo -)"
        free -b | head -2
    fi
} > "$OUT/machine.txt"

# ---------------------------------------------------------------- helpers
# serial.cpp imprime: N=.. n=.. tiempo=XX ms checksum=YY
run_serial() {  # N n reps
    for ((r = 1; r <= $3; r++)); do
        ./bin/serial "$1" "$2" | sed -E "s/N=([0-9]+) n=([0-9]+) tiempo=([0-9.]+) ms checksum=(.*)/\1 \2 \3 \4/" |
            awk -v r="$r" '{printf "serial,%s,%s,1,%d,%.6f,%s\n", $1, $2, r, $3/1000, $4}' >> "$CSV"
    done
}
run_omp() {  # bin p reps args...
    local bin=$1 p=$2 reps=$3; shift 3
    for ((r = 1; r <= reps; r++)); do
        OMP_NUM_THREADS=$p "./bin/$bin" "$@" | grep '^RESULT' |
            awk -F, -v r="$r" '{printf "%s,%s,%s,%s,%d,%s,%s\n", $2, $3, $4, $5, r, $6, $7}' >> "$CSV"
    done
}
reps_for() { (( $1 >= 4096 )) && echo "$REPS_BIG" || echo "$REPS"; }
log() { echo "[$(date +%H:%M:%S)] $*"; }

# ---------------------------------------------------------------- verificacion
log "Verificacion de correctitud (N=$N_MAIN, p=8)"
OMP_NUM_THREADS=8 ./bin/alg1_omp "$N_MAIN" --check | grep verify
OMP_NUM_THREADS=8 ./bin/alg2_dc_omp "$N_MAIN" "$NLEAF" --check | grep verify
$PY src/alg3_numba.py --N "$N_MAIN" --p 8 --reps 1 --check | grep verify

# ---------------------------------------------------------------- (a)
log "(a) serial, N=$N_MAIN, n en ${NS_LEAF[*]}"
for n in "${NS_LEAF[@]}"; do run_serial "$N_MAIN" "$n" "$REPS"; done

# ---------------------------------------------------------------- (b) (c) (e) (f)
for N in "${N_WEAK[@]}"; do
    R=$(reps_for "$N")
    if [[ "$N" != "$N_MAIN" ]]; then
        log "serial base N=$N"; run_serial "$N" "$N" "$R"
    fi
    for p in "${PS[@]}"; do
        log "alg1 N=$N p=$p";              run_omp alg1_omp "$p" "$R" "$N"
        log "alg2 N=$N n=$NLEAF p=$p";     run_omp alg2_dc_omp "$p" "$R" "$N" "$NLEAF"
    done
    log "alg3 numba N=$N"
    $PY src/alg3_numba.py --N "$N" --p "${PS[@]}" --reps "$R" | grep '^RESULT' |
        awk -F, '{k=$2 FS $3 FS $5; c[k]++; printf "%s,%s,%s,%s,%d,%s,%s\n", $2, $3, $4, $5, c[k], $6, $7}' >> "$CSV"
done

# ---------------------------------------------------------------- (c)/(e) barrido de n para Alg. 2
log "(e) alg2 barrido de n, N=$N_MAIN"
for n in "${NS_LEAF[@]}"; do
    [[ "$n" == "$NLEAF" ]] && continue   # ya medido arriba
    for p in "${PS[@]}"; do run_omp alg2_dc_omp "$p" "$REPS" "$N_MAIN" "$n"; done
done

log "Listo -> $CSV ($(($(wc -l < "$CSV") - 1)) mediciones)"
