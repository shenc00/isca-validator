"""Unit tests for naming convention rules."""
import pytest
from isca_validator.rules.naming_rules import (
    check_column_aliases,
    check_view_declarations,
    check_table_declarations,
)


def lines(text: str):
    return text.splitlines(keepends=True)


# Column aliases ---------------------------------------------------------------

def test_snake_case_alias_flagged():
    result = check_column_aliases(lines("SELECT one.Col AS sales_document_number FROM s_isca.t one"))
    assert any(v.rule_id == "NAME-COL-03" for v in result)


def test_lowercase_start_alias_flagged():
    result = check_column_aliases(lines("SELECT one.Col AS customerNumber FROM s_isca.t one"))
    assert any(v.rule_id == "NAME-COL-04" for v in result)


def test_pascal_case_alias_passes():
    result = check_column_aliases(lines("SELECT one.Col AS SalesDocumentNumber FROM s_isca.t one"))
    assert not result


def test_word_alias_skipped():
    result = check_column_aliases(lines("FROM s_isca.t one"))
    assert not result


# View declarations ------------------------------------------------------------

def test_view_missing_v_prefix_flagged():
    result = check_view_declarations(lines("CREATE OR REPLACE VIEW s_isca.otif_summary AS"))
    assert any(v.rule_id == "NAME-VIEW-01" for v in result)


def test_view_correct_prefix_passes():
    result = check_view_declarations(lines("CREATE OR REPLACE VIEW s_isca.v_otif_summary AS"))
    assert not result


def test_temp_view_missing_tv_prefix_flagged():
    result = check_view_declarations(lines("CREATE TEMPORARY VIEW staging_orders AS"))
    assert any(v.rule_id == "NAME-TMPVIEW-01" for v in result)


def test_temp_view_correct_prefix_passes():
    result = check_view_declarations(lines("CREATE TEMPORARY VIEW tv_staging_orders AS"))
    assert not result


# Table declarations -----------------------------------------------------------

def test_uppercase_table_name_flagged():
    result = check_table_declarations(lines("CREATE TABLE s_isca.SalesOrderSummary AS"))
    assert any(v.rule_id == "NAME-TBL-01" for v in result)


def test_lowercase_table_name_passes():
    result = check_table_declarations(lines("CREATE TABLE s_isca.sales_order_summary AS"))
    assert not result
