"""Construye notebooks/reproducir_oe5_oe6.ipynb (python herramientas_locales/construir_notebook.py)."""
from pathlib import Path

import nbformat as nbf

REPO = Path(__file__).resolve().parents[1]
REPO_GITHUB = "prttysav4ge/tesis-oe5-oe6"  # se reemplaza al crear el repositorio (ver README)

nb = nbf.v4.new_notebook()
C = []


def md(t):
    C.append(nbf.v4.new_markdown_cell(t.strip()))


def code(t):
    C.append(nbf.v4.new_code_cell(t.strip()))


md(f"""
# OE5 y OE6: reproducción de los resultados

Tesis «Uso de multi-agentes y su efecto en la calidad metodológica en proyectos de tesis en Ingeniería de la UPAO,
2026-2». Este cuaderno reproduce, **sin llamar a ninguna API**, todas las tablas y pruebas del quinto y del sexto
objetivo específico a partir de los datos anonimizados de `data/`, y muestra al lado el valor reportado en el
informe.

| Objetivo | Qué mide | Datos |
|---|---|---|
| OE5 | Calidad argumentativa (modelo de Toulmin) de la descripción del problema y de la justificación | `data/oe5_secciones.csv`, `data/oe5_retest.csv` |
| OE6 | Proporción de **deficiencias detectadas** por el evaluador en una entrega que se **corrigen** en la siguiente, con respaldo del cambio de texto (diff), GC frente a GE | `data/oe6_items.csv`, `data/oe6_dimensiones.csv` |
| Complemento | Uso de MentorIA en el GE por semana | `data/uso_mentoria_semana.csv` |

**Tres hechos que el estudio distingue:** (a) *deficiencia detectada*: el evaluador califica «no cumple» un criterio;
(b) *observación comunicada*: MentorIA le dio al estudiante una recomendación concreta; (c) *corrección*: el criterio
pasa a «cumple» en la entrega siguiente. **El OE6 mide (a) → (c)**, no (b).

Proyectos: P01–P36 (16 GC y 20 GE), identificadores anónimos. Mediciones: semanas 4, 5, 6, 7 y 9.
Ejecutar con *Entorno de ejecución → Ejecutar todas*. La última sección es opcional y es la única que usa la API.
""")

md("## 1. Preparación")
code(f"""
import os, sys, subprocess
REPO_GITHUB = "{REPO_GITHUB}"
EN_COLAB = "google.colab" in sys.modules
if EN_COLAB and not os.path.exists("tesis-oe5-oe6"):
    # Repositorio privado: un token de GitHub de solo lectura, guardado en los Secretos de Colab
    # (icono de la llave, nombre GITHUB_TOKEN) o escrito al ejecutar. Nunca se escribe en el código.
    try:
        from google.colab import userdata
        token = userdata.get("GITHUB_TOKEN")
    except Exception:
        from getpass import getpass
        token = getpass("Token de GitHub (solo lectura): ")
    subprocess.run(["git", "clone", "-q", f"https://{{token}}@github.com/{{REPO_GITHUB}}.git", "tesis-oe5-oe6"], check=True)
    del token
if os.path.exists("tesis-oe5-oe6"):
    os.chdir("tesis-oe5-oe6")
elif os.path.basename(os.getcwd()) == "notebooks":
    os.chdir("..")
if EN_COLAB:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"], check=True)
sys.path.insert(0, os.getcwd())
print("Carpeta de trabajo:", os.path.basename(os.getcwd()))
""")
code("""
import pandas as pd
from IPython.display import Image, Markdown, display
from src import auditoria, figuras, oe5, oe6, resultados, uso_mentoria
pd.set_option("display.max_colwidth", 120); pd.set_option("display.width", 200); pd.set_option("display.max_rows", 200)
T = resultados.generar_todo()   # todas las tablas quedan también en results/ (CSV) y las figuras en results/figuras/
pd.read_csv("data/muestra.csv").grupo.value_counts()
""")

