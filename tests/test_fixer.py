"""Unit tests for the auto-fixer."""
from isca_validator.fixer import fix_lines


def lines(text: str):
    return text.splitlines(keepends=True)


def joined(ls):
    return "".join(ls)


def test_keyword_uppercased():
    result = fix_lines(lines("select one.Col from s_isca.t one"))
    assert "SELECT" in joined(result)
    assert "FROM" in joined(result)


def test_ifnull_replaced():
    result = fix_lines(lines("SELECT IFNULL(one.Col, 'x') FROM s_isca.t one"))
    assert "COALESCE" in joined(result)
    assert "IFNULL" not in joined(result)


def test_tab_replaced_with_spaces():
    result = fix_lines(lines("\tdf = spark.table('x')"), is_python=True)
    assert joined(result).startswith("    ")


def test_pandas_import_replaced():
    result = fix_lines(lines("import pandas as pd"), is_python=True)
    assert "pyspark.pandas" in joined(result)


def test_snake_case_alias_to_pascal():
    result = fix_lines(lines("SELECT one.Col AS sales_doc_number FROM s_isca.t one"))
    assert "SalesDocNumber" in joined(result)


def test_comment_not_modified():
    orig = "-- select * from something\n"
    result = fix_lines([orig])
    assert joined(result) == orig
