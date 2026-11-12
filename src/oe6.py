"""OE6: corrección, en la entrega siguiente, de las deficiencias detectadas por el sistema evaluador.

Terminología (se distingue de una observación comunicada al estudiante, que este análisis NO mide):
  deficiencia detectada  ítem de la rúbrica calificado «no cumple» en la entrega t, dentro de una dimensión que el
                         proyecto ya tenía redactada en t (los ítems de dimensiones aún no redactadas son avance
                         pendiente, no deficiencias);
  corrección             la deficiencia pasa a «cumple» en la entrega t+1;
  persistencia           sigue «no cumple»;
  retroceso              un ítem «cumple» en t pasa a «no cumple» en t+1.
  TC = correcciones / deficiencias (tasa de corrección; en el v15, «tasa de levantamiento», TL)
  TR = retrocesos / ítems cumplidos (tasa de retroceso)
Respaldo textual: cada dimensión se compara con su versión anterior (src/diff_versiones.py) y se clasifica en sin
cambio, superficial o sustantiva. Una corrección en una dimensión cuyo texto no cambió no puede atribuirse al
estudiante: refleja la variabilidad del evaluador sobre el mismo texto.
Entradas: data/oe6_items.csv (un ítem por proyecto e intervalo) y data/oe6_dimensiones.csv.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .estadistica import gee_binomial, holm, mann_whitney

DATA = Path(__file__).resolve().parents[1] / "data"
INTERVALOS = ["S4_S5", "S5_S6", "S6_S7", "S7_S9"]
CLASES = ["sin_cambio", "superficial", "sustantiva", "sin_datos"]


def cargar(data: Path = DATA) -> pd.DataFrame:
    df = pd.read_csv(data / "oe6_items.csv", dtype={"item": str})
    df["deficiencia"] = (df.puntaje_A == 0).astype(int)
    df["corregida"] = ((df.puntaje_A == 0) & (df.puntaje_B == 1)).astype(int)
    df["cumplido"] = (df.puntaje_A == 1).astype(int)
    df["retroceso"] = ((df.puntaje_A == 1) & (df.puntaje_B == 0)).astype(int)
    df["con_cambio_texto"] = df.clase_cambio.isin(["superficial", "sustantiva"]).astype(int)
    df["corregida_sust"] = ((df.corregida == 1) & (df.clase_cambio == "sustantiva")).astype(int)
    df["corregida_con_cambio"] = ((df.corregida == 1) & (df.con_cambio_texto == 1)).astype(int)
    return df


def _resumen(x: pd.DataFrame) -> dict:
    defi, corr = int(x.deficiencia.sum()), int(x.corregida.sum())
    cump, retr = int(x.cumplido.sum()), int(x.retroceso.sum())
    porclase = x[x.corregida == 1].clase_cambio.value_counts()
    return dict(deficiencias=defi, corregidas=corr, persistentes=defi - corr, TC=100 * corr / defi if defi else None,
                cumplidos=cump, retrocesos=retr, TR=100 * retr / cump if cump else None,
                **{f"corregidas_{c}": int(porclase.get(c, 0)) for c in CLASES})


def tabla_intervalos(df: pd.DataFrame) -> pd.DataFrame:
    """Tabla 31 del v15: por intervalo y grupo. Entregas nominales: proyectos con el mismo texto que la semana
    anterior (o sin entrega nueva), que conservan la calificación; en el total, suma de los intervalos."""
    filas = []
    for iv in INTERVALOS + ["Total"]:
        for g in ("GC", "GE"):
            x = df[(df.grupo == g) & ((df.intervalo == iv) | (iv == "Total"))]
            nom = x[x.nominal == 1].groupby("intervalo").proyecto.nunique().sum()
            filas.append(dict(intervalo=iv, grupo=g, entregas_nominales=int(nom), **_resumen(x)))
    return pd.DataFrame(filas)


def por_proyecto(df: pd.DataFrame, numerador: str = "corregida", filtro=None) -> pd.DataFrame:
    """TC acumulada de cada proyecto: suma de correcciones sobre suma de deficiencias de los intervalos.
    numerador: columna 0/1 que cuenta como corrección; filtro: máscara de filas que se conservan."""
    x = df if filtro is None else df[filtro]
    g = x.groupby(["proyecto", "grupo"])
    t = pd.DataFrame(dict(deficiencias=g.deficiencia.sum(), corregidas=g[numerador].sum(),
                          cumplidos=g.cumplido.sum(), retrocesos=g.retroceso.sum())).reset_index()
    t["TC"] = 100 * t.corregidas / t.deficiencias
    t["TR"] = 100 * t.retrocesos / t.cumplidos
    return t


def contraste(pp: pd.DataFrame, var: str = "TC", alternativa: str = "greater") -> dict:
    return mann_whitney(pp[pp.grupo == "GE"][var].dropna(), pp[pp.grupo == "GC"][var].dropna(), alternativa)


def respaldo_textual(df: pd.DataFrame) -> pd.DataFrame:
    """Tabla 32 del v15: TC y TR según la clase de cambio del texto, en las entregas con avance (no nominales)."""
    x = df[df.nominal == 0]
    filas = []
    for c in ["sin_cambio", "superficial", "sustantiva"]:
        y = x[x.clase_cambio == c]
        r = _resumen(y)
        filas.append(dict(clase_cambio=c, dimensiones=int(y.groupby(["intervalo", "proyecto", "dimension"]).ngroups),
                          deficiencias=r["deficiencias"], TC=r["TC"], cumplidos=r["cumplidos"], TR=r["TR"],
                          TC_GC=_resumen(y[y.grupo == "GC"])["TC"], TC_GE=_resumen(y[y.grupo == "GE"])["TC"]))
    return pd.DataFrame(filas)


def por_dimension(df: pd.DataFrame) -> pd.DataFrame:
    x = df[df.deficiencia == 1]
    g = x.groupby(["dimension", "grupo"])
    t = pd.DataFrame(dict(deficiencias=g.size(), corregidas=g.corregida.sum())).reset_index()
    t["TC"] = 100 * t.corregidas / t.deficiencias
    return t


def gee(df: pd.DataFrame, numerador: str = "corregida") -> dict:
    x = df[df.deficiencia == 1].assign(y=lambda d: d[numerador], GE=lambda d: (d.grupo == "GE").astype(int))
    return gee_binomial(x, y="y", grupo="GE", cluster="proyecto", fijo="intervalo")


def por_intervalo(df: pd.DataFrame) -> pd.DataFrame:
    """Contraste de la TC por proyecto en cada intervalo, con Holm para los cuatro (exploratorio)."""
    filas = []
    for iv in INTERVALOS:
        r = contraste(por_proyecto(df[df.intervalo == iv]))
        filas.append(dict(intervalo=iv, **r))
    t = pd.DataFrame(filas)
    t["p_holm"] = holm(list(t.p))
    return t


def analisis_completo(df: pd.DataFrame) -> dict:
    """Todas las cifras del OE6 en el v15 y los análisis nuevos de sensibilidad."""
    pp = por_proyecto(df)
    R = dict(
        tabla_intervalos=tabla_intervalos(df),
        respaldo_textual=respaldo_textual(df),
        por_dimension=por_dimension(df),
        por_intervalo=por_intervalo(df),
        # v15: contraste principal (todas las correcciones)
        principal_v15=contraste(pp),
        TR=contraste(pp, "TR", "two-sided"),
        # v15: sensibilidad (a) solo correcciones con revisión sustantiva en el numerador
        solo_sustantiva=contraste(por_proyecto(df, "corregida_sust")),
        sin_nominales=contraste(por_proyecto(df, filtro=df.nominal == 0)),
        gee=gee(df),
    )
    return R


def he6_v16(df: pd.DataFrame) -> pd.DataFrame:
    """HE6 reformulada (v16): proporción de deficiencias detectadas que se corrigen en la entrega siguiente CON
    modificación del texto de su dimensión. Contraste principal y análisis de sensibilidad, todos con la U de
    Mann-Whitney unilateral (H1: mayor en el GE) sobre la tasa acumulada de cada proyecto, salvo el GEE."""
    casos = [
        ("Principal: corrección con cambio de texto", "corregida_con_cambio", None),
        ("Todas las correcciones (contraste principal del v15)", "corregida", None),
        ("Solo correcciones con revisión sustantiva", "corregida_sust", None),
        ("Solo deficiencias de dimensiones revisadas (¿corrigen más cuando revisan?)", "corregida",
         df.con_cambio_texto == 1),
        ("Sin entregas nominales", "corregida_con_cambio", df.nominal == 0),
        ("Sin el intervalo S5-S6 (semana sin asesoría)", "corregida_con_cambio", df.intervalo != "S5_S6"),
    ]
    filas = []
    for nombre, num, filtro in casos:
        r = contraste(por_proyecto(df, num, filtro))
        filas.append(dict(analisis=nombre, Md_GC=r["Md_GC"], M_GC=r["M_GC"], Md_GE=r["Md_GE"], M_GE=r["M_GE"],
                          estadistico=f"U = {r['U']:.1f}", p=r["p"], efecto=f"δ = {r['delta']:+.2f}",
                          magnitud=r["magnitud"]))
    g = gee(df, "corregida_con_cambio")
    filas.append(dict(analisis="Por deficiencia (GEE binomial, corrección con cambio de texto)",
                      Md_GC=None, M_GC=None, Md_GE=None, M_GE=None,
                      estadistico=f"OR = {g['OR']:.2f} [{g['IC95'][0]:.2f}; {g['IC95'][1]:.2f}]",
                      p=g["p_unilateral"], efecto="", magnitud=""))
    return pd.DataFrame(filas)


def variabilidad_evaluador(df: pd.DataFrame) -> pd.DataFrame:
    """Correcciones sin cambio de texto (la calificación cambia sobre el mismo texto) por grupo, en las entregas
    reevaluadas. Las entregas nominales conservan la nota por regla y no pueden «corregir» por variabilidad, de
    modo que el grupo con más reevaluaciones recibe más correcciones espurias: por eso el contraste principal
    del v16 solo cuenta las correcciones con cambio de texto."""
    x = df[(df.nominal == 0) & (df.deficiencia == 1)]
    filas = []
    for g in ("GC", "GE"):
        y = x[x.grupo == g]
        sc = y[y.clase_cambio == "sin_cambio"]
        filas.append(dict(grupo=g, deficiencias_reevaluadas=len(y), en_dimensiones_sin_cambio=len(sc),
                          corregidas_sin_cambio=int(sc.corregida.sum()),
                          TC_sin_cambio=100 * sc.corregida.mean() if len(sc) else None,
                          pct_de_todas_las_correcciones=100 * sc.corregida.sum() / df[df.grupo == g].corregida.sum()))
    return pd.DataFrame(filas)


def concordancia_diff(data: Path = DATA) -> pd.DataFrame:
    """Contraste de las dos medidas del diff: % de palabras cambiadas (difflib, sobre la versión más larga)
    según la clase de cambio por oraciones, en las entregas reevaluadas."""
    d = pd.read_csv(data / "oe6_dimensiones.csv")
    d = d[(d.nominal == 0) & (d.clase_cambio != "sin_datos")]
    d["pct_palabras"] = 100 * d.palabras_cambiadas / d[["palabras_A", "palabras_B"]].max(axis=1).where(lambda s: s > 0)
    g = d.groupby("clase_cambio").pct_palabras
    return pd.DataFrame(dict(dimensiones=g.size(), Md=g.median(), P25=g.quantile(.25), P75=g.quantile(.75),
                             con_0_palabras=g.apply(lambda s: int((s == 0).sum())))).reindex(
        ["sin_cambio", "superficial", "sustantiva"]).reset_index()

