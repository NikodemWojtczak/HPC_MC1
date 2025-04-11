# notebooks/producer_sensor_timed.py
import time
import json
import random
from datetime import datetime
from kafka import KafkaProducer
import logging
import statistics  # Added for timing analysis

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Kafka Configuration (Assuming running inside Jupyter container)
KAFKA_BROKERS_INTERNAL = ["kafka1:9092", "kafka2:9092", "kafka3:9092"]
TOPIC_NAME = "sensor_data"


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
        # Optional: Reduce logging during timing runs if needed
        # logger.debug(f"Sent message to {record_metadata.topic} partition {record_metadata.partition} offset {record_metadata.offset}")
        return True
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return False


def main():
    try:
        producer = create_producer()
        if not producer:
            return

        iterations = 300  # Number of loops to time
        loop_times = []  # List to store duration of each loop

        logger.info(
            f"Starting timed run ({iterations} iterations) for topic '{TOPIC_NAME}'..."
        )

        for i in range(iterations):
            start_time = time.perf_counter()  # Start timer for the loop

            # --- Core loop logic ---
            data = generate_sensor_data()
            send_successful = send_data(producer, TOPIC_NAME, data)
            if not send_successful:
                logger.warning(f"Message send failed iteration {i+1}")
                # Decide if failed loops should be timed or handled differently

            # Include the sleep time as part of the loop duration
            time.sleep(1)
            # --- End Core loop logic ---

            end_time = time.perf_counter()  # End timer for the loop
            loop_times.append(end_time - start_time)

            if (i + 1) % 100 == 0:  # Log progress occasionally
                logger.info(f"Completed iteration {i+1}/{iterations}")

        # --- Calculate and print statistics ---
        if loop_times:
            avg_time = statistics.mean(loop_times)
            std_dev = statistics.stdev(loop_times) if len(loop_times) > 1 else 0
            logger.info(f"--- Timing Results ({iterations} iterations) ---")
            logger.info(f"Average loop time: {avg_time:.6f} seconds")
            logger.info(f"Standard deviation: {std_dev:.6f} seconds")
            logger.info(f"Min loop time: {min(loop_times):.6f} seconds")
            logger.info(f"Max loop time: {max(loop_times):.6f} seconds")
        else:
            logger.warning("No loop times recorded.")

    # --- Cleanup ---
    finally:
        if producer:
            producer.flush()  # Ensure all buffered messages are sent
            producer.close()
            logger.info("Producer closed.")


if __name__ == "__main__":
    main()
