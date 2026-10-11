"""plots.py - Genera figuras (PDF) y tablas (LaTeX) desde results/<maquina>/times.csv.

Uso: .venv/bin/python plots.py [maquina1 maquina2 ...]
     (por defecto: todas las carpetas de results/ que no terminan en -quick)

Salida: informe/figs/*.pdf  e  informe/tablas/*.tex
Se usa la mediana de las repeticiones. S(p) = T(1)/T(p) con T(1) = la misma
version ejecutada con 1 thread; E(p) = S(p)/p.
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter, LogLocator

ROOT = Path(__file__).parent
RES = ROOT / "results"
FIGS = ROOT / "informe" / "figs"
TABS = ROOT / "informe" / "tablas"
FIGS.mkdir(parents=True, exist_ok=True)
TABS.mkdir(parents=True, exist_ok=True)

N_MAIN = 2048
PS = [1, 2, 4, 8]

# Paleta categorica (slots 1-3 en orden fijo) y estilos por maquina.
VERSIONS = {
    "alg1_omp": ("Alg. 1 OpenMP (datos)", "#2a78d6", "o"),
    "alg2_dc_omp": ("Alg. 2 OpenMP (D\\&C tareas)", "#eb6834", "s"),
    "alg3_numba": ("Alg. 3 Numba (prange)", "#1baf7a", "^"),
}
MACHINE_LS = ["-", "--"]
IDEAL = dict(color="#8a8984", ls=":", lw=1.5, label="Ideal")
SEQ_BLUES = ["#c6dbf3", "#9cc2ec", "#6fa6e2", "#3f86d6", "#2a6bb8", "#1d5294", "#123a6c"]

plt.rcParams.update({
    # Figuras dibujadas al ancho real del texto (16.6 cm) => fuente impresa ~9 pt.
    "font.size": 9, "axes.titlesize": 9.5, "axes.labelsize": 9, "figure.titlesize": 10,
    "legend.fontsize": 8, "xtick.labelsize": 8, "ytick.labelsize": 8,
    "lines.linewidth": 1.6, "lines.markersize": 4.5, "figure.constrained_layout.use": True,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": "#e4e3df", "grid.linewidth": 0.8,
    "savefig.bbox": "tight", "pdf.fonttype": 42,
})


def label_tex(v):
    return VERSIONS[v][0]


def label_plt(v):
    return VERSIONS[v][0].replace("\\&", "&")


def load(machines):
    frames = []
    for m in machines:
        df = pd.read_csv(RES / m / "times.csv")
        df["machine"] = m
        frames.append(df)
    df = pd.concat(frames)
    return df.groupby(["machine", "version", "N", "n", "p"], as_index=False)["time_s"].median()


def nleaf_main(d, m):
    """n elegido para el Alg. 2 = el usado en todos los N (escalabilidad debil)."""
    a2 = d[(d.machine == m) & (d.version == "alg2_dc_omp")]
    counts = a2.groupby("n")["N"].nunique()
    return int(counts.idxmax())


def scaling(d, m, version, N, n=None):
    s = d[(d.machine == m) & (d.version == version) & (d.N == N)]
    if n is not None:
        s = s[s.n == n]
    s = s.set_index("p").sort_index()["time_s"]
    S = s.loc[1] / s
    E = S / S.index
    return pd.DataFrame({"T": s, "S": S, "E": E})


def save(fig, name):
    fig.savefig(FIGS / f"{name}.pdf")
    fig.savefig(FIGS / f"{name}.png", dpi=150)
    plt.close(fig)


def log_time_axis(ax):
    ax.set_yscale("log")
    ax.yaxis.set_major_locator(LogLocator(base=10, subs=(1, 2, 5)))
    ax.yaxis.set_minor_locator(LogLocator(base=10, subs=(1, 2, 3, 4, 5, 6, 7, 8, 9)))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:g}"))
    ax.yaxis.set_minor_formatter(FuncFormatter(lambda y, _: ""))


def bottom_legend(fig, ax, ncol):
    h, l = ax.get_legend_handles_labels()
    fig.legend(h, l, loc="outside lower center", ncol=ncol, frameon=False)


def setup_p_axis(ax):
    ax.set_xscale("log", base=2)
    ax.set_xticks(PS)
    ax.set_xticklabels([str(p) for p in PS])
    ax.set_xlabel("Threads $p$")


# --------------------------------------------------------------------- (a)
def fig_a(d, machines):
    fig, ax = plt.subplots(figsize=(5.2, 2.9))
    colors = ["#2a78d6", "#eb6834"]
    width = 0.8 / len(machines)
    for k, m in enumerate(machines):
        s = d[(d.machine == m) & (d.version == "serial") & (d.N == N_MAIN)]
        s = s.sort_values("n", ascending=False)
        xs = [i + (k - (len(machines) - 1) / 2) * width for i in range(len(s))]
        bars = ax.bar(xs, s.time_s, width=width * 0.92, color=colors[k], label=m)
        ax.bar_label(bars, fmt="%.2f", fontsize=7.5, padding=2, color="#52514e")
        ticks = [str(n) for n in s.n]
    ax.set_xticks(range(len(ticks)))
    ax.set_xticklabels(ticks)
    ax.set_xlabel("Tamaño de bloque $n$ (hoja)")
    ax.set_ylabel("Tiempo [s]")
    ax.set_title(f"(a) Serial D&C, $N={N_MAIN}$: tiempo vs tamaño de bloque")
    ax.grid(axis="x", visible=False)
    if len(machines) > 1:
        ax.legend(title="Computador")
    save(fig, "a_serial_bloque")

    rows = []
    for m in machines:
        s = d[(d.machine == m) & (d.version == "serial") & (d.N == N_MAIN)].set_index("n")["time_s"]
        rows.append(s.rename(m))
    t = pd.concat(rows, axis=1).sort_index(ascending=False)
    t.index.name = "$n$"
    write_table(t, "a_serial_bloque", "Tiempo serial [s] para $N=2048$ según tamaño de bloque $n$ (mediana).",
                fmt="{:.3f}")


# --------------------------------------------------------------------- (b)(c)(d)(e)
def fig_scaling(d, m, ls="-"):
    nb = nleaf_main(d, m)
    fig, axes = plt.subplots(1, 3, figsize=(6.5, 2.6))
    for v, (lab, col, mk) in VERSIONS.items():
        sc = scaling(d, m, v, N_MAIN, nb if v == "alg2_dc_omp" else None)
        lab_p = label_plt(v) + (f", $n={nb}$" if v == "alg2_dc_omp" else "")
        for ax, key in zip(axes, ["T", "S", "E"]):
            ax.plot(sc.index, sc[key], ls=ls, color=col, marker=mk, label=lab_p)
    axes[1].plot(PS, PS, **IDEAL)
    axes[2].plot(PS, [1] * 4, **IDEAL)
    t1 = scaling(d, m, "alg1_omp", N_MAIN)["T"].loc[1]
    axes[0].plot(PS, [t1 / p for p in PS], **{**IDEAL, "label": "Ideal (Alg. 1)"})
    log_time_axis(axes[0])
    axes[0].set_ylabel("Tiempo $T(p)$ [s]")
    axes[1].set_ylabel("Speedup $S(p)=T(1)/T(p)$")
    axes[2].set_ylabel("Eficiencia $E(p)=S(p)/p$")
    axes[2].set_ylim(0, 1.15)
    for ax, tit in zip(axes, ["Tiempo", "Speedup", "Eficiencia"]):
        setup_p_axis(ax)
        ax.set_title(tit)
    bottom_legend(fig, axes[0], ncol=4)
    fig.suptitle(f"(e) Escalamiento fuerte, $N={N_MAIN}$ — {m}")
    save(fig, f"e_escalamiento_{m}")

    # Tabla T, S, E por version (partes b, c, d).
    serial_best = d[(d.machine == m) & (d.version == "serial") & (d.N == N_MAIN)]["time_s"].min()
    rows = []
    for v in VERSIONS:
        sc = scaling(d, m, v, N_MAIN, nb if v == "alg2_dc_omp" else None)
        for p, r in sc.iterrows():
            rows.append({"Versión": label_tex(v), "$p$": p, "$T(p)$ [s]": r["T"],
                         "$S(p)$": r["S"], "$E(p)$": r["E"],
                         "$S_{abs}(p)$": serial_best / r["T"]})
    t = pd.DataFrame(rows).set_index(["Versión", "$p$"])
    write_table(t, f"bcd_escalamiento_{m}",
                f"Escalamiento fuerte con $N=2048$ en {m} (Alg. 2 con $n={nb}$). "
                f"$S_{{abs}}$ usa como referencia el mejor tiempo serial ({serial_best:.3f} s).",
                fmt="{:.3f}")


def fig_alg2_blocks(d, m):
    a2 = d[(d.machine == m) & (d.version == "alg2_dc_omp") & (d.N == N_MAIN)]
    ns = sorted(a2.n.unique())
    fig, axes = plt.subplots(1, 3, figsize=(6.5, 2.6))
    for col, n in zip(SEQ_BLUES[-len(ns):], ns):
        sc = scaling(d, m, "alg2_dc_omp", N_MAIN, n)
        for ax, key in zip(axes, ["T", "S", "E"]):
            ax.plot(sc.index, sc[key], color=col, marker="o", label=f"$n={n}$")
    axes[1].plot(PS, PS, **IDEAL)
    axes[2].plot(PS, [1] * 4, **IDEAL)
    log_time_axis(axes[0])
    axes[0].set_ylabel("Tiempo $T(p)$ [s]")
    axes[1].set_ylabel("Speedup $S(p)$")
    axes[2].set_ylabel("Eficiencia $E(p)$")
    axes[2].set_ylim(0, 1.15)
    for ax, tit in zip(axes, ["Tiempo", "Speedup", "Eficiencia"]):
        setup_p_axis(ax)
        ax.set_title(tit)
    bottom_legend(fig, axes[1], ncol=8)
    fig.suptitle(f"(e) Alg. 2: efecto del tamaño de bloque $n$, $N={N_MAIN}$ — {m}")
    save(fig, f"e_alg2_bloques_{m}")

    t = a2.pivot(index="n", columns="p", values="time_s").sort_index()
    t.columns = [f"$p={p}$" for p in t.columns]
    t.index.name = "$n$"
    write_table(t, f"e_alg2_bloques_{m}",
                f"Alg. 2: tiempo [s] según tamaño de bloque $n$ y threads $p$, $N=2048$, {m}.",
                fmt="{:.3f}")


# --------------------------------------------------------------------- (f)
def fig_weak(d, m):
    nb = nleaf_main(d, m)
    Ns = sorted(d[(d.machine == m) & (d.version == "alg1_omp")].N.unique())
    seq = SEQ_BLUES[2::2][: len(Ns)] if len(Ns) <= 3 else SEQ_BLUES[-len(Ns):]
    fig, axes = plt.subplots(2, 3, figsize=(6.5, 4.6), sharey="row")
    rows = []
    for j, (v, (lab, _, mk)) in enumerate(VERSIONS.items()):
        base = scaling(d, m, v, Ns[0], nb if v == "alg2_dc_omp" else None)["T"].loc[1]
        for col, N in zip(seq, Ns):
            sc = scaling(d, m, v, N, nb if v == "alg2_dc_omp" else None)
            # Eficiencia normalizada por trabajo (escalabilidad debil):
            # rendimiento por thread relativo a (N0, p=1).
            Ew = (N / Ns[0]) ** 3 * base / (sc.index * sc["T"])
            axes[0, j].plot(sc.index, sc["E"], color=col, marker=mk, label=f"$N={N}$")
            axes[1, j].plot(sc.index, Ew, color=col, marker=mk, label=f"$N={N}$")
            for p in sc.index:
                rows.append({"Versión": label_tex(v), "$N$": N, "$p$": p,
                             "$T$ [s]": sc["T"].loc[p], "$E$": sc["E"].loc[p], "$E_w$": Ew.loc[p],
                             "GFLOP/s": 2 * N**3 / sc["T"].loc[p] / 1e9})
        axes[0, j].set_title(label_plt(v))
    for ax in axes.flat:
        setup_p_axis(ax)
        ax.plot(PS, [1] * 4, **IDEAL)
        ax.set_ylim(0, None)
    axes[0, 0].set_ylabel("Eficiencia fuerte $E(p)$")
    axes[1, 0].set_ylabel("Eficiencia débil $E_w(N,p)$")
    bottom_legend(fig, axes[0, 0], ncol=4)
    fig.suptitle(f"(f) Escalabilidad al variar $N$ — {m}")
    save(fig, f"f_escalabilidad_{m}")
    t = pd.DataFrame(rows).set_index(["Versión", "$N$", "$p$"])
    write_table(t, f"f_escalabilidad_{m}",
                f"Escalabilidad con $N\\in\\{{{', '.join(map(str, Ns))}\\}}$ en {m}. "
                f"$E_w = (N/{Ns[0]})^3\\,T({Ns[0]},1)/(p\\,T(N,p))$.", fmt="{:.3f}")


# --------------------------------------------------------------------- (g)
def fig_compare(d, machines):
    fig, axes = plt.subplots(1, 3, figsize=(6.5, 2.6))
    for k, m in enumerate(machines):
        nb = nleaf_main(d, m)
        for v, (lab, col, mk) in VERSIONS.items():
            sc = scaling(d, m, v, N_MAIN, nb if v == "alg2_dc_omp" else None)
            for ax, key in zip(axes, ["T", "S", "E"]):
                ax.plot(sc.index, sc[key], color=col, marker=mk, ls=MACHINE_LS[k % 2],
                        mfc=col if k == 0 else "white", label=f"{label_plt(v)} — {m}")
    axes[1].plot(PS, PS, **IDEAL)
    axes[2].plot(PS, [1] * 4, **IDEAL)
    log_time_axis(axes[0])
    axes[0].set_ylabel("Tiempo $T(p)$ [s]")
    axes[1].set_ylabel("Speedup $S(p)$")
    axes[2].set_ylabel("Eficiencia $E(p)$")
    axes[2].set_ylim(0, 1.15)
    for ax, tit in zip(axes, ["Tiempo", "Speedup", "Eficiencia"]):
        setup_p_axis(ax)
        ax.set_title(tit)
    bottom_legend(fig, axes[0], ncol=len(machines))
    fig.suptitle(f"(g) Comparación entre computadores, $N={N_MAIN}$ (continua: {machines[0]}, punteada: {machines[1]})")
    save(fig, "g_comparacion")


def machine_table(machines):
    keys = ["cpu", "physical_cores", "logical_cores", "perf_cores", "eff_cores", "os", "compiler"]
    data = {}
    for m in machines:
        info = {}
        for line in (RES / m / "machine.txt").read_text().splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                k = k.strip()
                if k in ("Model name", "Nombre del modelo"):
                    k = "cpu"
                info.setdefault(k, v.strip())
        info["compiler"] = info.get("compiler", "-").split(" / ")[0].split(" (")[0]
        data[m] = {k: info.get(k, "-") for k in keys}
    t = pd.DataFrame(data)
    t.index = ["CPU", "Cores físicos", "Cores lógicos", "P-cores", "E-cores", "Sistema", "Compilador"]
    write_table(t, "g_maquinas", "Características de los computadores (completar la frecuencia de reloj).",
                fmt="{}", escape=True)


def write_table(t, name, caption, fmt="{:.3f}", escape=False):
    t = t.copy()
    for c in t.columns:
        t[c] = t[c].map(lambda x: fmt.format(x) if isinstance(x, (int, float)) and not isinstance(x, bool) else str(x))
    if escape:
        t = t.map(lambda s: s.replace("_", "\\_").replace("&", "\\&").replace("%", "\\%"))
        t.index = [str(i).replace("_", "\\_") for i in t.index]
        t.columns = [str(c).replace("_", "\\_") for c in t.columns]
    body = t.to_latex(escape=False, multirow=True)
    tex = (f"\\begin{{table}}[H]\n\\centering\\small\n\\caption{{{caption}}}\n"
           f"\\label{{tab:{name}}}\n{body}\\end{{table}}\n")
    (TABS / f"{name}.tex").write_text(tex)


def main():
    machines = sys.argv[1:] or sorted(p.name for p in RES.iterdir()
                                      if p.is_dir() and not p.name.endswith("-quick"))
    d = load(machines)
    global N_MAIN
    ser = d[d.version == "serial"].groupby("N")["n"].nunique()
    N_MAIN = int(ser.idxmax())  # N del barrido de bloques (2048; 512 en --quick)
    fig_a(d, machines)
    for k, m in enumerate(machines):
        fig_scaling(d, m)
        fig_alg2_blocks(d, m)
        fig_weak(d, m)
    if len(machines) > 1:
        fig_compare(d, machines)
    machine_table(machines)
    print("Figuras en", FIGS, "| Tablas en", TABS)


if __name__ == "__main__":
    main()
