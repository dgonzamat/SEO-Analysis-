import sys

import click

from .analyzer import analyze, analyze_html
from .report import write_output


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("url")
@click.option("--format", "fmt", type=click.Choice(["console", "json"]), default="console", help="Formato de salida.")
@click.option("--output", "-o", type=click.Path(dir_okay=False, writable=True), help="Archivo destino (por defecto stdout).")
@click.option("--html", "html_file", type=click.Path(exists=True, dir_okay=False), help="Analiza un archivo HTML local en vez de hacer fetch (útil si la IP está bloqueada o el sitio requiere auth).")
@click.option("--psi-api-key", envvar="PSI_API_KEY", help="API key de Google PageSpeed Insights (habilita Core Web Vitals).")
@click.option("--strategy", type=click.Choice(["mobile", "desktop"]), default="mobile", help="Estrategia de PageSpeed.")
@click.option("--fail-under", type=int, default=0, help="Sale con código 1 si el score global queda por debajo de este valor.")
def main(url: str, fmt: str, output: str | None, html_file: str | None, psi_api_key: str | None, strategy: str, fail_under: int) -> None:
    """Analiza una URL y emite un reporte SEO con score 0-100 y recomendaciones priorizadas."""
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

    if fail_under and report["score"]["overall_score"] < fail_under:
        sys.exit(1)


if __name__ == "__main__":
    main()
