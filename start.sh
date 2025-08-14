#!/bin/sh
set -e

echo "Waiting for Kafka Connect..."
until curl -s http://debezium:8083/connectors > /dev/null; do
    sleep 3
done
echo "Kafka Connect is ready."

if [ -f shows-connector.json ]; then
    echo "Creating Kafka connector..."
    curl -X POST http://debezium:8083/connectors \
         -H "Content-Type: application/json" \
         -d @shows-connector.json || true
else
    echo "shows-connector.json not found, skipping connector creation."
fi

exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload