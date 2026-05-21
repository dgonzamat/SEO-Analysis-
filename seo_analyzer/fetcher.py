import time
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import requests

USER_AGENT = (
    "Mozilla/5.0 (compatible; SEOAnalyzer/0.1; +https://github.com/dgonzamat/seo-analysis-)"
)


@dataclass
class FetchResult:
    url: str
    final_url: str
    status_code: int
    headers: dict
    html: str
    elapsed_ms: int
    redirects: int


def fetch(url: str, timeout: int = 15) -> FetchResult:
    if not urlparse(url).scheme:
        url = "https://" + url
    start = time.perf_counter()
    resp = requests.get(
        url,
        headers={"User-Agent": USER_AGENT, "Accept-Language": "en,es;q=0.9"},
        timeout=timeout,
        allow_redirects=True,
    )
    elapsed = int((time.perf_counter() - start) * 1000)
    return FetchResult(
        url=url,
        final_url=resp.url,
        status_code=resp.status_code,
        headers=dict(resp.headers),
        html=resp.text,
        elapsed_ms=elapsed,
        redirects=len(resp.history),
    )


def fetch_text(url: str, timeout: int = 10) -> tuple[int, str]:
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
            allow_redirects=True,
        )
        return resp.status_code, resp.text
    except requests.RequestException:
        return 0, ""


def origin(url: str) -> str:
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}"


def absolute(base: str, href: str) -> str:
    return urljoin(base, href)
