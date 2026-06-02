"""
Spark SQL coding standards per ISCA Data Engineering Standards (Section 3).
"""
import re
from typing import List

from .models import Violation

# All SQL keywords that must appear in UPPER CASE
_SQL_KEYWORDS = {
    "SELECT", "FROM", "WHERE", "JOIN", "LEFT", "RIGHT", "INNER", "OUTER",
    "FULL", "CROSS", "ON", "AND", "OR", "NOT", "IN", "IS", "NULL", "AS",
    "DISTINCT", "GROUP", "BY", "ORDER", "HAVING", "LIMIT", "UNION", "ALL",
    "INSERT", "INTO", "OVERWRITE", "TABLE", "CREATE", "DROP", "ALTER",
    "WITH", "CASE", "WHEN", "THEN", "ELSE", "END", "CAST", "COALESCE",
    "TRIM", "LTRIM", "RTRIM", "TO_DATE", "DATE_FORMAT", "SET", "VALUES",
    "UPDATE", "DELETE", "TRUNCATE", "VIEW", "TEMPORARY", "TEMP", "EXISTS",
    "BETWEEN", "LIKE", "ILIKE", "ASC", "DESC", "PARTITION", "OVER",
    "WINDOW", "ROW", "ROWS", "RANGE", "PRECEDING", "FOLLOWING", "CURRENT",
    "ROW_NUMBER", "RANK", "DENSE_RANK", "LAG", "LEAD", "SUM", "COUNT",
    "AVG", "MIN", "MAX", "FIRST", "LAST", "NVL", "NVL2", "DECODE",
    "NULLIF", "GREATEST", "LEAST", "REPLACE", "USING", "IF", "IFNULL",
    "CONCAT", "SUBSTR", "SUBSTRING", "LENGTH", "UPPER", "LOWER", "ROUND",
    "FLOOR", "CEIL", "CEILING", "ABS", "YEAR", "MONTH", "DAY", "HOUR",
    "MINUTE", "SECOND", "NOW", "CURRENT_DATE", "CURRENT_TIMESTAMP",
    "DATEDIFF", "DATE_ADD", "DATE_SUB", "ADD_MONTHS", "TRUNC", "RPAD",
    "LPAD", "SPLIT", "EXPLODE", "COLLECT_LIST", "COLLECT_SET",
    "ARRAY_CONTAINS", "SIZE", "STRUCT", "MAP", "NAMED_STRUCT",
    "INTERVAL", "EXTRACT", "TYPEOF", "TYPEOF",
}

_KEYWORD_PATTERN = re.compile(
    r'(?<![.\w])(' + '|'.join(re.escape(k) for k in sorted(_SQL_KEYWORDS, key=len, reverse=True)) + r')(?![\w])',
    re.IGNORECASE,
)

_SINGLE_LETTER_ALIAS = re.compile(
    r'\b(?:FROM|JOIN)\s+\S+\s+(?:AS\s+)?([A-Za-z])\b(?!\w)',
    re.IGNORECASE,
)

_AS_ALIAS = re.compile(r'\bAS\s+([A-Za-z_][A-Za-z0-9_]*)\b', re.IGNORECASE)

_TABLE_WORD_ALIASES = {
    "one", "two", "three", "four", "five",
    "six", "seven", "eight", "nine", "ten",
}


