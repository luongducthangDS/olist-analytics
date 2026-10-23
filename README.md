# Olist: do late deliveries cost reviews and customers?

Analysis of **96,470 delivered orders** from Olist, the largest Brazilian marketplace aggregator (public dataset,
Sep 2016 – Aug 2018). It starts from a business question, answers it in SQL, checks it with statistics, and ends in a
[one-page decision memo](docs/decision_memo.md) and an interactive dashboard.

![Dashboard](reports/figures/00_dashboard_preview.png)

## Answer

**Yes.** Late deliveries are the biggest controllable driver of bad reviews, and the lateness is concentrated in
time and on specific routes, so it can be fixed.

| Finding | Number |
|---|---|
| Late delivery rate | **6.8 %** of delivered orders |
| Review score, late vs on time | **2.27★ vs 4.29★**; 62 % vs 9 % give 1–2★ |
| Effect after controlling for category, price, freight, items, region (OLS, robust SE) | **−2.00★** (95 % CI −2.04 to −1.96); the raw gap is −2.02★, so controls barely change it |
| Effect on the chance of a 1–2★ review (logit, average marginal effect) | **+25.8 pp** |
| Dose-response | 1–3 days late 3.29★ → 4–7 days 2.10★ → 8+ days 1.70★ |
| Share of negative reviews linked to lateness | ≈ **28 %** (3,392 of 12,272), from 6.8 % of orders |
| Repeat purchase after a late vs on-time first order | **2.97 % vs 4.05 %** (−27 %), z = 3.28, p = 0.001, n = 55,905 |
| Peak months (Nov 2017, Feb & Mar 2018) | 22 % of orders, **48 % of late orders**; 4.5 % late outside them |
| Top 10 routes by excess late orders | 19 % of orders, **88 % of excess late orders**; SP → RJ alone: 600 |
| Customers who ever buy twice | 3.0 %; under 0.5 % return in any month, so RFM segmentation has almost no frequency signal |

**So what:** plan carrier capacity for peak months first, then fix 10 routes. Hold off on loyalty or RFM campaigns:
they would target a repeat base that barely exists.

## Method

1. **Model** (`sql/00_model.sql`, DuckDB): one row per delivered order. Several reviews per order are reduced to the
   latest one. The "main" category and seller are taken from the order's most expensive item. Lateness is measured
   in days against the date promised to the customer.
2. **Checks** (`tests/test_model.py`): one row per order, one review per order, values reconcile with the items
   table, scores in range, headline numbers reproducible.
3. **Analysis** (`analysis/run_analysis.py`):
   - Lateness buckets.
   - OLS with HC3 robust errors and a logit with marginal effects, both controlling for 20 categories and 27 states.
   - Ranking of routes by *excess* late orders (volume × rate above the national rate) instead of raw rate, so a
     route with 255 orders cannot outrank one with 8,154.
   - Repeat-purchase comparison restricted to customers with at least 180 days of follow-up (fixes right-censoring).
   - Two-proportion z-test.
   - Monthly cohorts.
4. **Outputs:**
   - `reports/results.json` (every number in this README).
   - `reports/figures/`.
   - `reports/dashboard.html` (interactive Plotly).
   - `powerbi/`: star-schema CSVs and `measures.dax` for rebuilding the report in Power BI.

## Run it

```bash
pip install -r requirements.txt
python scripts/get_data.py              # ~120 MB from the official olist/work-at-olist-data repo
pytest -q                               # 7 model checks
python analysis/run_analysis.py         # -> reports/results.json + figures
python analysis/build_dashboard.py      # -> reports/dashboard.html + powerbi/*.csv
```

## Decisions worth defending in an interview

- **Why rank routes by excess late orders, not late rate?** AL has the worst rate (21 %) but only 397 orders. SP → RJ
  has 14 % on 8,154 orders. Ops capacity goes where the most customers are hurt.
- **Why the 180-day window?** A customer who bought last month has had no time to come back. Without the window,
  recent customers drag both repeat rates down and blur the comparison.
- **Why is this "strong association" and not "proof"?** Lateness is not randomly assigned. The controls rule out the
  obvious confounders (category, price, region), and the gap does not shrink. Only an experiment, for example a
  voucher for late orders, would prove that fixing lateness brings customers back.
- **Why not RFM?** With 97 % one-time buyers, "F" is 1 for almost everyone. Recency × monetary, or simply first-order
  experience, is the more useful segmentation.

## Interview questions this project prepares for

1. Walk me through how you defined "late". What changes if you use the carrier's handover date instead?
2. Your regression has R² = 0.18. Is that a problem?
3. Why could padding the promised delivery date be a bad fix, even though it reduces "late" orders?
4. How would you design an experiment to prove that faster delivery brings customers back?

## Data and license

Code: MIT ([LICENSE](LICENSE)). Data: [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (CC BY-NC-SA 4.0), downloaded by `scripts/get_data.py`.