md("""
## 2. Auditoría: cada cifra del informe v15 frente al valor recalculado

`valor_informe` es la cifra escrita en el Informe de Tesis v15; `valor_recalculado` sale de `data/` con el código de
`src/`. Las diferencias tienen su explicación en la última columna.
""")
code("""
a = T["auditoria_v15"]
print(f"{len(a)} cifras auditadas: {a.coincide.sum()} coinciden; {(~a.coincide).sum()} difieren (todas explicadas).")
display(a[~a.coincide])
""")
code("display(a)  # tabla completa")

md("""
## 3. OE5: calidad argumentativa (índice argumentativo 2.0)

El índice se calculó con el prompt `src/prompts/argumentacion_toulmin_v2.md` (gpt-4.1, temperatura 0, semilla 42).
Las respuestas del modelo se verificaron con reglas fijas y aquí se usan los indicadores resultantes; el cuaderno no
vuelve a llamar al modelo (la sección 6 muestra una llamada sobre un texto de ejemplo).

**HE5**: U de Mann-Whitney unilateral (GE > GC) del cambio del índice de elaboración entre la primera y la última
medición con la sección completa, con corrección de Holm para las dos secciones.
""")
code("""
print("Tabla 29 del informe: perfil de componentes, S4 y S7")
display(T["oe5_tabla29_S4_S7"])
print("Tabla 30 del informe: índice de elaboración y pruebas")
display(T["oe5_tabla30_S4_S7"])
print("Prueba de la HE5 (informe: DP p Holm = .551; JU p = .013, p Holm = .027, δ = .44; se acepta de forma parcial)")
display(T["oe5_he5_S4_S7"])
""")
code("""
print("Validez convergente: Spearman entre el índice de elaboración y la calidad de la dimensión en la rúbrica")
display(T["oe5_spearman_S4_S7"].round(3))
print("Estabilidad test-retest en S4 (informe: 80.6 % funciones iguales, 65.4 % vínculos, CCI = .77 y .77)")
display(T["oe5_retest"].round(3))
display(Image("results/figuras/oe5_elaboracion_por_semana.png"))
""")
code("""
if "oe5_he5_S4_S9" in T:
    print("OE5 con la semana 9 (informe v16)")
    display(T["oe5_tabla30_S4_S9"]); display(T["oe5_he5_S4_S9"])
else:
    print("La semana 9 del OE5 aún no está en data/oe5_secciones.csv.")
""")

md("""
## 4. OE6: corrección de las deficiencias detectadas entre entregas consecutivas

- **Deficiencia detectada**: ítem «no cumple» en la entrega *t*, en una dimensión ya redactada en *t*.
- **Corrección**: el ítem pasa a «cumple» en *t+1*. **Retroceso**: un ítem «cumple» pasa a «no cumple».
- **Respaldo textual (diff)**: cada dimensión se compara con su versión anterior (`src/diff_versiones.py`):
  oraciones emparejadas por similitud TF-IDF de lemas con el método húngaro; umbrales τ = .35 y .75 →
  *sin cambio*, *superficial* o *sustantiva*. Una corrección **sin cambio de texto** refleja la variabilidad del
  evaluador sobre el mismo texto.
- **Entrega nominal**: mismo texto que la semana anterior (o sin entrega nueva); conserva la calificación.

En el informe v15 se llama «observación» a la deficiencia detectada y «tasa de levantamiento» (TL) a la tasa de
corrección (TC).
""")
code("""
print("Tabla 31 del informe (por intervalo y grupo)")
display(T["oe6_tabla31"].round(1))
print("Contraste por intervalo, Holm (informe: 1.000, < .001, 1.000, 1.000)")
display(T["oe6_por_intervalo"].round(4))
display(Image("results/figuras/oe6_correccion_por_intervalo.png"))
""")
code("""
print("Tabla 32 del informe: corrección según el cambio del texto (entregas reevaluadas)")
display(T["oe6_tabla32"].round(1))
print("Concordancia de las dos medidas del diff: palabras cambiadas por cada 100 (difflib) según la clase por oraciones")
display(T["oe6_concordancia_diff"].round(1))
display(Image("results/figuras/oe6_correccion_por_clase_de_cambio.png"))
""")
code("""
print("Contraste de la HE6 y sensibilidad.")
print("Informe v15 (fila 'Todas las correcciones'): Md 20.9 frente a 32.3; U = 249.5; p = .002; δ = +0.56")
display(T["oe6_he6_v16"].round(3))
print("Variabilidad del evaluador: correcciones sin cambio de texto, por grupo")
display(T["oe6_variabilidad"].round(1))
print("Retroceso acumulado (bilateral; informe: p = .886)")
display(T["oe6_TR"].round(3))
""")

