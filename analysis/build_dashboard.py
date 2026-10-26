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

# ---- Power BI export: star schema from sql/10_powerbi_export.sql, the same SQL the tests check -------------------
con.close()
pbi = ROOT / "powerbi"
pbi.mkdir(exist_ok=True)
exp = duckdb.connect()  # in memory, so the analysis database stays read-only
exp.execute(f"ATTACH '{ROOT / 'data' / 'olist.duckdb'}' AS olist (READ_ONLY)")
exp.execute("CREATE TABLE fct_orders AS SELECT * FROM olist.fct_orders")
exp.execute((ROOT / "sql" / "10_powerbi_export.sql").read_text())
for table in ["fact_orders", "dim_state", "dim_category", "dim_date"]:
    exp.execute(f"COPY pbi_{table} TO '{pbi / f'{table}.csv'}' (HEADER)")
print("wrote Power BI export to", pbi)
