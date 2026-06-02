"""
Auto-fixer: applies safe, mechanical corrections to a list of source lines.

Safe fixes (applied automatically):
  - SQL keywords → UPPER CASE
  - IFNULL → COALESCE
  - Standalone pandas import → pyspark.pandas
  - Tab indentation → 4 spaces
  - Column aliases snake_case → PascalCase (AS alias)
  - View names missing v_ prefix get it added
  - Temp view names missing tv_ prefix get it added
"""
import re
from typing import List

from .rules.sql_rules import _KEYWORD_PATTERN
from .rules.naming_rules import _AS_ALIAS_RE, _CREATE_VIEW_RE, _CREATE_TABLE_RE, _VALID_WORD_ALIASES, _bare, _to_pascal

_SQL_KEYWORDS_UPPER = {
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
    "DATEDIFF", "DATE_ADD", "DATE_SUB", "ADD_MONTHS", "TRUNC",
    "RPAD", "LPAD", "SPLIT", "EXPLODE", "COLLECT_LIST", "COLLECT_SET",
    "ARRAY_CONTAINS", "SIZE", "STRUCT", "MAP", "NAMED_STRUCT",
    "INTERVAL", "EXTRACT",
}

_KEYWORD_RE = re.compile(
    r'(?<![.\w])(' + '|'.join(re.escape(k) for k in sorted(_SQL_KEYWORDS_UPPER, key=len, reverse=True)) + r')(?![\w])',
    re.IGNORECASE,
)


def _is_comment(line: str) -> bool:
    s = line.strip()
    return s.startswith('--') or s.startswith('#')


def _is_magic(line: str) -> bool:
    return line.strip().startswith('%')


def _fix_keyword_case(line: str) -> str:
    """Uppercase all SQL keywords in a line."""
    def repl(m: re.Match) -> str:
        return m.group(1).upper()
    return _KEYWORD_RE.sub(repl, line)


def _fix_ifnull(line: str) -> str:
    return re.sub(r'\bIFNULL\b', 'COALESCE', line, flags=re.IGNORECASE)


def _fix_pandas_import(line: str) -> str:
    line = re.sub(r'\bimport\s+pandas\s+as\s+\w+', 'import pyspark.pandas as ps', line)
    line = re.sub(r'\bimport\s+pandas\b', 'import pyspark.pandas as ps', line)
    return line


def _fix_tab_indent(line: str) -> str:
    return line.replace('\t', '    ')


def _fix_column_aliases(line: str) -> str:
    """Convert snake_case AS aliases to PascalCase."""
    def repl(m: re.Match) -> str:
        alias = m.group(1).strip('`"\'')
        if alias.lower() in _VALID_WORD_ALIASES:
            return m.group(0)
        if '_' in alias:
            return m.group(0).replace(alias, _to_pascal(alias))
        if alias and alias[0].islower():
            return m.group(0).replace(alias, alias[0].upper() + alias[1:])
        return m.group(0)
    return _AS_ALIAS_RE.sub(repl, line)


def _fix_view_prefix(line: str) -> str:
    """Add v_ or tv_ prefix to CREATE VIEW / CREATE TEMPORARY VIEW statements."""
    match = _CREATE_VIEW_RE.search(line)
    if not match:
        return line
    is_temp = match.group(1) is not None
    view_ref = match.group(2)
    bare = _bare(view_ref)
    prefix = 'tv_' if is_temp else 'v_'
    if not bare.lower().startswith(prefix):
        new_bare = (prefix + bare).lower()
        line = line.replace(bare, new_bare, 1)
    elif bare != bare.lower():
        line = line.replace(bare, bare.lower(), 1)
    return line


def _fix_table_name_case(line: str) -> str:
    match = _CREATE_TABLE_RE.search(line)
    if not match:
        return line
    table_ref = match.group(1)
    bare = _bare(table_ref)
    if bare != bare.lower():
        line = line.replace(bare, bare.lower(), 1)
    return line


def fix_lines(lines: List[str], is_python: bool = False) -> List[str]:
    """
    Apply all safe auto-fixes to a list of source lines.
    Returns a new list of fixed lines.
    """
    fixed: List[str] = []
    for line in lines:
        orig = line
        if not _is_comment(line) and not _is_magic(line):
            if is_python:
                line = _fix_tab_indent(line)
                line = _fix_pandas_import(line)
            else:
                line = _fix_keyword_case(line)
                line = _fix_ifnull(line)
                line = _fix_column_aliases(line)
                line = _fix_view_prefix(line)
                line = _fix_table_name_case(line)
        fixed.append(line)
    return fixed
