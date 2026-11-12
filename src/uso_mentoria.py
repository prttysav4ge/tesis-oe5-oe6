"""Uso de MentorIA en el Grupo Experimental: descripción por semana y relación exploratoria con el OE6.

1. Descriptivo (con resultados): data/uso_mentoria_semana.csv, registros automáticos del sistema agregados por
   proyecto y semana de uso (lunes a domingo). La semana S5 incluye todo el uso desde el inicio; S9 reúne las
   semanas 8 y 9, porque en la semana 8 no hubo medición.

2. Vínculo entre la observación comunicada y la corrección (`vincular`), con las revisiones que MentorIA hizo a
   pedido de los estudiantes (data/mentoria_observaciones.csv). Distingue tres hechos que no son equivalentes:
     (a) deficiencia detectada   el evaluador califica «no cumple» un criterio (OE6, con resultados);
     (b) observación comunicada  MentorIA le dio al estudiante una recomendación concreta (registro de la
                                 conversación);
     (c) corrección              el criterio pasa a «cumple» en la entrega siguiente y el texto cambió.
   El OE6 mide (a) -> (c) en ambos grupos. El análisis complementario mide (b) -> (c) solo en el GE, con su n real.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .estadistica import spearman

DATA = Path(__file__).resolve().parents[1] / "data"
SEMANA_A_INTERVALO = {"S5": "S4_S5", "S6": "S5_S6", "S7": "S6_S7", "S9": "S7_S9"}


def cargar(data: Path = DATA) -> pd.DataFrame:
    return pd.read_csv(data / "uso_mentoria_semana.csv")


def por_semana(u: pd.DataFrame) -> pd.DataFrame:
    g = u.groupby("semana_de_uso")
    usuarios = u[u.consultas > 0].groupby("semana_de_uso").consultas
    return pd.DataFrame({
        "proyectos del GE": g.size(),
        "proyectos con consultas": g.consultas.apply(lambda s: int((s > 0).sum())),
        "consultas": g.consultas.sum(),
        "consultas por proyecto usuario (Md)": usuarios.median(),
        "revisiones de secciones": g.revisiones_secciones.sum(),
        "revisiones completas": g.revisiones_completas.sum(),
        "días con consultas": g.dias_con_consultas.sum(),
        "minutos en sesiones con consultas": g.minutos_sesiones_con_consultas.sum().round(0),
        "sesiones sin mensajes": g.sesiones_sin_mensajes.sum(),
    }).reset_index().rename(columns={"semana_de_uso": "semana de uso"})


def uso_y_correccion(u: pd.DataFrame, df_oe6: pd.DataFrame) -> dict:
    """Exploratorio, solo GE: consultas de la semana frente a la tasa de corrección con cambio de texto del
    intervalo que termina en esa semana (proyecto x intervalo; medidas repetidas, sin inferencia causal)."""
    from .oe6 import por_proyecto

    filas = []
    for s, iv in SEMANA_A_INTERVALO.items():
        x = df_oe6[(df_oe6.grupo == "GE") & (df_oe6.intervalo == iv)]
        pp = por_proyecto(x, "corregida_con_cambio").merge(u[u.semana_de_uso == s][["proyecto", "consultas"]],
                                                         on="proyecto")
        filas.append(pp.assign(intervalo=iv))
    z = pd.concat(filas)
    resumen = z.groupby(z.consultas > 0).TC.agg(["size", "median", "mean"]).rename(
        index={False: "sin consultas", True: "con consultas"})
    return dict(datos=z, resumen=resumen, spearman=spearman(list(z.consultas), list(z.TC)))


# ---------------------------------------------------------------- de la observación comunicada a la corrección
# MentorIA revisa con la rúbrica institucional de 33 criterios (puntaje 0-3); el evaluador, con la rúbrica de 100
# ítems en 15 dimensiones. Correspondencia por contenido del criterio (None: sin dimensión equivalente en el
# evaluador: citas y referencias, procedimiento y aspectos administrativos).
MAPA_ITEMS = {1: 1, 2: 1, 3: 1, 4: 2, 5: 2, 6: 4, 7: 4, 8: 5, 9: 3, 10: 5, 11: 7, 12: 7, 13: 7, 14: 7, 15: None,
              16: 7, 17: None, 18: 8, 19: 8, 20: 9, 21: 10, 22: 11, 23: 12, 24: 13, 25: 14, 26: None, 27: 15,
              28: None, 29: None, 30: None, 31: None, 32: None, 33: None}


def cargar_observaciones(data: Path = DATA) -> pd.DataFrame:
    """data/mentoria_observaciones.csv: un criterio revisado por MentorIA en una revisión de un proyecto del GE,
    con el intervalo de entregas al que se vincula. comunicada = 1 si MentorIA lo calificó por debajo del máximo
    (observación comunicada al estudiante)."""
    return pd.read_csv(data / "mentoria_observaciones.csv")


def descriptivo_observaciones(ob: pd.DataFrame) -> pd.DataFrame:
    x = ob[ob.comunicada == 1]
    g = x.groupby("intervalo")
    return pd.DataFrame({"revisiones de MentorIA": g.revision.nunique(), "proyectos": g.proyecto.nunique(),
                         "observaciones comunicadas": g.size(),
                         "con dimensión equivalente": g.dimension.apply(lambda s: int(s.notna().sum())),
                         "pares proyecto-dimensión": x.dropna(subset=["dimension"]).groupby("intervalo").apply(
                             lambda d: d.groupby(["proyecto", "dimension"]).ngroups)}).reset_index()


def vincular(ob: pd.DataFrame, df_oe6: pd.DataFrame) -> dict:
    """Vincula (b) observación comunicada con (a) deficiencia detectada y (c) corrección con cambio de texto, en
    el GE. Unidad de exposición: proyecto x intervalo x dimensión del evaluador.
      seguimiento   por cada par proyecto-intervalo-dimensión con observación comunicada: si el evaluador
                    registraba deficiencias en esa dimensión (a) y si al menos una se corrigió con cambio de texto
                    (c); también si el texto de la dimensión se revisó;
      comparación   deficiencias del GE en dimensiones con observación comunicada frente a las de dimensiones
                    sin ella, dentro de los proyecto-intervalos en que MentorIA hizo al menos una revisión
                    (mismo proyecto, misma semana); GEE binomial agrupado por proyecto.
    """
    from .estadistica import gee_binomial

    ge = df_oe6[df_oe6.grupo == "GE"]
    com = ob[(ob.comunicada == 1) & ob.dimension.notna()].assign(dimension=lambda d: d.dimension.astype(int))
    expo = com.groupby(["proyecto", "intervalo", "dimension"]).size().rename("observaciones").reset_index()
    dims = ge.groupby(["proyecto", "intervalo", "dimension"]).agg(
        deficiencias=("deficiencia", "sum"), corregidas_con_cambio=("corregida_con_cambio", "sum"),
        texto_revisado=("con_cambio_texto", "max")).reset_index()
    seg = expo.merge(dims, on=["proyecto", "intervalo", "dimension"], how="left")
    seg["estado"] = seg.apply(lambda f: "dimensión no redactada en la entrega anterior" if pd.isna(f.deficiencias)
                              else "sin deficiencias en el evaluador" if f.deficiencias == 0
                              else "corregida con cambio de texto" if f.corregidas_con_cambio > 0
                              else "no corregida", axis=1)
    resumen_seg = seg.groupby("estado").size().rename("pares").reset_index()
    con_def = seg[seg.deficiencias > 0]

    revisados = ob[ob.dimension.notna()][["proyecto", "intervalo"]].drop_duplicates()
    x = ge[ge.deficiencia == 1].merge(revisados, on=["proyecto", "intervalo"])
    x = x.merge(expo[["proyecto", "intervalo", "dimension"]].assign(comunicada=1),
                on=["proyecto", "intervalo", "dimension"], how="left").fillna({"comunicada": 0})
    comp = x.groupby("comunicada").agg(deficiencias=("corregida_con_cambio", "size"),
                                       corregidas_con_cambio=("corregida_con_cambio", "sum"),
                                       proyectos=("proyecto", "nunique")).reset_index()
    comp["TC_con_cambio"] = 100 * comp.corregidas_con_cambio / comp.deficiencias
    comp["comunicada"] = comp.comunicada.map({0: "sin observación de MentorIA", 1: "con observación de MentorIA"})
    modelo = None
    if x.comunicada.nunique() == 2 and x.proyecto.nunique() >= 5:
        try:
            modelo = gee_binomial(x.assign(y=x.corregida_con_cambio, com=x.comunicada.astype(int)),
                                  y="y", grupo="com", cluster="proyecto", fijo="intervalo")
        except Exception as e:  # pocos datos: se informa sin modelo
            modelo = dict(error=str(e))
    return dict(seguimiento=seg, resumen_seguimiento=resumen_seg,
                atendidas=dict(pares_con_deficiencia=len(con_def),
                               corregidos=int((con_def.corregidas_con_cambio > 0).sum()),
                               texto_revisado=int((con_def.texto_revisado == 1).sum()),
                               proyectos=int(con_def.proyecto.nunique())),
                comparacion=comp, gee=modelo, n_proyecto_intervalos=int(len(revisados)))
