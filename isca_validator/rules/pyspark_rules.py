"""
PySpark coding standards per ISCA Data Engineering Standards (Section 4).
"""
import re
from typing import List

from .models import Violation


def _is_comment(line: str) -> bool:
    return line.strip().startswith('#')


def check_wildcard_imports(lines: List[str]) -> List[Violation]:
    """PY-01 — Avoid wildcard imports; call out functions explicitly."""
    violations = []
    for i, line in enumerate(lines, 1):
        if _is_comment(line):
            continue
        if re.search(r'\bfrom\s+\S+\s+import\s+\*', line):
            violations.append(Violation(
                line_no=i,
                rule_id="PY-01",
                severity="error",
                message="Wildcard import ('import *') is not allowed.",
                suggestion=(
                    "Explicitly list the functions you need. "
                    "E.g.: from pyspark.sql.functions import col, split"
                ),
                original_text=line.rstrip(),
            ))
    return violations


def check_pandas_import(lines: List[str]) -> List[Violation]:
    """PY-02 — Use pyspark.pandas, not standalone pandas."""
    violations = []
    for i, line in enumerate(lines, 1):
        if _is_comment(line):
            continue
        # Flag 'import pandas' or 'from pandas import' when pyspark is not part of it
        if re.search(r'\bimport\s+pandas\b', line) or re.search(r'\bfrom\s+pandas\b', line):
            fixed = re.sub(r'\bimport\s+pandas\b', 'import pyspark.pandas as ps', line)
            fixed = re.sub(r'\bfrom\s+pandas\b', 'from pyspark.pandas', fixed)
            violations.append(Violation(
                line_no=i,
                rule_id="PY-02",
                severity="error",
                message="Standalone 'pandas' import is not allowed; use the PySpark Pandas API.",
                suggestion="Replace 'import pandas as pd' with 'import pyspark.pandas as ps'.",
                original_text=line.rstrip(),
                fixed_text=fixed.rstrip(),
            ))
    return violations


def check_indentation(lines: List[str]) -> List[Violation]:
    """PY-03 — Use 4 spaces per indentation level (no tabs, no 2-space indent)."""
    violations = []
    for i, line in enumerate(lines, 1):
        if not line.rstrip():
            continue
        # Detect tab indentation
        if line.startswith('\t'):
            violations.append(Violation(
                line_no=i,
                rule_id="PY-03",
                severity="error",
                message="Tab indentation detected; use 4 spaces per indent level.",
                suggestion="Replace each tab character with 4 spaces.",
                original_text=line.rstrip(),
                fixed_text=line.rstrip().replace('\t', '    '),
            ))
            continue
        # Detect 2-space indentation (leading spaces not multiple of 4)
        leading = len(line) - len(line.lstrip(' '))
        if leading > 0 and leading % 4 != 0:
            violations.append(Violation(
                line_no=i,
                rule_id="PY-03",
                severity="warning",
                message=f"Indentation of {leading} space(s) is not a multiple of 4.",
                suggestion="Use exactly 4 spaces per indentation level.",
                original_text=line.rstrip(),
            ))
    return violations


class PySparkRules:
    """Aggregates all PySpark checks."""

    _checks = [
        check_wildcard_imports,
        check_pandas_import,
        check_indentation,
    ]

    def run(self, lines: List[str]) -> List[Violation]:
        results: List[Violation] = []
        for check in self._checks:
            results.extend(check(lines))
        return sorted(results, key=lambda v: v.line_no)
