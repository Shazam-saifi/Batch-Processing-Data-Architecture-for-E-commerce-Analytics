# Batch Processing Data Architecture for E-commerce Analytics

This project implements the submitted conception-phase design as a containerized batch-processing data architecture for e-commerce analytics using an Instacart-style dataset.

The system ingests raw order data, publishes validated records to Kafka, processes scheduled batch analytics with Spark, stores curated outputs in PostgreSQL, exposes ML-ready customer features, and orchestrates the workflow with Airflow.

## Architecture

```text
Raw CSV Files
    |
    v
Data Ingestion Service
    |
    v
Apache Kafka Topic: ecommerce.orders
    |
    v
Apache Spark Batch Job
    |
    v
PostgreSQL Analytics Tables
    |
    v
ML Customer Feature Table
    |
    v
Airflow Scheduling and Monitoring
```

## Microservices

| Service | Purpose | Technology |
| --- | --- | --- |
| Data ingestion | Validates raw order rows and publishes them to Kafka | Python, Docker |
| Kafka | Decouples ingestion from processing and persists messages | Apache Kafka |
| Spark | Cleans data and generates batch aggregates | PySpark |
| PostgreSQL | Stores structured analytics outputs | PostgreSQL |
| Airflow | Orchestrates daily, weekly, and monthly workflows | Apache Airflow |
| ML delivery layer | Publishes customer-level feature outputs for model training or scoring | PostgreSQL, CSV preview |

## Business Insights

The batch job produces these analytics tables:

- `monthly_sales`: monthly order and revenue trends
- `top_products`: most purchased products by quantity and revenue
- `customer_metrics`: customer purchase frequency, spend, retention indicators
- `category_performance`: product category revenue and basket behavior
- `ml_customer_features`: model-ready customer features and repeat-customer label

## Project Structure

```text
.
├── airflow/dags/ecommerce_batch_pipeline.py
├── data/raw/orders.csv
├── docker-compose.yml
├── docs/architecture.md
├── ingestion_service/
│   ├── Dockerfile
│   ├── producer.py
│   └── requirements.txt
├── spark_jobs/
│   ├── Dockerfile
│   ├── batch_analytics.py
│   └── requirements.txt
├── sql/init.sql
├── scripts/run_local_batch.sh
└── tests/test_transformations.py
```

## Quick Start

### Local Preview Without Docker

If Docker is not installed, you can still run a dependency-free preview of the analytics logic:

```bash
python3 scripts/local_preview.py
```

This writes CSV outputs to `data/processed/`.

When the official Instacart archive exists at `data/raw/instacart/`, the preview writes:

```text
instacart_monthly_sales.csv
instacart_top_products.csv
instacart_customer_metrics.csv
instacart_category_performance.csv
instacart_ml_customer_features.csv
```

The default preview uses the first 250,000 order-product rows so it runs quickly:

```bash
python3 scripts/local_preview.py
```

To process more rows:

```bash
INSTACART_MAX_ROWS=1000000 python3 scripts/local_preview.py
```

To process the full archive:

```bash
INSTACART_MAX_ROWS=0 python3 scripts/local_preview.py
```

### Full Container Stack

1. Review the example environment values:

   ```bash
   cat .env.example
   ```

   The Docker Compose stack uses these local defaults. Create a `.env` file only if you want to keep private overrides outside version control.

2. Start the stack:

   ```bash
   docker compose up --build
   ```

3. In another terminal, run ingestion:

   ```bash
   docker compose run --rm --build ingestion
   ```

4. Run the Spark batch job:

   ```bash
   docker compose run --rm --build spark-job
   ```

5. Query PostgreSQL:

   ```bash
   docker compose exec postgres psql -U ecommerce -d ecommerce_analytics
   ```

   PostgreSQL is also exposed on host port `5433` by default to avoid conflicts
   with local database installs. Override it with `POSTGRES_HOST_PORT=5432`
   if you want the original host port.

   Example:

   ```sql
   select * from analytics.monthly_sales;
   select * from analytics.top_products limit 10;
   select * from analytics.ml_customer_features limit 10;
   ```

Airflow UI is available at `http://localhost:8081` by default after the stack is
running. Kafka is exposed on host port `19092` by default. Override these with
`AIRFLOW_HOST_PORT=8080` or `KAFKA_HOST_PORT=9092` if you want the original host
ports. Default credentials are configured in `.env.example`.

## Dataset

The project includes two dataset options:

- `data/raw/orders.csv`: a small Instacart-like sample file for quick Docker pipeline demos.
- `data/raw/instacart/`: the official Instacart Market Basket Analysis archive.

The official archive contains:

```text
aisles.csv
departments.csv
order_products__prior.csv
order_products__train.csv
orders.csv
products.csv
```

The official Instacart data does not include prices or real calendar dates. The local preview reconstructs approximate order dates from `days_since_prior_order` and reports basket volume metrics instead of true revenue.

## Conception Phase Alignment

| PDF section | Project implementation |
| --- | --- |
| Project overview | README objective and end-to-end batch analytics workflow |
| Selected dataset | Sample Instacart-like file plus official Instacart archive support |
| System architecture | Ingestion, Kafka, Spark, PostgreSQL, Airflow, and ML feature delivery |
| Microservices design | Dedicated Docker services for ingestion, messaging, processing, storage, and orchestration |
| Docker and IaC | `docker-compose.yml`, service Dockerfiles, environment configuration, and SQL schema |
| Reliability | Kafka durability, Airflow retries, PostgreSQL health checks, restart policies |
| Scalability | Kafka partitions, Spark batch processing, independent service scaling |
| Maintainability | Modular Python services, documented architecture, repeatable local preview, tests |
| Security and governance | Environment-based credentials, validation, logs, version-controlled infrastructure |
| Advantages and disadvantages | Documented trade-offs in `docs/architecture.md` |
| Conclusion | Working prototype demonstrates the proposed conception-phase architecture |

## Reliability

- Kafka topic persistence keeps ingested records durable.
- Airflow tasks use retries and retry delays.
- Docker restart policies are set on long-running services.
- PostgreSQL stores processed outputs in typed analytics tables.
- Service boundaries isolate failures between ingestion, messaging, processing, and storage.

## Scalability

- Kafka topic partitioning supports higher ingestion throughput.
- Spark jobs can move from local mode to a distributed Spark cluster.
- Each service can scale independently behind its container boundary.
- Batch outputs are append-safe and can be partitioned by processing date.

## Security and Governance

- Credentials are provided through environment variables.
- Raw ingestion validates required fields and numeric values.
- Processing writes logs for observability.
- Infrastructure configuration is version controlled.
- Database volumes can be backed up independently from application containers.
- ML-ready outputs are generated from curated analytics data rather than directly from unchecked raw files.
