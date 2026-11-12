"""Genera todas las tablas del OE5 y del OE6 en results/ (CSV) a partir de data/. Sin API."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import auditoria, figuras, oe5, oe6, uso_mentoria

RESULTS = Path(__file__).resolve().parents[1] / "results"


def guardar(nombre: str, t: pd.DataFrame) -> pd.DataFrame:
    RESULTS.mkdir(exist_ok=True)
    t.to_csv(RESULTS / nombre, index=False, encoding="utf-8")
    return t


def semanas_oe5() -> list[str]:
    s = pd.read_csv(oe5.DATA / "oe5_secciones.csv").semana.unique()
    return sorted(s, key=lambda x: int(x[1:]))


def tabla29(df: pd.DataFrame, semanas=("S4", "S7")) -> pd.DataFrame:
    filas = []
    for sid, nombre in oe5.SECCIONES.items():
        for s in semanas:
            for g in ("GC", "GE"):
                p = oe5.perfil(df, s, sid, g)
                filas.append({"sección": nombre, "semana": s, "grupo": g, "n": p["n"],
                              "afirmaciones por sección (Md)": p["afirmaciones_Md"],
                              **{f"% con {k}": round(p[f"pct_con_{k}"], 1) for k in oe5.APOYOS},
                              "secciones con garantía": p["secciones_con_garantia"],
                              "índice de elaboración (Md)": p["elaboracion_Md"],
                              "índice estructural 2.0 (Md)": p["estructural_Md"],
                              "índice estructural 1.1 (Md)": p["v11_Md"]})
    return pd.DataFrame(filas)


def tabla30(df: pd.DataFrame, semanas: list[str]) -> pd.DataFrame:
    w = oe5.consecutivas(df, semanas)
    h = oe5.he5(df)
    filas = []
    for sid, nombre in oe5.SECCIONES.items():
        for g in ("GC", "GE", "Total"):
            f = {"sección": nombre, "grupo": g}
            for s in semanas:
                x = df[(df.semana == s) & (df.seccion == sid) & ((df.grupo == g) | (g == "Total"))]
                f[f"Md {s}"] = round(x.indice_elaboracion.median(), 1)
            for a, b in zip(semanas, semanas[1:]):
                r = w[(f"{a}_{b}", sid)][g]
                f[f"{a}-{b}: +/−, p"] = f"{r['aumentan']}/{r['disminuyen']}, " + (f"{r['p']:.3f}" if r["p"] else "—")
            if g == "GC":
                f["U; p (Holm)"] = f"U = {h[sid]['U']}; {h[sid]['p']:.3f} ({h[sid]['p_holm']:.3f})"
            filas.append(f)
    return pd.DataFrame(filas)


def he5_tabla(df: pd.DataFrame) -> pd.DataFrame:
    filas = []
    for ind, nombre in (("indice_elaboracion", "índice de elaboración (principal)"),
                        ("indice_estructural", "índice estructural")):
        h = oe5.he5(df, ind)
        for sid, sec in oe5.SECCIONES.items():
            r = h[sid]
            filas.append({"índice": nombre, "sección": sec, "n GC / GE": f"{r['n_GC']} / {r['n_GE']}",
                          "Md cambio GC": r["Md_GC"], "Md cambio GE": r["Md_GE"], "U": r["U"],
                          "p unilateral": round(r["p"], 4), "p Holm": round(r["p_holm"], 4),
                          "δ de Cliff": round(r["delta"], 2), "rechaza H0": r["rechaza_H0"]})
        filas.append({"índice": nombre, "sección": "DECISIÓN", "n GC / GE": h["decision"]})
    return pd.DataFrame(filas)


def generar_todo() -> dict:
    """Corre todo y devuelve las tablas (también quedan en results/ y las figuras en results/figuras/)."""
    T = {}
    T["auditoria_v15"] = guardar("auditoria_v15.csv", auditoria.auditar_v15())
    # OE5: reproducción del v15 (S4-S7) y, si existe la semana 9, el análisis completo
    for etiqueta, semanas in (("S4_S7", ["S4", "S5", "S6", "S7"]), ("S4_S9", semanas_oe5())):
        if etiqueta == "S4_S9" and "S9" not in semanas:
            continue
        d = oe5.cargar(semanas=semanas)
        T[f"oe5_tabla29_{etiqueta}"] = guardar(f"oe5_tabla29_{etiqueta}.csv", tabla29(d, (semanas[0], semanas[-1])))
        T[f"oe5_tabla30_{etiqueta}"] = guardar(f"oe5_tabla30_{etiqueta}.csv", tabla30(d, semanas))
        T[f"oe5_he5_{etiqueta}"] = guardar(f"oe5_he5_{etiqueta}.csv", he5_tabla(d))
        sp = oe5.validez_convergente(d)
        T[f"oe5_spearman_{etiqueta}"] = guardar(f"oe5_spearman_{etiqueta}.csv", pd.DataFrame(
            [dict(semana=s, seccion=oe5.SECCIONES[sid], **v) for (s, sid), v in sp.items()]))
        figuras.oe5_elaboracion(d, semanas)
    T["oe5_retest"] = guardar("oe5_retest.csv", pd.DataFrame([oe5.retest()]))
    # OE6
    d6 = oe6.cargar()
    T["oe6_tabla31"] = guardar("oe6_tabla31_por_intervalo.csv", oe6.tabla_intervalos(d6))
    T["oe6_tabla32"] = guardar("oe6_tabla32_respaldo_textual.csv", oe6.respaldo_textual(d6))
    T["oe6_por_intervalo"] = guardar("oe6_contraste_por_intervalo.csv", oe6.por_intervalo(d6))
    T["oe6_por_dimension"] = guardar("oe6_por_dimension.csv", oe6.por_dimension(d6))
    T["oe6_he6_v16"] = guardar("oe6_he6_v16_sensibilidad.csv", oe6.he6_v16(d6))
    T["oe6_variabilidad"] = guardar("oe6_variabilidad_evaluador.csv", oe6.variabilidad_evaluador(d6))
    T["oe6_concordancia_diff"] = guardar("oe6_concordancia_diff.csv", oe6.concordancia_diff())
    T["oe6_TR"] = guardar("oe6_retroceso.csv", pd.DataFrame([oe6.contraste(oe6.por_proyecto(d6), "TR", "two-sided")]))
    figuras.oe6_por_intervalo(d6)
    figuras.oe6_por_clase(d6)
    # Uso de MentorIA
    u = uso_mentoria.cargar()
    T["uso_por_semana"] = guardar("uso_mentoria_por_semana.csv", uso_mentoria.por_semana(u))
    ex = uso_mentoria.uso_y_correccion(u, d6)
    T["uso_y_correccion"] = guardar("uso_mentoria_y_correccion.csv", ex["resumen"].reset_index())
    T["uso_y_correccion_spearman"] = ex["spearman"]
    figuras.uso_por_semana(u)
    return T
