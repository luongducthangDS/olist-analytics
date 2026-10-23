"""Olist delivery & satisfaction analysis. Produces reports/results.json and reports/figures/*.png.

Business question: do late deliveries hurt satisfaction and repeat purchase, and where should Olist fix
delivery first?  Run from the project root:  python analysis/run_analysis.py
"""
import json
from pathlib import Path

import duckdb
import matplotlib
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.proportion import proportions_ztest

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "reports" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

INK, MUTED, GRID = "#1F2937", "#6B7280", "#E5E7EB"
BLUE, RED = "#2563EB", "#DC2626"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": MUTED,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.titlelocation": "left",
                     "axes.titleweight": "bold", "axes.titlecolor": INK})


def load() -> pd.DataFrame:
    con = duckdb.connect(str(ROOT / "data" / "olist.duckdb"))
    con.execute("SET enable_progress_bar = false")
    con.execute(f"SET file_search_path = '{ROOT}'")
    con.execute((ROOT / "sql" / "00_model.sql").read_text())
    return con.execute("SELECT * FROM fct_orders").df()


def style(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color=GRID)
    ax.set_axisbelow(True)


def kpis(df):
    reviewed = df.dropna(subset=["review_score"])
    return {
        "delivered_orders": int(len(df)),
        "customers": int(df.customer_unique_id.nunique()),
        "period": f"{df.purchased_at.min():%Y-%m-%d} to {df.purchased_at.max():%Y-%m-%d}",
        "gmv_brl": round(float(df.order_value.sum()), 2),
        "late_rate": round(float(df.is_late.mean()), 4),
        "late_orders": int(df.is_late.sum()),
        "avg_review": round(float(reviewed.review_score.mean()), 3),
        "reviewed_orders": int(len(reviewed)),
    }


def lateness_buckets(df):
    r = df.dropna(subset=["review_score"]).copy()
    r["bucket"] = pd.cut(r.days_late, [-1e9, 0, 3, 7, 1e9], labels=["On time", "1-3 days", "4-7 days", "8+ days"])
    t = r.groupby("bucket", observed=True).agg(
        orders=("order_id", "size"), avg_review=("review_score", "mean"),
        share_1_2_stars=("review_score", lambda s: (s <= 2).mean()))
    fig, ax = plt.subplots(figsize=(7, 3.8))
    colors = [BLUE] + [RED] * 3
    bars = ax.bar(t.index.astype(str), t.avg_review, color=colors, width=0.6)
    for b, (_, row) in zip(bars, t.iterrows()):
        ax.text(b.get_x() + b.get_width() / 2, row.avg_review + 0.08,
                f"{row.avg_review:.2f}★\n{row.share_1_2_stars:.0%} give 1-2★", ha="center", color=INK, fontsize=9)
    ax.set_ylim(0, 5.4)
    ax.set_ylabel("average review score")
    ax.set_title("The later the delivery, the worse the review")
    style(ax)
    fig.tight_layout()
    fig.savefig(FIG / "01_review_by_lateness.png", dpi=140)
    plt.close(fig)
    return t.reset_index().assign(bucket=lambda d: d.bucket.astype(str)).round(4).to_dict("records")


def regression(df):
    """Is the late effect just category / price / region? Control for them."""
    r = df.dropna(subset=["review_score", "freight_ratio"]).copy()
    top = r.main_category.value_counts().index[:20]
    r["category"] = np.where(r.main_category.isin(top), r.main_category, "other")
    r["log_value"] = np.log(r.order_value)
    r["low_score"] = (r.review_score <= 2).astype(int)
    r["is_late"] = r.is_late.astype(int)
    r["same_state"] = r.same_state.astype(int)
    rhs = "is_late + log_value + freight_ratio + items + same_state + C(category) + C(customer_state)"
    ols = smf.ols(f"review_score ~ {rhs}", data=r).fit(cov_type="HC3")
    logit = smf.logit(f"low_score ~ {rhs}", data=r).fit(disp=False)
    ci = ols.conf_int().loc["is_late"]
    me = logit.get_margeff(at="overall").summary_frame().loc["is_late"]
    raw_gap = r.loc[r.is_late == 1, "review_score"].mean() - r.loc[r.is_late == 0, "review_score"].mean()
    return {
        "n": int(ols.nobs),
        "raw_gap_stars": round(float(raw_gap), 3),
        "ols_late_coef_stars": round(float(ols.params["is_late"]), 3),
        "ols_late_ci95": [round(float(ci[0]), 3), round(float(ci[1]), 3)],
        "ols_r2": round(float(ols.rsquared), 3),
        "logit_late_marginal_effect_low_score": round(float(me["dy/dx"]), 4),
        "logit_late_me_ci95": [round(float(me["Conf. Int. Low"]), 4), round(float(me["Cont. Int. Hi."]), 4)],
        "controls": "log order value, freight/price ratio, item count, same-state shipping, top-20 category, customer state",
    }


