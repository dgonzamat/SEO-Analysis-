"""Expande un sitemap.xml (o un sitemap index) a la lista de URLs que contiene.

XML files normalmente no disparan challenges de Cloudflare/Akamai, así que
es una vía limpia para enumerar URLs de un sitio aunque el HTML esté protegido.
"""

import xml.etree.ElementTree as ET

from .fetcher import fetch_text

NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def expand_sitemap(url: str, max_urls: int = 500) -> list[str]:
    """Return the list of URLs declared in a sitemap.

    Soporta sitemap simple (<urlset>) y sitemap index (<sitemapindex>) recursivo.
    Lanza RuntimeError si el sitemap no es accesible o el XML es inválido.
    """
    status, body = fetch_text(url, timeout=30)
    if status != 200:
        raise RuntimeError(f"sitemap {url} returned status {status}")

    try:
        root = ET.fromstring(body)
    except ET.ParseError as exc:
        raise RuntimeError(f"invalid XML in {url}: {exc}")

    tag = root.tag.lower()
    if tag.endswith("sitemapindex"):
        urls: list[str] = []
        for loc in root.findall("sm:sitemap/sm:loc", NS):
            if loc.text:
                urls.extend(expand_sitemap(loc.text.strip(), max_urls - len(urls)))
                if len(urls) >= max_urls:
                    return urls[:max_urls]
        return urls[:max_urls]

    if tag.endswith("urlset"):
        urls = [e.text.strip() for e in root.findall("sm:url/sm:loc", NS) if e.text]
        return urls[:max_urls]

    raise RuntimeError(f"unexpected root element <{root.tag}> in {url}")
