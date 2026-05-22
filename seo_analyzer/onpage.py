from urllib.parse import urlparse

from bs4 import BeautifulSoup

from .issues import Issue

TITLE_MIN, TITLE_MAX = 30, 60
DESC_MIN, DESC_MAX = 70, 160


def _text(node) -> str:
    return node.get_text(strip=True) if node else ""


def check_onpage(html: str, final_url: str) -> tuple[list[Issue], dict]:
    soup = BeautifulSoup(html, "lxml")
    issues: list[Issue] = []
    metrics: dict = {}

    html_tag = soup.find("html")
    lang = html_tag.get("lang") if html_tag else None
    metrics["lang"] = lang
    if not lang:
        issues.append(Issue(
            code="lang_missing",
            category="onpage",
            severity="medium",
            message="El atributo lang en <html> no está definido.",
            recommendation='Agrega <html lang="es"> (o el idioma correspondiente) para accesibilidad y SEO.',
        ))

    title = _text(soup.title)
    metrics["title"] = title
    metrics["title_length"] = len(title)
    if not title:
        issues.append(Issue(
            code="title_missing",
            category="onpage",
            severity="critical",
            message="La página no tiene <title>.",
            recommendation="Agrega un <title> único, descriptivo y con la keyword principal (30-60 chars).",
        ))
    elif len(title) < TITLE_MIN:
        issues.append(Issue(
            code="title_too_short",
            category="onpage",
            severity="medium",
            message=f"El título tiene {len(title)} caracteres (mínimo recomendado {TITLE_MIN}).",
            recommendation=f"Expande el título a {TITLE_MIN}-{TITLE_MAX} caracteres incluyendo la keyword principal.",
            evidence=title,
        ))
    elif len(title) > TITLE_MAX:
        issues.append(Issue(
            code="title_too_long",
            category="onpage",
            severity="low",
            message=f"El título tiene {len(title)} caracteres (máximo recomendado {TITLE_MAX}).",
            recommendation=f"Acorta el título a {TITLE_MIN}-{TITLE_MAX} caracteres para evitar truncamiento en SERP.",
            evidence=title,
        ))

    desc_tag = soup.find("meta", attrs={"name": "description"})
    description = (desc_tag.get("content") or "").strip() if desc_tag else ""
    metrics["meta_description"] = description
    metrics["meta_description_length"] = len(description)
    if not description:
        issues.append(Issue(
            code="meta_description_missing",
            category="onpage",
            severity="high",
            message="No hay meta description.",
            recommendation="Agrega <meta name='description'> de 70-160 caracteres que invite al click.",
        ))
    elif len(description) < DESC_MIN:
        issues.append(Issue(
            code="meta_description_short",
            category="onpage",
            severity="low",
            message=f"Meta description corta ({len(description)} chars).",
            recommendation=f"Apunta a {DESC_MIN}-{DESC_MAX} caracteres para aprovechar el snippet.",
            evidence=description,
        ))
    elif len(description) > DESC_MAX:
        issues.append(Issue(
            code="meta_description_long",
            category="onpage",
            severity="low",
            message=f"Meta description larga ({len(description)} chars), Google la truncará.",
            recommendation=f"Recorta a {DESC_MIN}-{DESC_MAX} chars.",
            evidence=description,
        ))

    h1s = [_text(h) for h in soup.find_all("h1")]
    metrics["h1_count"] = len(h1s)
    metrics["h1"] = h1s
    if len(h1s) == 0:
        issues.append(Issue(
            code="h1_missing",
            category="onpage",
            severity="high",
            message="No hay etiqueta <h1>.",
            recommendation="Cada página debe tener un <h1> único con la keyword principal.",
        ))
    elif len(h1s) > 1:
        issues.append(Issue(
            code="h1_multiple",
            category="onpage",
            severity="medium",
            message=f"La página tiene {len(h1s)} <h1>. Lo recomendable es uno solo.",
            recommendation="Deja un único <h1> y convierte los demás en <h2>/<h3>.",
            evidence=" | ".join(h1s[:3]),
        ))

    heading_counts = {f"h{i}": len(soup.find_all(f"h{i}")) for i in range(1, 7)}
    metrics["headings"] = heading_counts
    if sum(heading_counts.values()) <= 1:
        issues.append(Issue(
            code="headings_flat",
            category="onpage",
            severity="medium",
            message="La página casi no usa headings (H2-H6).",
            recommendation="Estructura el contenido con H2/H3 para mejorar legibilidad y SEO semántico.",
        ))

    images = soup.find_all("img")
    images_no_alt = [img for img in images if not (img.get("alt") or "").strip()]
    metrics["images_total"] = len(images)
    metrics["images_without_alt"] = len(images_no_alt)
    if images and len(images_no_alt) / len(images) > 0.2:
        issues.append(Issue(
            code="images_alt_missing",
            category="onpage",
            severity="medium",
            message=f"{len(images_no_alt)} de {len(images)} imágenes sin atributo alt.",
            recommendation="Agrega alt descriptivo a cada imagen relevante (deja alt='' solo para decorativas).",
        ))

    host = urlparse(final_url).netloc
    links = soup.find_all("a", href=True)
    internal, external = [], []
    for a in links:
        href = a["href"]
        if href.startswith("#") or href.startswith("javascript:") or href.startswith("mailto:"):
            continue
        netloc = urlparse(href).netloc
        if not netloc or netloc == host:
            internal.append(href)
        else:
            external.append(href)
    metrics["links_internal"] = len(internal)
    metrics["links_external"] = len(external)
    if len(internal) < 3:
        issues.append(Issue(
            code="internal_links_few",
            category="onpage",
            severity="low",
            message=f"Solo {len(internal)} enlaces internos.",
            recommendation="Agrega enlaces internos contextuales para distribuir autoridad y mejorar el crawl.",
        ))

    og_tags = {m.get("property"): m.get("content") for m in soup.find_all("meta") if m.get("property", "").startswith("og:")}
    metrics["open_graph"] = og_tags
    required_og = {"og:title", "og:description", "og:image", "og:url"}
    missing_og = required_og - set(og_tags.keys())
    if missing_og:
        issues.append(Issue(
            code="open_graph_incomplete",
            category="onpage",
            severity="low",
            message=f"Open Graph incompleto: faltan {', '.join(sorted(missing_og))}.",
            recommendation="Completa og:title, og:description, og:image y og:url para previews en redes sociales.",
        ))

    twitter_card = soup.find("meta", attrs={"name": "twitter:card"})
    metrics["twitter_card"] = bool(twitter_card)
    if not twitter_card:
        issues.append(Issue(
            code="twitter_card_missing",
            category="onpage",
            severity="low",
            message="No hay etiqueta twitter:card.",
            recommendation="Agrega <meta name='twitter:card' content='summary_large_image'> para X/Twitter.",
        ))

    body_text = soup.get_text(separator=" ", strip=True)
    words = [w for w in body_text.split() if w]
    metrics["word_count"] = len(words)
    if len(words) < 300:
        issues.append(Issue(
            code="thin_content",
            category="onpage",
            severity="high",
            message=f"Contenido muy corto ({len(words)} palabras).",
            recommendation="Para SEO competitivo apunta a 600+ palabras de contenido sustantivo.",
        ))

    return issues, metrics
