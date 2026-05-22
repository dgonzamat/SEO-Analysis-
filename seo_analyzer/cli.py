import json
import os
import re
import sys

import click

from .analyzer import analyze, analyze_html
from .report import write_output
from .sitemap import expand_sitemap


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("url")
@click.option("--format", "fmt", type=click.Choice(["console", "json"]), default="console", help="Formato de salida.")
@click.option("--output", "-o", type=click.Path(dir_okay=False, writable=True), help="Archivo destino (por defecto stdout). Ignorado con --sitemap.")
@click.option("--html", "html_file", type=click.Path(exists=True, dir_okay=False), help="Analiza un archivo HTML local en vez de hacer fetch (útil si la IP está bloqueada o el sitio requiere auth).")
@click.option("--sitemap", "sitemap_mode", is_flag=True, help="Trata la URL como un sitemap.xml: expande, audita cada URL listada y escribe un JSON por URL en --out-dir.")
@click.option("--out-dir", type=click.Path(file_okay=False), default="reports", help="Directorio de salida cuando se usa --sitemap (default: reports/).")
@click.option("--max-urls", type=int, default=200, help="Máximo de URLs a auditar desde el sitemap (default: 200).")
@click.option("--psi-api-key", envvar="PSI_API_KEY", help="API key de Google PageSpeed Insights (habilita Core Web Vitals).")
@click.option("--strategy", type=click.Choice(["mobile", "desktop"]), default="mobile", help="Estrategia de PageSpeed.")
@click.option("--fail-under", type=int, default=0, help="Sale con código 1 si el score global queda por debajo de este valor (ignorado con --sitemap).")
def main(url: str, fmt: str, output: str | None, html_file: str | None, sitemap_mode: bool, out_dir: str, max_urls: int, psi_api_key: str | None, strategy: str, fail_under: int) -> None:
    """Analiza una URL y emite un reporte SEO con score 0-100 y recomendaciones priorizadas."""
    if sitemap_mode:
        _crawl_sitemap(url, out_dir, max_urls, psi_api_key, strategy)
        return

    try:
        if html_file:
            with open(html_file, encoding="utf-8") as f:
                html = f.read()
            report = analyze_html(url, html, psi_api_key=psi_api_key, psi_strategy=strategy)
        else:
            report = analyze(url, psi_api_key=psi_api_key, psi_strategy=strategy)
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Error al analizar la URL: {exc}", err=True)
        sys.exit(2)

    write_output(report, fmt, output)

    overall = report["score"].get("overall_score")
    if fail_under and overall is not None and overall < fail_under:
        sys.exit(1)


def _crawl_sitemap(sitemap_url: str, out_dir: str, max_urls: int, psi_api_key: str | None, strategy: str) -> None:
    try:
        urls = expand_sitemap(sitemap_url, max_urls=max_urls)
    except RuntimeError as exc:
        click.echo(f"No pude leer el sitemap: {exc}", err=True)
        sys.exit(2)

    if not urls:
        click.echo("El sitemap está vacío.", err=True)
        sys.exit(2)

    os.makedirs(out_dir, exist_ok=True)
    click.echo(f"Sitemap: {sitemap_url} → {len(urls)} URLs a auditar")
    summary = []

    for i, target in enumerate(urls, 1):
        slug = _slug(target)
        click.echo(f"  [{i}/{len(urls)}] {target}")
        try:
            report = analyze(target, psi_api_key=psi_api_key, psi_strategy=strategy)
        except Exception as exc:  # noqa: BLE001
            click.echo(f"      error: {exc}", err=True)
            summary.append({"url": target, "slug": slug, "error": str(exc)})
            continue
        path = os.path.join(out_dir, f"{slug}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        summary.append({
            "url": target,
            "slug": slug,
            "score": report["score"].get("overall_score"),
            "grade": report["score"].get("grade"),
            "blocked": report["score"].get("blocked", False),
            "protection": (report.get("protection") or {}).get("name"),
            "report": f"{slug}.json",
        })

    summary_path = os.path.join(out_dir, "summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({"sitemap": sitemap_url, "results": summary}, f, indent=2, ensure_ascii=False)

    _write_index(out_dir, sitemap_url, summary)
    click.echo(f"\nResumen: {summary_path}")


def _slug(url: str) -> str:
    s = re.sub(r"^https?://", "", url)
    s = re.sub(r"[^a-zA-Z0-9._-]+", "_", s).strip("_")
    return (s or "root")[:120]


def _write_index(out_dir: str, sitemap_url: str, summary: list[dict]) -> None:
    lines = [
        f"# SEO Crawl — {sitemap_url}",
        "",
        f"Auditadas: {len(summary)} URLs",
        "",
        "| Score | Grade | URL | Notas |",
        "|------:|:-----:|-----|-------|",
    ]
    ranked = sorted(summary, key=lambda r: (r.get("score") is None, r.get("score") or -1))
    for r in ranked:
        score = r.get("score")
        score_str = f"{score}" if score is not None else "—"
        grade = r.get("grade") or "—"
        notes = []
        if r.get("error"):
            notes.append(f"error: {r['error']}")
        if r.get("blocked"):
            notes.append(f"bloqueado por {r.get('protection') or 'WAF'}")
        lines.append(f"| {score_str} | {grade} | [{r['url']}]({r['url']}) | {', '.join(notes) or ''} |")
    with open(os.path.join(out_dir, "index.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
