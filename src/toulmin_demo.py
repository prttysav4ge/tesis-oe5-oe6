"""Demostración del índice argumentativo 2.0 sobre un texto de ejemplo (sección opcional del notebook).

Mismo prompt (src/prompts/argumentacion_toulmin_v2.md), mismo modelo y parámetros (gpt-4.1, temperatura 0,
semilla 42) y la misma verificación y puntuación que el estudio (oe56/toulmin_v2.py). Diferencias con el
estudio, solo para que corra sin el material privado: el texto se divide en párrafos por líneas en blanco y en
unidades por oraciones (el estudio usa la geometría del PDF y spaCy), y la cohesión léxica usa palabras
normalizadas en lugar de lemas. UNA llamada a la API por sección analizada.
"""
from __future__ import annotations

import re
import statistics as st
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

PROMPT = (Path(__file__).resolve().parent / "prompts" / "argumentacion_toulmin_v2.md").read_text(encoding="utf-8")
SECCIONES = {"S02": "Descripción y delimitación del problema", "S05": "Justificación, importancia y viabilidad"}
APOYOS = ["dato", "garantia", "respaldo", "calificador", "refutacion"]
COMPONENTES = ["afirmacion"] + APOYOS

# Diccionario de atenuadores del sistema evaluador (Evaluador-Tesis, backend/graph/argumentacion.py,
# commit c2b0f28), reproducido para que la demostración no dependa de ese repositorio.
CALIFICADORES = [
    r"probablemente", r"posiblemente", r"presumiblemente", r"aparentemente", r"al parecer", r"quiz[aá]s?",
    r"tal vez", r"podr[ií]a(n)?", r"pudiera(n)?", r"puede(n)? que", r"es posible que", r"es probable que",
    r"suele(n)?", r"tiende(n)? a", r"en general", r"generalmente", r"por lo general", r"habitualmente",
    r"frecuentemente", r"a menudo", r"en la mayor[ií]a de", r"en gran medida", r"en cierta medida",
    r"en parte", r"solo en parte", r"parcialmente", r"relativamente", r"en principio",
    r"parece(n)? que", r"sugiere(n)? que", r"se estima que",
    r"pr[aá]cticamente (nul[oa]s?|inexistentes?|ningun[oa]?s?|imposibles?|todos?|todas?|iguales?|ausentes?)",
]
PATRON_CALIFICADOR = re.compile(r"\b(" + "|".join(CALIFICADORES) + r")\b", re.IGNORECASE)


class Garantia(BaseModel):
    unidad: str
    dato: str = Field(description="id de la unidad de dato que esta garantía conecta con la afirmación")


class Respaldo(BaseModel):
    unidad: str
    garantia: Optional[str] = Field(default=None, description="id de la garantía que respalda; null si respalda la afirmación")


class Refutacion(BaseModel):
    unidad: str
    responde_en: Optional[str] = Field(default=None, description="id de la unidad que responde a la objeción; null si no se responde")


class Argumento(BaseModel):
    afirmacion: str = Field(description="id de la unidad que contiene la afirmación del autor")
    central: bool = Field(description="true si es la afirmación central de la sección")
    datos: list[str]
    garantias: list[Garantia]
    respaldos: list[Respaldo]
    refutaciones: list[Refutacion]


class RespuestaToulminV2(BaseModel):
    afirmaciones: list[Argumento]


def dividir(texto: str) -> list[dict]:
    """Unidades [Pn-Um]: párrafos separados por línea en blanco; unidades = oraciones."""
    unidades = []
    parrafos = [p.strip() for p in re.split(r"\n\s*\n", texto.strip()) if p.strip()]
    for i, par in enumerate(parrafos, 1):
        for j, o in enumerate([o for o in re.split(r"(?<=[.!?])\s+", par) if o.strip()], 1):
            unidades.append(dict(id=f"P{i}-U{j}", parrafo=f"P{i}", texto=o.strip(),
                                 lemas=re.findall(r"\w{4,}", o.lower())))
    return unidades


def prompt_de(sid: str, unidades: list[dict]) -> str:
    bloques, actual = [], None
    for u in unidades:
        if u["parrafo"] != actual:
            actual = u["parrafo"]
            bloques.append(f"\n[{actual}] (párrafo)")
        bloques.append(f"[{u['id']}] {u['texto']}")
    return PROMPT.replace("{seccion}", SECCIONES[sid]).replace("{unidades}", "\n".join(bloques).strip())


