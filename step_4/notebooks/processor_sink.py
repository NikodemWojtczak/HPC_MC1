# processor_sink.py
import time
import json
import csv
import os
from kafka import KafkaConsumer, KafkaProducer
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Kafka Configuration (Same notes as producers apply)
KAFKA_BROKERS_INTERNAL = ["kafka1:9092", "kafka2:9092", "kafka3:9092"]
INPUT_TOPICS = ["sensor_data", "user_activity"]
OUTPUT_TOPIC = "processed_data"
CONSUMER_GROUP_ID = "processor-group"  # Consumer group for reading input
SINK_CONSUMER_GROUP_ID = (
    "sink-group"  # Separate consumer group for reading processed data
)
CSV_FILE_PATH = "/home/jovyan/processed_data.csv"  # Path inside the Jupyter container


def create_consumer(topics, group_id):
    """Creates and returns a KafkaConsumer instance."""
    try:
        consumer = KafkaConsumer(
            *topics,  # Unpack the list of topics
            bootstrap_servers=KAFKA_BROKERS_INTERNAL,
            group_id=group_id,
            auto_offset_reset="earliest",  # Start reading from the beginning of the topic if no offset found
            value_deserializer=lambda v: json.loads(
                v.decode("utf-8")
            ),  # Deserialize bytes to JSON
            consumer_timeout_ms=1000,  # Stop blocking for messages after 1 second
        )
        logger.info(
            f"Kafka Consumer for group '{group_id}' created successfully, subscribed to {topics}."
        )
        return consumer
    except Exception as e:
        logger.error(f"Error creating Kafka consumer for group '{group_id}': {e}")
        return None


def create_producer():
    """Creates and returns a KafkaProducer instance."""
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKERS_INTERNAL,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            acks="all",
            retries=5,
        )
        logger.info("Kafka Producer (for processed data) created successfully.")
        return producer
    except Exception as e:
        logger.error(f"Error creating Kafka producer: {e}")
        return None


def process_message(message):
    """Processes a raw message based on its topic."""
    topic = message.topic
    data = message.value
    processed = None

    logger.debug(f"Processing message from topic '{topic}'")

    if topic == "sensor_data":
        temp = data.get("temperature_celsius", 0)
        status = "Normal"
        if temp > 24.0:
            status = "Warning"
        elif temp < 19.0:
            status = "Low"

        processed = {
            "processing_timestamp": datetime.now().isoformat(),
            "original_timestamp": data.get("timestamp"),
            "type": "sensor",
            "sensor_id": data.get("sensor_id"),
            "temperature": temp,
            "humidity": data.get("humidity_percent"),
            "status": status,
        }
    elif topic == "user_activity":
        processed = {
            "processing_timestamp": datetime.now().isoformat(),
            "original_timestamp": data.get("event_timestamp"),
            "type": "activity",
            "user": data.get("user_id"),
            "action": data.get("action"),
            "details": data.get("details", {}),  # Pass details through
        }
    else:
        logger.warning(f"Received message from unknown topic: {topic}")

    return processed


def send_processed_data(producer, topic, data):
    """Sends processed data to the output Kafka topic."""
    if data is None:
        return False
    try:
        future = producer.send(topic, value=data)
        future.get(timeout=10)  # Wait for send confirmation
        logger.debug(f"Sent processed message to topic '{topic}'")
        return True
    except Exception as e:
        logger.error(f"Error sending processed message: {e}")
        return False


def write_to_csv(data, filepath):
    """Appends processed data to a CSV file."""
    file_exists = os.path.isfile(filepath)
    # Flatten the data for CSV writing, handle nested 'details' dict
    flat_data = {}
    for key, value in data.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                flat_data[f"{key}_{sub_key}"] = sub_value
        else:
            flat_data[key] = value

    try:
        with open(filepath, "a", newline="", encoding="utf-8") as csvfile:
            headers = list(flat_data.keys())
            writer = csv.DictWriter(csvfile, fieldnames=headers)

            if not file_exists or os.path.getsize(filepath) == 0:
                writer.writeheader()  # Write header only if file is new/empty

            writer.writerow(flat_data)
            logger.debug(f"Appended record to {filepath}")
    except Exception as e:
        logger.error(f"Error writing to CSV file {filepath}: {e}")


def main():
    # Part 1: Consume raw data, process it, produce to processed_data topic
    input_consumer = create_consumer(INPUT_TOPICS, CONSUMER_GROUP_ID)
    output_producer = create_producer()

    # Part 2: Consume processed data and write to CSV
    sink_consumer = create_consumer([OUTPUT_TOPIC], SINK_CONSUMER_GROUP_ID)

    if not input_consumer or not output_producer or not sink_consumer:
        logger.error("Initialization failed. Exiting.")
        return

    logger.info(f"Starting processor and sink. Press Ctrl+C to stop.")
    logger.info(
        f"Input topics: {INPUT_TOPICS}, Output topic: {OUTPUT_TOPIC}, Sink file: {CSV_FILE_PATH}"
    )

    try:
        while True:
            processed_count = 0
            # Poll for raw messages
            raw_messages = input_consumer.poll(timeout_ms=100)  # Poll for up to 100ms
            if raw_messages:
                for topic_partition, messages in raw_messages.items():
                    for message in messages:
                        logger.info(
                            f"Received raw message: Topic={message.topic}, Offset={message.offset}"
                        )
                        processed_data = process_message(message)
                        if processed_data:
                            if send_processed_data(
                                output_producer, OUTPUT_TOPIC, processed_data
                            ):
                                processed_count += 1

                # Commit offsets for the raw input consumer after processing a batch
                input_consumer.commit()
                logger.info(f"Processed and sent {processed_count} messages.")

            # Poll for processed messages to write to CSV
            sink_messages = sink_consumer.poll(timeout_ms=100)  # Poll for up to 100ms
            if sink_messages:
                written_count = 0
                for topic_partition, messages in sink_messages.items():
                    for message in messages:
                        logger.info(
                            f"Received processed message for sink: Offset={message.offset}"
                        )
                        write_to_csv(message.value, CSV_FILE_PATH)
                        written_count += 1

                # Commit offsets for the sink consumer after writing a batch
                sink_consumer.commit()
                logger.info(f"Wrote {written_count} processed records to CSV.")

            # If no messages were received in either poll, sleep briefly
            if not raw_messages and not sink_messages:
                time.sleep(0.5)

    except KeyboardInterrupt:
        logger.info("Stopping processor and sink...")
    except Exception as e:
        logger.error(
            f"An unexpected error occurred: {e}", exc_info=True
        )  # Log traceback
    finally:
        if output_producer:
            output_producer.flush()
            output_producer.close()
            logger.info("Output producer closed.")
        if input_consumer:
            input_consumer.close()
            logger.info("Input consumer closed.")
        if sink_consumer:
            sink_consumer.close()
            logger.info("Sink consumer closed.")


if __name__ == "__main__":
    main()
