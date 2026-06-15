from pyspark.sql import SparkSession

from spark_jobs.batch_analytics import (
    category_performance,
    clean_orders,
    customer_metrics,
    ml_customer_features,
    monthly_sales,
    top_products,
)


def test_batch_aggregations():
    spark = SparkSession.builder.master("local[1]").appName("test-ecommerce-analytics").getOrCreate()
    rows = [
        (1, 101, 1, 1, 9, None, 10, "Banana", "fresh fruits", "produce", 2, 0.5, 0, "2025-01-03"),
        (2, 101, 2, 2, 10, 4, 10, "Banana", "fresh fruits", "produce", 3, 0.5, 1, "2025-01-07"),
        (3, 102, 1, 3, 11, None, 20, "Spinach", "vegetables", "produce", 1, 4.0, 0, "2025-02-01"),
    ]
    columns = [
        "order_id",
        "user_id",
        "order_number",
        "order_dow",
        "order_hour_of_day",
        "days_since_prior_order",
        "product_id",
        "product_name",
        "aisle",
        "department",
        "quantity",
        "unit_price",
        "reordered",
        "order_date",
    ]
    frame = spark.createDataFrame(rows, columns)
    frame = frame.withColumn("order_date", frame.order_date.cast("date"))

    cleaned = clean_orders(frame)

    sales = {str(row.sales_month): row.gross_revenue for row in monthly_sales(cleaned).collect()}
    assert sales["2025-01-01"] == 2.5
    assert sales["2025-02-01"] == 4.0

    products = top_products(cleaned).collect()
    assert products[0].product_name == "Banana"
    assert products[0].total_quantity == 5

    customers = {row.user_id: row.retention_flag for row in customer_metrics(cleaned).collect()}
    assert customers[101] is True
    assert customers[102] is False

    categories = category_performance(cleaned).collect()
    assert categories[0].department == "produce"
    assert categories[0].gross_revenue == 6.5

    features = {row.user_id: row for row in ml_customer_features(cleaned).collect()}
    assert features[101].order_count == 2
    assert features[101].repeat_customer_label is True
    assert features[102].department_count == 1

    spark.stop()
