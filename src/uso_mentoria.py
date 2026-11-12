"""Uso de MentorIA en el Grupo Experimental: descripción por semana y relación exploratoria con el OE6.

1. Descriptivo (con resultados): data/uso_mentoria_semana.csv, registros automáticos del sistema agregados por
   proyecto y semana de uso (lunes a domingo). La semana S5 incluye todo el uso desde el inicio; S9 reúne las
   semanas 8 y 9, porque en la semana 8 no hubo medición.

2. Vínculo entre la observación comunicada y la corrección (EN DESARROLLO, sin resultados). Ver el plan en
   `plan_vinculo_recomendaciones()`. Distingue tres hechos que no son equivalentes:
     (a) deficiencia detectada   el evaluador califica «no cumple» un criterio (OE6, con resultados);
     (b) observación comunicada  MentorIA le dio al estudiante una recomendación concreta (registro de la
                                 conversación);
     (c) corrección              el criterio pasa a «cumple» en la entrega siguiente y el texto cambió.
   El OE6 mide (a) -> (c) en ambos grupos. El análisis complementario mide (b) -> (c) solo en el GE.
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


# ---------------------------------------------------------------- análisis en desarrollo
COLUMNAS_RECOMENDACIONES = ["proyecto", "fecha", "semana_de_uso", "modo", "dimension", "item_rubrica",
                            "recomendacion_resumida", "codificador"]


def plan_vinculo_recomendaciones() -> str:
    return """ANÁLISIS COMPLEMENTARIO DEL GE: DE LA OBSERVACIÓN COMUNICADA A LA CORRECCIÓN (en desarrollo)

Insumo: los mensajes de MentorIA registrados en su base de datos (conversaciones y respuestas, con fecha y
proyecto), exportados con una consulta de solo lectura, anonimizados (P01-P36) y sin el texto del estudiante.

Procedimiento:
 1. Unidad: cada recomendación concreta de MentorIA (b), con su fecha y la semana de uso.
 2. Codificación: cada recomendación se asigna a la dimensión y al ítem de la rúbrica que aborda. La realizan
    dos investigadores de forma independiente (acuerdo con kappa de Cohen) o, si se automatiza, un modelo de
    lenguaje validado contra esa codificación manual en una muestra.
 3. Vínculo: la recomendación se asocia a la entrega inmediatamente posterior a su fecha y se verifica, con
    los datos del OE6, si el ítem estaba incumplido en la entrega anterior (a) y si pasó a cumplirse con
    cambio de texto en la dimensión (c).
 4. Indicadores: proporción de recomendaciones atendidas = (b con a -> c) / (b con a); comparación con la
    tasa de corrección de las deficiencias del mismo proyecto que NO recibieron recomendación (control
    dentro del proyecto), mediante un modelo binomial con efecto aleatorio del proyecto.
 5. Alcance: solo el GE y solo los proyectos y semanas con consultas (en S8-S9 consultaron 2 proyectos),
    por lo que se reporta como análisis complementario, con su n real.

Estado: diseño y código listos (vincular_recomendaciones); la extracción de los registros de conversación
está en desarrollo, por lo que este análisis no tiene resultados en el presente informe."""


def vincular_recomendaciones(recomendaciones: pd.DataFrame, df_oe6: pd.DataFrame) -> pd.DataFrame:
    """recomendaciones: columnas COLUMNAS_RECOMENDACIONES (una fila por recomendación codificada).
    Devuelve, por recomendación, si el ítem era una deficiencia y si se corrigió con cambio de texto en la
    entrega siguiente."""
    faltan = set(COLUMNAS_RECOMENDACIONES) - set(recomendaciones.columns)
    if faltan:
        raise ValueError(f"Faltan columnas: {sorted(faltan)}")
    r = recomendaciones.assign(intervalo=recomendaciones.semana_de_uso.map(SEMANA_A_INTERVALO),
                               item=recomendaciones.item_rubrica.astype(str))
    m = r.merge(df_oe6[["proyecto", "intervalo", "item", "deficiencia", "corregida_con_cambio"]],
                on=["proyecto", "intervalo", "item"], how="left")
    m["estado"] = m.apply(lambda f: "ítem no evaluado" if pd.isna(f.deficiencia) else
                          "no era deficiencia" if f.deficiencia == 0 else
                          "corregida con cambio de texto" if f.corregida_con_cambio == 1 else "no corregida", axis=1)
    return m
