from .issues import SEVERITY_WEIGHT, Issue


def score_report(issues: list[Issue]) -> dict:
    """Compute a 0-100 SEO score and per-category breakdown.

    Each category starts at 100 and loses points per issue weighted by severity, floored at 0.
    The global score is the weighted average across categories actually evaluated.
    """
    categories = ("onpage", "technical", "performance")
    by_cat: dict[str, list[Issue]] = {c: [] for c in categories}
    for issue in issues:
        by_cat.setdefault(issue.category, []).append(issue)

    breakdown: dict[str, dict] = {}
    for cat in categories:
        cat_issues = by_cat[cat]
        deductions = sum(SEVERITY_WEIGHT.get(i.severity, 0) for i in cat_issues)
        score = max(0, 100 - deductions)
        breakdown[cat] = {
            "score": score,
            "deductions": deductions,
            "issue_count": len(cat_issues),
        }

    weights = {"onpage": 0.45, "technical": 0.35, "performance": 0.20}
    total_weight = 0.0
    weighted_sum = 0.0
    for cat, info in breakdown.items():
        if info["issue_count"] == 0 and cat == "performance":
            continue
        w = weights[cat]
        weighted_sum += info["score"] * w
        total_weight += w
    overall = round(weighted_sum / total_weight) if total_weight else 0

    severity_counts = {sev: 0 for sev in SEVERITY_WEIGHT}
    for i in issues:
        severity_counts[i.severity] = severity_counts.get(i.severity, 0) + 1

    return {
        "overall_score": overall,
        "grade": grade(overall),
        "categories": breakdown,
        "severity_counts": severity_counts,
        "total_issues": len(issues),
    }


def grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def prioritize(issues: list[Issue]) -> list[Issue]:
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    return sorted(issues, key=lambda i: (order.get(i.severity, 9), i.category, i.code))
