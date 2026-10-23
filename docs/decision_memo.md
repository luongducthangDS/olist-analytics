# Memo: late deliveries are Olist's biggest controllable driver of bad reviews

**To:** Head of Operations · **Data:** 96,470 delivered orders, Sep 2016 – Aug 2018 · **Full analysis:** `reports/results.json`

## Recommendation

1. **Plan peak-season carrier capacity first.** Three months (Nov 2017, Feb 2018, Mar 2018) held 22 % of orders but
   **48 % of all late deliveries**. Outside those months the late rate is 4.5 %, against 12–19 % inside them.
2. **Then fix 10 routes.** The 10 worst seller→customer routes carry 19 % of orders but **88 % of the late orders above
   the national rate**. SP → RJ alone accounts for 600 excess late orders: 14 % of its 8,154 orders arrive late.
3. **Do not fund an RFM / loyalty campaign yet.** Only 3.0 % of customers ever buy twice, and under 0.5 % come back in
   any given month. There is almost no repeat base for such a campaign to work on.

## Why

| Finding | Number | How sure |
|---|---|---|
| Late orders get worse reviews | 2.27★ vs 4.29★ on time; 62 % vs 9 % give 1–2★ | Very: 95,824 reviewed orders |
| …and it is not explained by product, price or region | −2.00★ after controls (95 % CI −2.04 to −1.96); +25.8 pp chance of a 1–2★ review | Strong association. Not an experiment, so it is not proof of cause, but the gap does not shrink when controls are added |
| The later, the worse | 1–3 days late: 3.29★ · 4–7 days: 2.10★ · 8+ days: 1.70★ | A clear dose-response |
| Late orders drive a large share of bad reviews | 6.8 % of orders, but ≈ 3,390 of 12,272 negative reviews (28 %) are in excess of the on-time rate | Upper bound |
| A late first order loses repeat customers | 2.97 % buy again vs 4.05 % after an on-time first order (−27 %), p = 0.001 | Customers with ≥ 180 days to come back (n = 55,905) |

## What it is worth (rough)

Bringing the three peak months down to the off-peak late rate (4.5 %) would have avoided about 2,200 late orders.
At +25.8 pp per late order, that is roughly **570 fewer 1–2★ reviews** over the period, about 5 % of all negative
reviews. It would also keep part of the repeat-purchase gap shown above.

## What this does not prove

- The causes of the spikes are not in the data. November coincides with Black Friday (+63 % orders vs October). February
  and March 2018 need a conversation with the logistics team.
- "Late" is measured against the date promised to the customer. Padding the promise would reduce lateness on paper
  but could lower conversion. That trade-off needs an A/B test, not this dataset.
- Reviews are self-selected: 646 delivered orders (0.7 %) have no review.
