from datetime import datetime, timezone

from .fetcher import fetch
from .onpage import check_onpage
from .performance import check_performance
from .scoring import prioritize, score_report
from .technical import check_technical


def analyze(url: str, psi_api_key: str | None = None, psi_strategy: str = "mobile") -> dict:
    """Run the full SEO analysis on a URL and return a structured report."""
    fetched = fetch(url)

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
        "score": score,
        "metrics": {
            "onpage": onpage_metrics,
            "technical": tech_metrics,
            "performance": perf_metrics,
        },
        "issues": [i.to_dict() for i in prioritize(all_issues)],
    }
