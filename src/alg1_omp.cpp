// alg1_omp.cpp - Algoritmo 1: paralelismo de datos con OpenMP.
// Se paraleliza el loop externo (filas i) de la multiplicacion densa i-k-j.
// Cada thread escribe un conjunto disjunto de filas de C, por lo que no hay
// condiciones de carrera ni se necesita sincronizacion.
// Uso: OMP_NUM_THREADS=p ./alg1_omp [N] [--check]

#include "common.hpp"
#include <omp.h>

void multiply_omp(const double* A, const double* B, double* C, int N) {
    #pragma omp parallel for schedule(static)
    for (int i = 0; i < N; ++i) {
        for (int k = 0; k < N; ++k) {
            double a = A[i * N + k];
            for (int j = 0; j < N; ++j) {
                C[i * N + j] += a * B[k * N + j];
            }
        }
    }
}

int main(int argc, char** argv) {
    int N = (argc > 1 && argv[1][0] != '-') ? std::atoi(argv[1]) : 2048;
    int p = omp_get_max_threads();

    std::vector<double> A(static_cast<size_t>(N) * N), B(A.size()), C(A.size(), 0.0);
    init_matrix(A, N, 1);
    init_matrix(B, N, 2);

    double t0 = now_s();
    multiply_omp(A.data(), B.data(), C.data(), N);
    double t = now_s() - t0;

    print_result("alg1_omp", N, N, p, t, checksum(C));
    if (has_flag(argc, argv, "--check") && !verify(A, B, C, N)) return 1;
    return 0;
}
