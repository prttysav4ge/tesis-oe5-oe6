"""OE5: calidad argumentativa (modelo de Toulmin) de la descripción del problema (S02) y la justificación (S05).

Entrada: data/oe5_secciones.csv, una fila por sección completa, proyecto y semana, con los indicadores del índice
argumentativo 2.0 ya calculados a partir de la respuesta guardada del modelo (gpt-4.1, temperatura 0, semilla 42)
y verificada con reglas fijas (src del estudio: oe56/toulmin_v2.py). El notebook no llama a la API para esto.
  indice_estructural   tipos de componente presentes en la sección sobre seis (%)
  indice_elaboracion   media, sobre las afirmaciones, de la proporción de los cinco apoyos que tiene cada una (%)
  afirm_con_<c>        proporción de afirmaciones con al menos un componente c vinculado y verificado
HE5: U de Mann-Whitney unilateral (GE > GC) del cambio del índice de elaboración entre la primera y la última
medición con la sección completa, con Holm para las dos secciones.
"""
from __future__ import annotations

import statistics as st
from pathlib import Path

import pandas as pd

from .estadistica import cci_2_1, holm, mann_whitney, spearman, wilcoxon_aumento

DATA = Path(__file__).resolve().parents[1] / "data"
SECCIONES = {"S02": "Descripción del problema", "S05": "Justificación"}
APOYOS = ["dato", "garantia", "respaldo", "calificador", "refutacion"]


def cargar(data: Path = DATA, semanas=("S4", "S5", "S6", "S7")) -> pd.DataFrame:
    df = pd.read_csv(data / "oe5_secciones.csv")
    return df[df.semana.isin(semanas)].copy()


def perfil(df: pd.DataFrame, semana: str, seccion: str, grupo: str | None = None) -> dict:
    """Tabla 29: perfil de componentes. % de afirmaciones con cada apoyo = suma ponderada por afirmaciones."""
    x = df[(df.semana == semana) & (df.seccion == seccion)]
    if grupo:
        x = x[x.grupo == grupo]
    tot = x.afirmaciones.sum()
    r = dict(n=len(x), afirmaciones_Md=st.median(x.afirmaciones),
             **{f"pct_con_{k}": 100 * (x[f"afirm_con_{k}"] * x.afirmaciones).sum() / tot for k in APOYOS},
             secciones_con_garantia=int(x.pres_garantia.sum()),
             elaboracion_Md=st.median(x.indice_elaboracion), estructural_Md=st.median(x.indice_estructural),
             v11_Md=st.median(x.indice_v11.dropna()) if x.indice_v11.notna().any() else None,
             niveles=x.nivel.value_counts().to_dict(),
             vinculos_entre_parrafos_pct=100 * x.vinculos_entre_parrafos.sum() / x.vinculos_total.sum(),
             vinculos_con_lema_pct=100 * x.vinculos_con_lema.sum() / x.vinculos_total.sum())
    return r


def consecutivas(df: pd.DataFrame, semanas: list[str], indice: str = "indice_elaboracion") -> dict:
    """Wilcoxon unilateral del cambio entre mediciones consecutivas (proyectos con la sección en ambas)."""
    w = df.pivot_table(index=["proyecto", "grupo", "seccion"], columns="semana", values=indice).reset_index()
    out = {}
    for a, b in zip(semanas, semanas[1:]):
        for sid in SECCIONES:
            x = w[(w.seccion == sid)].dropna(subset=[a, b])
            dif = {g: list(x[x.grupo == g][b] - x[x.grupo == g][a]) for g in ("GC", "GE")}
            out[(f"{a}_{b}", sid)] = {"GC": wilcoxon_aumento(dif["GC"]), "GE": wilcoxon_aumento(dif["GE"]),
                                      "Total": wilcoxon_aumento(dif["GC"] + dif["GE"])}
    return out


def cambio_total(df: pd.DataFrame, indice: str = "indice_elaboracion") -> pd.DataFrame:
    """Cambio entre la primera y la última medición con la sección completa (proyectos con >= 2 mediciones)."""
    orden = {s: i for i, s in enumerate(sorted(df.semana.unique(), key=lambda s: int(s[1:])))}
    x = df.assign(o=df.semana.map(orden)).sort_values("o")
    g = x.groupby(["proyecto", "grupo", "seccion"])
    t = g[indice].agg(["first", "last", "count"]).reset_index()
    t = t[t["count"] >= 2]
    t["cambio"] = t["last"] - t["first"]
    return t


def he5(df: pd.DataFrame, indice: str = "indice_elaboracion") -> dict:
    t = cambio_total(df, indice)
    res = {sid: mann_whitney(t[(t.seccion == sid) & (t.grupo == "GE")].cambio,
                             t[(t.seccion == sid) & (t.grupo == "GC")].cambio) for sid in SECCIONES}
    for sid, pa in zip(SECCIONES, holm([res[s]["p"] for s in SECCIONES])):
        res[sid]["p_holm"] = pa
        res[sid]["rechaza_H0"] = pa < .05
        res[sid]["wilcoxon_dentro"] = {g: wilcoxon_aumento(t[(t.seccion == sid) & (t.grupo == g)].cambio)
                                       for g in ("GC", "GE")}
    k = sum(res[s]["rechaza_H0"] for s in SECCIONES)
    res["decision"] = "se acepta Hi" if k == 2 else "se acepta de forma parcial" if k == 1 else "no se acepta Hi"
    return res


def validez_convergente(df: pd.DataFrame, indice: str = "indice_elaboracion") -> dict:
    return {(s, sid): spearman(list(x[indice]), list(x.calidad_dim))
            for (s, sid), x in df.groupby(["semana", "seccion"])}


def comparacion_v11(df: pd.DataFrame, seccion: str = "S02") -> dict:
    x = df[(df.seccion == seccion) & df.indice_v11.notna()]
    en33 = lambda c: 100 * ((x[c] - 33.3).abs() < .1).mean()
    return dict(n_pares=len(x), valores_v11=x.indice_v11.nunique(), valores_estructural=x.indice_estructural.nunique(),
                valores_elaboracion=x.indice_elaboracion.nunique(), pct33_v11=en33("indice_v11"),
                pct33_estructural=en33("indice_estructural"),
                mayor=int((x.indice_estructural > x.indice_v11).sum()),
                igual=int((x.indice_estructural == x.indice_v11).sum()),
                menor=int((x.indice_estructural < x.indice_v11).sum()))


def retest(data: Path = DATA) -> dict:
    r = pd.read_csv(data / "oe5_retest.csv")
    return dict(secciones=len(r), unidades=int(r.unidades.sum()),
                funciones_iguales_pct=100 * r.unidades_misma_funcion.sum() / r.unidades.sum(),
                vinculos_iguales_pct=100 * r.vinculos_comunes.sum() / r.vinculos_union.sum(),
                cci_elaboracion=cci_2_1(zip(r.elaboracion_1, r.elaboracion_2)),
                cci_estructural=cci_2_1(zip(r.estructural_1, r.estructural_2)))
