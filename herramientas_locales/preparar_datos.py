"""Genera data/ (anonimizado) a partir del material privado del estudio. NO se ejecuta en Colab.

Requiere, en la carpeta raíz del estudio (--raiz, por defecto la carpeta que contiene este repositorio):
  RESULTADOS-TESIS/   calificaciones del sistema evaluador (S<N>_items_long.csv, registro_entregas.csv,
                      longitudinal/datos_crudos.csv) y registros de uso de MentorIA (uso_mentoria/)
  oe56/               división del texto (salidas/division), respuestas del modelo del índice 2.0
                      (salidas/toulmin_v2, salidas/toulmin_v2_retest) y su código (division.py, fase2.py,
                      fase3.py, toulmin_v2.py); su entorno virtual tiene spaCy y el backend del evaluador.
Uso (con el Python de oe56):  oe56\\.venv\\Scripts\\python.exe herramientas_locales\\preparar_datos.py

Nunca llama a la API: si falta la respuesta guardada de una sección, se detiene.
Salida (sin textos, nombres, correos ni identificadores originales):
  data/muestra.csv               proyecto (P01-P36) y grupo
  data/oe6_items.csv             un ítem de la rúbrica por proyecto e intervalo, en las dimensiones redactadas
  data/oe6_dimensiones.csv       una dimensión por proyecto e intervalo: clase de cambio del texto y palabras
  data/oe5_secciones.csv         una sección (descripción del problema o justificación) por proyecto y semana
  data/oe5_retest.csv            S4: índices de la primera y la segunda corrida sobre el mismo texto
  data/uso_mentoria_semana.csv   consultas y minutos por proyecto del GE y semana de uso
La correspondencia entre los identificadores originales y P01-P36 se guarda FUERA del repositorio
(oe56/privado/mapeo_ids_PRIVADO.csv).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from src.diff_versiones import alinear, clase_dimension, palabras, palabras_cambiadas  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--raiz", default=str(REPO.parent))
ap.add_argument("--semanas-oe5", default="S4,S5,S6,S7,S9")
ARGS = ap.parse_args()
RAIZ = Path(ARGS.raiz)
RT = RAIZ / "RESULTADOS-TESIS"
OE56 = RAIZ / "oe56"
DATA = REPO / "data"
SEMANAS = ["S4", "S5", "S6", "S7", "S9"]

sys.path.insert(0, str(OE56))
os.chdir(OE56)
import fase2  # noqa: E402  (oraciones_dim: oraciones de la división, con las cláusulas reunidas)
import fase3  # noqa: E402  (v11: índice 1.1 guardado por el evaluador)
import toulmin_v2 as tv  # noqa: E402


def leer(ruta: Path) -> list[dict]:
    return list(csv.DictReader(open(ruta, encoding="utf-8-sig")))


def escribir(nombre: str, filas: list[dict]) -> None:
    DATA.mkdir(exist_ok=True)
    with open(DATA / nombre, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    print(f"  data/{nombre}: {len(filas)} filas")


# ---------------------------------------------------------------- muestra y anonimización
crudos = leer(RT / "longitudinal" / "datos_crudos.csv")
muestra = sorted(r["proyecto_id"] for r in crudos if r["semana"] == "S4" and r["entrega"] == "evaluada")
assert len(muestra) == 36, len(muestra)
orden = muestra[:]
random.Random(20262).shuffle(orden)  # el número P no revela el código original
ANON = {pid: f"P{i + 1:02d}" for i, pid in enumerate(orden)}
GRUPO = {pid: "GE" if pid.startswith("E") else "GC" for pid in muestra}
priv = OE56 / "privado"
priv.mkdir(exist_ok=True)
with open(priv / "mapeo_ids_PRIVADO.csv", "w", newline="", encoding="utf-8") as fh:
    csv.writer(fh).writerows([("id_original", "id_anonimo")] + sorted(ANON.items()))
print("Muestra: 36 proyectos (16 GC, 20 GE); mapeo guardado fuera del repositorio.")
escribir("muestra.csv", [dict(proyecto=ANON[p], grupo=GRUPO[p]) for p in sorted(muestra, key=ANON.get)])

redactadas = {(r["semana"], r["proyecto_id"]): {int(x) for x in r["dims_redactadas"].split(",") if x} for r in crudos}
decision = {(r["semana"], r["proyecto_id"]): r["decision"] for r in leer(RT / "registro_entregas.csv")}


def items(semana: str) -> dict:
    d = defaultdict(dict)
    for r in leer(RT / semana / f"{semana}_items_long.csv"):
        d[r["proyecto_id"]][r["item_id"]] = (int(r["dimension"]), int(r["puntaje_sistema"]))
    return d


def division(semana: str, pid: str) -> dict:
    f = OE56 / "salidas" / "division" / semana / f"{pid}.json"
    if not f.exists():
        return {}
    return {int(k[1:]): v for k, v in json.loads(f.read_text(encoding="utf-8"))["dimensiones"].items()}


def texto_dim(dim: dict) -> str:
    return " ".join(u["texto"] for p in dim["parrafos"] for u in p["unidades"] if not u["ruido"])


# ---------------------------------------------------------------- OE6
print("OE6: ítems y cambio del texto por dimensión")
it = {s: items(s) for s in SEMANAS}
f_items, f_dims = [], []
for SA, SB in zip(SEMANAS, SEMANAS[1:]):
    tag = f"{SA}_{SB}"
    for pid in muestra:
        dims = redactadas.get((SA, pid), set())
        dec = decision.get((SB, pid), "")
        nominal = dec in ("sin_cambios", "sin_avance")
        # Versión anterior = la última entrega CALIFICADA: si SA fue «sin avance», su nota es la de la semana
        # previa y el texto que la produjo es el de esa semana, no el PDF descargado en SA.
        sa = SA
        while decision.get((sa, pid)) == "sin_avance":
            sa = SEMANAS[SEMANAS.index(sa) - 1]
        A = division(sa, pid)
        B = A if dec == "sin_avance" else division(SB, pid)  # sin avance: no hay entrega nueva
        clase = {}
        for d in sorted(dims):
            if nominal:
                conteo, cl = Counter(sin_cambio=1), "sin_cambio"
            elif d not in A or d not in B:
                conteo, cl = Counter(), "sin_datos"
            else:
                conteo = Counter(c for c, _, _ in alinear(fase2.oraciones_dim(A[d]), fase2.oraciones_dim(B[d])))
                cl = clase_dimension(conteo)
            pa = palabras(texto_dim(A[d])) if d in A else []
            pb = palabras(texto_dim(B[d])) if d in B else []
            clase[d] = cl
            f_dims.append(dict(intervalo=tag, proyecto=ANON[pid], grupo=GRUPO[pid], nominal=int(nominal),
                               tipo_entrega=dec, dimension=d, clase_cambio=cl,
                               **{f"oraciones_{k}": conteo[k] for k in ("sin_cambio", "superficial", "sustantiva",
                                                                       "anadida", "eliminada")},
                               palabras_A=len(pa), palabras_B=len(pb),
                               palabras_cambiadas=0 if nominal else palabras_cambiadas(pa, pb)))
        for item, (d, pA) in sorted(it[SA][pid].items()):
            if d not in dims:
                continue
            pB = it[SB][pid][item][1]
            f_items.append(dict(intervalo=tag, proyecto=ANON[pid], grupo=GRUPO[pid], nominal=int(nominal),
                                dimension=d, item=item, puntaje_A=pA, puntaje_B=pB, clase_cambio=clase[d]))
escribir("oe6_items.csv", f_items)
escribir("oe6_dimensiones.csv", f_dims)

# verificación contra las salidas con que se redactó el v15 (fase5_levantamiento.py)
viejo = Counter()
for SA, SB in zip(SEMANAS, SEMANAS[1:]):
    for r in leer(OE56 / "fase5" / f"observaciones_{SA}_{SB}.csv"):
        viejo[(r["intervalo"], ANON[r["proyecto"]], r["item"], r["puntaje_A"], r["puntaje_B"], r["cambio_texto"])] += 1
nuevo = Counter((f["intervalo"], f["proyecto"], f["item"], str(f["puntaje_A"]), str(f["puntaje_B"]), f["clase_cambio"])
                for f in f_items)
print(f"  coincidencia con fase5 (ítem, puntajes y clase de cambio): {sum((viejo & nuevo).values())} de "
      f"{sum(viejo.values())} filas de fase5 y {sum(nuevo.values())} nuevas")

# ---------------------------------------------------------------- OE5
print("OE5: índice argumentativo 2.0 desde las respuestas guardadas del modelo")
DIM_RUBRICA = {"S02": 2, "S05": 5}


def respuesta_guardada(carpeta: Path, semana: str, pid: str, sid: str, dim: dict) -> dict | None:
    f = carpeta / semana / f"{pid}_{sid}.json"
    if not f.exists():
        return None
    d = json.loads(f.read_text(encoding="utf-8"))
    h = hashlib.sha256(tv.prompt_de(sid, dim).encode("utf-8")).hexdigest()
    if d.get("prompt_sha256") != h:
        sys.exit(f"La respuesta guardada de {semana} {pid} {sid} no corresponde al texto actual: revisar.")
    return d


def calidad_dim(semana: str) -> dict:
    d = defaultdict(lambda: defaultdict(list))
    for pid, its in it[semana].items():
        for _, (dim, p) in its.items():
            d[pid][dim].append(p)
    return {p: {k: 100 * st.mean(v) for k, v in dd.items()} for p, dd in d.items()}


f_sec, faltan = [], []
for s in ARGS.semanas_oe5.split(","):
    q = calidad_dim(s)
    for pid in muestra:
        for sid, dim in fase3.secciones_elegibles(s, pid).items():
            d = respuesta_guardada(OE56 / "salidas" / "toulmin_v2", s, pid, sid, dim)
            if d is None:
                faltan.append((s, pid, sid))
                continue
            us = tv.unidades_de(dim)
            ver = tv.verificar(d["respuesta"], us)
            pun = tv.puntuar(ver, len(us))
            v = fase3.v11(s, pid, sid)
            f_sec.append(dict(
                semana=s, proyecto=ANON[pid], grupo=GRUPO[pid], seccion=sid, unidades=pun["n_unidades"],
                parrafos=len(dim["parrafos"]), afirmaciones=pun["n_afirmaciones"],
                **{f"pres_{c}": int(c in pun["presentes"]) for c in tv.COMPONENTES},
                **{f"afirm_con_{k}": x for k, x in pun["perfil_afirmaciones"].items()},
                indice_estructural=round(100 * pun["indice_estructural"], 1),
                indice_elaboracion=round(100 * pun["indice_elaboracion"], 1), nivel=pun["nivel"],
                vinculos_total=pun["vinculos_total"], vinculos_entre_parrafos=pun["vinculos_entre_parrafos"],
                vinculos_con_lema=pun["vinculos_con_lema_compartido"], descartes=sum(ver["descartes"].values()),
                indice_v11=round(100 * v["indice_estructural"], 1) if v else None,
                calidad_dim=round(q[pid][DIM_RUBRICA[sid]], 1) if pid in q and DIM_RUBRICA[sid] in q[pid] else None,
                reutilizada=int(bool(d.get("reutilizada_de")))))
if faltan:
    print(f"  AVISO: {len(faltan)} secciones sin respuesta guardada (no se llama a la API): "
          f"{sorted({s for s, _, _ in faltan})}")
escribir("oe5_secciones.csv", f_sec)

f_rt = []
for pid in muestra:
    for sid, dim in fase3.secciones_elegibles("S4", pid).items():
        d1 = respuesta_guardada(OE56 / "salidas" / "toulmin_v2", "S4", pid, sid, dim)
        d2 = respuesta_guardada(OE56 / "salidas" / "toulmin_v2_retest", "S4", pid, sid, dim)
        us = tv.unidades_de(dim)
        v1, v2 = tv.verificar(d1["respuesta"], us), tv.verificar(d2["respuesta"], us)
        p1, p2 = tv.puntuar(v1, len(us)), tv.puntuar(v2, len(us))
        e1, e2 = fase3.etiquetas_unidad(v1), fase3.etiquetas_unidad(v2)
        l1, l2 = fase3.vinculos(v1), fase3.vinculos(v2)
        f_rt.append(dict(proyecto=ANON[pid], grupo=GRUPO[pid], seccion=sid, unidades=len(us),
                         unidades_misma_funcion=sum(e1.get(u["id"], set()) == e2.get(u["id"], set()) for u in us),
                         vinculos_comunes=len(l1 & l2), vinculos_union=len(l1 | l2),
                         mismas_afirmaciones=int({a["afirmacion"] for a in v1["argumentos"]}
                                                 == {a["afirmacion"] for a in v2["argumentos"]}),
                         elaboracion_1=p1["indice_elaboracion"], elaboracion_2=p2["indice_elaboracion"],
                         estructural_1=p1["indice_estructural"], estructural_2=p2["indice_estructural"]))
escribir("oe5_retest.csv", f_rt)

# ---------------------------------------------------------------- uso de MentorIA (solo GE, agregados)
print("Uso de MentorIA")
CAMPOS = ["consultas", "consultas_rapidas", "mejoras_rapidas", "revisiones_secciones", "revisiones_completas",
          "dias_con_consultas", "sesiones_con_consultas", "sesiones_sin_mensajes", "minutos_sesiones_con_consultas",
          "minutos_sesiones_sin_mensajes"]
uso = []
for r in leer(RT / "uso_mentoria" / "uso_por_proyecto_semana.csv"):
    if r["proyecto_id"] in ANON:
        uso.append(dict(proyecto=ANON[r["proyecto_id"]], semana_de_uso=r["semana_de_uso"], n_autores=r["n_autores"],
                        **{c: r[c] for c in CAMPOS}))
escribir("uso_mentoria_semana.csv", sorted(uso, key=lambda x: (x["semana_de_uso"], x["proyecto"])))
print("Listo.")
