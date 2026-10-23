"""Build reports/dashboard.html (interactive, opens in any browser) and the Power BI export in powerbi/.

Run after run_analysis.py:  python analysis/build_dashboard.py
"""
import json
from pathlib import Path

import duckdb
from plotly.subplots import make_subplots

ROOT = Path(__file__).resolve().parents[1]
BLUE, RED, MUTED = "#2563EB", "#DC2626", "#6B7280"

con = duckdb.connect(str(ROOT / "data" / "olist.duckdb"), read_only=True)
res = json.loads((ROOT / "reports" / "results.json").read_text())

monthly = con.execute("""
    SELECT purchase_month, count(*) AS orders, avg(is_late::INT) AS late_rate, avg(review_score) AS avg_review
    FROM fct_orders WHERE purchase_month BETWEEN '2017-01-01' AND '2018-07-01'
    GROUP BY 1 ORDER BY 1""").df()
buckets = res["lateness_buckets"]
states = con.execute("""
    SELECT customer_state, count(*) orders, avg(is_late::INT) late_rate, avg(review_score) avg_review
    FROM fct_orders GROUP BY 1 HAVING count(*) >= 300 ORDER BY late_rate DESC""").df()
routes = res["where_to_fix"]["top10_routes_by_excess_late"]

fig = make_subplots(
    rows=2, cols=2, vertical_spacing=0.16, horizontal_spacing=0.1,
    subplot_titles=("Orders and late-delivery rate by month", "Review score by days late",
                    "Late rate vs. volume by customer state", "Top 10 routes by excess late orders"),
    specs=[[{"secondary_y": True}, {}], [{}, {}]],
)
fig.add_bar(x=monthly.purchase_month, y=monthly.orders, name="orders", marker_color="#BFDBFE", row=1, col=1)
fig.add_scatter(x=monthly.purchase_month, y=monthly.late_rate, name="late rate", line={"color": RED, "width": 2.5},
                row=1, col=1, secondary_y=True, hovertemplate="%{y:.1%}")
fig.add_bar(x=[b["bucket"] for b in buckets], y=[b["avg_review"] for b in buckets],
            marker_color=[BLUE, RED, RED, RED], text=[f"{b['avg_review']:.2f}★" for b in buckets],
            textposition="outside", name="avg review", row=1, col=2)
fig.add_scatter(x=states.orders, y=states.late_rate, mode="markers+text", text=states.customer_state,
                textposition="top center", marker={"size": 9, "color": states.late_rate, "colorscale": "Reds"},
                name="state", hovertemplate="%{text}: %{y:.1%} late, %{x:,} orders", row=2, col=1)
fig.add_bar(y=[r["route"] for r in routes][::-1], x=[r["excess_late"] for r in routes][::-1], orientation="h",
            marker_color=RED, name="excess late",
            text=[f"{r['late_rate']:.0%} late of {r['orders']:,}" for r in routes][::-1], textposition="auto",
            row=2, col=2)
fig.update_yaxes(tickformat=".0%", secondary_y=True, row=1, col=1)
fig.update_yaxes(range=[0, 5], row=1, col=2)
fig.update_xaxes(type="log", title_text="orders (log scale)", row=2, col=1)
fig.update_yaxes(tickformat=".0%", row=2, col=1)
k = res["kpis"]
fig.update_layout(
    height=900, template="plotly_white", showlegend=False, margin={"t": 140},
    title={"x": 0.01, "text": (
        f"<b>Olist: late deliveries cost reviews and repeat customers</b><br>"
        f"<span style='font-size:13px;color:{MUTED}'>{k['delivered_orders']:,} delivered orders · "
        f"{k['period']} · late rate {k['late_rate']:.1%} · avg review {k['avg_review']:.2f}★ · "
        f"late orders = 6.8% of orders but ~{res['impact']['share_of_negative_reviews_explained_by_lateness']:.0%} "
        f"of 1-2★ reviews</span>")},
)
out = ROOT / "reports" / "dashboard.html"
fig.write_html(out, include_plotlyjs="cdn", full_html=True)
print("wrote", out)

# ---- Power BI export: a small star schema + measures ------------------------------------------------
pbi = ROOT / "powerbi"
pbi.mkdir(exist_ok=True)
con.execute(f"""COPY (SELECT order_id, customer_unique_id, customer_state, seller_state, route, main_category,
                purchase_month, purchased_at::DATE AS purchase_date, delivery_days, days_late, is_late,
                items, items_value, freight_value, order_value, review_score FROM fct_orders)
                TO '{pbi / 'fact_orders.csv'}' (HEADER)""")
con.execute(f"""COPY (SELECT DISTINCT main_category AS category FROM fct_orders ORDER BY 1)
                TO '{pbi / 'dim_category.csv'}' (HEADER)""")
con.execute(f"""COPY (SELECT DISTINCT customer_state AS state FROM fct_orders ORDER BY 1)
                TO '{pbi / 'dim_state.csv'}' (HEADER)""")
con.execute(f"""COPY (SELECT d::DATE AS date, year(d) AS year, month(d) AS month, date_trunc('month', d)::DATE AS month_start
                FROM range(DATE '2016-09-01', DATE '2018-09-01', INTERVAL 1 DAY) t(d))
                TO '{pbi / 'dim_date.csv'}' (HEADER)""")
print("wrote Power BI export to", pbi)
