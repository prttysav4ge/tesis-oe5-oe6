# Tarea

Analizas la sección "{seccion}" de un proyecto de tesis de pregrado con el modelo de argumentación de Toulmin, como en la minería de argumentos: identificas los componentes y las relaciones entre ellos. El texto está dividido en párrafos ([P1], [P2]...) y cada párrafo en unidades numeradas ([P2-U3]: unidad 3 del párrafo 2). Una unidad es una oración o, cuando un conector lo justifica, una parte de una oración. No calificas la calidad ni opinas: solo indicas qué unidad cumple qué función y respecto de qué afirmación.

Trabaja en dos pasos y devuelve el resultado de ambos en la misma respuesta.

**Paso A. Afirmaciones.** Identifica las afirmaciones del AUTOR DEL PROYECTO, es decir, las posturas que la sección busca sostener ante un lector que podría cuestionarlas:
- La **afirmación central** (marca "central": true): lo que la sección quiere demostrar en conjunto; en la descripción del problema, que el problema existe y es relevante; en la justificación, que el estudio es necesario o valioso. Suele haber una, a veces dos.
- Las **afirmaciones intermedias** del autor que sostienen a la central: que algo es grave, deficiente o insuficiente; que hay una carencia o una brecha; que el estudio aporta algo concreto. Normalmente son pocas.
- Toda unidad del autor que señala un vacío o una carencia con sus propias palabras es afirmación, aunque se exprese como un hecho: "no existe una caracterización formal de...", "ningún estudio aborda...".
- Una unidad que informa un hecho, una cifra o un hallazgo y lo atribuye a una fuente (con cita o mencionando al autor) es un DATO, aunque describa una carencia: no la registres como afirmación.
- No conviertas en afirmación cada unidad: rótulos, transiciones, definiciones, preguntas de investigación, objetivos y descripciones de la propuesta o del procedimiento no son afirmaciones.

**Paso B. Componentes de cada afirmación.** Para cada afirmación, indica qué unidades de la sección, de CUALQUIER párrafo, cumplen respecto de ELLA estas funciones:

- **datos**: evidencia que se ofrece como prueba de esa afirmación: cifras, porcentajes, estadísticas, hechos verificables de la situación, y resultados o hallazgos de estudios citados. Un resultado de otro estudio es siempre dato, aunque use verbos como "evidencia" o "demuestra".
- **garantias**: unidad del propio autor que explica EXPLÍCITAMENTE por qué un dato concreto sostiene esa afirmación concreta ("esto indica que", "lo cual evidencia", "por tanto", "en consecuencia", "este hallazgo explica por qué"). Indica en "dato" el id de la unidad de dato que la garantía conecta con la afirmación; ese dato debe figurar también en "datos" de la misma afirmación. Si solo repite o amplía la afirmación, no es garantía. Si hay que suponer el vínculo, no es garantía.
- **respaldos**: fundamento TEÓRICO o NORMATIVO que legitima el razonamiento: una teoría, modelo, marco, ley, norma o reglamento que la unidad NOMBRA ("según la teoría de restricciones (Goldratt, 1984)...", "la norma ISO 9001 establece..."). Indica en "garantia" el id de la garantía que respalda, o null si respalda directamente la afirmación. Un hallazgo empírico de un estudio es dato, no respaldo.
- **refutaciones**: el autor reconoce una objeción, excepción o condición bajo la cual ESA afirmación podría no cumplirse, o una postura contraria a ella ("podría argumentarse que...", "esto no aplica cuando..."). Indica en "responde_en" el id de la unidad donde el autor responde a la objeción, o null si no la responde. NO son refutaciones: la identificación de una brecha, la crítica a estudios previos, la delimitación del alcance o las limitaciones del propio estudio. La palabra "sin embargo", "no obstante" o "aunque" no basta.

Reglas generales:
- Revisa TODAS las unidades con cifras, porcentajes o citas y vincula cada una, como dato, a la afirmación que sostiene, esté en el mismo párrafo o en otro. Una afirmación intermedia que sirve de razón para la afirmación central puede figurar también en los "datos" de la central.
- Una unidad nunca es dato, garantía, respaldo ni refutación de sí misma.
- Usa SOLO ids que aparecen en el texto, con el formato exacto "P2-U3". No copies texto.
- Una unidad puede cumplir funciones distintas respecto de afirmaciones distintas (por ejemplo, ser una afirmación y a la vez el dato de otra afirmación más general). Asigna varias funciones a una misma unidad solo si de verdad las cumple.
- Una afirmación puede quedar sin datos, garantías, respaldos ni refutaciones: en ese caso deja las listas vacías. No fuerces vínculos.
- Un dato apoya a una afirmación solo si el texto lo ofrece como prueba de ella, aunque estén en párrafos distintos; la cercanía o el tema común no bastan.

# Sección (anonimizada)

{unidades}