md("""
## 5. Uso de MentorIA en el Grupo Experimental

Registros automáticos del sistema (conteos; no incluyen el texto de las conversaciones). La semana S9 reúne el uso
de las semanas 8 y 9.
""")
code("""
display(T["uso_por_semana"])
display(Image("results/figuras/uso_mentoria_por_semana.png"))
print("Exploratorio (solo GE, proyecto x intervalo): tasa de corrección con cambio de texto según hubo consultas")
display(T["uso_y_correccion"].round(1)); print(T["uso_y_correccion_spearman"])
print(uso_mentoria.plan_vinculo_recomendaciones())
""")

md("""
## 6. (Opcional) Ver el procedimiento en acción sobre un texto de ejemplo

Los textos de `data/ejemplo_ficticio/` son **ficticios**: no pertenecen a ningún proyecto del estudio.

**6.1 Diff entre dos versiones (sin API).**
""")
code("""
from src.diff_versiones import comparar_textos, diff_lineas
leer = lambda f: open(f, encoding="utf-8").read().split("\\n", 2)[2]
v1 = leer("data/ejemplo_ficticio/descripcion_problema_v1.txt")
v2 = leer("data/ejemplo_ficticio/descripcion_problema_v2.txt")
r = comparar_textos(v1, v2)
print("Clase de cambio de la dimensión:", r["clase"], "| oraciones:", r["oraciones"],
      f"| palabras cambiadas por cada 100: {r['pct_palabras_cambiadas']:.1f}")
display(pd.DataFrame(r["detalle"], columns=["clase", "versión anterior", "versión nueva"]))
print(diff_lineas(v1, v2))
""")
md("""
**6.2 Índice argumentativo 2.0 sobre la versión nueva (usa la API de OpenAI: 1 llamada a gpt-4.1, del orden de
US$ 0.01).** Cambie `EJECUTAR = True` para correrla. La clave se lee de los Secretos de Colab (`OPENAI_API_KEY`) o
se pide al ejecutar; nunca se escribe en el código.
""")
code("""
EJECUTAR = False
if EJECUTAR:
    from src import toulmin_demo as td
    try:
        from google.colab import userdata
        clave = userdata.get("OPENAI_API_KEY")
    except Exception:
        from getpass import getpass
        clave = getpass("Clave de la API de OpenAI: ")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "openai==3.35.1", "pydantic==2.14.1"], check=True)
    unidades = td.dividir(v2)
    print(td.prompt_de("S02", unidades)[-1500:])
    respuesta = td.llamar(td.prompt_de("S02", unidades), clave)   # <- única llamada a la API
    del clave
    ver = td.verificar(respuesta, unidades)
    print("Puntaje:", td.puntuar(ver), "| descartes de la verificación:", ver["descartes"])
    texto = {u["id"]: u["texto"] for u in unidades}
    for a in ver["argumentos"]:
        print("\\nAFIRMACIÓN", a["afirmacion"], texto[a["afirmacion"]])
        for d in a["datos"]: print("   dato     ", d, texto[d][:90])
        for g in a["garantias"]: print("   garantía ", g["unidad"], texto[g["unidad"]][:90], "(conecta", g["dato"], ")")
        for x in a["respaldos"]: print("   respaldo ", x["unidad"], texto[x["unidad"]][:90])
        for x in a["refutaciones"]: print("   refutación", x["unidad"], texto[x["unidad"]][:90], "(responde en", x["responde_en"], ")")
else:
    print("Sección opcional no ejecutada (EJECUTAR = False).")
""")

nb["cells"] = C
nb["metadata"] = {"kernelspec": {"name": "python3", "display_name": "Python 3"}, "language_info": {"name": "python"},
                  "colab": {"provenance": []}}
destino = REPO / "notebooks" / "reproducir_oe5_oe6.ipynb"
destino.parent.mkdir(exist_ok=True)
nbf.write(nb, destino)
print(destino)
