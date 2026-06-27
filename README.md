# Batch Processing Data Architecture for E-Commerce Analytics

## Project Overview

This project implements a scalable batch-processing data architecture for e-commerce analytics using modern data engineering technologies. The system ingests transactional data from the Instacart Market Basket Analysis dataset, processes it through a distributed batch-processing pipeline, and generates analytical datasets that can support business intelligence and future machine learning applications.

The architecture follows a microservices-based design and is fully containerized using Docker. Workflow orchestration is managed by Apache Airflow, while Apache Kafka provides reliable message streaming between services. Apache Spark performs batch processing and data aggregation before storing analytical results in PostgreSQL.

This project was developed as part of the **DLMDSEDE02 – Data Engineering** module at **IU International University of Applied Sciences**.

---

# Architecture

```

                 Instacart Dataset

                         │

                         ▼

              Data Ingestion Service

                         │

                  Publish Events

                         ▼

                  Apache Kafka

                         │

                  Stream Processing

                         ▼

                  Apache Spark

                         │

                  Processed Data

                         ▼

                   PostgreSQL

                 /             \

                ▼               ▼

      Analytics Tables   ML Feature Tables

                ▲

                │

         Apache Airflow

     (Workflow Orchestration)

```

---

# Technology Stack

| Technology | Purpose |

|------------|---------|

| Python | Data ingestion and automation |

| Apache Kafka | Message broker |

| Apache Spark | Batch processing |

| PostgreSQL | Data storage |

| Apache Airflow | Workflow orchestration |

| Docker | Containerization |

| Docker Compose | Infrastructure as Code |

| Git | Version Control |

| GitHub | Repository Hosting |

---

# Features

- Batch processing pipeline

- Docker-based microservices

- Apache Kafka messaging

- Apache Spark transformations

- PostgreSQL analytical storage

- Apache Airflow workflow orchestration

- Machine learning feature generation

- Reproducible Infrastructure as Code deployment

---

# Repository Structure

```

Batch-Processing-Data-Architecture-for-E-commerce-Analytics/

│

├── airflow/

│   └── dags/

│

├── data/

│   └── raw/

│

├── docs/

│

├── ingestion_service/

│

├── scripts/

│

├── spark_jobs/

│

├── sql/

│

├── tests/

│

├── docker-compose.yml

│

├── requirements.txt

│

├── .env.example

│

└── README.md

```

---

# Dataset

Dataset:

**Instacart Market Basket Analysis**

The dataset contains customer orders, product information, departments, aisles, and purchasing history that are used to simulate a real-world e-commerce batch-processing environment.

---

# Data Processing Workflow

1. Read Instacart dataset

2. Validate incoming records

3. Publish events to Apache Kafka

4. Consume events using Apache Spark

5. Clean and transform data

6. Generate analytical datasets

7. Store results in PostgreSQL

8. Orchestrate execution using Apache Airflow

---

# Generated Analytics

The pipeline generates several analytical datasets including:

- Monthly Sales

- Top Products

- Customer Metrics

- Category Performance

- Machine Learning Customer Features

These datasets support future business intelligence and predictive analytics applications.

---

# Prerequisites

Before running the project, install:

- Docker Desktop

- Docker Compose

- Git

- Python 3.11+

- PostgreSQL (if running outside Docker)

---

# Installation

Clone the repository

```bash

git clone https://github.com/Shazam-saifi/Batch-Processing-Data-Architecture-for-E-commerce-Analytics.git

```

Navigate into the project

```bash

cd Batch-Processing-Data-Architecture-for-E-commerce-Analytics

```

Create the environment configuration

```bash

cp .env.example .env

```

---

# Running the Project

Start all services

```bash

docker compose up --build

```

Verify running containers

```bash

docker ps

```

Open Airflow

```

http://localhost:8080

```

Trigger the batch-processing workflow.

---

# Expected Pipeline

```

Dataset

    │

    ▼

Ingestion Service

    │

    ▼

Kafka

    │

    ▼

Spark

    │

    ▼

PostgreSQL

```

---
