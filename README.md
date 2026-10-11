# IIC3533 · Tarea 2 — Multiplicación de matrices con OpenMP y Numba

| Archivo | Contenido |
|---|---|
| `serial.cpp` | Referencia serial provista (Alg. 1 con `n=N`, Alg. 2 con `n<N`) |
| `src/alg1_omp.cpp` | (b) Paralelismo de datos: `omp parallel for` sobre las filas |
| `src/alg2_dc_omp.cpp` | (c) Dividir y conquistar con `omp task` (4 tareas por nivel) |
| `src/alg3_numba.py` | (d) Numba `@njit(parallel=True)` + `prange` |
| `run_all.sh` | Corre todos los experimentos → `results/<etiqueta>/times.csv` + `machine.txt` |
| `plots.py` | Figuras (`informe/figs/`) y tablas LaTeX (`informe/tablas/`) |

Todas las versiones verifican su resultado contra la referencia serial (`--check`) e imprimen el mismo checksum.

## Correr en el segundo computador (Ubuntu)

```bash
git clone git@github.com:br0nhg/IIC3533-Tarea2-HPC.git
cd IIC3533-Tarea2-HPC
./setup.sh                          # apt build-essential + venv con numpy/numba/matplotlib/pandas
./run_all.sh pc2-ubuntu --quick     # prueba rápida (segundos)
./run_all.sh pc2-ubuntu 2>&1 | tee results/pc2-ubuntu.log   # corrida completa (~10-20 min). No usar el PC mientras corre.
git add results/pc2-ubuntu results/pc2-ubuntu.log && git commit -m "Resultados pc2-ubuntu" && git push
```

Antes de correr, cerrar otros programas y dejar el PC enchufado (modo rendimiento).

## Generar figuras

```bash
.venv/bin/python plots.py           # usa todas las carpetas results/* (excepto *-quick)
```

## Variables de `run_all.sh`
`REPS` (repeticiones, por defecto 5), `REPS_BIG` (para N=4096, por defecto 3) y `NLEAF` (n del Alg. 2, por defecto 128, elegido con un barrido para p=8).
