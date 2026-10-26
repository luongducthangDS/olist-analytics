# Rebuild the report in Power BI (about 45 minutes)

The repo ships the model, not a click-built file: `analysis/build_dashboard.py` exports a star schema to
`powerbi/*.csv` (SQL in `sql/10_powerbi_export.sql`, keys checked by `pytest`), `power_query.m` loads it with fixed
types, and `measures.dax` holds the measures.

## 1. Export (2 minutes)

```bash
python analysis/run_analysis.py
python analysis/build_dashboard.py   # -> powerbi/fact_orders.csv, dim_state.csv, dim_category.csv, dim_date.csv
```

## 2. Load (10 minutes)

1. *File > Options and settings > Options > Current File > Data Load*: untick **Autodetect new relationships**.
2. *Transform data > Manage Parameters > New*: name `Folder`, type Text, value = full path of `powerbi\` with the
   trailing backslash.
3. For each block in [`power_query.m`](power_query.m): *New Source > Blank Query > Advanced Editor*, paste, name the
   query after the block. *Close & Apply*.
4. Row counts: `fact_orders` 96,470 · `dim_state` 27 · `dim_category` 74 · `dim_date` 730.

## 3. Model (5 minutes)

Three relationships, many-to-one, single direction:

| From | To |
|---|---|
| `fact_orders[purchase_date]` | `dim_date[date]` |
| `fact_orders[customer_state]` | `dim_state[state]` |
| `fact_orders[main_category]` | `dim_category[category]` |

Mark `dim_date` as the date table (*Table tools > Mark as date table*, column `date`).

## 4. Measures (10 minutes)

Create the 9 measures in [`measures.dax`](measures.dax). Formats: `Late Rate`, `Negative Review Rate`,
`Repeat Customer Rate` as percentage with one decimal; `Avg Review` with two decimals.

Read the comment above `Excess Late Orders`: a filter on `dim_state` reaches the fact table through the
relationship, so removing the filter on `fact_orders[customer_state]` alone is not enough.

## 5. One page (20 minutes)

- Cards: `Orders`, `Late Rate`, `Avg Review`, `Negative Review Rate`.
- Line and clustered column chart: X `dim_date[month_start]`, column `Orders`, line `Late Rate`.
- Matrix: rows `dim_state[region]` then `dim_state[state_name]`; values `Orders`, `Late Rate`, `Excess Late Orders`,
  `Avg Review`; sorted by `Excess Late Orders`.
- Bar chart: Y `fact_orders[route]`, X `Excess Late Orders`, visual filter *Top N* = 10 by `Excess Late Orders`.
- Clustered bar chart: Y `fact_orders[is_late]`, X `Avg Review`.

## 6. Check before the screenshot

The numbers must match `reports/results.json`:

| Measure | Expected |
|---|---|
| Orders | 96,470 |
| Late Rate | 6.8% |
| Avg Review | 4.16 |
| Negative Review Rate | 12.8% |
| Excess Late Orders, route SP -> RJ | ≈ 600 |
| Excess Late Orders by region | Nordeste ≈ +537, Sudeste ≈ −435 |
| Excess Late Orders, state RJ | ≈ 659 |

If every state or region shows 0, the measure lost `REMOVEFILTERS ( dim_state )`.

## 7. Save

Save as `powerbi/olist_delivery.pbix`, export a screenshot to `reports/figures/04_powerbi_report.png` and add it to
the main README.
