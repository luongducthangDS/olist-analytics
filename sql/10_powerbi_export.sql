-- Power BI star schema built from fct_orders (sql/00_model.sql).
-- Written to powerbi/*.csv by analysis/build_dashboard.py; keys and coverage are checked in tests/test_model.py.

CREATE OR REPLACE TABLE pbi_fact_orders AS
SELECT order_id, customer_unique_id, customer_state, seller_state, route, main_category, purchase_month,
       purchased_at::DATE AS purchase_date, delivery_days, days_late, is_late, items, items_value, freight_value,
       order_value, review_score
FROM fct_orders;

-- Customer states with their name and IBGE macro-region, so the report can drill region -> state.
CREATE OR REPLACE TABLE pbi_dim_state AS
SELECT state, n.state_name, n.region
FROM (SELECT DISTINCT customer_state AS state FROM fct_orders) s
LEFT JOIN (VALUES
    ('AC', 'Acre', 'Norte'), ('AP', 'Amapá', 'Norte'), ('AM', 'Amazonas', 'Norte'), ('PA', 'Pará', 'Norte'),
    ('RO', 'Rondônia', 'Norte'), ('RR', 'Roraima', 'Norte'), ('TO', 'Tocantins', 'Norte'),
    ('AL', 'Alagoas', 'Nordeste'), ('BA', 'Bahia', 'Nordeste'), ('CE', 'Ceará', 'Nordeste'),
    ('MA', 'Maranhão', 'Nordeste'), ('PB', 'Paraíba', 'Nordeste'), ('PE', 'Pernambuco', 'Nordeste'),
    ('PI', 'Piauí', 'Nordeste'), ('RN', 'Rio Grande do Norte', 'Nordeste'), ('SE', 'Sergipe', 'Nordeste'),
    ('DF', 'Distrito Federal', 'Centro-Oeste'), ('GO', 'Goiás', 'Centro-Oeste'), ('MT', 'Mato Grosso', 'Centro-Oeste'),
    ('MS', 'Mato Grosso do Sul', 'Centro-Oeste'),
    ('ES', 'Espírito Santo', 'Sudeste'), ('MG', 'Minas Gerais', 'Sudeste'), ('RJ', 'Rio de Janeiro', 'Sudeste'),
    ('SP', 'São Paulo', 'Sudeste'),
    ('PR', 'Paraná', 'Sul'), ('RS', 'Rio Grande do Sul', 'Sul'), ('SC', 'Santa Catarina', 'Sul')
) n(state, state_name, region) USING (state)
ORDER BY state;

CREATE OR REPLACE TABLE pbi_dim_category AS
SELECT DISTINCT main_category AS category FROM fct_orders ORDER BY 1;

CREATE OR REPLACE TABLE pbi_dim_date AS
SELECT d::DATE AS date, year(d) AS year, month(d) AS month, date_trunc('month', d)::DATE AS month_start
FROM range(DATE '2016-09-01', DATE '2018-09-01', INTERVAL 1 DAY) t(d);
