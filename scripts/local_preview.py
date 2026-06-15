import csv
import os
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_ORDERS = ROOT / "data" / "raw" / "orders.csv"
INSTACART_DIR = ROOT / "data" / "raw" / "instacart"
OUTPUT_DIR = ROOT / "data" / "processed"


def month_start(value: str) -> str:
    parsed = datetime.strptime(value, "%Y-%m-%d").date()
    return date(parsed.year, parsed.month, 1).isoformat()


def write_csv(name: str, rows: list[dict[str, object]], fields: list[str]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with (OUTPUT_DIR / name).open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def run_sample_preview() -> None:
    orders = []
    with SAMPLE_ORDERS.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        for row in reader:
            quantity = int(row["quantity"])
            unit_price = Decimal(row["unit_price"])
            if quantity <= 0 or unit_price < 0:
                continue
            row["order_id"] = int(row["order_id"])
            row["user_id"] = int(row["user_id"])
            row["product_id"] = int(row["product_id"])
            row["quantity"] = quantity
            row["unit_price"] = unit_price
            row["reordered"] = int(row["reordered"] or 0)
            row["line_revenue"] = quantity * unit_price
            row["sales_month"] = month_start(row["order_date"])
            orders.append(row)

    write_csv(
        "monthly_sales.csv",
        build_sample_monthly_sales(orders),
        ["sales_month", "order_count", "customer_count", "item_count", "gross_revenue", "avg_order_value"],
    )
    write_csv(
        "top_products.csv",
        build_sample_top_products(orders),
        ["product_id", "product_name", "department", "order_count", "total_quantity", "gross_revenue", "reorder_rate"],
    )
    write_csv(
        "customer_metrics.csv",
        build_sample_customer_metrics(orders),
        [
            "user_id",
            "order_count",
            "item_count",
            "gross_revenue",
            "first_order_date",
            "last_order_date",
            "active_months",
            "retention_flag",
        ],
    )
    write_csv(
        "category_performance.csv",
        build_sample_category_performance(orders),
        ["department", "order_count", "product_count", "item_count", "gross_revenue"],
    )
    write_csv(
        "ml_customer_features.csv",
        build_sample_ml_customer_features(orders),
        [
            "user_id",
            "order_count",
            "item_count",
            "gross_revenue",
            "avg_line_revenue",
            "avg_item_quantity",
            "reorder_rate",
            "department_count",
            "active_months",
            "last_order_date",
            "repeat_customer_label",
        ],
    )
    print(f"Wrote sample analytics preview files to {OUTPUT_DIR}")


def build_sample_monthly_sales(orders: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped = defaultdict(lambda: {"orders": set(), "customers": set(), "items": 0, "revenue": Decimal("0")})
    for row in orders:
        group = grouped[row["sales_month"]]
        group["orders"].add(row["order_id"])
        group["customers"].add(row["user_id"])
        group["items"] += row["quantity"]
        group["revenue"] += row["line_revenue"]

    output = []
    for sales_month, group in sorted(grouped.items()):
        order_count = len(group["orders"])
        revenue = group["revenue"]
        output.append(
            {
                "sales_month": sales_month,
                "order_count": order_count,
                "customer_count": len(group["customers"]),
                "item_count": group["items"],
                "gross_revenue": f"{revenue:.2f}",
                "avg_order_value": f"{(revenue / order_count):.2f}",
            }
        )
    return output


def build_sample_top_products(orders: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped = defaultdict(
        lambda: {
            "product_name": "",
            "department": "",
            "orders": set(),
            "quantity": 0,
            "revenue": Decimal("0"),
            "reorders": 0,
            "rows": 0,
        }
    )
    for row in orders:
        group = grouped[row["product_id"]]
        group["product_name"] = row["product_name"]
        group["department"] = row["department"]
        group["orders"].add(row["order_id"])
        group["quantity"] += row["quantity"]
        group["revenue"] += row["line_revenue"]
        group["reorders"] += row["reordered"]
        group["rows"] += 1

    output = []
    for product_id, group in grouped.items():
        output.append(
            {
                "product_id": product_id,
                "product_name": group["product_name"],
                "department": group["department"],
                "order_count": len(group["orders"]),
                "total_quantity": group["quantity"],
                "gross_revenue": f"{group['revenue']:.2f}",
                "reorder_rate": f"{group['reorders'] / group['rows']:.4f}",
            }
        )
    return sorted(output, key=lambda row: (-row["total_quantity"], -Decimal(row["gross_revenue"])))


def build_sample_customer_metrics(orders: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped = defaultdict(lambda: {"orders": set(), "items": 0, "revenue": Decimal("0"), "dates": [], "months": set()})
    for row in orders:
        group = grouped[row["user_id"]]
        group["orders"].add(row["order_id"])
        group["items"] += row["quantity"]
        group["revenue"] += row["line_revenue"]
        group["dates"].append(row["order_date"])
        group["months"].add(row["sales_month"])

    output = []
    for user_id, group in grouped.items():
        order_count = len(group["orders"])
        output.append(
            {
                "user_id": user_id,
                "order_count": order_count,
                "item_count": group["items"],
                "gross_revenue": f"{group['revenue']:.2f}",
                "first_order_date": min(group["dates"]),
                "last_order_date": max(group["dates"]),
                "active_months": len(group["months"]),
                "retention_flag": order_count > 1,
            }
        )
    return sorted(output, key=lambda row: -Decimal(row["gross_revenue"]))


def build_sample_category_performance(orders: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped = defaultdict(lambda: {"orders": set(), "products": set(), "items": 0, "revenue": Decimal("0")})
    for row in orders:
        group = grouped[row["department"]]
        group["orders"].add(row["order_id"])
        group["products"].add(row["product_id"])
        group["items"] += row["quantity"]
        group["revenue"] += row["line_revenue"]

    output = []
    for department, group in grouped.items():
        output.append(
            {
                "department": department,
                "order_count": len(group["orders"]),
                "product_count": len(group["products"]),
                "item_count": group["items"],
                "gross_revenue": f"{group['revenue']:.2f}",
            }
        )
    return sorted(output, key=lambda row: -Decimal(row["gross_revenue"]))


def build_sample_ml_customer_features(orders: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped = defaultdict(
        lambda: {
            "orders": set(),
            "items": 0,
            "revenue": Decimal("0"),
            "line_revenues": [],
            "quantities": [],
            "reorders": 0,
            "rows": 0,
            "departments": set(),
            "months": set(),
            "dates": [],
        }
    )
    for row in orders:
        group = grouped[row["user_id"]]
        group["orders"].add(row["order_id"])
        group["items"] += row["quantity"]
        group["revenue"] += row["line_revenue"]
        group["line_revenues"].append(row["line_revenue"])
        group["quantities"].append(row["quantity"])
        group["reorders"] += row["reordered"]
        group["rows"] += 1
        group["departments"].add(row["department"])
        group["months"].add(row["sales_month"])
        group["dates"].append(row["order_date"])

    output = []
    for user_id, group in grouped.items():
        order_count = len(group["orders"])
        output.append(
            {
                "user_id": user_id,
                "order_count": order_count,
                "item_count": group["items"],
                "gross_revenue": f"{group['revenue']:.2f}",
                "avg_line_revenue": f"{sum(group['line_revenues'], Decimal('0')) / group['rows']:.2f}",
                "avg_item_quantity": f"{sum(group['quantities']) / group['rows']:.2f}",
                "reorder_rate": f"{group['reorders'] / group['rows']:.4f}",
                "department_count": len(group["departments"]),
                "active_months": len(group["months"]),
                "last_order_date": max(group["dates"]),
                "repeat_customer_label": order_count > 1,
            }
        )
    return sorted(output, key=lambda row: row["user_id"])


def load_lookup(path: Path, key: str) -> dict[int, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as source:
        return {int(row[key]): row for row in csv.DictReader(source)}


def build_order_calendar() -> dict[int, dict[str, object]]:
    orders = {}
    user_dates = defaultdict(lambda: date(2025, 1, 1))
    with (INSTACART_DIR / "orders.csv").open(newline="", encoding="utf-8") as source:
        for row in csv.DictReader(source):
            user_id = int(row["user_id"])
            days_since_prior = row["days_since_prior_order"]
            if row["order_number"] != "1" and days_since_prior:
                user_dates[user_id] += timedelta(days=int(float(days_since_prior)))
            order_date = user_dates[user_id]
            orders[int(row["order_id"])] = {
                "user_id": user_id,
                "eval_set": row["eval_set"],
                "order_number": int(row["order_number"]),
                "order_dow": int(row["order_dow"]),
                "order_hour_of_day": int(row["order_hour_of_day"]),
                "order_date": order_date.isoformat(),
                "sales_month": date(order_date.year, order_date.month, 1).isoformat(),
            }
    return orders


def order_product_paths() -> list[Path]:
    return [
        INSTACART_DIR / "order_products__prior.csv",
        INSTACART_DIR / "order_products__train.csv",
    ]


def configured_row_limit() -> int | None:
    value = os.getenv("INSTACART_MAX_ROWS", "250000")
    if value in {"", "0", "all", "ALL"}:
        return None
    return int(value)


def run_instacart_preview() -> None:
    required = [
        INSTACART_DIR / "aisles.csv",
        INSTACART_DIR / "departments.csv",
        INSTACART_DIR / "orders.csv",
        INSTACART_DIR / "products.csv",
        *order_product_paths(),
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"missing Instacart files: {missing}")

    row_limit = configured_row_limit()
    aisles = load_lookup(INSTACART_DIR / "aisles.csv", "aisle_id")
    departments = load_lookup(INSTACART_DIR / "departments.csv", "department_id")
    products = load_lookup(INSTACART_DIR / "products.csv", "product_id")
    orders = build_order_calendar()

    monthly = defaultdict(lambda: {"orders": set(), "customers": set(), "items": 0})
    products_out = defaultdict(lambda: {"name": "", "department": "", "orders": set(), "items": 0, "reorders": 0, "rows": 0})
    customers = defaultdict(
        lambda: {"orders": set(), "items": 0, "dates": [], "months": set(), "departments": set(), "reorders": 0, "rows": 0}
    )
    categories = defaultdict(lambda: {"orders": set(), "products": set(), "items": 0})

    processed = 0
    for path in order_product_paths():
        with path.open(newline="", encoding="utf-8") as source:
            for row in csv.DictReader(source):
                order_id = int(row["order_id"])
                order = orders.get(order_id)
                if not order:
                    continue

                product_id = int(row["product_id"])
                product = products[product_id]
                department = departments[int(product["department_id"])]["department"]
                aisle = aisles[int(product["aisle_id"])]["aisle"]
                reordered = int(row["reordered"])

                month_group = monthly[order["sales_month"]]
                month_group["orders"].add(order_id)
                month_group["customers"].add(order["user_id"])
                month_group["items"] += 1

                product_group = products_out[product_id]
                product_group["name"] = product["product_name"]
                product_group["department"] = department
                product_group["orders"].add(order_id)
                product_group["items"] += 1
                product_group["reorders"] += reordered
                product_group["rows"] += 1

                customer_group = customers[order["user_id"]]
                customer_group["orders"].add(order_id)
                customer_group["items"] += 1
                customer_group["dates"].append(order["order_date"])
                customer_group["months"].add(order["sales_month"])
                customer_group["departments"].add(department)
                customer_group["reorders"] += reordered
                customer_group["rows"] += 1

                category_group = categories[department]
                category_group["orders"].add(order_id)
                category_group["products"].add(product_id)
                category_group["items"] += 1

                processed += 1
                if row_limit and processed >= row_limit:
                    break
        if row_limit and processed >= row_limit:
            break

    monthly_rows = [
        {
            "sales_month": month,
            "order_count": len(group["orders"]),
            "customer_count": len(group["customers"]),
            "item_count": group["items"],
            "avg_basket_size": f"{group['items'] / len(group['orders']):.2f}",
        }
        for month, group in sorted(monthly.items())
    ]
    product_rows = [
        {
            "product_id": product_id,
            "product_name": group["name"],
            "department": group["department"],
            "order_count": len(group["orders"]),
            "item_count": group["items"],
            "reorder_rate": f"{group['reorders'] / group['rows']:.4f}",
        }
        for product_id, group in products_out.items()
    ]
    customer_rows = [
        {
            "user_id": user_id,
            "order_count": len(group["orders"]),
            "item_count": group["items"],
            "first_order_date": min(group["dates"]),
            "last_order_date": max(group["dates"]),
            "active_months": len(group["months"]),
            "retention_flag": len(group["orders"]) > 1,
        }
        for user_id, group in customers.items()
    ]
    category_rows = [
        {
            "department": department,
            "order_count": len(group["orders"]),
            "product_count": len(group["products"]),
            "item_count": group["items"],
        }
        for department, group in categories.items()
    ]
    feature_rows = [
        {
            "user_id": user_id,
            "order_count": len(group["orders"]),
            "item_count": group["items"],
            "avg_basket_lines": f"{group['items'] / len(group['orders']):.2f}",
            "reorder_rate": f"{group['reorders'] / group['rows']:.4f}",
            "department_count": len(group["departments"]),
            "active_months": len(group["months"]),
            "last_order_date": max(group["dates"]),
            "repeat_customer_label": len(group["orders"]) > 1,
        }
        for user_id, group in customers.items()
    ]

    write_csv(
        "instacart_monthly_sales.csv",
        monthly_rows,
        ["sales_month", "order_count", "customer_count", "item_count", "avg_basket_size"],
    )
    write_csv(
        "instacart_top_products.csv",
        sorted(product_rows, key=lambda row: (-row["item_count"], row["product_name"]))[:100],
        ["product_id", "product_name", "department", "order_count", "item_count", "reorder_rate"],
    )
    write_csv(
        "instacart_customer_metrics.csv",
        sorted(customer_rows, key=lambda row: -row["item_count"])[:1000],
        ["user_id", "order_count", "item_count", "first_order_date", "last_order_date", "active_months", "retention_flag"],
    )
    write_csv(
        "instacart_category_performance.csv",
        sorted(category_rows, key=lambda row: -row["item_count"]),
        ["department", "order_count", "product_count", "item_count"],
    )
    write_csv(
        "instacart_ml_customer_features.csv",
        sorted(feature_rows, key=lambda row: row["user_id"])[:1000],
        [
            "user_id",
            "order_count",
            "item_count",
            "avg_basket_lines",
            "reorder_rate",
            "department_count",
            "active_months",
            "last_order_date",
            "repeat_customer_label",
        ],
    )
    limit_text = "all rows" if row_limit is None else f"{processed:,} order-product rows"
    print(f"Wrote Instacart analytics preview for {limit_text} to {OUTPUT_DIR}")


def main() -> None:
    if INSTACART_DIR.exists():
        run_instacart_preview()
    else:
        run_sample_preview()


if __name__ == "__main__":
    main()
