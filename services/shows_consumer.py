from kafka import KafkaConsumer
import json
import threading
import os
import datetime
from core.elasticsearch import es_client

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC_SHOWS = os.getenv("KAFKA_TOPIC_SHOWS", "pgserver.public.shows")
ELASTICSEARCH_SHOWS_INDEX = os.getenv("ELASTICSEARCH_SHOWS_INDEX", "shows")

consumer = KafkaConsumer(
    KAFKA_TOPIC_SHOWS,
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='shows-consumer-group'
)


def ensure_index():
    print('++', es_client.ping())
    if not es_client.indices.exists(index='shows'):
        mapping = {
            "mappings": {
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "text"},
                    "location": {"type": "text"},
                    "start_time": {"type": "date"},
                    "description": {"type": "text"},
                    "performer": {"type": "text"}
                }
            }
        }
        es_client.indices.create(index=ELASTICSEARCH_SHOWS_INDEX,
                                 body=mapping, ignore=400)


def consume_and_index():
    ensure_index()
    for message in consumer:
        value = message.value

        after = value.get("after")
        if after:
            doc = {
                "id": after.get("id"),
                "name": after.get("name"),
                "location": after.get("location"),
                "start_time": datetime.datetime.fromtimestamp(after.get("start_time") / 1_000_000).isoformat(),
                "description": after.get("description"),
                "performer": after.get("performer")
            }

            es_client.index(index=ELASTICSEARCH_SHOWS_INDEX,
                            id=after["id"], document=doc)
            print(f"✅ Indexed to {ELASTICSEARCH_SHOWS_INDEX}: {doc}")
        else:
            print("⚠️ Skipped message without 'after' data")


def start_consumer_thread():
    thread = threading.Thread(target=consume_and_index, daemon=True)
    thread.start()

# Call start_consumer_thread() in your FastAPI app startup event
