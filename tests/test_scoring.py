from seo_analyzer.issues import Issue
from seo_analyzer.scoring import grade, prioritize, score_report


def issue(code, category, severity):
    return Issue(code=code, category=category, severity=severity, message="m", recommendation="r")


def test_score_empty_is_100():
    report = score_report([])
    assert report["overall_score"] == 100
    assert report["grade"] == "A"
    assert report["total_issues"] == 0


def test_critical_onpage_drops_score():
    report = score_report([issue("title_missing", "onpage", "critical")])
    assert report["categories"]["onpage"]["score"] == 85
    assert report["overall_score"] < 100


def test_prioritize_orders_by_severity():
    issues = [
        issue("a", "onpage", "low"),
        issue("b", "technical", "critical"),
        issue("c", "onpage", "high"),
    ]
    ordered = prioritize(issues)
    assert [i.severity for i in ordered] == ["critical", "high", "low"]


def test_grade_thresholds():
    assert grade(95) == "A"
    assert grade(85) == "B"
    assert grade(75) == "C"
    assert grade(65) == "D"
    assert grade(50) == "F"


def test_floored_at_zero():
    many = [issue(f"x{i}", "onpage", "critical") for i in range(20)]
    report = score_report(many)
    assert report["categories"]["onpage"]["score"] == 0
