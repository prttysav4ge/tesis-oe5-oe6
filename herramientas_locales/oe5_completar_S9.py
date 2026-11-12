"""Completa el índice argumentativo 2.0 (OE5) en la medición de la semana 9. Usa la API de OpenAI. NO se
ejecuta en Colab.

Mismo procedimiento que S4-S7 (oe56/fase3.py y oe56/toulmin_v2.py, sin cambios): gpt-4.1, temperatura 0,
semilla 42, el mismo prompt; las secciones con el mismo texto que una entrega anterior reutilizan su respuesta
(caché por huella del prompt) y no se pagan. La clave se lee de oe56/.env (nunca del código).

Uso (con el Python de oe56):
  oe56\\.venv\\Scripts\\python.exe herramientas_locales\\oe5_completar_S9.py              cuenta, sin llamar
  oe56\\.venv\\Scripts\\python.exe herramientas_locales\\oe5_completar_S9.py --confirmar 47  llama si son <= 47
"""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "oe56"))
os.chdir(RAIZ / "oe56")
import fase3  # noqa: E402
import toulmin_v2 as tv  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--confirmar", type=int, default=None, help="máximo de llamadas autorizadas")
a = ap.parse_args()

fase3.indexar_respuestas()
pendientes, reutilizables = [], 0
for pid in fase3.entregas("S9"):
    for sid, dim in fase3.secciones_elegibles("S9", pid).items():
        h = hashlib.sha256(tv.prompt_de(sid, dim).encode("utf-8")).hexdigest()
        if (fase3.RESP / "S9" / f"{pid}_{sid}.json").exists() or h in fase3._por_hash:
            reutilizables += 1
        else:
            pendientes.append((pid, sid, dim))
print(f"S9: {reutilizables + len(pendientes)} secciones elegibles; {reutilizables} reutilizan una respuesta guardada; "
      f"{len(pendientes)} requieren llamada a la API.")
if a.confirmar is None:
    sys.exit("Sin --confirmar: no se llamó a la API.")
if len(pendientes) > a.confirmar:
    sys.exit(f"Se requieren {len(pendientes)} llamadas, más que las {a.confirmar} autorizadas: no se llamó a la API.")

costo, hechas = 0.0, 0
for pid in fase3.entregas("S9"):
    for sid, dim in fase3.secciones_elegibles("S9", pid).items():
        d, ver, pun = fase3.resultado("S9", pid, sid, dim)
        if not d.get("reutilizada_de") and d.get("costo_usd"):
            hechas += 1
            costo += d["costo_usd"]
print(f"Listo: {hechas} llamadas nuevas, US$ {costo:.4f}.")
(Path(__file__).resolve().parents[1] / "herramientas_locales" / "costo_oe5_S9.json").write_text(
    json.dumps(dict(llamadas=hechas, costo_usd=round(costo, 4), modelo="gpt-4.1", temperatura=0, semilla=42)),
    encoding="utf-8")
