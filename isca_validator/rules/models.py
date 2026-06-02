from dataclasses import dataclass, field


@dataclass
class Violation:
    line_no: int
    rule_id: str
    severity: str       # "error" | "warning"
    message: str
    suggestion: str
    original_text: str = ""
    fixed_text: str = ""

    def __str__(self) -> str:
        parts = [
            f"  [{self.severity.upper()}] Line {self.line_no} | {self.rule_id}",
            f"  Message   : {self.message}",
            f"  Suggestion: {self.suggestion}",
        ]
        if self.original_text:
            parts.append(f"  Code      : {self.original_text.strip()}")
        if self.fixed_text:
            parts.append(f"  Fixed     : {self.fixed_text.strip()}")
        return "\n".join(parts)