def where_to_fix(df):
    overall = df.is_late.mean()
    st = df.groupby("customer_state").agg(orders=("order_id", "size"), late_rate=("is_late", "mean"),
                                          late_orders=("is_late", "sum"))
    st = st[st.orders >= 300].sort_values("late_rate", ascending=False)
    routes = df.groupby("route").agg(orders=("order_id", "size"), late_rate=("is_late", "mean"),
                                     late_orders=("is_late", "sum"))
    routes = routes[routes.orders >= 200]
    # excess late orders = late orders above what the national rate would predict for that volume
    routes["excess_late"] = routes.late_orders - routes.orders * overall
    routes = routes.sort_values("excess_late", ascending=False)
    top10 = routes.head(10)
    excess_total = routes.excess_late.clip(lower=0).sum()

    fig, ax = plt.subplots(figsize=(8, 4.2))
    y = st.head(12)
    ax.barh(y.index[::-1], y.late_rate[::-1], color=[RED if v > overall * 1.5 else BLUE for v in y.late_rate[::-1]])
    ax.axvline(overall, color=MUTED, ls="--", lw=1)
    ax.text(overall, -0.9, f" national {overall:.1%}", color=MUTED, fontsize=9)
    for i, (s, row) in enumerate(y[::-1].iterrows()):
        ax.text(row.late_rate + 0.003, i, f"{row.late_rate:.1%}  ({int(row.orders):,} orders)", va="center", fontsize=8.5, color=INK)
    ax.set_xlim(0, y.late_rate.max() * 1.45)
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.set_title("Late-delivery rate by customer state (states with ≥300 orders)")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIG / "02_late_rate_by_state.png", dpi=140)
    plt.close(fig)

    return {
        "national_late_rate": round(float(overall), 4),
        "worst_states": st.head(5).round(4).reset_index().to_dict("records"),
        "best_states": st.tail(3).round(4).reset_index().to_dict("records"),
        "top10_routes_by_excess_late": top10.round(4).reset_index().to_dict("records"),
        "top10_routes_share_of_excess_late": round(float(top10.excess_late.sum() / excess_total), 4),
        "top10_routes_share_of_orders": round(float(top10.orders.sum() / len(df)), 4),
    }


def repeat_after_late(df):
    """Does a late FIRST order reduce the chance of buying again?

    Right-censoring: a customer who first bought last week had no time to come back, so only customers
    whose first order is at least 180 days before the end of the data are compared.
    """
    end = df.purchased_at.max()
    first = df.sort_values("purchased_at").groupby("customer_unique_id").agg(
        first_at=("purchased_at", "first"), first_late=("is_late", "first"), orders=("order_id", "size"))
    eligible = first[first.first_at <= end - pd.Timedelta(days=180)].copy()
    eligible["repeat"] = eligible.orders >= 2
    g = eligible.groupby("first_late").repeat.agg(["sum", "count", "mean"])
    stat, p = proportions_ztest(g["sum"].values, g["count"].values)
    return {
        "customers_overall": int(len(first)),
        "repeat_rate_overall": round(float((first.orders >= 2).mean()), 4),
        "eligible_customers_180d": int(len(eligible)),
        "repeat_rate_first_on_time": round(float(g.loc[False, "mean"]), 4),
        "repeat_rate_first_late": round(float(g.loc[True, "mean"]), 4),
        "n_first_on_time": int(g.loc[False, "count"]),
        "n_first_late": int(g.loc[True, "count"]),
        "z": round(float(stat), 3),
        "p_value": float(p),
    }


