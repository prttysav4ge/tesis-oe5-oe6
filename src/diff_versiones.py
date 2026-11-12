"""Comparación de dos versiones de una dimensión del proyecto (tipo «git diff»), sin API.

Dos medidas complementarias:

1. Clase de cambio por oraciones (medida principal del OE6; Zhang y Litman, 2015):
   - cada oración se representa con un vector TF-IDF de sus lemas de contenido;
   - las oraciones de la versión anterior (A) y de la nueva (B) se emparejan una a una con el método húngaro
     (asignación óptima sobre la similitud coseno);
   - cada par se clasifica:
       sin cambio    mismos lemas y mismas cifras;
       superficial   similitud >= TAU_S (.75) y mismas cifras (cambia la redacción, no el contenido);
       sustantiva    similitud entre TAU_A (.35) y TAU_S, o cambian las cifras;
       añadida / eliminada   oración sin pareja (similitud < TAU_A).
   - la dimensión es «sustantiva» si tiene al menos una oración sustantiva, añadida o eliminada; «superficial»
     si solo tiene cambios superficiales, y «sin cambio» en otro caso.
   Umbrales fijados antes del análisis y verificados contra la anotación manual de 150 pares de oraciones
   (S6-S7; kappa de Cohen del módulo frente al consenso de los dos investigadores = .86).

2. Proporción de palabras cambiadas (difflib, como el comparador del evaluador): palabras insertadas, borradas
   o reemplazadas sobre la secuencia de palabras normalizadas (sin tildes ni signos, sin números sueltos de
   página), por cada 100 palabras de la versión más larga (puede superar 100 si se reescribe casi todo). Es la medida más cercana a un «git diff» por
   palabras y sirve de contraste de la medida 1.
"""
from __future__ import annotations

import difflib
import re
import unicodedata
from collections import Counter

from scipy.optimize import linear_sum_assignment
from sklearn.feature_extraction.text import TfidfVectorizer

TAU_A, TAU_S = 0.35, 0.75
CLASES_ORACION = ("sin_cambio", "superficial", "sustantiva", "anadida", "eliminada")


def normalizar(t: str) -> str:
    t = unicodedata.normalize("NFKD", t.lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def cifras(t: str) -> list[str]:
    return sorted(re.findall(r"\d+[.,]\d+|\d{2,}|\d+\s?%", t))


# ---------------------------------------------------------------- medida 1: oraciones
def _similitud(A: list[dict], B: list[dict]):
    docs = [" ".join(x["lemas"]) for x in A + B]
    if not any(docs):
        return None
    vec = TfidfVectorizer(analyzer=str.split).fit(docs)
    M = vec.transform(docs)
    return (M[:len(A)] @ M[len(A):].T).toarray()


def _iguales(a: dict, b: dict) -> bool:
    return a["lemas"] == b["lemas"] and cifras(a["texto"]) == cifras(b["texto"])


def alinear(A: list[dict], B: list[dict], tau_a: float = TAU_A, tau_s: float = TAU_S) -> list[tuple]:
    """Empareja las oraciones A (versión anterior) y B (nueva). Cada oración: {'texto': str, 'lemas': [str]}.
    Devuelve [(clase, oracion_A | None, oracion_B | None), ...]."""
    if not A:
        return [("anadida", None, b) for b in B]
    if not B:
        return [("eliminada", a, None) for a in A]
    S = _similitud(A, B)
    if S is None:
        return [("eliminada", a, None) for a in A] + [("anadida", None, b) for b in B]
    filas, cols = linear_sum_assignment(-S)
    usA, usB, pares = set(), set(), []
    for i, j in zip(filas, cols):
        if S[i, j] < tau_a and not _iguales(A[i], B[j]):
            continue
        usA.add(i); usB.add(j)
        if _iguales(A[i], B[j]):
            clase = "sin_cambio"
        elif S[i, j] >= tau_s and cifras(A[i]["texto"]) == cifras(B[j]["texto"]):
            clase = "superficial"
        else:
            clase = "sustantiva"
        pares.append((clase, A[i], B[j]))
    pares += [("eliminada", a, None) for i, a in enumerate(A) if i not in usA]
    pares += [("anadida", None, b) for j, b in enumerate(B) if j not in usB]
    return pares


def clase_dimension(conteo: Counter) -> str:
    if conteo["sustantiva"] or conteo["anadida"] or conteo["eliminada"]:
        return "sustantiva"
    if conteo["superficial"]:
        return "superficial"
    return "sin_cambio"


# ---------------------------------------------------------------- medida 2: palabras (difflib)
def palabras(texto: str) -> list[str]:
    """Palabras normalizadas sin números sueltos (en los PDF de las entregas suelen ser números de página)."""
    return [w for w in re.findall(r"[a-z0-9]+", normalizar(texto)) if not w.isdigit()]


def palabras_cambiadas(a: list[str], b: list[str]) -> int:
    """Palabras insertadas, borradas o reemplazadas entre a y b."""
    n = 0
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op != "equal":
            n += max(i2 - i1, j2 - j1)
    return n


def diff_lineas(texto_a: str, texto_b: str) -> str:
    """Diff legible, por oraciones, para mostrar en el notebook (formato unificado de git)."""
    return "\n".join(difflib.unified_diff(oraciones_simples(texto_a), oraciones_simples(texto_b),
                                          "version_anterior", "version_nueva", lineterm="", n=0))


# ---------------------------------------------------------------- textos sueltos (demo del notebook)
_PARADAS = set("""a al algo ante antes como con contra cual cuando de del desde donde dos el ella ellas ellos en entre
era es esa ese eso esta este esto estos estas fue han hay la las le les lo los mas mi muy no o otra otro para pero
por porque que quien se ser si sin sobre son su sus tambien tiene un una uno unos y ya""".split())


def oraciones_simples(texto: str) -> list[str]:
    return [o.strip() for o in re.split(r"(?<=[.!?;])\s+", texto.strip()) if o.strip()]


def preparar_texto(texto: str, lematizar=None) -> list[dict]:
    """Oraciones con «lemas» para alinear. Sin spaCy usa las palabras normalizadas de contenido; con
    lematizar=función(texto)->[lemas] (por ejemplo, spaCy es_core_news_md) reproduce el método del estudio."""
    out = []
    for o in oraciones_simples(texto):
        lem = lematizar(o) if lematizar else [w for w in re.findall(r"[a-zñ]+", normalizar(o)) if w not in _PARADAS]
        out.append(dict(texto=o, lemas=lem))
    return out


def comparar_textos(texto_a: str, texto_b: str, lematizar=None) -> dict:
    """Compara dos versiones de una sección con las dos medidas. Devuelve la clase de la dimensión, el
    detalle por oración y la proporción de palabras cambiadas."""
    A, B = preparar_texto(texto_a, lematizar), preparar_texto(texto_b, lematizar)
    pares = alinear(A, B)
    conteo = Counter(c for c, _, _ in pares)
    pa, pb = palabras(texto_a), palabras(texto_b)
    cambiadas = palabras_cambiadas(pa, pb)
    return dict(clase=clase_dimension(conteo), oraciones={k: conteo[k] for k in CLASES_ORACION},
                palabras_A=len(pa), palabras_B=len(pb), palabras_cambiadas=cambiadas,
                pct_palabras_cambiadas=100 * cambiadas / max(len(pa), len(pb)) if (pa or pb) else None,
                detalle=[(c, a["texto"] if a else None, b["texto"] if b else None) for c, a, b in pares])
