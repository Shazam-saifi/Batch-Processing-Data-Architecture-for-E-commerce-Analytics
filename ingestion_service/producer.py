#importing 
import csv
import json
import logging
import os
from decimal import Decimal, InvalidOperation
from pathlib import Path
from time import sleep

from confluent_kafka import Producer


REQUIRED_FIELDS = {
    "order_id",
    "user_id",
    "product_id",
    "product_name",
    "department",
    "quantity",
    "unit_price",
    "order_date",
}


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def validate_row(row: dict[str, str], line_number: int) -> dict[str, object]:
    missing = [field for field in REQUIRED_FIELDS if not row.get(field)]
    if missing:
        raise ValueError(f"line {line_number}: missing required fields {missing}")

    try:
        quantity = int(row["quantity"])
        unit_price = Decimal(row["unit_price"])
    except (ValueError, InvalidOperation) as exc:
        raise ValueError(f"line {line_number}: invalid numeric value") from exc

    if quantity <= 0 or unit_price < 0:
        raise ValueError(f"line {line_number}: quantity and price must be positive")

    cleaned = dict(row)
    cleaned["order_id"] = int(row["order_id"])
    cleaned["user_id"] = int(row["user_id"])
    cleaned["product_id"] = int(row["product_id"])
    cleaned["quantity"] = quantity
    cleaned["unit_price"] = float(unit_price)
    cleaned["reordered"] = int(row.get("reordered") or 0)
    cleaned["days_since_prior_order"] = (
        int(row["days_since_prior_order"]) if row.get("days_since_prior_order") else None
    )
    return cleaned


def delivery_report(error, message) -> None:
    if error is not None:
        logging.error("Kafka delivery failed: %s", error)
        return
    logging.debug("Delivered record to %s [%s]", message.topic(), message.partition())


def main() -> None:
    configure_logging()
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    topic = os.getenv("KAFKA_TOPIC", "ecommerce.orders")
    raw_path = Path(os.getenv("RAW_ORDERS_PATH", "/app/data/raw/orders.csv"))

    if not raw_path.exists():
        raise FileNotFoundError(f"raw dataset not found: {raw_path}")

    producer = Producer({"bootstrap.servers": bootstrap_servers})
    published = 0
    rejected = 0

    with raw_path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        for line_number, row in enumerate(reader, start=2):
            try:
                record = validate_row(row, line_number)
            except ValueError as exc:
                rejected += 1
                logging.warning("Rejected row: %s", exc)
                continue

            producer.produce(
                topic,
                key=str(record["order_id"]),
                value=json.dumps(record),
                callback=delivery_report,
            )
            producer.poll(0)
            published += 1

            if published % 1000 == 0:
                logging.info("Published %s records", published)
                sleep(0.1)

    producer.flush()
    logging.info("Ingestion finished: %s published, %s rejected", published, rejected)


if __name__ == "__main__":
    main()

