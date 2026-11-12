"""Pruebas estadísticas comunes del OE5 y del OE6.

Todas las funciones devuelven diccionarios simples (números redondeados solo al presentar, no al calcular).
"""
from __future__ import annotations

import math
import statistics as st

import numpy as np
from scipy.stats import mannwhitneyu, spearmanr, wilcoxon


def delta_cliff(x, y) -> float:
    """Delta de Cliff (Cliff, 1993): P(X > Y) - P(X < Y). Con la U de Mann-Whitney de x frente a y,
    equivale a 2U/(n1 n2) - 1 (correlación biserial de rangos)."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    mayor = (x[:, None] > y[None, :]).sum()
    menor = (x[:, None] < y[None, :]).sum()
    return float((mayor - menor) / (len(x) * len(y)))


def magnitud_cliff(d: float) -> str:
    """Umbrales de Romano et al. (2006)."""
    a = abs(d)
    return "despreciable" if a < .147 else "pequeño" if a < .33 else "mediano" if a < .474 else "grande"


def mann_whitney(ge, gc, alternativa: str = "greater") -> dict:
    """U de Mann-Whitney (GE frente a GC). alternativa='greater' prueba H1: GE > GC (unilateral)."""
    ge = [float(v) for v in ge if v is not None and not (isinstance(v, float) and math.isnan(v))]
    gc = [float(v) for v in gc if v is not None and not (isinstance(v, float) and math.isnan(v))]
    if len(ge) < 2 or len(gc) < 2:
        return dict(n_GE=len(ge), n_GC=len(gc), U=None, p=None, delta=None)
    r = mannwhitneyu(ge, gc, alternative=alternativa)
    d = delta_cliff(ge, gc)
    return dict(n_GE=len(ge), n_GC=len(gc), Md_GE=st.median(ge), Md_GC=st.median(gc),
                M_GE=st.mean(ge), M_GC=st.mean(gc), U=float(r.statistic), p=float(r.pvalue),
                delta=d, magnitud=magnitud_cliff(d))


def holm(ps: list[float]) -> list[float]:
    """Corrección de Holm (1979): ajuste secuencial de valores p para k pruebas."""
    orden = sorted(range(len(ps)), key=lambda i: ps[i])
    ajustados, previo = [None] * len(ps), 0.0
    for rango, i in enumerate(orden):
        previo = max(previo, min(1.0, (len(ps) - rango) * ps[i]))
        ajustados[i] = previo
    return ajustados


def wilcoxon_aumento(diferencias) -> dict:
    """Prueba de rangos con signo de Wilcoxon (1945), unilateral (H1: la diferencia es positiva).
    Los empates en cero se descartan (zero_method='wilcox')."""
    d = [float(x) for x in diferencias if x is not None]
    base = dict(n=len(d), aumentan=sum(x > 0 for x in d), disminuyen=sum(x < 0 for x in d),
                se_mantienen=sum(x == 0 for x in d))
    if len(d) < 2 or not any(d):
        return dict(base, W=None, p=None)
    r = wilcoxon(d, alternative="greater", zero_method="wilcox")
    return dict(base, W=float(r.statistic), p=float(r.pvalue))


def spearman(x, y) -> dict:
    """Correlación por rangos de Spearman (1904), bilateral."""
    pares = [(a, b) for a, b in zip(x, y) if a is not None and b is not None
             and not (isinstance(a, float) and math.isnan(a)) and not (isinstance(b, float) and math.isnan(b))]
    if len(pares) < 4:
        return dict(n=len(pares), rho=None, p=None)
    r = spearmanr([a for a, _ in pares], [b for _, b in pares])
    return dict(n=len(pares), rho=float(r.statistic), p=float(r.pvalue))


def cci_2_1(pares) -> float | None:
    """Correlación intraclase CCI(2,1): dos vías, efectos aleatorios, acuerdo absoluto, una medición
    (Shrout y Fleiss, 1979; interpretación de Koo y Li, 2016)."""
    pares = [(float(a), float(b)) for a, b in pares]
    n, k = len(pares), 2
    if n < 3:
        return None
    gm = st.mean(v for p in pares for v in p)
    filas = [st.mean(p) for p in pares]
    cols = [st.mean(p[j] for p in pares) for j in range(k)]
    ssr = k * sum((m - gm) ** 2 for m in filas)
    ssc = n * sum((m - gm) ** 2 for m in cols)
    sst = sum((v - gm) ** 2 for p in pares for v in p)
    sse = sst - ssr - ssc
    msr, msc, mse = ssr / (n - 1), ssc / (k - 1), sse / ((n - 1) * (k - 1))
    den = msr + (k - 1) * mse + k * (msc - mse) / n
    return (msr - mse) / den if den else None


def gee_binomial(df, y: str = "y", grupo: str = "GE", cluster: str = "proyecto", fijo: str = "intervalo") -> dict:
    """Ecuaciones de estimación generalizadas (Liang y Zeger, 1986), binomial con enlace logit, correlación
    intercambiable dentro del proyecto y efecto fijo del intervalo. Devuelve la razón de probabilidades del GE."""
    import statsmodels.api as sm
    import statsmodels.formula.api as smf

    m = smf.gee(f"{y} ~ {grupo} + C({fijo})", cluster, df, family=sm.families.Binomial(),
                cov_struct=sm.cov_struct.Exchangeable()).fit()
    b, p = float(m.params[grupo]), float(m.pvalues[grupo])
    lo, hi = m.conf_int().loc[grupo]
    return dict(n_observaciones=int(len(df)), n_proyectos=int(df[cluster].nunique()), OR=math.exp(b),
                IC95=[math.exp(lo), math.exp(hi)], p_unilateral=p / 2 if b > 0 else 1 - p / 2)
