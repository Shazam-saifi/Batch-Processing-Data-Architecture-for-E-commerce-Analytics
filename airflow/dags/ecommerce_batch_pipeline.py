from __future__ import annotations

import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator


default_args = {
    "owner": "data-engineering",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

PROJECT_DIR = os.getenv("AIRFLOW_PROJECT_DIR", "/opt/airflow/project")


with DAG(
    dag_id="ecommerce_batch_pipeline",
    description="Ingest Instacart-style orders and build batch analytics outputs.",
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["ecommerce", "batch", "analytics"],
) as dag:
    validate_source = BashOperator(
        task_id="validate_source_file",
        bash_command="test -s /opt/airflow/data/raw/orders.csv",
    )

    ingest_orders = BashOperator(
        task_id="ingest_orders_to_kafka",
        bash_command="docker compose run --rm --build ingestion",
        cwd=PROJECT_DIR,
    )

    run_spark_batch = BashOperator(
        task_id="run_spark_batch_analytics",
        bash_command="docker compose run --rm --build spark-job",
        cwd=PROJECT_DIR,
    )

    validate_source >> ingest_orders >> run_spark_batch
