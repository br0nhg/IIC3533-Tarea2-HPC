"""alg3_numba.py - Algoritmo 3: paralelismo de datos con Numba (prange).

Misma multiplicacion i-k-j que el Algoritmo 1; prange reparte las filas i
entre los threads. Las matrices se inicializan con la misma formula
determinista que serial.cpp, por lo que el checksum es comparable.

Uso: python alg3_numba.py --N 2048 --p 1 2 4 8 --reps 3 [--check]
Imprime lineas RESULT,alg3_numba,N,N,p,time_s,checksum
"""

import argparse
import time

import numpy as np
import numba
from numba import njit, prange


@njit(parallel=True, cache=True)
def matmul_prange(A, B, C):
    N = A.shape[0]
    for i in prange(N):
        for k in range(N):
            a = A[i, k]
            for j in range(N):
                C[i, j] += a * B[k, j]


def init_matrix(N, offset):
    i = np.arange(N, dtype=np.float64).reshape(-1, 1)
    j = np.arange(N, dtype=np.float64).reshape(1, -1)
    return np.ascontiguousarray(np.sin(i * 0.1 + j * 0.3 + offset))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--N", type=int, nargs="+", default=[2048])
    ap.add_argument("--p", type=int, nargs="+", default=[1, 2, 4, 8])
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    # Warm-up: fuerza la compilacion JIT antes de medir (mismos tipos).
    w = np.ones((8, 8))
    matmul_prange(w, w, np.zeros((8, 8)))

    for N in args.N:
        A = init_matrix(N, 1.0)
        B = init_matrix(N, 2.0)
        for p in args.p:
            numba.set_num_threads(p)
            # Warm-up del pool de threads con este p (no se mide).
            matmul_prange(w, w, np.zeros((8, 8)))
            for _ in range(args.reps):
                C = np.zeros((N, N))
                t0 = time.perf_counter()
                matmul_prange(A, B, C)
                t = time.perf_counter() - t0
                print(f"RESULT,alg3_numba,{N},{N},{p},{t:.6f},{C.sum():.6f}", flush=True)
            if args.check:
                ok = np.allclose(C, A @ B, rtol=0, atol=1e-9 * N)
                print(f"verify: N={N} p={p} -> {'OK' if ok else 'FAIL'}", flush=True)
                if not ok:
                    raise SystemExit(1)


if __name__ == "__main__":
    main()
