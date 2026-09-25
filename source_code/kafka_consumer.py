from kafka import KafkaConsumer
import json


KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
PAPER_UPLOADED_TOPIC = "paper-uploaded"


def start_consumer():
    """Start the Kafka consumer for paper-upload notifications."""

    consumer = KafkaConsumer(
        PAPER_UPLOADED_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda value: json.loads(
            value.decode("utf-8")
        ),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="smartresearchhub-notification-service",
    )

    print("Kafka consumer started.")
    print(f"Listening to topic: {PAPER_UPLOADED_TOPIC}")

    try:
        for message in consumer:
            paper_data = message.value

            print("\nNew paper upload notification")
            print("-" * 50)
            print(f"Paper ID   : {paper_data.get('paper_id')}")
            print(f"Title      : {paper_data.get('title')}")
            print(f"Domain     : {paper_data.get('domain')}")
            print(f"Year       : {paper_data.get('year')}")
            print(f"Uploaded by: {paper_data.get('uploaded_by')}")

    except KeyboardInterrupt:
        print("\nKafka consumer stopped.")

    finally:
        consumer.close()


if __name__ == "__main__":
    start_consumer()