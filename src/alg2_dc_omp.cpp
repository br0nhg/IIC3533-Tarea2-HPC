// alg2_dc_omp.cpp - Algoritmo 2: dividir y conquistar con tareas OpenMP.
//
// Se parte de multiply_rec de serial.cpp. En cada nivel se crean 4 tareas, una
// por cuadrante C_ij. Dentro de cada tarea los dos subproductos que acumulan en
// el mismo bloque (A_i1*B_1j y luego A_i2*B_2j) se ejecutan en secuencia, por
// lo que ninguna pareja de tareas concurrentes escribe el mismo bloque de C:
// no hay carreras y no se necesitan matrices temporales ni reducciones.
// El taskwait al final asegura que el bloque padre este completo al retornar.
//
// Cutoff: bajo la profundidad `cutoff` ya no se crean tareas (if(false) ejecuta
// inmediatamente en el mismo thread), para limitar el overhead de tareas
// diminutas. cutoff < 0 => tareas en todos los niveles.
//
// Uso: OMP_NUM_THREADS=p ./alg2_dc_omp [N] [n] [cutoff] [--check]

#include "common.hpp"
#include <omp.h>

static int g_cutoff = -1;

void multiply_rec_task(const MatView& A, const MatView& B, const MatView& C,
                       int n, int depth) {
    int s = C.size;
    if (s <= n) {
        multiply_leaf(A, B, C);
        return;
    }
    int h = s / 2;
    bool spawn = (g_cutoff < 0 || depth < g_cutoff);

    for (int bi = 0; bi < 2; ++bi) {
        for (int bj = 0; bj < 2; ++bj) {
            #pragma omp task firstprivate(bi, bj) if(spawn)
            {
                MatView Cij = C.sub(bi * h, bj * h, h);
                multiply_rec_task(A.sub(bi * h, 0, h), B.sub(0, bj * h, h), Cij, n, depth + 1);
                multiply_rec_task(A.sub(bi * h, h, h), B.sub(h, bj * h, h), Cij, n, depth + 1);
            }
        }
    }
    #pragma omp taskwait
}

int main(int argc, char** argv) {
    int N = (argc > 1 && argv[1][0] != '-') ? std::atoi(argv[1]) : 2048;
    int n = (argc > 2 && argv[2][0] != '-') ? std::atoi(argv[2]) : 64;
    g_cutoff = (argc > 3 && argv[3][0] != '-') ? std::atoi(argv[3]) : -1;
    int p = omp_get_max_threads();

    std::vector<double> A(static_cast<size_t>(N) * N), B(A.size()), C(A.size(), 0.0);
    init_matrix(A, N, 1);
    init_matrix(B, N, 2);

    MatView Av{ A.data(), N, N }, Bv{ B.data(), N, N }, Cv{ C.data(), N, N };

    double t0 = now_s();
    #pragma omp parallel
    #pragma omp single
    multiply_rec_task(Av, Bv, Cv, n, 0);
    double t = now_s() - t0;

    print_result("alg2_dc_omp", N, n, p, t, checksum(C));
    if (has_flag(argc, argv, "--check") && !verify(A, B, C, N)) return 1;
    return 0;
}
