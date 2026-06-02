"""Unit tests for PySpark coding standard rules."""
import pytest
from isca_validator.rules.pyspark_rules import (
    check_wildcard_imports,
    check_pandas_import,
    check_indentation,
)


def lines(text: str):
    return text.splitlines(keepends=True)


def test_wildcard_import_flagged():
    result = check_wildcard_imports(lines("from pyspark.sql.functions import *"))
    assert any(v.rule_id == "PY-01" for v in result)


def test_explicit_import_passes():
    result = check_wildcard_imports(lines("from pyspark.sql.functions import col, split"))
    assert not result


def test_pandas_import_flagged():
    result = check_pandas_import(lines("import pandas as pd"))
    assert any(v.rule_id == "PY-02" for v in result)


def test_pyspark_pandas_passes():
    result = check_pandas_import(lines("import pyspark.pandas as ps"))
    assert not result


def test_tab_indent_flagged():
    result = check_indentation(lines("\tdf = spark.read.csv(path)"))
    assert any(v.rule_id == "PY-03" for v in result)


def test_four_space_indent_passes():
    result = check_indentation(lines("    df = spark.read.csv(path)"))
    assert not result
