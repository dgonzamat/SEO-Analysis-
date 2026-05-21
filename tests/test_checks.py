from seo_analyzer.analyzer import analyze_html
from seo_analyzer.onpage import check_onpage

GOOD_HTML = """
<!doctype html>
<html lang="es">
  <head>
    <meta charset="utf-8">
    <title>Guía completa de análisis SEO técnico para 2026</title>
    <meta name="description" content="Aprende a auditar tu sitio paso a paso: meta tags, headings, Core Web Vitals, schema y más. Incluye checklist priorizado.">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="canonical" href="https://example.com/seo">
    <meta property="og:title" content="Guía SEO">
    <meta property="og:description" content="Auditoría SEO">
    <meta property="og:image" content="https://example.com/og.png">
    <meta property="og:url" content="https://example.com/seo">
    <meta name="twitter:card" content="summary_large_image">
  </head>
  <body>
    <h1>Guía SEO</h1>
    <h2>On-page</h2>
    <p>{}</p>
    <a href="/seccion">Interno 1</a>
    <a href="/otra">Interno 2</a>
    <a href="/tercera">Interno 3</a>
    <img src="x.png" alt="captura">
  </body>
</html>
""".format("palabra " * 400)


BAD_HTML = "<html><body><p>hola</p></body></html>"


def test_good_page_has_few_issues():
    issues, metrics = check_onpage(GOOD_HTML, "https://example.com/seo")
    codes = {i.code for i in issues}
    assert "title_missing" not in codes
    assert "h1_missing" not in codes
    assert "meta_description_missing" not in codes
    assert metrics["title_length"] > 0
    assert metrics["h1_count"] == 1


def test_bad_page_flags_essentials():
    issues, metrics = check_onpage(BAD_HTML, "https://example.com")
    codes = {i.code for i in issues}
    assert "title_missing" in codes
    assert "meta_description_missing" in codes
    assert "h1_missing" in codes
    assert "thin_content" in codes
    assert metrics["word_count"] < 50


def test_analyze_html_offline_skips_header_checks():
    report = analyze_html("https://example.com", GOOD_HTML)
    codes = {i["code"] for i in report["issues"]}
    # Offline mode no debe inventar issues de compresión ni TTFB
    assert "no_compression" not in codes
    assert "slow_response" not in codes
    assert "moderate_response" not in codes
    assert report["metrics"]["technical"]["offline_mode"] is True
    assert report["metrics"]["technical"]["ttfb_ms"] is None