def llamar(prompt: str, api_key: str, modelo: str = "gpt-4.1") -> dict:
    from openai import OpenAI
    r = OpenAI(api_key=api_key).chat.completions.parse(
        model=modelo, temperature=0, top_p=1, seed=42, messages=[{"role": "user", "content": prompt}],
        response_format=RespuestaToulminV2)
    return r.choices[0].message.parsed.model_dump()


def verificar(respuesta: dict, unidades: list[dict]) -> dict:
    """Verificación determinista del estudio: ids existentes, sin autovínculos, garantía con dato válido de la
    misma afirmación, respaldo con garantía válida; calificadores por diccionario."""
    ids = {u["id"]: u for u in unidades}
    lemas = {u["id"]: set(u["lemas"]) for u in unidades}
    descartes = dict(id_inexistente=0, autovinculo=0, garantia_sin_dato_valido=0, respaldo_garantia_invalida=0,
                     afirmacion_repetida=0)
    argumentos, vistos = [], set()
    for a in respuesta["afirmaciones"]:
        c = a["afirmacion"]
        if c not in ids:
            descartes["id_inexistente"] += 1
            continue
        if c in vistos:
            descartes["afirmacion_repetida"] += 1
            continue
        vistos.add(c)

        def valido(x):
            if x not in ids:
                descartes["id_inexistente"] += 1
                return False
            if x == c:
                descartes["autovinculo"] += 1
                return False
            return True

        datos = list(dict.fromkeys(d for d in a["datos"] if valido(d)))
        garantias = []
        for g in a["garantias"]:
            if not valido(g["unidad"]):
                continue
            if g["dato"] not in datos or g["dato"] == g["unidad"]:
                descartes["garantia_sin_dato_valido"] += 1
                continue
            garantias.append(g)
        g_ids = {g["unidad"] for g in garantias}
        respaldos = []
        for r in a["respaldos"]:
            if not valido(r["unidad"]):
                continue
            if r.get("garantia") is not None and r["garantia"] not in g_ids:
                descartes["respaldo_garantia_invalida"] += 1
                continue
            respaldos.append(r)
        refut = []
        for r in a["refutaciones"]:
            if not valido(r["unidad"]):
                continue
            resp = r.get("responde_en")
            refut.append(dict(unidad=r["unidad"], responde_en=resp if resp in ids and resp != r["unidad"] else None))
        calif = [m.group(0) for u in [c] + [g["unidad"] for g in garantias]
                 for m in PATRON_CALIFICADOR.finditer(ids[u]["texto"])]
        vinc = ([("dato", d) for d in datos] + [("garantia", g["unidad"]) for g in garantias]
                + [("respaldo", r["unidad"]) for r in respaldos] + [("refutacion", r["unidad"]) for r in refut])
        cohesion = [dict(tipo=t, unidad=u, mismo_parrafo=ids[u]["parrafo"] == ids[c]["parrafo"],
                         lemas_compartidos=len(lemas[u] & lemas[c])) for t, u in vinc]
        argumentos.append(dict(afirmacion=c, central=bool(a.get("central")), datos=datos, garantias=garantias,
                               respaldos=respaldos, refutaciones=refut, calificadores=calif, cohesion=cohesion,
                               apoyos={k: bool(v) for k, v in zip(APOYOS, (datos, garantias, respaldos, calif, refut))}))
    return dict(argumentos=argumentos, descartes=descartes)


def puntuar(ver: dict) -> dict:
    args = ver["argumentos"]
    presentes = [c for c in COMPONENTES if (c == "afirmacion" and args) or any(a["apoyos"].get(c) for a in args)]
    fundamentos = any(a["apoyos"]["dato"] or a["apoyos"]["garantia"] or a["apoyos"]["respaldo"] for a in args)
    refut = [r for a in args for r in a["refutaciones"]]
    respondidas = [r for r in refut if r["responde_en"]]
    nivel = (0 if not args else 1 if not fundamentos else 2 if not refut else 3 if not respondidas
             else 4 if len(respondidas) == 1 else 5)
    elab = [sum(a["apoyos"].values()) / len(APOYOS) for a in args]
    return dict(afirmaciones=len(args), presentes=presentes,
                indice_estructural=100 * len(presentes) / 6,
                indice_elaboracion=100 * st.mean(elab) if elab else 0.0, nivel_erduran=nivel,
                perfil={k: sum(a["apoyos"][k] for a in args) for k in APOYOS})
