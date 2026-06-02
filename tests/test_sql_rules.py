"""Unit tests for Spark SQL coding standard rules."""
import pytest
from isca_validator.rules.sql_rules import (
    check_select_star,
    check_keyword_case,
    check_order_by_numbers,
    check_schema_prefix,
    check_ifnull,
    check_ltrim_rtrim_together,
    check_drop_create_table,
    check_single_letter_aliases,
)


def lines(text: str):
    return text.splitlines(keepends=True)


# SQL-01 -----------------------------------------------------------------------

def test_select_star_flagged():
    result = check_select_star(lines("SELECT * FROM s_isca.orders one"))
    assert any(v.rule_id == "SQL-01" for v in result)


def test_select_star_not_flagged_when_explicit():
    result = check_select_star(lines("SELECT one.Col1, one.Col2 FROM s_isca.orders one"))
    assert not result


# SQL-02 -----------------------------------------------------------------------

def test_lowercase_keyword_flagged():
    result = check_keyword_case(lines("select one.Col1 from s_isca.orders one"))
    assert any(v.rule_id == "SQL-02" for v in result)


def test_uppercase_keywords_pass():
    result = check_keyword_case(lines("SELECT one.Col1 FROM s_isca.orders one"))
    assert not result


def test_comment_line_skipped():
    result = check_keyword_case(lines("-- select * from something"))
    assert not result


# SQL-03 -----------------------------------------------------------------------

def test_order_by_number_flagged():
    result = check_order_by_numbers(lines("ORDER BY 1, 2"))
    assert any(v.rule_id == "SQL-03" for v in result)


def test_order_by_name_passes():
    result = check_order_by_numbers(lines("ORDER BY one.Col1"))
    assert not result


# SQL-04 -----------------------------------------------------------------------

def test_missing_schema_prefix_flagged():
    result = check_schema_prefix(lines("SELECT one.Id FROM orders one"))
    assert any(v.rule_id == "SQL-04" for v in result)


def test_schema_prefix_passes():
    result = check_schema_prefix(lines("SELECT one.Id FROM s_isca.orders one"))
    assert not result


def test_temp_view_skipped():
    result = check_schema_prefix(lines("SELECT one.Id FROM tv_staging one"))
    assert not result


# SQL-05 -----------------------------------------------------------------------

def test_ifnull_flagged():
    result = check_ifnull(lines("SELECT IFNULL(one.Col, 'x') FROM s_isca.t one"))
    assert any(v.rule_id == "SQL-05" for v in result)
    assert result[0].fixed_text and "COALESCE" in result[0].fixed_text


def test_coalesce_passes():
    result = check_ifnull(lines("SELECT COALESCE(one.Col, 'x') FROM s_isca.t one"))
    assert not result


# SQL-06 -----------------------------------------------------------------------

def test_ltrim_rtrim_together_flagged():
    result = check_ltrim_rtrim_together(lines("SELECT LTRIM(RTRIM(one.Col)) FROM s_isca.t one"))
    assert any(v.rule_id == "SQL-06" for v in result)


def test_trim_alone_passes():
    result = check_ltrim_rtrim_together(lines("SELECT TRIM(one.Col) FROM s_isca.t one"))
    assert not result


# SQL-07 -----------------------------------------------------------------------

def test_drop_table_flagged():
    result = check_drop_create_table(lines("DROP TABLE s_isca.my_table"))
    assert any(v.rule_id == "SQL-07" for v in result)


# SQL-08 -----------------------------------------------------------------------

def test_single_letter_alias_flagged():
    result = check_single_letter_aliases(lines("SELECT a.Col FROM s_isca.orders a"))
    assert any(v.rule_id == "SQL-08" for v in result)


def test_word_alias_passes():
    result = check_single_letter_aliases(lines("SELECT one.Col FROM s_isca.orders one"))
    assert not result
