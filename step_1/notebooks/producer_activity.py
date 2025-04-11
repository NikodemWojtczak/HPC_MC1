# producer_activity.py
import time
import json
import random
from datetime import datetime
from kafka import KafkaProducer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Kafka Configuration (Same notes as producer_sensor.py apply)
KAFKA_BROKERS_INTERNAL = ["kafka1:9092", "kafka2:9092", "kafka3:9092"]
TOPIC_NAME = "user_activity"


def create_producer():
    """Creates and returns a KafkaProducer instance."""
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKERS_INTERNAL,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            acks="all",
            retries=5,
        )
        logger.info("Kafka Producer created successfully.")
        return producer
    except Exception as e:
        logger.error(f"Error creating Kafka producer: {e}")
        exit(1)


def generate_activity_data():
    """Generates a single user activity message."""
    user_id = f"user_{random.randint(100, 199)}"
    actions = ["view_page", "click_button", "add_to_cart", "purchase", "logout"]
    chosen_action = random.choice(actions)

    data = {
        "event_timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "session_id": f"session_{hash(user_id + str(datetime.now().date()))}",
        "action": chosen_action,
        "details": {},
    }

    if chosen_action in ["view_page", "click_button"]:
        data["details"]["page_url"] = f"/products/item_{random.randint(1, 50)}"
        if chosen_action == "click_button":
            data["details"]["button_id"] = random.choice(
                ["buy_now", "details", "add_wishlist"]
            )
    elif chosen_action == "add_to_cart":
        data["details"]["item_id"] = f"item_{random.randint(1, 50)}"
        data["details"]["quantity"] = random.randint(1, 3)
    elif chosen_action == "purchase":
        data["details"]["order_id"] = f"order_{random.randint(10000, 99999)}"
        data["details"]["total_amount"] = round(random.uniform(10.0, 500.0), 2)
        data["details"]["item_count"] = random.randint(1, 5)

    return data


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
        return

    logger.info(
        f"Starting data generation for topic '{TOPIC_NAME}'. Press Ctrl+C to stop."
    )

    try:
        while True:
            data = generate_activity_data()
            if send_data(producer, TOPIC_NAME, data):
                logger.info(f"Sent: {data}")
            else:
                logger.warning("Message send failed. Will retry next cycle.")
            # Send between 0.5 and 2.5 seconds
            time.sleep(random.uniform(0.5, 2.5))
    except KeyboardInterrupt:
        logger.info("Stopping producer...")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    finally:
        if producer:
            producer.flush()
            producer.close()
            logger.info("Producer closed.")


if __name__ == "__main__":
    main()
