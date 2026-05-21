from urllib.parse import urlparse

from bs4 import BeautifulSoup

from .fetcher import fetch_text, origin
from .issues import Issue


def check_technical(html: str, final_url: str, headers: dict, status_code: int, elapsed_ms: int) -> tuple[list[Issue], dict]:
    soup = BeautifulSoup(html, "lxml")
    issues: list[Issue] = []
    metrics: dict = {}

    parsed = urlparse(final_url)
    https = parsed.scheme == "https"
    metrics["https"] = https
    if not https:
        issues.append(Issue(
            code="not_https",
            category="technical",
            severity="critical",
            message="El sitio no usa HTTPS.",
            recommendation="Instala un certificado SSL y fuerza la redirección 301 de HTTP a HTTPS.",
        ))

    metrics["status_code"] = status_code
    if status_code >= 400:
        issues.append(Issue(
            code="bad_status",
            category="technical",
            severity="critical",
            message=f"La página devolvió status {status_code}.",
            recommendation="Corrige el error para que Google pueda indexar la URL.",
        ))

    canonical = soup.find("link", rel="canonical")
    canonical_href = canonical.get("href") if canonical else None
    metrics["canonical"] = canonical_href
    if not canonical_href:
        issues.append(Issue(
            code="canonical_missing",
            category="technical",
            severity="medium",
            message="No hay etiqueta canonical.",
            recommendation="Agrega <link rel='canonical' href='...'> apuntando a la URL preferida.",
        ))

    viewport = soup.find("meta", attrs={"name": "viewport"})
    metrics["viewport"] = bool(viewport)
    if not viewport:
        issues.append(Issue(
            code="viewport_missing",
            category="technical",
            severity="high",
            message="Falta meta viewport (no responsive).",
            recommendation="Agrega <meta name='viewport' content='width=device-width, initial-scale=1'>.",
        ))

    charset = soup.find("meta", charset=True) or soup.find("meta", attrs={"http-equiv": "Content-Type"})
    metrics["charset_declared"] = bool(charset)
    if not charset:
        issues.append(Issue(
            code="charset_missing",
            category="technical",
            severity="low",
            message="No se declaró charset.",
            recommendation="Agrega <meta charset='utf-8'> al inicio del <head>.",
        ))

    robots_meta = soup.find("meta", attrs={"name": "robots"})
    robots_content = (robots_meta.get("content") or "").lower() if robots_meta else ""
    metrics["robots_meta"] = robots_content
    if "noindex" in robots_content:
        issues.append(Issue(
            code="noindex",
            category="technical",
            severity="critical",
            message="La página tiene meta robots = noindex.",
            recommendation="Elimina 'noindex' si quieres que Google indexe esta URL.",
            evidence=robots_content,
        ))

    ld_json = soup.find_all("script", attrs={"type": "application/ld+json"})
    metrics["structured_data_blocks"] = len(ld_json)
    if not ld_json:
        issues.append(Issue(
            code="structured_data_missing",
            category="technical",
            severity="medium",
            message="No hay datos estructurados (JSON-LD).",
            recommendation="Agrega schema.org JSON-LD (Article, Product, Organization, etc.) para rich results.",
        ))

    root = origin(final_url)
    robots_status, robots_body = fetch_text(f"{root}/robots.txt")
    metrics["robots_txt"] = robots_status == 200
    if robots_status != 200:
        issues.append(Issue(
            code="robots_txt_missing",
            category="technical",
            severity="medium",
            message="robots.txt no es accesible.",
            recommendation=f"Publica {root}/robots.txt con directivas Allow/Disallow y referencia al sitemap.",
        ))
    elif "sitemap:" not in robots_body.lower():
        issues.append(Issue(
            code="robots_no_sitemap",
            category="technical",
            severity="low",
            message="robots.txt no referencia el sitemap.",
            recommendation="Agrega 'Sitemap: https://tu-dominio/sitemap.xml' en robots.txt.",
        ))

    sitemap_status, _ = fetch_text(f"{root}/sitemap.xml")
    metrics["sitemap_xml"] = sitemap_status == 200
    if sitemap_status != 200:
        issues.append(Issue(
            code="sitemap_missing",
            category="technical",
            severity="medium",
            message="sitemap.xml no es accesible en la raíz.",
            recommendation=f"Genera y publica {root}/sitemap.xml con todas las URLs indexables.",
        ))

    metrics["server"] = headers.get("Server", "")
    metrics["compression"] = headers.get("Content-Encoding", "")
    if not metrics["compression"]:
        issues.append(Issue(
            code="no_compression",
            category="technical",
            severity="medium",
            message="La respuesta no usa compresión (gzip/br).",
            recommendation="Habilita gzip o brotli en el servidor para reducir el peso de transferencia.",
        ))

    metrics["ttfb_ms"] = elapsed_ms
    if elapsed_ms > 1500:
        issues.append(Issue(
            code="slow_response",
            category="technical",
            severity="high",
            message=f"Respuesta lenta del servidor ({elapsed_ms} ms).",
            recommendation="Optimiza backend, usa CDN y caché. Objetivo TTFB < 800 ms.",
        ))
    elif elapsed_ms > 800:
        issues.append(Issue(
            code="moderate_response",
            category="technical",
            severity="medium",
            message=f"TTFB moderado ({elapsed_ms} ms).",
            recommendation="Apunta a TTFB < 800 ms con caché y CDN.",
        ))

    return issues, metrics
