"""Auditoría: cada cifra del OE5 y del OE6 que aparece en el Informe de Tesis v15, frente al valor recalculado
desde data/. Devuelve una tabla «apartado | cifra | valor en informe | valor recalculado | coincide | explicación».

Formato de los valores recalculados: el mismo del informe (porcentajes con un decimal, p con tres decimales y sin
cero inicial). «coincide» compara los textos ya formateados.
"""
from __future__ import annotations

import pandas as pd

from . import oe5, oe6


def p3(x):
    return "< .001" if x < .001 else f"{x:.3f}".replace("0.", ".", 1)


def f1(x):
    return f"{x:.1f}"


def d2(x):
    return f"{x:+.2f}" if x is not None else "—"


def r2(x):
    return f"{x:.2f}".replace("0.", ".", 1)


def miles(n):
    return f"{n:,}".replace(",", " ")


EXPLICACION = {
    "wilcoxon_dp": "No reproducible con los datos vigentes; ningún archivo de salida conserva el valor del informe. "
                   "Probablemente se copió de una corrida anterior a la versión 1.1 de la división, que cambió la "
                   "descripción del problema de un proyecto del GC en S5 y S6. No afecta a la HE5.",
    "v11": "Igual que el anterior: el resumen vigente (resumen_OE5_v2.json) da 74 y 18.",
    "sin_datos": "Faltaba 1 corrección: estaba en una dimensión sin texto dividido porque la versión anterior de "
                 "ese proyecto fue «sin avance» y se comparó con el PDF descargado, no con el texto calificado. "
                 "Corregido: la versión anterior es la última entrega calificada; la corrección es sustantiva.",
    "sustantiva": "Cambia por la misma corrección del caso «sin avance» (1 proyecto, 1 intervalo).",
    "redondeo": "Diferencia de redondeo: el script original redondeaba antes de resumir (la TL de cada proyecto a "
                "un decimal antes de la mediana, o el IC a tres decimales antes de dos). U y p no cambian.",
}


