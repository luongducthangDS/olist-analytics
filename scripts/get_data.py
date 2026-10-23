"""Download the public Olist dataset (official olist/work-at-olist-data repo) into data/raw/."""
import urllib.request
from pathlib import Path

BASE = "https://raw.githubusercontent.com/olist/work-at-olist-data/master/datasets/"
FILES = ["olist_customers_dataset.csv", "olist_order_items_dataset.csv", "olist_order_payments_dataset.csv",
         "olist_order_reviews_dataset.csv", "olist_orders_dataset.csv", "olist_products_dataset.csv",
         "olist_sellers_dataset.csv", "product_category_name_translation.csv"]
raw = Path(__file__).resolve().parents[1] / "data" / "raw"
raw.mkdir(parents=True, exist_ok=True)
for f in FILES:
    if not (raw / f).exists():
        print("downloading", f)
        urllib.request.urlretrieve(BASE + f, raw / f)
print("data ready in", raw)
