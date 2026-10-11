// common.hpp - Codigo compartido por las versiones paralelas.
// MatView, init_matrix y multiply_leaf son identicos a serial.cpp.

#pragma once

#include <vector>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <chrono>
#include <string>
#include <algorithm>

// Vista de un bloque s x s dentro de una matriz N x N (row-major), sin copiar.
struct MatView {
    double* data;
    int stride;
    int size;
    double& at(int i, int j) const { return data[i * stride + j]; }
    MatView sub(int r, int c, int s) const { return { data + r * stride + c, stride, s }; }
};

// Valor determinista en [-1, 1] segun la posicion (reproducible entre maquinas).
inline double det_value(int i, int j, double offset) {
    return std::sin(i * 0.1 + j * 0.3 + offset);
}

inline void init_matrix(std::vector<double>& M, int N, double offset) {
    for (int i = 0; i < N; ++i) {
        for (int j = 0; j < N; ++j) {
            M[i * N + j] = det_value(i, j, offset);
        }
    }
}

// Hoja: multiplicacion densa que acumula en C (C += A * B).
inline void multiply_leaf(const MatView& A, const MatView& B, const MatView& C) {
    int s = C.size;
    for (int i = 0; i < s; ++i) {
        for (int k = 0; k < s; ++k) {
            double a = A.at(i, k);
            for (int j = 0; j < s; ++j) {
                C.at(i, j) += a * B.at(k, j);
            }
        }
    }
}

inline double now_s() {
    return std::chrono::duration<double>(
        std::chrono::steady_clock::now().time_since_epoch()).count();
}

inline double checksum(const std::vector<double>& C) {
    double s = 0.0;
    for (double v : C) s += v;
    return s;
}

// Compara C contra la referencia serial (problema base, n = N).
// Devuelve true si el error maximo es menor a la tolerancia.
inline bool verify(const std::vector<double>& A, const std::vector<double>& B,
                   const std::vector<double>& C, int N) {
    std::vector<double> R(static_cast<size_t>(N) * N, 0.0);
    multiply_leaf({ const_cast<double*>(A.data()), N, N },
                  { const_cast<double*>(B.data()), N, N },
                  { R.data(), N, N });
    double max_err = 0.0;
    for (size_t idx = 0; idx < R.size(); ++idx) {
        max_err = std::max(max_err, std::fabs(R[idx] - C[idx]));
    }
    double tol = 1e-9 * N;
    std::printf("verify: max_err=%.3e tol=%.1e -> %s\n", max_err, tol,
                max_err < tol ? "OK" : "FAIL");
    return max_err < tol;
}

// Linea parseable por run_all.sh.
inline void print_result(const char* version, int N, int n, int p, double t, double cs) {
    std::printf("RESULT,%s,%d,%d,%d,%.6f,%.6f\n", version, N, n, p, t, cs);
}

inline bool has_flag(int argc, char** argv, const char* flag) {
    for (int i = 1; i < argc; ++i) {
        if (std::strcmp(argv[i], flag) == 0) return true;
    }
    return false;
}
