"""Figuras del OE5, del OE6 y del uso de MentorIA (matplotlib). Se guardan en results/figuras/."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from . import oe5, oe6, uso_mentoria  # noqa: E402

SALIDA = Path(__file__).resolve().parents[1] / "results" / "figuras"
COLOR = {"GC": "#2a78d6", "GE": "#eb6834"}  # paleta categórica validada (azul, naranja)
NOMBRE = {"GC": "Grupo Control", "GE": "Grupo Experimental"}
TINTA, TINTA2, REJILLA = "#0b0b0b", "#52514e", "#e4e3df"


def _estilo(ax, titulo, ylabel):
    ax.set_title(titulo, loc="left", fontsize=11, color=TINTA)
    ax.set_ylabel(ylabel, color=TINTA2, fontsize=9)
    ax.tick_params(colors=TINTA2, labelsize=9)
    ax.grid(axis="y", color=REJILLA, linewidth=.8)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(REJILLA)


def _guardar(fig, nombre):
    SALIDA.mkdir(parents=True, exist_ok=True)
    ruta = SALIDA / nombre
    fig.savefig(ruta, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return ruta


def oe5_elaboracion(df, semanas):
    """Mediana del índice de elaboración por semana, sección y grupo."""
    fig, axs = plt.subplots(1, 2, figsize=(10, 3.6), sharey=True)
    for ax, (sid, nombre) in zip(axs, oe5.SECCIONES.items()):
        for g in ("GC", "GE"):
            y = [oe5.perfil(df, s, sid, g)["elaboracion_Md"] for s in semanas]
            ax.plot(semanas, y, color=COLOR[g], linewidth=2, marker="o", markersize=6, label=NOMBRE[g])
            ax.annotate(f"{y[-1]:.1f}", (len(semanas) - 1, y[-1]), xytext=(6, 0), textcoords="offset points",
                        va="center", fontsize=8, color=TINTA2)
        _estilo(ax, nombre, "Índice de elaboración, mediana (%)" if sid == "S02" else "")
    axs[0].legend(frameon=False, fontsize=8, loc="lower right")
    return _guardar(fig, "oe5_elaboracion_por_semana.png")


def oe6_por_intervalo(df):
    """Tasa de corrección por intervalo y grupo: con cambio de texto (relleno) y sin cambio (contorno)."""
    fig, ax = plt.subplots(figsize=(9, 3.8))
    ancho = .38
    for k, g in enumerate(("GC", "GE")):
        x = [i + (k - .5) * ancho for i in range(len(oe6.INTERVALOS))]
        con, sin = [], []
        for iv in oe6.INTERVALOS:
            y = df[(df.grupo == g) & (df.intervalo == iv) & (df.deficiencia == 1)]
            con.append(100 * y.corregida_con_cambio.mean())
            sin.append(100 * (y.corregida.sum() - y.corregida_con_cambio.sum()) / len(y))
        ax.bar(x, con, ancho - .03, color=COLOR[g], label=f"{NOMBRE[g]}: con cambio de texto")
        ax.bar(x, sin, ancho - .03, bottom=con, color="white", edgecolor=COLOR[g], hatch="///", linewidth=1,
               label=f"{NOMBRE[g]}: sin cambio de texto (variabilidad del evaluador)")
        for xi, a, b in zip(x, con, sin):
            ax.text(xi, a + b + .8, f"{a:.1f}", ha="center", fontsize=8, color=TINTA2)
    ax.set_xticks(range(len(oe6.INTERVALOS)), [iv.replace("_", "→") for iv in oe6.INTERVALOS])
    _estilo(ax, "Deficiencias detectadas que se corrigen en la entrega siguiente", "% de las deficiencias")
    ax.legend(frameon=False, fontsize=7.5, ncol=2, loc="upper center", bbox_to_anchor=(.5, -.12))
    return _guardar(fig, "oe6_correccion_por_intervalo.png")


def oe6_por_clase(df):
    t = oe6.respaldo_textual(df)
    fig, ax = plt.subplots(figsize=(7, 3.4))
    etiquetas = {"sin_cambio": "Sin cambio", "superficial": "Superficial", "sustantiva": "Sustantiva"}
    ancho = .38
    for k, g in enumerate(("GC", "GE")):
        x = [i + (k - .5) * ancho for i in range(3)]
        y = list(t[f"TC_{g}"])
        ax.bar(x, y, ancho - .03, color=COLOR[g], label=NOMBRE[g])
        for xi, v in zip(x, y):
            ax.text(xi, v + .8, f"{v:.1f}", ha="center", fontsize=8, color=TINTA2)
    ax.set_xticks(range(3), [etiquetas[c] for c in t.clase_cambio])
    _estilo(ax, "Corrección según el cambio del texto de la dimensión", "% de las deficiencias corregidas")
    ax.legend(frameon=False, fontsize=8)
    return _guardar(fig, "oe6_correccion_por_clase_de_cambio.png")


def uso_por_semana(u):
    t = uso_mentoria.por_semana(u)
    fig, ax = plt.subplots(figsize=(6.5, 3.2))
    ax.bar(t["semana de uso"], t["proyectos con consultas"], .55, color=COLOR["GE"])
    for i, v in enumerate(t["proyectos con consultas"]):
        ax.text(i, v + .3, str(v), ha="center", fontsize=9, color=TINTA2)
    ax.set_ylim(0, 20)
    _estilo(ax, "Proyectos del Grupo Experimental que consultaron MentorIA (de 20)", "Proyectos")
    return _guardar(fig, "uso_mentoria_por_semana.png")
