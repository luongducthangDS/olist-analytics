"""Generate publication-quality figures for Olist Analytics README.
Generates:
- 00_dashboard_preview.png (Composite 4-panel executive overview, zero collision)
- 01_review_by_lateness.png (Standalone: Dose-response review score collapse)
- 02_late_rate_by_state.png (Standalone: Late rate by customer state)
- 03_excess_late_routes.png (Standalone: Top 10 routes by excess late orders)
- 04_monthly_late_spikes.png (Standalone: Peak month seasonality spikes)
"""
from pathlib import Path
import duckdb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "reports" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

INK, MUTED, GRID = "#111827", "#4B5563", "#E5E7EB"
BLUE, RED, GREEN, AMBER = "#1D4ED8", "#DC2626", "#059669", "#D97706"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 10,
    "axes.edgecolor": GRID,
    "axes.labelcolor": MUTED,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.titlelocation": "left",
    "axes.titleweight": "bold",
    "axes.titlecolor": INK
})


def generate():
    con = duckdb.connect(str(ROOT / "data" / "olist.duckdb"))
    con.execute("SET enable_progress_bar = false")
    con.execute(f"SET file_search_path = '{ROOT}'")
    con.execute((ROOT / "sql" / "00_model.sql").read_text())

    # =========================================================================
    # 1. COMPOSITE DASHBOARD PREVIEW (00_dashboard_preview.png)
    # =========================================================================
    fig, axes = plt.subplots(2, 2, figsize=(15, 9.8), dpi=160)
    fig.patch.set_facecolor("#FAFAFA")
    for ax in axes.flat:
        ax.set_facecolor("white")
        ax.spines[["top", "right"]].set_visible(False)
        ax.set_axisbelow(True)

    # Panel A: Review Score by Lateness Bucket (Dose-Response)
    axes[0, 0].grid(axis="y", color=GRID, linestyle="--", alpha=0.7)
    buckets = [
        ("On time", 4.29, 9.3, BLUE),
        ("1–3 days late", 3.29, 32.1, RED),
        ("4–7 days late", 2.10, 67.7, RED),
        ("8+ days late", 1.70, 79.3, RED),
    ]
    x1 = [b[0] for b in buckets]
    y1 = [b[1] for b in buckets]
    c1 = [b[3] for b in buckets]
    bars1 = axes[0, 0].bar(x1, y1, color=c1, width=0.52, zorder=3)
    axes[0, 0].set_title("A. Review Score Collapse by Delivery Lateness (Dose-Response)")
    axes[0, 0].set_ylabel("Average Review Score (★)")
    axes[0, 0].set_ylim(0, 5.4)
    for b, b_info in zip(bars1, buckets):
        h = b.get_height()
        axes[0, 0].text(b.get_x() + b.get_width() / 2, h + 0.12,
                        f"{h:.2f}★\n({b_info[2]:.0f}% give 1–2★)", ha="center", va="bottom",
                        fontsize=8.5, fontweight="bold", color=INK)

    # Panel B: Repeat Purchase Gap (180-Day Cohort)
    axes[0, 1].grid(axis="y", color=GRID, linestyle="--", alpha=0.7)
    repeat_data = [
        ("First Order ON TIME\n(52,125 customers)", 4.04, GREEN),
        ("First Order LATE\n(3,780 customers)", 3.07, RED),
    ]
    x2 = [r[0] for r in repeat_data]
    y2 = [r[1] for r in repeat_data]
    c2 = [r[2] for r in repeat_data]
    bars2 = axes[0, 1].bar(x2, y2, color=c2, width=0.45, zorder=3)
    axes[0, 1].set_title("B. Repeat Purchase Rate (Mature 180-Day Window)")
    axes[0, 1].set_ylabel("Repeat Purchase Rate (%)")
    axes[0, 1].set_ylim(0, 6.2)
    for b in bars2:
        h = b.get_height()
        axes[0, 1].text(b.get_x() + b.get_width() / 2, h + 0.15,
                        f"{h:.2f}%", ha="center", va="bottom",
                        fontsize=10, fontweight="bold", color=INK)
    axes[0, 1].text(0.5, 5.2, "-24% Drop in Repeat Purchases\n(z = 2.95, p = 0.003)",
                    ha="center", fontsize=9, fontweight="bold", color=RED)

    # Panel C: Top 8 Routes by Excess Late Orders (Horizontal barh eliminates collision!)
    axes[1, 0].grid(axis="x", color=GRID, linestyle="--", alpha=0.7)
    top_routes = con.execute("""
        WITH r AS (
            SELECT
                seller_state || ' -> ' || customer_state AS route,
                count(*) AS orders,
                sum(is_late::INT) AS late_orders,
                avg(is_late::INT) AS late_rate,
                sum(is_late::INT) - count(*) * 0.0677 AS excess_late
            FROM fct_orders
            GROUP BY 1
            HAVING count(*) >= 200
        )
        SELECT route, round(excess_late, 0) AS excess, round(late_rate*100, 1) AS rate, orders
        FROM r
        ORDER BY excess DESC
        LIMIT 8
    """).fetchall()

    y3_names = [r[0] for r in top_routes[::-1]]
    x3_vals = [float(r[1]) for r in top_routes[::-1]]
    bars3 = axes[1, 0].barh(y3_names, x3_vals, color=[RED if "RJ" in n else BLUE for n in y3_names], height=0.55, zorder=3)
    axes[1, 0].set_title("C. Top Routes by Excess Late Orders (Above National Benchmark)")
    axes[1, 0].set_xlabel("Excess Late Orders (Orders above 6.8% benchmark)")
    axes[1, 0].set_xlim(0, max(x3_vals) * 1.45)
    for b, r in zip(bars3, top_routes[::-1]):
        w = b.get_width()
        axes[1, 0].text(w + 12, b.get_y() + b.get_height() / 2,
                        f"+{int(w)} orders ({r[2]}% late)", va="center", ha="left",
                        fontsize=8.5, fontweight="bold", color=INK)

    # Panel D: Seasonality Spike Months
    axes[1, 1].grid(axis="y", color=GRID, linestyle="--", alpha=0.7)
    season = con.execute("""
        SELECT
            strftime(purchase_month, '%Y-%m') AS ym,
            round(avg(is_late::INT)*100, 1) AS late_pct,
            count(*) AS total_orders
        FROM fct_orders
        WHERE purchase_month >= '2017-01-01'
        GROUP BY 1
        ORDER BY 1
    """).fetchall()
    x4 = [s[0] for s in season]
    y4 = [s[1] for s in season]
    c4 = [RED if s[0] in ['2017-11', '2018-02', '2018-03'] else BLUE for s in season]
    bars4 = axes[1, 1].bar(x4, y4, color=c4, width=0.6, zorder=3)
    axes[1, 1].axhline(6.8, color=INK, linestyle="--", linewidth=1.2, label="National Benchmark (6.8%)")
    axes[1, 1].set_title("D. Seasonality: Late Rate Spikes in Peak Months")
    axes[1, 1].set_ylabel("Late Delivery Rate (%)")
    axes[1, 1].set_ylim(0, 24)
    axes[1, 1].tick_params(axis="x", rotation=40)
    axes[1, 1].legend(loc="upper left", frameon=True, fontsize=8)
    for b in bars4:
        h = b.get_height()
        if h > 10:
            axes[1, 1].text(b.get_x() + b.get_width() / 2, h + 0.6,
                            f"{h:.1f}%", ha="center", va="bottom",
                            fontsize=8, fontweight="bold", color=RED)

    fig.suptitle("OLIST E-COMMERCE LOGISTICS & CUSTOMER SATISFACTION DASHBOARD",
                 fontsize=14, fontweight="bold", y=0.98, color=INK)
    fig.subplots_adjust(top=0.93, bottom=0.08, left=0.10, right=0.96, hspace=0.34, wspace=0.28)
    out0 = FIG / "00_dashboard_preview.png"
    fig.savefig(out0, dpi=160)
    plt.close(fig)
    print(f"Generated {out0}")

    # =========================================================================
    # 2. STANDALONE FIGURE 1: DOSE-RESPONSE (01_review_by_lateness.png)
    # =========================================================================
    fig1, ax1 = plt.subplots(figsize=(10, 5.5), dpi=160)
    fig1.patch.set_facecolor("white")
    ax1.set_facecolor("white")
    ax1.spines[["top", "right"]].set_visible(False)
    ax1.grid(axis="y", color=GRID, linestyle="--", alpha=0.7)
    ax1.set_axisbelow(True)

    b_dose = ax1.bar(x1, y1, color=c1, width=0.5, zorder=3)
    ax1.set_title("The Later the Delivery, the Worse the Review: Dose-Response Analysis", fontsize=12, pad=12)
    ax1.set_ylabel("Average Review Score (★)", fontsize=10)
    ax1.set_ylim(0, 5.5)

    for b, b_info in zip(b_dose, buckets):
        h = b.get_height()
        ax1.text(b.get_x() + b.get_width() / 2, h + 0.12,
                 f"{h:.2f}★\n({b_info[2]:.0f}% give 1–2★)", ha="center", va="bottom",
                 fontweight="bold", fontsize=9.5, color=INK)

    fig1.tight_layout()
    out1 = FIG / "01_review_by_lateness.png"
    fig1.savefig(out1, dpi=160)
    plt.close(fig1)
    print(f"Generated {out1}")

    # =========================================================================
    # 3. STANDALONE FIGURE 2: LATE RATE BY STATE (02_late_rate_by_state.png)
    # =========================================================================
    state_data = con.execute("""
        SELECT
            customer_state,
            count(*) AS orders,
            round(avg(is_late::INT)*100, 1) AS late_rate
        FROM fct_orders
        GROUP BY customer_state
        HAVING count(*) >= 300
        ORDER BY late_rate DESC
        LIMIT 10
    """).fetchall()
    y_st_names = [s[0] for s in state_data[::-1]]
    x_st_vals = [s[2] for s in state_data[::-1]]
    c_st = [RED if s[0] in ['AL', 'MA', 'RJ'] else BLUE for s in state_data[::-1]]

    fig2, ax2 = plt.subplots(figsize=(10, 5.8), dpi=160)
    fig2.patch.set_facecolor("white")
    ax2.set_facecolor("white")
    ax2.spines[["top", "right"]].set_visible(False)
    ax2.grid(axis="x", color=GRID, linestyle="--", alpha=0.7)
    ax2.set_axisbelow(True)

    b_st = ax2.barh(y_st_names, x_st_vals, color=c_st, height=0.55, zorder=3)
    ax2.axvline(6.8, color=INK, linestyle="--", linewidth=1.2, label="National Benchmark (6.8%)")
    ax2.set_title("Geographic Disparity: Customer States with Highest Late Delivery Rate", fontsize=12, pad=12)
    ax2.set_xlabel("Late Delivery Rate (%)", fontsize=10)
    ax2.set_xlim(0, max(x_st_vals) * 1.40)
    ax2.legend(loc="lower right", frameon=True, fontsize=9)

    for b, s in zip(b_st, state_data[::-1]):
        w = b.get_width()
        ax2.text(w + 0.4, b.get_y() + b.get_height() / 2,
                 f"{w:.1f}% ({s[1]:,} orders)", va="center", ha="left",
                 fontsize=8.5, fontweight="bold", color=INK)

    fig2.subplots_adjust(left=0.12, right=0.92, top=0.90, bottom=0.12)
    out2 = FIG / "02_late_rate_by_state.png"
    fig2.savefig(out2, dpi=160)
    plt.close(fig2)
    print(f"Generated {out2}")

    # =========================================================================
    # 4. STANDALONE FIGURE 3: TOP 10 ROUTES BY EXCESS LATE ORDERS (03_excess_late_routes.png)
    # =========================================================================
    fig3, ax3 = plt.subplots(figsize=(10.5, 5.8), dpi=160)
    fig3.patch.set_facecolor("white")
    ax3.set_facecolor("white")
    ax3.spines[["top", "right"]].set_visible(False)
    ax3.grid(axis="x", color=GRID, linestyle="--", alpha=0.7)
    ax3.set_axisbelow(True)

    b_routes = ax3.barh(y3_names, x3_vals, color=[RED if "RJ" in n else BLUE for n in y3_names], height=0.55, zorder=3)
    ax3.set_title("Top Logistic Bottlenecks: SP -> RJ Alone Accounts for ~600 Excess Late Orders", fontsize=12, pad=12)
    ax3.set_xlabel("Excess Late Orders (Orders above what national 6.8% rate would predict)", fontsize=10)
    ax3.set_xlim(0, max(x3_vals) * 1.55)

    for b, r in zip(b_routes, top_routes[::-1]):
        w = b.get_width()
        ax3.text(w + 12, b.get_y() + b.get_height() / 2,
                 f"+{int(w)} excess ({r[2]}% late on {r[3]:,} orders)", va="center", ha="left",
                 fontsize=8.5, fontweight="bold", color=INK)

    fig3.subplots_adjust(left=0.14, right=0.92, top=0.90, bottom=0.12)
    out3 = FIG / "03_excess_late_routes.png"
    fig3.savefig(out3, dpi=160)
    plt.close(fig3)
    print(f"Generated {out3}")

    # =========================================================================
    # 4. STANDALONE FIGURE 3: MONTHLY LATE SPIKES (04_monthly_late_spikes.png)
    # =========================================================================
    fig4, ax4 = plt.subplots(figsize=(10, 5.5), dpi=160)
    fig4.patch.set_facecolor("white")
    ax4.set_facecolor("white")
    ax4.spines[["top", "right"]].set_visible(False)
    ax4.grid(axis="y", color=GRID, linestyle="--", alpha=0.7)
    ax4.set_axisbelow(True)

    b_mon = ax4.bar(x4, y4, color=c4, width=0.55, zorder=3)
    ax4.axhline(6.8, color=INK, linestyle="--", linewidth=1.2, label="National Benchmark (6.8%)")
    ax4.set_title("Seasonality Concentration: 48% of All Late Orders Occur in 3 Peak Months", fontsize=12, pad=12)
    ax4.set_ylabel("Late Delivery Rate (%)", fontsize=10)
    ax4.set_ylim(0, 24)
    ax4.tick_params(axis="x", rotation=35)
    ax4.legend(loc="upper left", frameon=True, fontsize=9)

    for b in b_mon:
        h = b.get_height()
        if h > 8:
            ax4.text(b.get_x() + b.get_width() / 2, h + 0.6,
                     f"{h:.1f}%", ha="center", va="bottom",
                     fontsize=8.5, fontweight="bold", color=RED if h > 10 else INK)

    fig4.tight_layout()
    out4 = FIG / "04_monthly_late_spikes.png"
    fig4.savefig(out4, dpi=160)
    plt.close(fig4)
    print(f"Generated {out4}")


if __name__ == "__main__":
    generate()
