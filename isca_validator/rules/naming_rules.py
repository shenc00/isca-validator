"""
Naming convention rules per ISCA Data Engineering Standards (Section 2).
"""
import re
from typing import List, Optional

from .models import Violation

_VALID_WORD_ALIASES = {
    "one", "two", "three", "four", "five",
    "six", "seven", "eight", "nine", "ten",
}

_AS_ALIAS_RE = re.compile(r'\bAS\s+([A-Za-z_`"][A-Za-z0-9_`"]*)', re.IGNORECASE)
_CREATE_VIEW_RE = re.compile(
    r'\bCREATE\s+(?:OR\s+REPLACE\s+)?(?:(TEMPORARY|TEMP)\s+)?VIEW\s+([^\s(]+)',
    re.IGNORECASE,
)
_CREATE_TABLE_RE = re.compile(
    r'\bCREATE\s+(?:OR\s+REPLACE\s+)?TABLE\s+([^\s(]+)',
    re.IGNORECASE,
)


def _bare(name: str) -> str:
    """Strip schema prefix and quoting."""
    return name.split('.')[-1].strip('`"\' ;()')


def _to_pascal(snake: str) -> str:
    return ''.join(w.capitalize() for w in snake.split('_'))


def _is_comment(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith('--') or stripped.startswith('#')


def _is_magic_cmd(line: str) -> bool:
    return line.strip().startswith('%')


# ---------------------------------------------------------------------------
# Column (AS alias) naming
# ---------------------------------------------------------------------------

def _check_column_name(alias: str, line_no: int) -> Optional[Violation]:
    """Columns must be PascalCase, no special chars, max 255."""
    if len(alias) > 255:
        return Violation(
            line_no=line_no,
            rule_id="NAME-COL-01",
            severity="error",
            message=f"Column alias '{alias}' exceeds 255 characters.",
            suggestion="Shorten the column name to 255 characters or fewer.",
            original_text=alias,
        )
    if re.search(r'[^A-Za-z0-9_]', alias):
        return Violation(
            line_no=line_no,
            rule_id="NAME-COL-02",
            severity="error",
            message=f"Column alias '{alias}' contains special characters or spaces.",
            suggestion="Use only letters, digits, and underscores in column names.",
            original_text=alias,
        )
    # PascalCase: no underscores, first letter uppercase
    if '_' in alias:
        pascal = _to_pascal(alias)
        return Violation(
            line_no=line_no,
            rule_id="NAME-COL-03",
            severity="error",
            message=f"Column alias '{alias}' uses snake_case; PascalCase is required.",
            suggestion=f"Rename to '{pascal}'.",
            original_text=alias,
            fixed_text=pascal,
        )
    if alias and alias[0].islower():
        pascal = alias[0].upper() + alias[1:]
        return Violation(
            line_no=line_no,
            rule_id="NAME-COL-04",
            severity="error",
            message=f"Column alias '{alias}' starts with a lowercase letter; PascalCase required.",
            suggestion=f"Rename to '{pascal}'.",
            original_text=alias,
            fixed_text=pascal,
        )
    return None


def check_column_aliases(lines: List[str]) -> List[Violation]:
    """NAME-COL — Column AS aliases must be PascalCase."""
    violations: List[Violation] = []
    for i, line in enumerate(lines, 1):
        if _is_comment(line) or _is_magic_cmd(line):
            continue
        for match in _AS_ALIAS_RE.finditer(line):
            alias = match.group(1).strip('`"\'')
            # Skip word-style table aliases
            if alias.lower() in _VALID_WORD_ALIASES:
                continue
            # Skip known schema names
            if alias.lower() in {'s_isc', 's_isca', 'b_um_isc', 'b_um_isca', 'g_isc', 'g_isca'}:
                continue
            v = _check_column_name(alias, i)
            if v:
                violations.append(v)
    return violations


# ---------------------------------------------------------------------------
# View naming
# ---------------------------------------------------------------------------

def check_view_declarations(lines: List[str]) -> List[Violation]:
    """NAME-VIEW / NAME-TMPVIEW — Views must start with v_, temp views with tv_."""
    violations: List[Violation] = []
    for i, line in enumerate(lines, 1):
        if _is_comment(line) or _is_magic_cmd(line):
            continue
        match = _CREATE_VIEW_RE.search(line)
        if not match:
            continue
        is_temp = match.group(1) is not None
        view_ref = match.group(2)
        bare = _bare(view_ref)

        if is_temp:
            if not bare.lower().startswith('tv_'):
                violations.append(Violation(
                    line_no=i,
                    rule_id="NAME-TMPVIEW-01",
                    severity="error",
                    message=f"Temporary view '{bare}' must start with 'tv_'.",
                    suggestion=f"Rename to 'tv_{bare}' (all lowercase).",
                    original_text=line.rstrip(),
                    fixed_text=line.rstrip().replace(bare, f"tv_{bare.lower()}"),
                ))
            elif bare != bare.lower():
                violations.append(Violation(
                    line_no=i,
                    rule_id="NAME-TMPVIEW-02",
                    severity="error",
                    message=f"Temporary view '{bare}' must be fully lowercase.",
                    suggestion=f"Rename to '{bare.lower()}'.",
                    original_text=line.rstrip(),
                    fixed_text=line.rstrip().replace(bare, bare.lower()),
                ))
        else:
            if not bare.lower().startswith('v_'):
                violations.append(Violation(
                    line_no=i,
                    rule_id="NAME-VIEW-01",
                    severity="error",
                    message=f"View '{bare}' must start with 'v_'.",
                    suggestion=f"Rename to 'v_{bare.lower()}'.",
                    original_text=line.rstrip(),
                    fixed_text=line.rstrip().replace(bare, f"v_{bare.lower()}"),
                ))
            elif bare != bare.lower():
                violations.append(Violation(
                    line_no=i,
                    rule_id="NAME-VIEW-02",
                    severity="error",
                    message=f"View '{bare}' must be fully lowercase.",
                    suggestion=f"Rename to '{bare.lower()}'.",
                    original_text=line.rstrip(),
                    fixed_text=line.rstrip().replace(bare, bare.lower()),
                ))
    return violations


# ---------------------------------------------------------------------------
# Table naming
# ---------------------------------------------------------------------------

def check_table_declarations(lines: List[str]) -> List[Violation]:
    """NAME-TBL — Tables must be lowercase, underscore-separated, no special chars."""
    violations: List[Violation] = []
    for i, line in enumerate(lines, 1):
        if _is_comment(line) or _is_magic_cmd(line):
            continue
        match = _CREATE_TABLE_RE.search(line)
        if not match:
            continue
        table_ref = match.group(1)
        bare = _bare(table_ref)

        if bare != bare.lower():
            violations.append(Violation(
                line_no=i,
                rule_id="NAME-TBL-01",
                severity="error",
                message=f"Table name '{bare}' must be lowercase.",
                suggestion=f"Rename to '{bare.lower()}'.",
                original_text=line.rstrip(),
                fixed_text=line.rstrip().replace(bare, bare.lower()),
            ))
        if re.search(r'[^a-z0-9_]', bare.lower()):
            violations.append(Violation(
                line_no=i,
                rule_id="NAME-TBL-02",
                severity="error",
                message=f"Table name '{bare}' contains characters other than lowercase letters, digits, or underscores.",
                suggestion="Use only a-z, 0-9, and _ in table names.",
                original_text=line.rstrip(),
            ))
    return violations


# ---------------------------------------------------------------------------
# Aggregator
# ---------------------------------------------------------------------------

class NamingRules:
    """Aggregates all naming convention checks."""

    _checks = [
        check_column_aliases,
        check_view_declarations,
        check_table_declarations,
    ]

    def run(self, lines: List[str]) -> List[Violation]:
        results: List[Violation] = []
        for check in self._checks:
            results.extend(check(lines))
        return sorted(results, key=lambda v: v.line_no)
