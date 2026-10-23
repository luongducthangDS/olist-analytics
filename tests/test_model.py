"""Checks on the analysis model: if these fail, every number in the memo is suspect."""
from pathlib import Path

import duckdb
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def con():
    c = duckdb.connect()
    c.execute("SET enable_progress_bar = false")
    c.execute(f"SET file_search_path = '{ROOT}'")
    c.execute((ROOT / "sql" / "00_model.sql").read_text())
    return c


def one(con, sql):
    return con.execute(sql).fetchone()[0]


def test_one_row_per_order(con):
    assert one(con, "SELECT count(*) - count(DISTINCT order_id) FROM fct_orders") == 0


def test_one_review_per_order(con):
    assert one(con, "SELECT count(*) - count(DISTINCT order_id) FROM order_review") == 0


def test_only_delivered_orders_with_a_delivery_date(con):
    assert one(con, "SELECT count(*) FROM fct_orders WHERE delivered_at IS NULL") == 0


def test_order_value_matches_items_table(con):
    gap = one(con, """
        SELECT abs(sum(f.items_value) - (SELECT sum(price) FROM read_csv('data/raw/olist_order_items_dataset.csv')
                                         WHERE order_id IN (SELECT order_id FROM fct_orders)))
        FROM fct_orders f""")
    assert gap < 0.01


def test_is_late_matches_days_late(con):
    assert one(con, "SELECT count(*) FROM fct_orders WHERE is_late <> (days_late > 0)") == 0


def test_review_scores_in_range(con):
    assert one(con, "SELECT count(*) FROM fct_orders WHERE review_score NOT BETWEEN 1 AND 5") == 0


def test_headline_numbers_are_reproducible(con):
    """The memo quotes these; if the model changes they must be re-checked."""
    assert one(con, "SELECT count(*) FROM fct_orders") == 96_470
    assert round(one(con, "SELECT avg(is_late::INT) FROM fct_orders"), 4) == 0.0677