def cohorts(df):
    df = df.assign(purchase_month=pd.to_datetime(df.purchase_month))
    first = df.groupby("customer_unique_id").purchase_month.min().rename("cohort")
    d = df.join(first, on="customer_unique_id")
    # cohorts with at least 6 months of follow-up and a meaningful size
    d = d[(d.cohort >= "2017-01-01") & (d.cohort <= "2018-02-01")]
    d["age"] = ((d.purchase_month.dt.year - d.cohort.dt.year) * 12 + d.purchase_month.dt.month - d.cohort.dt.month)
    m = d.groupby(["cohort", "age"]).customer_unique_id.nunique().unstack(fill_value=0)
    ret = m.div(m[0], axis=0)
    fig, ax = plt.subplots(figsize=(9, 4.6))
    shown = ret.iloc[:, 1:7]
    im = ax.imshow(shown.values * 100, cmap="Blues", aspect="auto", vmin=0, vmax=1)
    ax.set_xticks(range(shown.shape[1]), [f"M+{c}" for c in shown.columns])
    ax.set_yticks(range(len(shown)), [f"{c:%Y-%m}" for c in shown.index])
    for (i, j), v in np.ndenumerate(shown.values * 100):
        ax.text(j, i, f"{v:.2f}%", ha="center", va="center", fontsize=7.5, color=INK)
    ax.set_title("Monthly cohort retention: under 1% of customers come back in any later month")
    fig.colorbar(im, ax=ax, label="% of cohort buying again")
    fig.tight_layout()
    fig.savefig(FIG / "03_cohort_retention.png", dpi=140)
    plt.close(fig)
    return {"avg_month1_retention": round(float(ret[1].mean()), 4),
            "avg_month1_to_6_retention": round(float(ret.iloc[:, 1:7].mean().mean()), 4)}


def seasonality(df):
    """Are late orders spread evenly over time, or concentrated in a few peak months?"""
    m = df.groupby(pd.to_datetime(df.purchase_month)).agg(orders=("order_id", "size"), late=("is_late", "sum"))
    m = m[m.orders >= 500]
    m["late_rate"] = m.late / m.orders
    spikes = m[m.late_rate > 2 * df.is_late.mean() * 0.8]  # months above ~1.6x the overall rate
    rest = df[~pd.to_datetime(df.purchase_month).isin(spikes.index)]
    return {
        "spike_months": {f"{k:%Y-%m}": round(float(v), 4) for k, v in spikes.late_rate.items()},
        "spike_share_of_orders": round(float(spikes.orders.sum() / len(df)), 4),
        "spike_share_of_late_orders": round(float(spikes.late.sum() / df.is_late.sum()), 4),
        "late_rate_outside_spikes": round(float(rest.is_late.mean()), 4),
    }


def impact(df):
    r = df.dropna(subset=["review_score"])
    p_late = (r[r.is_late].review_score <= 2).mean()
    p_ok = (r[~r.is_late].review_score <= 2).mean()
    late_n = int(r.is_late.sum())
    excess_neg = late_n * (p_late - p_ok)
    total_neg = int((r.review_score <= 2).sum())
    return {"late_reviewed_orders": late_n,
            "excess_negative_reviews_from_lateness": int(round(excess_neg)),
            "all_negative_reviews": total_neg,
            "share_of_negative_reviews_explained_by_lateness": round(float(excess_neg / total_neg), 4),
            "note": "upper bound if lateness were the only difference between late and on-time orders; "
                    "the regression shows the gap barely shrinks after controls"}


def main():
    df = load()
    results = {
        "kpis": kpis(df),
        "lateness_buckets": lateness_buckets(df),
        "regression": regression(df),
        "where_to_fix": where_to_fix(df),
        "repeat_purchase": repeat_after_late(df),
        "seasonality": seasonality(df),
        "cohorts": cohorts(df),
        "impact": impact(df),
    }
    out = ROOT / "reports" / "results.json"
    out.write_text(json.dumps(results, indent=2, default=str))
    print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    main()