def _is_comment(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith('--') or stripped.startswith('#')


def _is_magic_cmd(line: str) -> bool:
    """Skip Databricks magic commands like %sql, %python, %run."""
    return line.strip().startswith('%')


def check_select_star(lines: List[str]) -> List[Violation]:
    """SQL-01 — Do not use SELECT *."""
    violations = []
    for i, line in enumerate(lines, 1):
        if _is_comment(line) or _is_magic_cmd(line):
            continue
        if re.search(r'\bSELECT\s+\*', line, re.IGNORECASE):
            violations.append(Violation(
                line_no=i,
                rule_id="SQL-01",
                severity="error",
                message="SELECT * is not allowed.",
                suggestion="Explicitly list each required column name.",
                original_text=line.rstrip(),
            ))
    return violations


def check_keyword_case(lines: List[str]) -> List[Violation]:
    """SQL-02 — SQL keywords must be UPPER CASE."""
    violations = []
    for i, line in enumerate(lines, 1):
        if _is_comment(line) or _is_magic_cmd(line):
            continue
        for match in _KEYWORD_PATTERN.finditer(line):
            word = match.group(1)
            if word != word.upper():
                fixed_line = line[:match.start(1)] + word.upper() + line[match.end(1):]
                violations.append(Violation(
                    line_no=i,
                    rule_id="SQL-02",
                    severity="error",
                    message=f"SQL keyword '{word}' must be UPPER CASE.",
                    suggestion=f"Change '{word}' to '{word.upper()}'.",
                    original_text=line.rstrip(),
                    fixed_text=fixed_line.rstrip(),
                ))
                break  # one violation per line (the fixer handles all in that line)
    return violations


def check_order_by_numbers(lines: List[str]) -> List[Violation]:
    """SQL-03 — Do not use column position numbers in ORDER BY."""
    violations = []
    order_by_pattern = re.compile(r'\bORDER\s+BY\s+([\d\s,]+)(?:ASC|DESC|$|\n)', re.IGNORECASE)
    for i, line in enumerate(lines, 1):
        if _is_comment(line) or _is_magic_cmd(line):
            continue
        match = order_by_pattern.search(line)
        if match:
            nums = [p.strip() for p in match.group(1).split(',') if p.strip().isdigit()]
            if nums:
                violations.append(Violation(
                    line_no=i,
                    rule_id="SQL-03",
                    severity="error",
                    message=f"ORDER BY uses column position number(s): {', '.join(nums)}.",
                    suggestion="Replace positional numbers with explicit column names.",
                    original_text=line.rstrip(),
                ))
    return violations


def check_schema_prefix(lines: List[str]) -> List[Violation]:
    """SQL-04 — Always add schema prefix to table references."""
    violations = []
    from_join_re = re.compile(r'\b(FROM|JOIN)\s+(`?)([A-Za-z_][A-Za-z0-9_]*)(`?)', re.IGNORECASE)
    for i, line in enumerate(lines, 1):
        if _is_comment(line) or _is_magic_cmd(line):
            continue
        for match in from_join_re.finditer(line):
            table_ref = match.group(3)
            # Skip temp views (tv_) and CTEs — they have no schema by design
            if table_ref.lower().startswith('tv_'):
                continue
            # Check if a dot follows (schema.table)
            after = line[match.end():]
            if not after.lstrip().startswith('.') and '.' not in match.group(0):
                violations.append(Violation(
                    line_no=i,
                    rule_id="SQL-04",
                    severity="warning",
                    message=f"Table '{table_ref}' referenced without a schema prefix.",
                    suggestion=f"Add schema prefix: e.g., 's_isca.{table_ref}' or 'b_um_isca.{table_ref}'.",
                    original_text=line.rstrip(),
                ))
    return violations


def check_ifnull(lines: List[str]) -> List[Violation]:
    """SQL-05 — Use COALESCE instead of IFNULL."""
    violations = []
    for i, line in enumerate(lines, 1):
        if _is_comment(line) or _is_magic_cmd(line):
            continue
        if re.search(r'\bIFNULL\b', line, re.IGNORECASE):
            fixed = re.sub(r'\bIFNULL\b', 'COALESCE', line, flags=re.IGNORECASE)
            violations.append(Violation(
                line_no=i,
                rule_id="SQL-05",
                severity="error",
                message="IFNULL is not allowed; use COALESCE instead.",
                suggestion="Replace IFNULL(expr, val) with COALESCE(expr, val).",
                original_text=line.rstrip(),
                fixed_text=fixed.rstrip(),
            ))
    return violations


def check_ltrim_rtrim_together(lines: List[str]) -> List[Violation]:
    """SQL-06 — Use TRIM; avoid LTRIM and RTRIM used together."""
    violations = []
    for i, line in enumerate(lines, 1):
        if _is_comment(line) or _is_magic_cmd(line):
            continue
        has_ltrim = bool(re.search(r'\bLTRIM\b', line, re.IGNORECASE))
        has_rtrim = bool(re.search(r'\bRTRIM\b', line, re.IGNORECASE))
        if has_ltrim and has_rtrim:
            violations.append(Violation(
                line_no=i,
                rule_id="SQL-06",
                severity="error",
                message="LTRIM and RTRIM used together on the same line.",
                suggestion="Use TRIM(expr) instead of LTRIM(RTRIM(expr)).",
                original_text=line.rstrip(),
            ))
    return violations


def check_drop_create_table(lines: List[str]) -> List[Violation]:
    """SQL-07 — Do not DROP and CREATE TABLE; use INSERT OVERWRITE TABLE."""
    violations = []
    # Use ''.join so lines that already end in \n don't accumulate extra newlines
    full_text = ''.join(lines)
    for match in re.finditer(r'\bDROP\s+TABLE\b', full_text, re.IGNORECASE):
        line_no = full_text[:match.start()].count('\n') + 1
        violations.append(Violation(
            line_no=line_no,
            rule_id="SQL-07",
            severity="error",
            message="DROP TABLE is not allowed in scripts.",
            suggestion="Use INSERT OVERWRITE TABLE instead of DROP TABLE + CREATE TABLE.",
            original_text=lines[line_no - 1].rstrip(),
        ))
    drop_positions = [m.start() for m in re.finditer(r'\bDROP\s+TABLE\b', full_text, re.IGNORECASE)]
    for match in re.finditer(r'\bCREATE\s+(?:OR\s+REPLACE\s+)?TABLE\b', full_text, re.IGNORECASE):
        line_no = full_text[:match.start()].count('\n') + 1
        # Only flag if a DROP TABLE actually precedes this CREATE TABLE in the file
        if any(drop_pos < match.start() for drop_pos in drop_positions):
            violations.append(Violation(
                line_no=line_no,
                rule_id="SQL-07",
                severity="error",
                message="CREATE TABLE following DROP TABLE is not allowed.",
                suggestion="Use INSERT OVERWRITE TABLE instead.",
                original_text=lines[line_no - 1].rstrip(),
            ))
    return violations


def check_single_letter_aliases(lines: List[str]) -> List[Violation]:
    """SQL-08 — Do not use single-letter table aliases (a, b, x, y…); use one, two, three…"""
    violations = []
    for i, line in enumerate(lines, 1):
        if _is_comment(line) or _is_magic_cmd(line):
            continue
        for match in _SINGLE_LETTER_ALIAS.finditer(line):
            alias = match.group(1)
            if alias.upper() not in _SQL_KEYWORDS:
                violations.append(Violation(
                    line_no=i,
                    rule_id="SQL-08",
                    severity="error",
                    message=f"Single-letter table alias '{alias}' is not allowed.",
                    suggestion="Use descriptive word aliases: 'one', 'two', 'three', etc.",
                    original_text=line.rstrip(),
                ))
    return violations


def check_unqualified_select_columns(lines: List[str]) -> List[Violation]:
    """SQL-09 — Always qualify column names in SELECT with a table alias."""
    violations = []
    in_select = False
    select_lines: List[int] = []

    for i, line in enumerate(lines, 1):
        if _is_comment(line) or _is_magic_cmd(line):
            continue
        upper = line.upper().strip()
        if re.match(r'^SELECT\b', upper):
            in_select = True
        if in_select and re.match(r'^FROM\b', upper):
            in_select = False
        if in_select:
            # Look for column expressions not prefixed by alias.
            # Heuristic: flag lines that have a bare WORD (no dot) not matching a function call
            tokens = re.findall(r'\b([A-Za-z_][A-Za-z0-9_]*)\s*(?=[,\n]|$)', line)
            for tok in tokens:
                if tok.upper() in _SQL_KEYWORDS:
                    continue
                if '.' not in line and not re.search(r'\w+\s*\(', line):
                    violations.append(Violation(
                        line_no=i,
                        rule_id="SQL-09",
                        severity="warning",
                        message="Column reference appears unqualified (no table alias prefix).",
                        suggestion="Qualify with table alias: e.g., 'one.ColumnName'.",
                        original_text=line.rstrip(),
                    ))
                    break
    return violations


def check_intermediate_tables(lines: List[str]) -> List[Violation]:
    """SQL-10 — Avoid intermediate tables; use temporary views (tv_) instead."""
    violations = []
    create_table_re = re.compile(
        r'\bCREATE\s+(?:OR\s+REPLACE\s+)?TABLE\s+(\S+)', re.IGNORECASE
    )
    for i, line in enumerate(lines, 1):
        if _is_comment(line) or _is_magic_cmd(line):
            continue
        match = create_table_re.search(line)
        if match:
            table_name = match.group(1).strip('`"\'();')
            bare = table_name.split('.')[-1]
            # If not a DDL notebook file (heuristic: flag tables that look intermediate)
            if not bare.endswith('_ddl') and not bare.lower().startswith('tv_'):
                violations.append(Violation(
                    line_no=i,
                    rule_id="SQL-10",
                    severity="warning",
                    message=f"Consider replacing intermediate table '{bare}' with a temporary view.",
                    suggestion=f"Use CREATE TEMPORARY VIEW tv_{bare} AS ... instead.",
                    original_text=line.rstrip(),
                ))
    return violations


def check_udf_usage(lines: List[str]) -> List[Violation]:
    """SQL-11 — Avoid User Defined Functions (UDFs)."""
    violations = []
    udf_re = re.compile(r'\bCREATE\s+(?:OR\s+REPLACE\s+)?(?:TEMPORARY\s+)?FUNCTION\b', re.IGNORECASE)
    for i, line in enumerate(lines, 1):
        if _is_comment(line) or _is_magic_cmd(line):
            continue
        if udf_re.search(line):
            violations.append(Violation(
                line_no=i,
                rule_id="SQL-11",
                severity="warning",
                message="UDF definition detected.",
                suggestion="Avoid UDFs; use built-in Databricks/Spark SQL functions instead. "
                           "Only create UDFs when the requirement cannot be met with built-in functions.",
                original_text=line.rstrip(),
            ))
    return violations


def check_insert_overwrite(lines: List[str]) -> List[Violation]:
    """SQL-12 — Use INSERT OVERWRITE TABLE rather than repeated CREATE TABLE."""
    violations = []
    for i, line in enumerate(lines, 1):
        if _is_comment(line) or _is_magic_cmd(line):
            continue
        # Flag bare INSERT INTO that is not INSERT OVERWRITE
        if re.search(r'\bINSERT\s+INTO\b(?!\s+OVERWRITE)', line, re.IGNORECASE):
            violations.append(Violation(
                line_no=i,
                rule_id="SQL-12",
                severity="warning",
                message="INSERT INTO detected; prefer INSERT OVERWRITE TABLE for idempotent loads.",
                suggestion="Use INSERT OVERWRITE TABLE <schema.table> SELECT ... instead.",
                original_text=line.rstrip(),
            ))
    return violations


class SQLRules:
    """Aggregates all Spark SQL checks."""

    _checks = [
        check_select_star,
        check_keyword_case,
        check_order_by_numbers,
        check_schema_prefix,
        check_ifnull,
        check_ltrim_rtrim_together,
        check_drop_create_table,
        check_single_letter_aliases,
        check_unqualified_select_columns,
        check_intermediate_tables,
        check_udf_usage,
        check_insert_overwrite,
    ]

    def run(self, lines: List[str]) -> List[Violation]:
        results: List[Violation] = []
        for check in self._checks:
            results.extend(check(lines))
        return sorted(results, key=lambda v: v.line_no)
