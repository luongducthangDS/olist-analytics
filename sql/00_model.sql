-- Analysis model: one row per DELIVERED order, enriched with delivery timing, value, product and review.
-- Built in DuckDB straight from the raw Olist CSVs (run by analysis/build_model.py).

CREATE OR REPLACE TABLE category_translation AS
SELECT * FROM read_csv('data/raw/product_category_name_translation.csv', header = true);

-- Olist allows several reviews per order; keep the latest answer so each order counts once.
CREATE OR REPLACE TABLE order_review AS
SELECT order_id, review_score, review_comment_message IS NOT NULL AS has_comment
FROM read_csv('data/raw/olist_order_reviews_dataset.csv', header = true)
QUALIFY row_number() OVER (PARTITION BY order_id ORDER BY review_answer_timestamp DESC) = 1;

-- Item-level facts rolled up to the order. "Main" category / seller = the most expensive item's.
CREATE OR REPLACE TABLE order_value AS
WITH items AS (
    SELECT i.order_id, i.price, i.freight_value, s.seller_state,
           coalesce(t.product_category_name_english, p.product_category_name, 'unknown') AS category,
           row_number() OVER (PARTITION BY i.order_id ORDER BY i.price DESC, i.order_item_id) AS rk
    FROM read_csv('data/raw/olist_order_items_dataset.csv', header = true) i
    JOIN read_csv('data/raw/olist_products_dataset.csv', header = true) p USING (product_id)
    JOIN read_csv('data/raw/olist_sellers_dataset.csv', header = true) s USING (seller_id)
    LEFT JOIN category_translation t USING (product_category_name)
)
SELECT order_id,
       count(*)                                     AS items,
       sum(price)                                   AS items_value,
       sum(freight_value)                           AS freight_value,
       max(CASE WHEN rk = 1 THEN category END)      AS main_category,
       max(CASE WHEN rk = 1 THEN seller_state END)  AS seller_state
FROM items
GROUP BY order_id;

CREATE OR REPLACE TABLE fct_orders AS
SELECT
    o.order_id,
    c.customer_unique_id,
    c.customer_state,
    v.seller_state,
    v.seller_state || ' -> ' || c.customer_state                             AS route,
    c.customer_state = v.seller_state                                        AS same_state,
    o.order_purchase_timestamp                                               AS purchased_at,
    date_trunc('month', o.order_purchase_timestamp)::DATE                    AS purchase_month,
    o.order_delivered_customer_date                                          AS delivered_at,
    o.order_estimated_delivery_date                                          AS promised_at,
    date_diff('day', o.order_purchase_timestamp, o.order_delivered_customer_date) AS delivery_days,
    date_diff('day', o.order_estimated_delivery_date::DATE, o.order_delivered_customer_date::DATE) AS days_late,
    o.order_delivered_customer_date::DATE > o.order_estimated_delivery_date::DATE AS is_late,
    v.items, v.items_value, v.freight_value,
    v.items_value + v.freight_value                                          AS order_value,
    v.freight_value / nullif(v.items_value, 0)                               AS freight_ratio,
    v.main_category,
    r.review_score,
    r.has_comment
FROM read_csv('data/raw/olist_orders_dataset.csv', header = true) o
JOIN read_csv('data/raw/olist_customers_dataset.csv', header = true) c USING (customer_id)
JOIN order_value v USING (order_id)
LEFT JOIN order_review r USING (order_id)
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL;
