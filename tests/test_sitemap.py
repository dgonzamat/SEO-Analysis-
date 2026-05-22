from unittest.mock import patch

from seo_analyzer.sitemap import expand_sitemap

URLSET = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://digiconsult.ing/</loc></url>
  <url><loc>https://digiconsult.ing/p/foo</loc></url>
  <url><loc>https://digiconsult.ing/p/bar</loc></url>
</urlset>
"""

INDEX = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://digiconsult.ing/sitemap-products.xml</loc></sitemap>
  <sitemap><loc>https://digiconsult.ing/sitemap-pages.xml</loc></sitemap>
</sitemapindex>
"""


def test_expand_urlset():
    with patch("seo_analyzer.sitemap.fetch_text", return_value=(200, URLSET)):
        urls = expand_sitemap("https://digiconsult.ing/sitemap.xml")
    assert urls == [
        "https://digiconsult.ing/",
        "https://digiconsult.ing/p/foo",
        "https://digiconsult.ing/p/bar",
    ]


def test_expand_sitemap_index_recurses():
    pages = "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'><url><loc>https://digiconsult.ing/about</loc></url></urlset>"
    def fake(url, timeout=30):
        if url.endswith("sitemap.xml"):
            return 200, INDEX
        if "products" in url:
            return 200, URLSET
        return 200, pages
    with patch("seo_analyzer.sitemap.fetch_text", side_effect=fake):
        urls = expand_sitemap("https://digiconsult.ing/sitemap.xml")
    assert "https://digiconsult.ing/p/foo" in urls
    assert "https://digiconsult.ing/about" in urls


def test_max_urls_honored():
    with patch("seo_analyzer.sitemap.fetch_text", return_value=(200, URLSET)):
        urls = expand_sitemap("https://digiconsult.ing/sitemap.xml", max_urls=2)
    assert len(urls) == 2
