# Architecture Notes

## Objective

Design a scalable, reliable, and maintainable batch-processing architecture for large e-commerce transaction data. The implementation follows the submitted conception-phase microservices model and uses Docker for reproducible deployment.

## Data Flow

1. Raw Instacart-style CSV files are placed in `data/raw`.
2. The ingestion service validates required fields and publishes clean order-line records to Kafka.
3. Kafka persists records on the `ecommerce.orders` topic and decouples ingestion from processing.
4. Spark reads the validated batch file in this local implementation and produces business aggregates.
5. PostgreSQL stores curated analytics tables in the `analytics` schema.
6. The ML delivery layer exposes customer-level feature records in `analytics.ml_customer_features`.
7. Airflow schedules and monitors the pipeline with retry behavior.

Kafka is included as the durable ingestion buffer proposed in the conception phase. For the local batch prototype, Spark reads the CSV source directly so the project can run without a long-lived Kafka consumer checkpoint. In a production extension, the Spark source can be changed to Kafka or to a Kafka-backed landing table without changing the downstream analytics tables.

## Processing Logic

Spark performs:

- null handling on required identifiers, dates, quantity, and price.
- invalid row filtering for non-positive quantities and negative prices
- line revenue calculation
- monthly sales aggregation
- product ranking and reorder-rate calculation
- customer metrics and retention flag calculation
- department-level category performance
- customer-level ML feature engineering and repeat-customer labeling

## Analytics and ML Outputs

| Output | Purpose |
| --- | --- |
| `analytics.monthly_sales` | Tracks monthly order volume, customer count, item count, revenue, and average order value |
| `analytics.top_products` | Ranks products by quantity, revenue, and reorder behavior |
| `analytics.customer_metrics` | Summarizes customer purchase frequency, value, and retention signals |
| `analytics.category_performance` | Compares department-level order, product, item, and revenue performance |
| `analytics.ml_customer_features` | Provides model-ready features such as order count, spend, reorder rate, category breadth, activity months, and repeat-customer label |

## Reliability Design

- Kafka uses persisted topics and partitioning.
- Airflow tasks retry failed steps.
- PostgreSQL health checks prevent dependent jobs from running too early.
- Containers isolate services and use restart policies where appropriate.
- Database data is stored in a named Docker volume.
- The local preview can regenerate analytics CSVs from raw data when the full container stack is unavailable.

## Scalability Design

- Kafka partitions can be increased for higher throughput.
- Spark can be pointed at a cluster manager for distributed execution.
- Services can be scaled independently.
- Output tables can be partitioned by date for larger historical loads.
- The ML delivery table can be consumed by downstream model training, scoring, or dashboard services without reprocessing raw files.

## Maintainability Design

- Ingestion, transformation, orchestration, and schema concerns are separated into dedicated folders.
- Spark transformations are written as testable functions.
- Dockerfiles and `docker-compose.yml` keep runtime dependencies reproducible.
- Architecture and quick-start documentation are version controlled with the code.
- The preview script provides a lightweight way to validate output shape before running the full stack.

## Security and Governance

- Database credentials live in environment variables.
- Ingestion validates schema fields before publishing.
- Logs are emitted from ingestion and processing services.
- Infrastructure is represented as version-controlled code.
- PostgreSQL data can be backed up from the named Docker volume.
- Curated analytics and feature tables create a governed boundary between raw input files and downstream consumers.

## Advantages and Disadvantages

Advantages:

- The architecture separates ingestion, processing, orchestration, and storage responsibilities.
- Docker Compose makes the prototype reproducible on a local machine.
- Spark and Kafka leave a clear path to higher-volume processing.
- PostgreSQL keeps analytics outputs queryable with standard SQL.
- The ML feature table connects the batch platform to future predictive analytics work.

Disadvantages:

- The local prototype uses a single Kafka broker and single PostgreSQL instance.
- Spark currently reads the local batch file directly rather than consuming Kafka as its primary source.
- The official Instacart dataset lacks prices and real dates, so preview outputs use basket-volume metrics and reconstructed dates.
- Production-grade secrets management, access control, lineage, and monitoring would need additional services.

## Conclusion

The implementation demonstrates the conception-phase architecture as a working batch analytics prototype. It includes the requested microservices, Docker-based infrastructure, analytics storage, orchestration, reliability and scalability considerations, and an explicit ML data delivery layer.
