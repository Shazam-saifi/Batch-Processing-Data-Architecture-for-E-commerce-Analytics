#importing
import logging
import os
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DateType,
    DoubleType,
    IntegerType,
    StructField,
    StructType,
    StringType,
)


ORDER_SCHEMA = StructType(
    [
        StructField("order_id", IntegerType(), False),
        StructField("user_id", IntegerType(), False),
        StructField("order_number", IntegerType(), True),
        StructField("order_dow", IntegerType(), True),
        StructField("order_hour_of_day", IntegerType(), True),
        StructField("days_since_prior_order", IntegerType(), True),
        StructField("product_id", IntegerType(), False),
        StructField("product_name", StringType(), False),
        StructField("aisle", StringType(), True),
        StructField("department", StringType(), False),
        StructField("quantity", IntegerType(), False),
        StructField("unit_price", DoubleType(), False),
        StructField("reordered", IntegerType(), True),
        StructField("order_date", DateType(), False),
    ]
)


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def clean_orders(orders: DataFrame) -> DataFrame:
    return (
        orders.dropna(subset=["order_id", "user_id", "product_id", "quantity", "unit_price", "order_date"])
        .filter((F.col("quantity") > 0) & (F.col("unit_price") >= 0))
        .withColumn("line_revenue", F.round(F.col("quantity") * F.col("unit_price"), 2))
        .withColumn("sales_month", F.trunc(F.col("order_date"), "month"))
        .withColumn("is_reordered", F.coalesce(F.col("reordered"), F.lit(0)))
    )


def monthly_sales(cleaned: DataFrame) -> DataFrame:
    per_order = cleaned.groupBy("sales_month", "order_id").agg(
        F.first("user_id").alias("user_id"),
        F.sum("quantity").alias("order_items"),
        F.sum("line_revenue").alias("order_revenue"),
    )
    return (
        per_order.groupBy("sales_month")
        .agg(
            F.countDistinct("order_id").cast("int").alias("order_count"),
            F.countDistinct("user_id").cast("int").alias("customer_count"),
            F.sum("order_items").cast("int").alias("item_count"),
            F.round(F.sum("order_revenue"), 2).alias("gross_revenue"),
            F.round(F.avg("order_revenue"), 2).alias("avg_order_value"),
        )
        .orderBy("sales_month")
    )


def top_products(cleaned: DataFrame) -> DataFrame:
    return (
        cleaned.groupBy("product_id", "product_name", "department")
        .agg(
            F.countDistinct("order_id").cast("int").alias("order_count"),
            F.sum("quantity").cast("int").alias("total_quantity"),
            F.round(F.sum("line_revenue"), 2).alias("gross_revenue"),
            F.round(F.avg("is_reordered"), 4).alias("reorder_rate"),
        )
        .orderBy(F.desc("total_quantity"), F.desc("gross_revenue"))
    )


def customer_metrics(cleaned: DataFrame) -> DataFrame:
    return (
        cleaned.groupBy("user_id")
        .agg(
            F.countDistinct("order_id").cast("int").alias("order_count"),
            F.sum("quantity").cast("int").alias("item_count"),
            F.round(F.sum("line_revenue"), 2).alias("gross_revenue"),
            F.min("order_date").alias("first_order_date"),
            F.max("order_date").alias("last_order_date"),
            F.countDistinct("sales_month").cast("int").alias("active_months"),
        )
        .withColumn("retention_flag", F.col("order_count") > 1)
        .orderBy(F.desc("gross_revenue"))
    )


def category_performance(cleaned: DataFrame) -> DataFrame:
    return (
        cleaned.groupBy("department")
        .agg(
            F.countDistinct("order_id").cast("int").alias("order_count"),
            F.countDistinct("product_id").cast("int").alias("product_count"),
            F.sum("quantity").cast("int").alias("item_count"),
            F.round(F.sum("line_revenue"), 2).alias("gross_revenue"),
        )
        .orderBy(F.desc("gross_revenue"))
    )


def ml_customer_features(cleaned: DataFrame) -> DataFrame:
    return (
        cleaned.groupBy("user_id")
        .agg(
            F.countDistinct("order_id").cast("int").alias("order_count"),
            F.sum("quantity").cast("int").alias("item_count"),
            F.round(F.sum("line_revenue"), 2).alias("gross_revenue"),
            F.round(F.avg("line_revenue"), 2).alias("avg_line_revenue"),
            F.round(F.avg("quantity"), 2).alias("avg_item_quantity"),
            F.round(F.avg("is_reordered"), 4).alias("reorder_rate"),
            F.countDistinct("department").cast("int").alias("department_count"),
            F.countDistinct("sales_month").cast("int").alias("active_months"),
            F.max("order_date").alias("last_order_date"),
        )
        .withColumn("repeat_customer_label", F.col("order_count") > 1)
        .orderBy("user_id")
    )


def write_table(frame: DataFrame, table_name: str) -> None:
    db = os.getenv("POSTGRES_DB", "ecommerce_analytics")
    user = os.getenv("POSTGRES_USER", "ecommerce")
    password = os.getenv("POSTGRES_PASSWORD", "ecommerce_password")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    url = f"jdbc:postgresql://{host}:{port}/{db}"

    frame.write.format("jdbc").mode("overwrite").option("url", url).option(
        "dbtable", f"analytics.{table_name}"
    ).option("user", user).option("password", password).option("driver", "org.postgresql.Driver").save()


def main() -> None:
    configure_logging()
    raw_path = Path(os.getenv("RAW_ORDERS_PATH", "/app/data/raw/orders.csv"))
    spark = (
        SparkSession.builder.appName("ecommerce-batch-analytics")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )

    logging.info("Reading raw orders from %s", raw_path)
    orders = spark.read.csv(str(raw_path), header=True, schema=ORDER_SCHEMA)
    cleaned = clean_orders(orders).cache()

    outputs = {
        "monthly_sales": monthly_sales(cleaned),
        "top_products": top_products(cleaned),
        "customer_metrics": customer_metrics(cleaned),
        "category_performance": category_performance(cleaned),
        "ml_customer_features": ml_customer_features(cleaned),
    }

    for table_name, frame in outputs.items():
        logging.info("Writing analytics.%s", table_name)
        write_table(frame, table_name)

    spark.stop()
    logging.info("Batch analytics completed")


if __name__ == "__main__":
    main()
