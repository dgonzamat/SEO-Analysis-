import os

import requests

from .issues import Issue

PSI_ENDPOINT = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"


def check_performance(url: str, strategy: str = "mobile", api_key: str | None = None) -> tuple[list[Issue], dict]:
    """Query Google PageSpeed Insights for Core Web Vitals.

    Returns empty issues/metrics if no API key is provided or the call fails — the rest of the
    report still works, performance just won't be scored.
    """
    api_key = api_key or os.environ.get("PSI_API_KEY")
    issues: list[Issue] = []
    metrics: dict = {"strategy": strategy, "enabled": bool(api_key)}

    if not api_key:
        return issues, metrics

    try:
        params = {"url": url, "strategy": strategy, "key": api_key, "category": "performance"}
        resp = requests.get(PSI_ENDPOINT, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as exc:
        metrics["error"] = str(exc)
        return issues, metrics

    lighthouse = data.get("lighthouseResult", {})
    audits = lighthouse.get("audits", {})
    perf_score = (lighthouse.get("categories", {}).get("performance", {}) or {}).get("score")
    metrics["performance_score"] = round(perf_score * 100) if perf_score is not None else None

    def numeric(audit_id: str) -> float | None:
        a = audits.get(audit_id, {})
        v = a.get("numericValue")
        return float(v) if v is not None else None

    lcp = numeric("largest-contentful-paint")
    cls = numeric("cumulative-layout-shift")
    inp = numeric("interaction-to-next-paint") or numeric("experimental-interaction-to-next-paint")
    tbt = numeric("total-blocking-time")
    fcp = numeric("first-contentful-paint")
    metrics.update({"lcp_ms": lcp, "cls": cls, "inp_ms": inp, "tbt_ms": tbt, "fcp_ms": fcp})

    if lcp is not None and lcp > 2500:
        issues.append(Issue(
            code="lcp_poor",
            category="performance",
            severity="high" if lcp > 4000 else "medium",
            message=f"LCP de {int(lcp)} ms (objetivo < 2500 ms).",
            recommendation="Optimiza la imagen/hero del above-the-fold, usa preload y reduce el bloqueo de render.",
        ))
    if cls is not None and cls > 0.1:
        issues.append(Issue(
            code="cls_poor",
            category="performance",
            severity="high" if cls > 0.25 else "medium",
            message=f"CLS de {cls:.2f} (objetivo < 0.1).",
            recommendation="Reserva dimensiones para imágenes/iframes y evita insertar contenido sobre el viewport visible.",
        ))
    if inp is not None and inp > 200:
        issues.append(Issue(
            code="inp_poor",
            category="performance",
            severity="high" if inp > 500 else "medium",
            message=f"INP de {int(inp)} ms (objetivo < 200 ms).",
            recommendation="Reduce JavaScript en main thread, divide tareas largas y prioriza interacciones del usuario.",
        ))
    if tbt is not None and tbt > 300:
        issues.append(Issue(
            code="tbt_high",
            category="performance",
            severity="medium",
            message=f"Total Blocking Time alto ({int(tbt)} ms).",
            recommendation="Difiere/elimina JavaScript no crítico (defer, async, code splitting).",
        ))

    return issues, metrics
