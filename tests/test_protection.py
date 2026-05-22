from seo_analyzer.analyzer import analyze_html
from seo_analyzer.protection import detect_protection


CF_CHALLENGE_HTML = """<!DOCTYPE html>
<html lang="en-US"><head><title>Just a moment...</title>
<script src="https://challenges.cloudflare.com/turnstile/v0/api.js"></script>
<meta name="robots" content="noindex,nofollow"></head><body></body></html>
"""


def test_detect_cloudflare_via_header():
    info = detect_protection("<html></html>", {"cf-mitigated": "challenge"}, 403)
    assert info and info["type"] == "cloudflare"


def test_detect_cloudflare_via_title():
    info = detect_protection(CF_CHALLENGE_HTML, {}, 403)
    assert info and info["type"] == "cloudflare"


def test_detect_cloudflare_via_server_plus_script():
    info = detect_protection(
        "<html><body>blocked <script src='https://challenges.cloudflare.com/x.js'></script></body></html>",
        {"server": "cloudflare"}, 403,
    )
    assert info and info["type"] == "cloudflare"


def test_no_false_positive_on_normal_html():
    assert detect_protection("<html><title>Hola</title><body>contenido normal</body></html>", {"server": "nginx"}, 200) is None


def test_analyze_html_short_circuits_on_challenge():
    report = analyze_html("https://digiconsult.ing/", CF_CHALLENGE_HTML)
    assert report["protection"]["type"] == "cloudflare"
    assert report["score"]["blocked"] is True
    assert report["score"]["overall_score"] is None
    assert len(report["issues"]) == 1
    assert report["issues"][0]["code"] == "anti_bot_protection"
