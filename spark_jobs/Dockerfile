FROM apache/spark:3.5.1

USER root
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY batch_analytics.py .

CMD ["spark-submit", "--packages", "org.postgresql:postgresql:42.7.3", "/app/batch_analytics.py"]
