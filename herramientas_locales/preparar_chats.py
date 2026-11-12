"""Genera data/mentoria_observaciones.csv (anonimizado) a partir de los registros de MentorIA. NO corre en Colab.

Entrada privada: chats_mentorIA/observaciones.csv (criterios que MentorIA calificó en cada revisión del proyecto,
con correo y texto de la observación) y RESULTADOS-TESIS/uso_mentoria/mapeo_cuentas_mentoria_PRIVADO.csv (cuenta
-> proyecto). Salida: sin correos, sin identificadores de cuenta ni de conversación y sin el texto de la observación.

Reglas:
  - Observación comunicada (b): criterio calificado por MentorIA por debajo de su puntaje máximo en una revisión
    que el estudiante solicitó (revisión completa o de secciones).
  - Solo cuentas vinculadas a un proyecto del GE. Se excluye la cuenta de un investigador (sin proyecto), que revisó
    los 20 proyectos en una sola sesión (24-25/09): esas observaciones no se comunicaron a los estudiantes.
  - Vínculo temporal: la observación se asocia a la primera entrega posterior a su fecha (cortes: domingo 23:59 de
    las semanas 4, 5, 6, 7 y 9) y al intervalo que termina en ella; las anteriores al corte de la semana 4 se
    asocian al intervalo S4-S5 (marcadas en «antes_de_S4»); las posteriores a la semana 9 se descartan.
"""
import csv
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
RAIZ = REPO.parent
sys.path.insert(0, str(REPO))
from src.uso_mentoria import MAPA_ITEMS  # noqa: E402

ob = pd.read_csv(RAIZ / "chats_mentorIA" / "observaciones.csv")
cuentas = pd.read_csv(RAIZ / "RESULTADOS-TESIS" / "uso_mentoria" / "mapeo_cuentas_mentoria_PRIVADO.csv",
                      encoding="utf-8-sig")
anon = {r["id_original"]: r["id_anonimo"]
        for r in csv.DictReader(open(RAIZ / "oe56" / "privado" / "mapeo_ids_PRIVADO.csv", encoding="utf-8"))}
proyecto = dict(zip(cuentas.email.str.lower().str.strip(), cuentas.proyecto_id))
ob["pid"] = ob.email.str.lower().str.strip().map(proyecto)
excluidas = ob[ob.pid.isna()]
print(f"Filas: {len(ob)}; sin proyecto (excluidas): {len(excluidas)} de {excluidas.user_id.nunique()} cuenta(s)")
ob = ob[ob.pid.notna() & ob.pid.isin(anon)].copy()

cortes = pd.to_datetime(["2026-09-27 23:59:59", "2026-10-04 23:59:59", "2026-10-11 23:59:59",
                         "2026-10-18 23:59:59", "2026-11-01 23:59:59"])
t = pd.to_datetime(ob.fecha_hora_lima)
ob["tramo"] = pd.cut(t, [pd.Timestamp("2026-01-01")] + list(cortes) + [pd.Timestamp("2027-01-01")],
                     labels=["antes_de_S4", "S4_S5", "S5_S6", "S6_S7", "S7_S9", "despues_de_S9"]).astype(str)
ob = ob[ob.tramo != "despues_de_S9"]
ob["intervalo"] = ob.tramo.replace({"antes_de_S4": "S4_S5"})
revision = {m: f"R{i + 1:03d}" for i, m in enumerate(sorted(ob.mensaje_id.unique()))}
out = pd.DataFrame(dict(
    proyecto=ob.pid.map(anon), intervalo=ob.intervalo, antes_de_S4=(ob.tramo == "antes_de_S4").astype(int),
    revision=ob.mensaje_id.map(revision), fuente=ob.fuente, item_mentoria=ob["item"],
    dimension=ob["item"].map(MAPA_ITEMS).astype("Int64"), estado=ob.estado.fillna("revision_secciones"),
    puntaje=ob.puntaje, maximo=ob.maximo,
    comunicada=(ob.puntaje < ob.maximo).astype(int)))
out = out.sort_values(["intervalo", "proyecto", "revision", "item_mentoria"])
out.to_csv(REPO / "data" / "mentoria_observaciones.csv", index=False, encoding="utf-8")
print(f"data/mentoria_observaciones.csv: {len(out)} filas; {out.proyecto.nunique()} proyectos; "
      f"{out.comunicada.sum()} observaciones comunicadas")
