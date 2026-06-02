"""
Formats validation results into a human-readable report.
"""
from typing import List, Dict
from .rules.models import Violation


_SEVERITY_ORDER = {"error": 0, "warning": 1}

_RULE_DOCS: Dict[str, str] = {
    # SQL rules
    "SQL-01": "Do not use SELECT *; explicitly list column names. [Sec.3]",
    "SQL-02": "SQL keywords must be UPPER CASE. [Sec.3]",
    "SQL-03": "Do not use column position numbers in ORDER BY. [Sec.3]",
    "SQL-04": "Always add schema prefix to table references (e.g. s_isca.table). [Sec.3]",
    "SQL-05": "Use COALESCE instead of IFNULL. [Sec.3]",
    "SQL-06": "Use TRIM; do not use LTRIM and RTRIM together. [Sec.3]",
    "SQL-07": "Do not DROP and CREATE TABLE; use INSERT OVERWRITE TABLE. [Sec.3]",
    "SQL-08": "Do not use single-letter table aliases (a, b, x, y); use one, two, three. [Sec.3]",
    "SQL-09": "Always qualify column names in SELECT with a table alias. [Sec.3]",
    "SQL-10": "Avoid intermediate tables; use temporary views (tv_) instead. [Sec.3]",
    "SQL-11": "Avoid UDFs; use built-in Databricks functions. [Sec.3]",
    "SQL-12": "Prefer INSERT OVERWRITE TABLE for idempotent data loads. [Sec.3]",
    # Naming rules
    "NAME-COL-01": "Column alias cannot exceed 255 characters. [Sec.2b]",
    "NAME-COL-02": "Column alias must not contain special characters. [Sec.2b]",
    "NAME-COL-03": "Column alias must use PascalCase, not snake_case. [Sec.2b]",
    "NAME-COL-04": "Column alias must start with an uppercase letter (PascalCase). [Sec.2b]",
    "NAME-VIEW-01": "View name must start with 'v_'. [Sec.2c]",
    "NAME-VIEW-02": "View name must be fully lowercase. [Sec.2c]",
    "NAME-TMPVIEW-01": "Temporary view name must start with 'tv_'. [Sec.2d]",
    "NAME-TMPVIEW-02": "Temporary view name must be fully lowercase. [Sec.2d]",
    "NAME-TBL-01": "Table name must be lowercase. [Sec.2a]",
    "NAME-TBL-02": "Table name must use only a-z, 0-9, and underscores. [Sec.2a]",
    # PySpark rules
    "PY-01": "Wildcard imports are not allowed; list functions explicitly. [Sec.4]",
    "PY-02": "Use pyspark.pandas instead of standalone pandas. [Sec.4]",
    "PY-03": "Use 4 spaces per indentation level; no tabs. [Sec.4]",
}


def build_report(violations: List[Violation], source_file: str = "") -> str:
    if not violations:
        return _header(source_file) + "\n  No violations found. Script conforms to ISCA standards.\n"

    errors = [v for v in violations if v.severity == "error"]
    warnings = [v for v in violations if v.severity == "warning"]

    lines: List[str] = [_header(source_file)]
    lines.append(
        f"  Summary: {len(errors)} error(s), {len(warnings)} warning(s) "
        f"across {len(violations)} violation(s)\n"
    )

    if errors:
        lines.append("=" * 70)
        lines.append("  ERRORS")
        lines.append("=" * 70)
        for v in sorted(errors, key=lambda x: x.line_no):
            lines.append(_format_violation(v))

    if warnings:
        lines.append("=" * 70)
        lines.append("  WARNINGS")
        lines.append("=" * 70)
        for v in sorted(warnings, key=lambda x: x.line_no):
            lines.append(_format_violation(v))

    lines.append("=" * 70)
    lines.append("  RULE REFERENCE")
    lines.append("=" * 70)
    seen_rules = sorted({v.rule_id for v in violations})
    for rule_id in seen_rules:
        doc = _RULE_DOCS.get(rule_id, "See ISCA Data Engineering Standards document.")
        lines.append(f"  {rule_id:<22} {doc}")

    return "\n".join(lines) + "\n"


def _header(source_file: str) -> str:
    sep = "=" * 70
    title = "  ISCA Data Engineering Standards — Validation Report"
    if source_file:
        title += f"\n  File: {source_file}"
    return f"\n{sep}\n{title}\n{sep}\n"


def _format_violation(v: Violation) -> str:
    parts = [
        f"\n  [{v.severity.upper():7}] Line {v.line_no:>4} | {v.rule_id}",
        f"  Message   : {v.message}",
        f"  Suggestion: {v.suggestion}",
    ]
    if v.original_text:
        parts.append(f"  Code      : {v.original_text.strip()}")
    if v.fixed_text:
        parts.append(f"  Fixed     : {v.fixed_text.strip()}")
    return "\n".join(parts)