def auditar_v15() -> pd.DataFrame:
    filas = []

    def fila(apartado, cifra, informe, recalculado, explicacion=""):
        filas.append(dict(apartado=apartado, cifra=cifra, valor_informe=str(informe),
                          valor_recalculado=str(recalculado), coincide=str(informe) == str(recalculado),
                          explicacion=explicacion))

    # ------------------------------------------------------------------ OE5 (S4 a S7, como en el v15)
    d5 = oe5.cargar()
    P = lambda s, sid, g=None: oe5.perfil(d5, s, sid, g)
    a = P("S4", "S02")
    fila("6.5.1", "Descripciones del problema completas en S4", 33, a["n"])
    fila("6.5.1", "Justificaciones completas en S4", 25, P("S4", "S05")["n"])
    fila("6.5.1", "Afirmaciones por sección, DP S4 (Md)", 5, int(a["afirmaciones_Md"]))
    for k, v in (("dato", "70.4"), ("garantia", "6.5"), ("respaldo", "2.2"), ("calificador", "5.4"),
                 ("refutacion", "0.5")):
        fila("6.5.1", f"% afirmaciones con {k}, DP S4", v, f1(a[f"pct_con_{k}"]))
    j = P("S4", "S05")
    fila("6.5.1", "% afirmaciones con dato, JU S4", "66.2", f1(j["pct_con_dato"]))
    fila("6.5.1", "% afirmaciones con garantía, JU S4", "5.5", f1(j["pct_con_garantia"]))
    fila("6.5.1", "Secciones con garantía, DP S4", 10, a["secciones_con_garantia"])
    fila("6.5.1", "Secciones con garantía, JU S4", 6, j["secciones_con_garantia"])
    fila("6.5.1", "% vínculos entre párrafos, DP S4", "57.3", f1(a["vinculos_entre_parrafos_pct"]))
    fila("6.5.1", "% vínculos con lema compartido, DP S4", "67.9", f1(a["vinculos_con_lema_pct"]))
    fila("6.5.1", "DP S4 en el nivel 2 de Erduran", 32, a["niveles"].get(2, 0))
    s7, j7 = P("S7", "S02"), P("S7", "S05")
    fila("6.5.1", "% con dato / garantía, DP S7", "81.2 / 7.6", f"{f1(s7['pct_con_dato'])} / {f1(s7['pct_con_garantia'])}")
    fila("6.5.1", "% con dato / garantía, JU S7", "74.5 / 4.5", f"{f1(j7['pct_con_dato'])} / {f1(j7['pct_con_garantia'])}")
    # Tabla 29 completa
    t29 = {("S02", "S4", "GC"): ["6", "70.8", "5.6", "1.1", "7.9", "0.0", "3", "18.4", "41.6", "33.3"],
           ("S02", "S4", "GE"): ["5", "70.1", "7.2", "3.1", "3.1", "1.0", "7", "16.7", "50.0", "33.3"],
           ("S02", "S7", "GC"): ["5", "81.2", "6.9", "3.0", "1.0", "1.0", "6", "20.0", "50.0", "33.3"],
           ("S02", "S7", "GE"): ["7", "81.2", "8.1", "2.7", "2.0", "0.7", "11", "20.0", "50.0", "50.0"],
           ("S05", "S4", "GC"): ["7", "71.6", "5.2", "1.7", "2.6", "4.3", "3", "15.2", "41.6", "41.6"],
           ("S05", "S4", "GE"): ["7", "58.8", "5.9", "0.0", "1.2", "0.0", "3", "10.0", "33.3", "33.3"],
           ("S05", "S7", "GC"): ["10", "69.5", "2.3", "0.9", "0.9", "1.9", "4", "15.3", "33.3", "50.0"],
           ("S05", "S7", "GE"): ["8", "80.8", "7.2", "3.0", "2.4", "1.8", "8", "20.0", "41.6", "33.3"]}
    trunc = lambda x: f"{int(x * 10) / 10:.1f}"  # el informe trunca 41.65 a 41.6
    for (sid, s, g), vals in t29.items():
        x = P(s, sid, g)
        rec = [f"{x['afirmaciones_Md']:.0f}"] + [f1(x[f"pct_con_{k}"]) for k in oe5.APOYOS] + \
              [str(x["secciones_con_garantia"]), f1(x["elaboracion_Md"]), trunc(x["estructural_Md"]), trunc(x["v11_Md"])]
        exp = "Mediana 5.5 / 10.5 / 7.5 redondeada al par más cercano." if sid + s + g in ("S02S4GC", "S05S7GC", "S05S7GE") else ""
        fila("Tabla 29", f"{'DP' if sid == 'S02' else 'JU'} {s} {g}: Md afirm., %dato, %garantía, %respaldo, "
             "%calificador, %refutación, secc. con garantía, Md elaboración, Md estructural, Md v1.1",
             " | ".join(vals), " | ".join(rec), exp)
    cv = oe5.comparacion_v11(d5, "S02")
    fila("6.5.1", "Valores distintos: estructural 2.0 / v1.1 / elaboración (DP)", "4 / 3 / 40",
         f"{cv['valores_estructural']} / {cv['valores_v11']} / {cv['valores_elaboracion']}")
    fila("6.5.1", "% secciones con 33.3 %: v1.1 → 2.0", "54.3 → 36.2", f"{f1(cv['pct33_v11'])} → {f1(cv['pct33_estructural'])}")
    fila("6.5.1", "Estructural 2.0 frente a 1.1: mayor / igual / menor (de 138)", "46 / 75 / 17",
         f"{cv['mayor']} / {cv['igual']} / {cv['menor']}", EXPLICACION["v11"])
    # 6.5.2 y Tabla 30
    for sid, s4, s7 in (("S02", "16.7", "20.0"), ("S05", "15.0", "18.0")):
        fila("6.5.2", f"Md elaboración {oe5.SECCIONES[sid]}, S4 → S7", f"{s4} → {s7}",
             f"{f1(P('S4', sid)['elaboracion_Md'])} → {f1(P('S7', sid)['elaboracion_Md'])}")
    w = oe5.consecutivas(d5, ["S4", "S5", "S6", "S7"])
    inf_w = {("S02", "Total"): ["15/10 .124", "14/10 .269", "11/14 .611"],
             ("S05", "Total"): ["13/5 .037", "12/8 .081", "9/19 .763"],
             ("S02", "GC"): [".328", ".249", ".518"], ("S02", "GE"): [".136", ".351", ".703"],
             ("S05", "GC"): [".444", ".500", ".876"], ("S05", "GE"): [".005", ".078", ".377"]}
    for (sid, g), vals in inf_w.items():
        for iv, v in zip(["S4_S5", "S5_S6", "S6_S7"], vals):
            r = w[(iv, sid)][g]
            rec = (f"{r['aumentan']}/{r['disminuyen']} {p3(r['p'])}" if g == "Total" else p3(r["p"]))
            fila("6.5.2 / Tabla 30", f"Wilcoxon {oe5.SECCIONES[sid]} {g} {iv} (aumentos/disminuciones p)", v, rec,
                 EXPLICACION["wilcoxon_dp"] if sid == "S02" and g in ("GC", "Total") and v != rec else "")
    for sid in oe5.SECCIONES:
        for s in ("S4", "S5", "S6", "S7"):
            fila("Tabla 30", f"Md elaboración {oe5.SECCIONES[sid]} {s} GC / GE / Total",
                 {("S02", "S4"): "18.4 / 16.7 / 16.7", ("S02", "S5"): "20.0 / 20.0 / 20.0",
                  ("S02", "S6"): "20.0 / 20.0 / 20.0", ("S02", "S7"): "20.0 / 20.0 / 20.0",
                  ("S05", "S4"): "15.2 / 10.0 / 15.0", ("S05", "S5"): "17.3 / 19.3 / 18.6",
                  ("S05", "S6"): "18.0 / 20.0 / 20.0", ("S05", "S7"): "15.3 / 20.0 / 18.0"}[(sid, s)],
                 " / ".join(f1(P(s, sid, g)["elaboracion_Md"] + 1e-9) for g in ("GC", "GE"))
                 + " / " + f1(P(s, sid)["elaboracion_Md"]))
    h = oe5.he5(d5)
    he = oe5.he5(d5, "indice_estructural")
    fila("6.5.2", "HE5 DP: Md cambio GE / GC; U; p", "3.1 / 2.5; U = 156.5; p = .551",
         f"{f1(h['S02']['Md_GE'])} / {f1(h['S02']['Md_GC'] + 1e-9)}; U = {h['S02']['U']}; p = {p3(h['S02']['p'])}",
         "Md GE = 3.15 y Md GC = 2.45: el informe redondea 3.15 hacia abajo y 2.45 hacia arriba. " + EXPLICACION["redondeo"])
    fila("6.5.2", "HE5 JU: U; p; δ", "U = 230.0; p = .013; δ = .44",
         f"U = {h['S05']['U']}; p = {p3(h['S05']['p'])}; δ = {r2(h['S05']['delta'])}",
         "El párrafo del v15 está dañado («pn = 20 y 16»): falta la frase de la justificación (Md 3.1 frente a -1.4).")
    fila("6.5.4", "p ajustado por Holm DP / JU (elaboración)", ".551 / .027",
         f"{p3(h['S02']['p_holm'])} / {p3(h['S05']['p_holm'])}")
    fila("6.5.4", "p estructural DP / JU; ajustados", ".645 / .095; .645 / .189",
         f"{p3(he['S02']['p'])} / {p3(he['S05']['p'])}; {p3(he['S02']['p_holm'])} / {p3(he['S05']['p_holm'])}")
    fila("6.5.4", "Decisión HE5", "se acepta de forma parcial", h["decision"])
    sp = oe5.validez_convergente(d5)
    for (s, sid), v in (("S4", "S02"), ".04 .847 33"), (("S7", "S02"), ".05 .762 36"), (("S4", "S05"), ".02 .933 25"), \
                        (("S7", "S05"), ".22 .206 36"):
        r = sp[(s, sid)]
        fila("6.5.3", f"Spearman elaboración-calidad {oe5.SECCIONES[sid]} {s} (ρ p n)", v,
             f"{r2(r['rho'])} {p3(r['p'])} {r['n']}", "ρ = .035: " + EXPLICACION["redondeo"] if (s, sid) == ("S4", "S02") else "")
    rt = oe5.retest()
    fila("5.6.7", "Retest: secciones / unidades", "58 / 1 215", f"{rt['secciones']} / {miles(rt['unidades'])}")
    fila("5.6.7", "Retest: % funciones iguales / % vínculos iguales", "80.6 / 65.4",
         f"{f1(rt['funciones_iguales_pct'])} / {f1(rt['vinculos_iguales_pct'])}")
    fila("5.6.7", "CCI(2,1) elaboración / estructural", ".77 / .77",
         f"{r2(rt['cci_elaboracion'])} / {r2(rt['cci_estructural'])}")

    # ------------------------------------------------------------------ OE6
    d6 = oe6.cargar()
    t = oe6.tabla_intervalos(d6)
    inf31 = {("S4_S5", "GC"): "1 276 91 33.0 23 4.5", ("S4_S5", "GE"): "3 238 64 26.9 26 5.3",
             ("S5_S6", "GC"): "11 276 12 4.3 7 1.0", ("S5_S6", "GE"): "0 256 92 35.9 49 7.2",
             ("S6_S7", "GC"): "1 290 89 30.7 51 7.5", ("S6_S7", "GE"): "3 318 100 31.4 34 3.1",
             ("S7_S9", "GC"): "1 288 57 19.8 39 4.9", ("S7_S9", "GE"): "2 260 72 27.7 53 4.3",
             ("Total", "GC"): "14 1 130 249 22.0 120 4.5", ("Total", "GE"): "8 1 072 328 30.6 162 4.6"}
    for (iv, g), v in inf31.items():
        r = t[(t.intervalo == iv) & (t.grupo == g)].iloc[0]
        rec = f"{r.entregas_nominales} {miles(r.deficiencias)} {r.corregidas} {f1(r.TC)} {r.retrocesos} {f1(r.TR)}"
        fila("Tabla 31", f"{iv} {g}: nominales, observaciones, levantadas, TL, retrocesos, TR", v, rec)
    tot = t[t.intervalo == "Total"]
    fila("6.6.1", "Observaciones acumuladas", "2 202", miles(int(tot.deficiencias.sum())))
    pi = oe6.por_intervalo(d6)
    fila("Tabla 31 (nota)", "p de Holm por intervalo S4-S5, S5-S6, S6-S7, S7-S9", "1.000, < .001, 1.000, 1.000",
         ", ".join(p3(x) for x in pi.p_holm))
    corr = d6[d6.corregida == 1].clase_cambio.value_counts()
    n = int(d6.corregida.sum())
    fila("6.6.2", "Levantadas: total = sustantiva + superficial + sin cambio", "577 = 519 + 14 + 43 (suman 576)",
         f"{n} = {corr.get('sustantiva', 0)} + {corr.get('superficial', 0)} + {corr.get('sin_cambio', 0)}",
         EXPLICACION["sin_datos"])
    fila("6.6.2", "% levantadas con revisión sustantiva / sin cambio", "89.9 / 7.5",
         f"{f1(100 * corr.get('sustantiva', 0) / n)} / {f1(100 * corr.get('sin_cambio', 0) / n)}", EXPLICACION["sustantiva"])
    rt6 = oe6.respaldo_textual(d6).set_index("clase_cambio")
    inf32 = {"sin_cambio": "319 515 8.3 1 304 2.7", "superficial": "48 79 17.7 214 3.3",
             "sustantiva": "720 1 275 40.7 3 611 6.5"}
    for c, v in inf32.items():
        r = rt6.loc[c]
        fila("Tabla 32", f"{c}: dimensiones, observaciones, TL, cumplidos, TR", v,
             f"{int(r.dimensiones)} {miles(int(r.deficiencias))} {f1(r.TC)} {miles(int(r.cumplidos))} {f1(r.TR)}",
             EXPLICACION["sustantiva"] if c == "sustantiva" else "")
    fila("6.6.2", "TL sin cambio de texto GC / GE", "7.9 / 8.9",
         f"{f1(rt6.loc['sin_cambio'].TC_GC)} / {f1(rt6.loc['sin_cambio'].TC_GE)}")
    pdim = oe6.por_dimension(d6).set_index(["dimension", "grupo"])
    for dim, nombre, v in ((2, "descripción del problema", "44.3 de 174 / 13.0 de 208"),
                           (7, "marco teórico", "57.8 / 36.0"), (8, "hipótesis", "45.5 / 10.0"),
                           (9, "variables", "58.1 / 25.0"), (3, "formulación", "36.7 de 30 / 22.7 de 97")):
        ge, gc = pdim.loc[(dim, "GE")], pdim.loc[(dim, "GC")]
        if dim == 2:
            rec = f"{f1(ge.TC)} de {int(ge.deficiencias)} / {f1(gc.TC)} de {int(gc.deficiencias)}"
        elif dim == 3:
            rec = f"{f1(gc.TC)} de {int(gc.deficiencias)} / {f1(ge.TC)} de {int(ge.deficiencias)}"
        else:
            rec = f"{f1(ge.TC)} / {f1(gc.TC)}"
        fila("6.6.2", f"TL por dimensión: {nombre} (GE / GC)", v, rec)
    pr = oe6.contraste(oe6.por_proyecto(d6))
    fila("6.6.3 / Tabla 33", "TL acumulada: Md (M) GC; Md (M) GE; U; p; δ", "20.9 (22.8); 32.3 (32.1); 249.5; .002; +0.56",
         f"{f1(pr['Md_GC'])} ({f1(pr['M_GC'])}); {f1(pr['Md_GE'])} ({f1(pr['M_GE'])}); {pr['U']}; {p3(pr['p'])}; "
         f"{d2(pr['delta'])}")
    ss = oe6.contraste(oe6.por_proyecto(d6, "corregida_sust"))
    fila("6.6.3 / Tabla 33", "TL con revisión sustantiva: Md (M) GC; Md (M) GE; U; p; δ",
         "17.5 (20.5); 31.5 (29.4); 243.0; .004; +0.52",
         f"{f1(ss['Md_GC'])} ({f1(ss['M_GC'])}); {f1(ss['Md_GE'])} ({f1(ss['M_GE'])}); {ss['U']}; {p3(ss['p'])}; "
         f"{d2(ss['delta'])}", EXPLICACION["sustantiva"] + " " + EXPLICACION["redondeo"])
    sn = oe6.contraste(oe6.por_proyecto(d6, filtro=d6.nominal == 0))
    fila("6.6.3 / Tabla 33", "TL sin entregas nominales: Md (M) GC; Md (M) GE; U; p; δ",
         "27.6 (28.6); 33.8 (34.9); 215.5; .040; +0.35",
         f"{f1(sn['Md_GC'])} ({f1(sn['M_GC'])}); {f1(sn['Md_GE'])} ({f1(sn['M_GE'])}); {sn['U']}; {p3(sn['p'])}; "
         f"{d2(sn['delta'])}", EXPLICACION["redondeo"])
    g = oe6.gee(d6)
    fila("6.6.3 / Tabla 33", "GEE: OR [IC 95 %]; p", "1.45 [1.05; 1.99]; .011",
         f"{g['OR']:.2f} [{g['IC95'][0]:.2f}; {g['IC95'][1]:.2f}]; {p3(g['p_unilateral'])}",
         "Límite superior 1.9846: " + EXPLICACION["redondeo"])
    tr = oe6.contraste(oe6.por_proyecto(d6), "TR", "two-sided")
    fila("6.6.3 / Tabla 33", "TR acumulada: Md GC; Md GE; U; p bilateral", "5.0; 4.9; 155.0; .886",
         f"{f1(tr['Md_GC'])}; {f1(tr['Md_GE'])}; {tr['U']}; {p3(tr['p'])}", EXPLICACION["redondeo"])
    return pd.DataFrame(filas)
