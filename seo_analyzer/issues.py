from dataclasses import dataclass, asdict
from typing import Literal

Severity = Literal["critical", "high", "medium", "low", "info"]
Category = Literal["onpage", "technical", "performance"]

SEVERITY_WEIGHT: dict[str, int] = {
    "critical": 15,
    "high": 8,
    "medium": 4,
    "low": 1,
    "info": 0,
}


@dataclass
class Issue:
    code: str
    category: Category
    severity: Severity
    message: str
    recommendation: str
    evidence: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
