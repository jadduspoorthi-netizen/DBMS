from kafka import KafkaProducer
import json


KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
PAPER_UPLOADED_TOPIC = "paper-uploaded"


def get_kafka_producer():
    """Create and return a Kafka producer."""
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
    )


def publish_paper_uploaded(paper_data: dict):
    """Publish a paper-upload notification to Kafka."""
    producer = get_kafka_producer()

    producer.send(
        PAPER_UPLOADED_TOPIC,
        value=paper_data,
    )

    producer.flush()
    producer.close()

    return {
        "message": "Paper upload notification published to Kafka.",
        "topic": PAPER_UPLOADED_TOPIC,
    }
