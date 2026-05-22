"""Detect WAF / anti-bot challenge pages so we don't score them as if they were the site.

Si el fetch recibió una página de challenge (Cloudflare, Akamai, DataDome, etc.),
el HTML no representa el sitio real. Analizarlo da métricas falsas y recomendaciones
inaccionables. Esta función detecta esos casos para que el analizador corte temprano
y muestre un mensaje claro al usuario.
"""

from bs4 import BeautifulSoup


def detect_protection(html: str, headers: dict, status_code: int) -> dict | None:
    """Return {type, name, evidence} if this is a WAF/anti-bot challenge, else None."""
    h = {k.lower(): str(v) for k, v in headers.items()}

    if h.get("cf-mitigated", "").lower() == "challenge":
        return _info("cloudflare", "Cloudflare bot challenge", "header cf-mitigated: challenge")

    server = h.get("server", "").lower()
    lower_html = html[:50000].lower() if html else ""

    if server == "cloudflare" and status_code in (403, 503):
        if "challenges.cloudflare.com" in lower_html or "cf-chl" in lower_html:
            return _info("cloudflare", "Cloudflare bot challenge", "server cloudflare + script challenges.cloudflare.com")

    if html:
        try:
            soup = BeautifulSoup(html, "lxml")
            title = (soup.title.get_text(strip=True) if soup.title else "").lower()
        except Exception:
            title = ""
        if title in ("just a moment...", "just a moment…"):
            return _info("cloudflare", "Cloudflare bot challenge", 'title "Just a moment..."')
        if "attention required" in title and "cloudflare" in lower_html:
            return _info("cloudflare", "Cloudflare 1020 / firewall block", 'title "Attention Required"')

    if h.get("x-dd-b") or "datadome" in lower_html and status_code in (403, 429):
        return _info("datadome", "DataDome", "DataDome signature en headers o HTML")

    if server.startswith("akamaighost") and status_code in (403, 503):
        return _info("akamai", "Akamai Bot Manager", "server: AkamaiGHost + Access Denied")

    if "px-captcha" in lower_html or "perimeterx" in lower_html:
        return _info("perimeterx", "PerimeterX / Human Security", "marcadores px-captcha/perimeterx en HTML")

    if "incapsula" in lower_html or "_incap_" in lower_html:
        return _info("imperva", "Imperva / Incapsula", "marcadores incapsula en HTML")

    return None


def _info(kind: str, name: str, evidence: str) -> dict:
    return {"type": kind, "name": name, "evidence": evidence}
