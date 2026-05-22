from datetime import datetime, timezone

from .fetcher import FetchResult, fetch
from .issues import Issue
from .onpage import check_onpage
from .performance import check_performance
from .protection import detect_protection
from .scoring import prioritize, score_report
from .technical import check_technical


def analyze(url: str, psi_api_key: str | None = None, psi_strategy: str = "mobile") -> dict:
    """Run the full SEO analysis on a URL and return a structured report."""
    return _analyze(fetch(url), psi_api_key, psi_strategy)


def analyze_html(url: str, html: str, psi_api_key: str | None = None, psi_strategy: str = "mobile") -> dict:
    """Analyze HTML provided directly, skipping the HTTP fetch.

    Útil cuando el sitio bloquea la IP desde donde corre el analizador o cuando
    se quiere analizar staging / contenido detrás de auth. Los checks técnicos
    que dependen de headers (compresión, TTFB) se omiten en este modo.
    """
    fetched = FetchResult(
        url=url, final_url=url, status_code=200, headers={}, html=html, elapsed_ms=0, redirects=0
    )
    return _analyze(fetched, psi_api_key, psi_strategy)


def _analyze(fetched: FetchResult, psi_api_key: str | None, psi_strategy: str) -> dict:
    protection = detect_protection(fetched.html, fetched.headers, fetched.status_code)
    if protection:
        return _blocked_report(fetched, protection)

    onpage_issues, onpage_metrics = check_onpage(fetched.html, fetched.final_url)
    tech_issues, tech_metrics = check_technical(
        fetched.html, fetched.final_url, fetched.headers, fetched.status_code, fetched.elapsed_ms
    )
    perf_issues, perf_metrics = check_performance(
        fetched.final_url, strategy=psi_strategy, api_key=psi_api_key
    )

    all_issues = onpage_issues + tech_issues + perf_issues
    score = score_report(all_issues)

    return {
        "url": fetched.url,
        "final_url": fetched.final_url,
        "status_code": fetched.status_code,
        "redirects": fetched.redirects,
        "ttfb_ms": fetched.elapsed_ms,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "protection": None,
        "score": score,
        "metrics": {
            "onpage": onpage_metrics,
            "technical": tech_metrics,
            "performance": perf_metrics,
        },
        "issues": [i.to_dict() for i in prioritize(all_issues)],
    }


def _blocked_report(fetched: FetchResult, protection: dict) -> dict:
    issue = Issue(
        code="anti_bot_protection",
        category="technical",
        severity="critical",
        message=f"Análisis bloqueado: {protection['name']} interceptó la petición.",
        recommendation=(
            "El HTML recibido es la página de challenge, no tu sitio real, "
            "así que cualquier puntaje aquí sería falso. Para auditar SEO de verdad: "
            "(1) abre la URL en un navegador, guarda el HTML, y corre `seo-analyze --html FILE URL`, "
            "(2) usa una herramienta con IP residencial (Screaming Frog en tu equipo), "
            "(3) o whitelist la IP del crawler en tu WAF."
        ),
        evidence=protection["evidence"],
    )
    return {
        "url": fetched.url,
        "final_url": fetched.final_url,
        "status_code": fetched.status_code,
        "redirects": fetched.redirects,
        "ttfb_ms": fetched.elapsed_ms,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "protection": protection,
        "score": {
            "overall_score": None,
            "grade": "—",
            "categories": {},
            "severity_counts": {"critical": 1, "high": 0, "medium": 0, "low": 0, "info": 0},
            "total_issues": 1,
            "blocked": True,
        },
        "metrics": {},
        "issues": [issue.to_dict()],
    }
