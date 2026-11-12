# OE5 y OE6: reproducción de resultados

Repositorio de la tesis **«Uso de multi-agentes y su efecto en la calidad metodológica en proyectos de tesis en
Ingeniería de la UPAO, 2026-2»**, solo para el quinto y el sexto objetivo específico. Contiene los datos
anonimizados, el código y un cuaderno de Google Colab que reproduce, **sin llamar a ninguna API**, todas las tablas
y pruebas de esos objetivos que aparecen en el informe, con el valor reportado al lado.

[![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/prttysav4ge/tesis-oe5-oe6/blob/main/notebooks/reproducir_oe5_oe6.ipynb)

## Qué se mide

| Objetivo | Pregunta | Prueba principal |
|---|---|---|
| **OE5** | ¿Mejora más en el Grupo Experimental (GE) que en el Grupo Control (GC) la calidad argumentativa (modelo de Toulmin) de la descripción del problema y de la justificación? | U de Mann-Whitney unilateral sobre el cambio del índice de elaboración, con corrección de Holm para las dos secciones |
| **OE6** | ¿Qué proporción de las **deficiencias detectadas** por el sistema evaluador en una entrega se **corrige** en la entrega siguiente, con cambio del texto, en cada grupo? | U de Mann-Whitney unilateral sobre la tasa de corrección acumulada por proyecto; sensibilidad y GEE binomial |

El estudio distingue tres hechos:

1. **Deficiencia detectada**: el evaluador califica «no cumple» un criterio de la rúbrica.
2. **Observación comunicada**: MentorIA le dio al estudiante una recomendación concreta.
3. **Corrección**: el criterio pasa a «cumple» en la entrega siguiente y el texto de su dimensión cambió.

**El OE6 mide 1 → 3 en ambos grupos.** El análisis 2 → 3, solo posible en el GE, está planteado en
`src/uso_mentoria.py` y en desarrollo, sin resultados.

Muestra analítica: 36 proyectos (P01–P36; 16 GC y 20 GE). Mediciones en las semanas 4, 5, 6, 7 y 9.

## Cómo ejecutarlo

**En Google Colab:**

1. Pulse el botón «Abrir en Colab». Si es la primera vez, autorice a Colab a leer repositorios privados de GitHub.
2. En Colab, abra el panel de **Secretos** (icono de la llave) y cree `GITHUB_TOKEN` con un token de GitHub de solo
   lectura para este repositorio. Si no lo crea, el cuaderno se lo pedirá al ejecutar, sin mostrarlo.
3. Use *Entorno de ejecución → Ejecutar todas* (tarda unos dos minutos).

**En una computadora, con Python 3.12 o 3.13:**

```
python -m venv .venv
.venv\Scripts\activate           (en Linux o macOS: source .venv/bin/activate)
pip install -r requirements.txt
jupyter notebook notebooks/reproducir_oe5_oe6.ipynb
```

## Qué reproduce cada sección del cuaderno

| Sección | Contenido | Apartados del informe |
|---|---|---|
| 1 | Clonado, instalación y cálculo de todas las tablas (también en `results/`) | — |
| 2 | **Auditoría**: cada cifra del OE5 y del OE6 del informe v15 frente al valor recalculado, con la explicación de cada diferencia | 5.6.7, 6.5, 6.6 |
| 3 | OE5: perfil de componentes, índice por semana, Wilcoxon, HE5, Spearman con la rúbrica, retest y figura | 6.5, Tablas 29 y 30 |
| 4 | OE6: corrección por intervalo, respaldo textual (diff), concordancia de las dos medidas del diff, HE6 con sensibilidad, variabilidad del evaluador y figuras | 6.6, Tablas 31 a 33 |
| 5 | Uso de MentorIA por semana y relación exploratoria con la corrección; plan del análisis recomendación → corrección | 6.6, limitaciones |
| 6 | **Opcional**: el diff sobre dos versiones de un texto ficticio (sin API) y el índice argumentativo 2.0 sobre ese texto (1 llamada a gpt-4.1; la clave se toma de los Secretos de Colab `OPENAI_API_KEY` o se pide con `getpass`) | 5.6.7, 5.6.8 |

## Estructura

```
notebooks/reproducir_oe5_oe6.ipynb   cuaderno principal
src/
  estadistica.py      Mann-Whitney y delta de Cliff, Holm, Wilcoxon, Spearman, CCI(2,1), GEE
  diff_versiones.py   comparación de versiones: clase de cambio por oraciones y palabras cambiadas (difflib)
  oe5.py              análisis del OE5
  oe6.py              análisis del OE6
  uso_mentoria.py     uso de MentorIA y vínculo recomendación → corrección (en desarrollo)
  auditoria.py        cifras del informe v15 frente a las recalculadas
  resultados.py       genera todas las tablas en results/
  figuras.py          figuras en results/figuras/
  toulmin_demo.py     índice argumentativo 2.0 sobre un texto de ejemplo (sección opcional)
  prompts/            prompt del índice argumentativo 2.0
data/                 datos anonimizados (diccionario abajo) y textos ficticios de ejemplo
results/              tablas (CSV) y figuras generadas
herramientas_locales/ scripts que generan data/ desde el material privado; NO corren en Colab
```

## Diccionario de datos

| Archivo | Una fila es | Columnas principales |
|---|---|---|
| `muestra.csv` | un proyecto | `proyecto` (P01–P36), `grupo` (GC/GE) |
| `oe6_items.csv` | un ítem de la rúbrica de una dimensión ya redactada, por proyecto e intervalo | `intervalo` (S4_S5…S7_S9), `nominal` (1 = mismo texto o sin entrega nueva), `dimension`, `item`, `puntaje_A` y `puntaje_B` (1 = cumple, en la entrega anterior y en la siguiente), `clase_cambio` del texto de la dimensión |
| `oe6_dimensiones.csv` | una dimensión por proyecto e intervalo | `clase_cambio`, número de oraciones `sin_cambio`, `superficial`, `sustantiva`, `anadida`, `eliminada`; `palabras_A`, `palabras_B`, `palabras_cambiadas` (difflib) |
| `oe5_secciones.csv` | una sección completa por proyecto y semana | `seccion` (S02 = descripción del problema, S05 = justificación), `afirmaciones`, `pres_<componente>`, `afirm_con_<componente>`, `indice_estructural`, `indice_elaboracion`, `nivel`, vínculos, `indice_v11`, `calidad_dim` (calidad de la dimensión en la rúbrica, %) |
| `oe5_retest.csv` | una sección de S4 analizada dos veces | funciones y vínculos coincidentes; índices de la primera y la segunda corrida |
| `uso_mentoria_semana.csv` | un proyecto del GE por semana de uso | consultas, revisiones, días y minutos con consultas, sesiones sin mensajes |
| `plantilla_recomendaciones_mentoria.csv` | (vacía) formato del análisis en desarrollo | — |

## Procedencia y versiones

- Calificaciones de la rúbrica (100 ítems, 15 dimensiones): sistema evaluador multiagente
  [Mclever2/Evaluador-Tesis](https://github.com/Mclever2/Evaluador-Tesis), commit
  [`c2b0f28`](https://github.com/Mclever2/Evaluador-Tesis/commit/c2b0f284c611a8553fa5884cd0d6ce54cf86084b)
  (segmentador corregido). El mismo extractor, anonimizador y segmentador se usaron para dividir el texto del OE5 y
  del OE6.
- Intervención: [Mclever2/MentorIA-Tesis](https://github.com/Mclever2/MentorIA-Tesis); commit vigente al
  12/11/2026:
  [`cbdfcee`](https://github.com/Mclever2/MentorIA-Tesis/commit/cbdfceef077f8ebc9797c534da65420fde43c295).
- Índice argumentativo 2.0: gpt-4.1, temperatura 0, semilla 42; prompt en `src/prompts/`.
- Los datos de `data/` se generan con `herramientas_locales/preparar_datos.py` a partir del material privado del
  estudio. Ese script verifica que la tabla de ítems del OE6 coincida con la usada en el informe.

## Privacidad

`data/` no contiene nombres, correos, textos de los proyectos ni los códigos originales de los proyectos. Los
identificadores P01–P36 se asignaron al azar, y su correspondencia con los originales se guarda fuera de este
repositorio. El `.gitignore` bloquea archivos `*PRIVADO*`, `.env`, documentos (`.docx`, `.pdf`) y carpetas de
entregas. Los textos de `data/ejemplo_ficticio/` son inventados.
