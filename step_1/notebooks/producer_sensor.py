# producer_sensor.py
import time
import json
import random
from datetime import datetime
from kafka import KafkaProducer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Kafka Configuration
KAFKA_BROKERS = [
    "localhost:9092",
    "localhost:9093",
    "localhost:9094",
]
TOPIC_NAME = "sensor_data"


KAFKA_BROKERS_INTERNAL = ["kafka1:9092", "kafka2:9092", "kafka3:9092"]


def create_producer():
    """Creates and returns a KafkaProducer instance."""
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKERS_INTERNAL,
            value_serializer=lambda v: json.dumps(v).encode(
                "utf-8"
            ),  # Serialize JSON to bytes
            acks="all",  # Wait for all in-sync replicas to acknowledge
            retries=5,  # Retry sending up to 5 times
        )
        logger.info("Kafka Producer created successfully.")
        return producer
    except Exception as e:
        logger.error(f"Error creating Kafka producer: {e}")
        exit(1)


def generate_sensor_data():
    """Generates a single sensor data message."""
    return {
        "timestamp": datetime.now().isoformat(),
        "sensor_id": f"sensor_{random.randint(1, 5)}",
        "temperature_celsius": round(random.uniform(18.0, 25.0), 2),
        "humidity_percent": round(random.uniform(40.0, 60.0), 2),
    }


def send_data(producer, topic, data):
    """Sends data to the specified Kafka topic."""
    try:
        future = producer.send(topic, value=data)
        record_metadata = future.get(timeout=10)
        logger.debug(
            f"Sent message to {record_metadata.topic} partition {record_metadata.partition} offset {record_metadata.offset}"
        )
        return True
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return False


def main():
    producer = create_producer()
    if not producer:
        return  # Exit if producer creation failed

    logger.info(
        f"Starting data generation for topic '{TOPIC_NAME}'. Press Ctrl+C to stop."
    )

    try:
        while True:
            data = generate_sensor_data()
            if send_data(producer, TOPIC_NAME, data):
                logger.info(f"Sent: {data}")
            else:
                logger.warning("Message send failed. Will retry next cycle.")
            time.sleep(1)  # Send every 1 second
    except KeyboardInterrupt:
        logger.info("Stopping producer...")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    finally:
        if producer:
            producer.flush()  # Ensure all buffered messages are sent
            producer.close()
            logger.info("Producer closed.")


if __name__ == "__main__":
    main()
