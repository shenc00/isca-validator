"""
Main orchestrator: loads a notebook, runs all applicable rule sets,
produces a report and an auto-fixed version of the script.
"""
import os
import json
from typing import List, Tuple

from .rules.models import Violation
from .rules.sql_rules import SQLRules
from .rules.naming_rules import NamingRules
from .rules.pyspark_rules import PySparkRules
from .reporter import build_report
from .fixer import fix_lines


def _read_lines(path: str) -> Tuple[List[str], bool]:
    """
    Read source lines from a .sql, .py, or Databricks .ipynb notebook.
    Returns (lines, is_python).
    """
    ext = os.path.splitext(path)[1].lower()
    if ext == ".ipynb":
        return _read_ipynb(path)
    with open(path, encoding="utf-8") as fh:
        lines = fh.readlines()
    is_python = ext == ".py"
    return lines, is_python


def _read_ipynb(path: str) -> Tuple[List[str], bool]:
    """Extract source lines from a Jupyter/Databricks notebook (.ipynb)."""
    with open(path, encoding="utf-8") as fh:
        nb = json.load(fh)

    all_lines: List[str] = []
    is_python = False
    kernel = nb.get("metadata", {}).get("kernelspec", {}).get("language", "").lower()
    if kernel in ("python", "python3"):
        is_python = True

    for cell in nb.get("cells", []):
        cell_type = cell.get("cell_type", "")
        source = cell.get("source", [])
        if isinstance(source, str):
            source = source.splitlines(keepends=True)
        if cell_type in ("code", "markdown"):
            all_lines.extend(source)
            if source and not source[-1].endswith('\n'):
                all_lines.append('\n')

    return all_lines, is_python


class Validator:
    def __init__(self, path: str):
        self.path = path
        self.lines, self.is_python = _read_lines(path)

    def validate(self) -> List[Violation]:
        """Run all applicable rules and return a flat list of violations."""
        violations: List[Violation] = []

        if self.is_python:
            violations.extend(PySparkRules().run(self.lines))
            # PySpark files can also contain embedded SQL strings — run SQL rules too
            violations.extend(SQLRules().run(self.lines))
            violations.extend(NamingRules().run(self.lines))
        else:
            violations.extend(SQLRules().run(self.lines))
            violations.extend(NamingRules().run(self.lines))

        return sorted(violations, key=lambda v: (v.line_no, v.rule_id))

    def report(self) -> str:
        violations = self.validate()
        return build_report(violations, source_file=self.path)

    def fix(self) -> str:
        """Return the auto-corrected script as a single string."""
        return "".join(fix_lines(self.lines, is_python=self.is_python))

    def save_fixed(self, output_path: str | None = None) -> str:
        """Write the fixed script to output_path (or <orig>_fixed.<ext>) and return the path."""
        if output_path is None:
            base, ext = os.path.splitext(self.path)
            output_path = f"{base}_fixed{ext}"
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(self.fix())
        return output_path
