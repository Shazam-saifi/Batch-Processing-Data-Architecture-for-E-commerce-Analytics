#!/usr/bin/env bash
set -euo pipefail

docker compose up -d postgres kafka zookeeper
docker compose run --rm ingestion
docker compose run --rm spark-job

