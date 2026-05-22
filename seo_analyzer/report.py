import json
import sys

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[31m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"

SEVERITY_COLOR = {
    "critical": RED + BOLD,
    "high": RED,
    "medium": YELLOW,
    "low": CYAN,
    "info": DIM,
}

SEVERITY_LABEL = {
    "critical": "CRÍTICO",
    "high": "ALTO",
    "medium": "MEDIO",
    "low": "BAJO",
    "info": "INFO",
}


def _color(text: str, color: str, use_color: bool) -> str:
    return f"{color}{text}{RESET}" if use_color else text


def render_console(report: dict, use_color: bool = True) -> str:
    out: list[str] = []
    score = report["score"]
    protection = report.get("protection")
    overall = score["overall_score"]
    grade = score["grade"]

    out.append(_color("═" * 70, CYAN, use_color))
    out.append(_color("  REPORTE SEO", BOLD + CYAN, use_color))
    out.append(_color("═" * 70, CYAN, use_color))
    out.append(f"  URL analizada: {report['final_url']}")
    out.append(f"  Status HTTP:   {report['status_code']}    Redirects: {report['redirects']}    TTFB: {report['ttfb_ms']} ms")
    out.append(f"  Analizado:     {report['analyzed_at']}")
    out.append("")

    if protection:
        out.append(_color(f"  ⚠  ANÁLISIS BLOQUEADO POR {protection['name'].upper()}", BOLD + RED, use_color))
        out.append(f"  Evidencia: {protection['evidence']}")
        out.append("")
        out.append("  El HTML recibido es la página de challenge del WAF, no tu sitio real.")
        out.append("  Cualquier score aquí sería engañoso, así que se omite.")
        out.append("")
        out.append(_color("─" * 70, DIM, use_color))
        out.append(_color("  CÓMO CONTINUAR", BOLD, use_color))
        out.append(_color("─" * 70, DIM, use_color))
        for issue in report["issues"]:
            out.append(f"  → {issue['recommendation']}")
        out.append("")
        out.append(_color("═" * 70, CYAN, use_color))
        return "\n".join(out)

    grade_color = GREEN if overall >= 80 else YELLOW if overall >= 60 else RED
    out.append(_color(f"  SCORE GLOBAL: {overall}/100   GRADE: {grade}", BOLD + grade_color, use_color))
    out.append("")
    out.append(_color("  Desglose por categoría:", BOLD, use_color))
    for cat, info in score["categories"].items():
        bar = _bar(info["score"])
        out.append(f"    {cat:<12} {info['score']:>3}/100  {bar}  ({info['issue_count']} problemas)")
    out.append("")

    counts = score["severity_counts"]
    out.append(
        "  Problemas: "
        + _color(f"{counts.get('critical', 0)} críticos", RED + BOLD, use_color) + ", "
        + _color(f"{counts.get('high', 0)} altos", RED, use_color) + ", "
        + _color(f"{counts.get('medium', 0)} medios", YELLOW, use_color) + ", "
        + _color(f"{counts.get('low', 0)} bajos", CYAN, use_color)
    )
    out.append("")
    out.append(_color("─" * 70, DIM, use_color))
    out.append(_color("  RECOMENDACIONES PRIORIZADAS", BOLD, use_color))
    out.append(_color("─" * 70, DIM, use_color))

    issues = report["issues"]
    if not issues:
        out.append(_color("  ¡Sin problemas detectados! 🎉", GREEN, use_color))
    else:
        for idx, issue in enumerate(issues, 1):
            sev = issue["severity"]
            tag = _color(f"[{SEVERITY_LABEL[sev]}]", SEVERITY_COLOR[sev], use_color)
            out.append(f"  {idx:>2}. {tag} ({issue['category']}) {issue['message']}")
            out.append(f"      → {issue['recommendation']}")
            if issue.get("evidence"):
                evidence = issue["evidence"]
                if len(evidence) > 120:
                    evidence = evidence[:117] + "..."
                out.append(_color(f"      evidencia: {evidence}", DIM, use_color))
            out.append("")

    out.append(_color("═" * 70, CYAN, use_color))
    return "\n".join(out)


def _bar(score: int, width: int = 20) -> str:
    filled = int(round(score / 100 * width))
    return "█" * filled + "░" * (width - filled)


def render_json(report: dict, indent: int = 2) -> str:
    return json.dumps(report, indent=indent, ensure_ascii=False)


def write_output(report: dict, fmt: str, output_path: str | None) -> None:
    if fmt == "json":
        content = render_json(report)
    else:
        content = render_console(report, use_color=output_path is None and sys.stdout.isatty())

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
    else:
        print(content)
