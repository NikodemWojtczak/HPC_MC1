# notebooks/processor_sink_partitioned_output.py
import time
import json
import csv
import os
from kafka import KafkaConsumer, KafkaProducer
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Kafka Configuration
KAFKA_BROKERS_INTERNAL = [
    "kafka1:9092",
    "kafka2:9092",
    "kafka3:9092",
]  # Adjust if needed
INPUT_TOPICS = ["sensor_data", "user_activity"]
OUTPUT_TOPIC = "processed_data"
# Use distinct group IDs for this experiment run
CONSUMER_GROUP_ID = "processor-group-parallel"
SINK_CONSUMER_GROUP_ID = "sink-group-parallel"
# Define the two output file paths within the container (/home/jovyan/ is mapped to ./notebooks)
CSV_FILE_PATH_A = "/home/jovyan/processed_split_A.csv"
CSV_FILE_PATH_B = "/home/jovyan/processed_split_B.csv"
# Define which partitions map to which file (assuming 6 partitions total for input topics)
PARTITIONS_FILE_A = {0, 1, 2}
PARTITIONS_FILE_B = {3, 4, 5}

# --- Functions ---


def create_consumer(topics, group_id):
    try:
        consumer = KafkaConsumer(
            *topics,
            bootstrap_servers=KAFKA_BROKERS_INTERNAL,
            group_id=group_id,
            auto_offset_reset="earliest",
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            consumer_timeout_ms=1000,  # Poll timeout
        )
        logger.info(f"Consumer group '{group_id}' created for topics {topics}.")
        return consumer
    except Exception as e:
        logger.error(f"Error creating consumer {group_id}: {e}")
        return None


def create_producer():
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKERS_INTERNAL,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            acks="all",
            retries=5,
        )
        logger.info("Kafka Producer (for processed data) created.")
        return producer
    except Exception as e:
        logger.error(f"Error creating producer: {e}")
        return None


def process_message(message):
    """Processes raw message and adds source partition info."""
    topic = message.topic
    data = message.value
    processed = None
    if topic == "sensor_data":
        temp = data.get("temperature_celsius", 0)
        status = "Normal"
        if temp > 24.0:
            status = "Warning"
        elif temp < 19.0:
            status = "Low"
        processed = {
            "original_timestamp": data.get("timestamp"),
            "type": "sensor",
            "sensor_id": data.get("sensor_id"),
            "temperature": temp,
            "humidity": data.get("humidity_percent"),
            "status": status,
        }
    elif topic == "user_activity":
        processed = {
            "original_timestamp": data.get("event_timestamp"),
            "type": "activity",
            "user": data.get("user_id"),
            "action": data.get("action"),
            "details": data.get("details", {}),
        }
    else:
        logger.warning(f"Unhandled topic: {topic}")

    # Add common processing timestamp and SOURCE PARTITION
    if processed:
        processed["processing_timestamp"] = datetime.now().isoformat()
        processed["source_partition"] = message.partition  # Add the source partition

    return processed


def send_processed_data(producer, topic, data):
    if data is None:
        return False
    try:
        producer.send(topic, value=data).get(timeout=10)
        return True
    except Exception as e:
        logger.error(f"Error sending processed message: {e}")
        return False


def write_to_csv(data, filepath):
    """Appends data to the specified CSV file."""
    file_exists = os.path.isfile(filepath)
    flat_data = {}
    # Flatten dict, handle 'details' field carefully maybe
    for key, value in data.items():
        if isinstance(value, dict) and key == "details":
            flat_data[key] = json.dumps(value)  # Store details as JSON string
        elif isinstance(value, dict):  # Flatten other potential dicts (if any)
            for sub_key, sub_value in value.items():
                flat_data[f"{key}_{sub_key}"] = sub_value
        else:
            flat_data[key] = value
    try:
        with open(filepath, "a", newline="", encoding="utf-8") as csvfile:
            if not flat_data:
                return
            headers = list(flat_data.keys())
            headers.sort()  # Ensure consistent header order
            writer = csv.DictWriter(csvfile, fieldnames=headers, extrasaction="ignore")
            if not file_exists or os.path.getsize(filepath) == 0:
                writer.writeheader()
            writer.writerow(flat_data)
            logger.debug(f"Appended record to {filepath}")
    except Exception as e:
        logger.error(f"Error writing to CSV {filepath}: {e}")


# --- Main Loop ---
def main():
    input_consumer = create_consumer(INPUT_TOPICS, CONSUMER_GROUP_ID)
    output_producer = create_producer()
    sink_consumer = create_consumer([OUTPUT_TOPIC], SINK_CONSUMER_GROUP_ID)
    if not all([input_consumer, output_producer, sink_consumer]):
        logger.error("Init failed.")
        return

    logger.info("Starting partitioned output processor/sink. Press Ctrl+C to stop.")
    logger.info(f"Output File A (Partitions {PARTITIONS_FILE_A}): {CSV_FILE_PATH_A}")
    logger.info(f"Output File B (Partitions {PARTITIONS_FILE_B}): {CSV_FILE_PATH_B}")

    try:
        while True:
            # Consume and Process Raw Data
            raw_messages = input_consumer.poll(timeout_ms=1000)
            if raw_messages:
                for tp, messages in raw_messages.items():
                    logger.info(f"Processing batch from partition {tp.partition}...")
                    for message in messages:
                        processed_data = process_message(
                            message
                        )  # Adds 'source_partition'
                        if processed_data:
                            send_processed_data(
                                output_producer, OUTPUT_TOPIC, processed_data
                            )
                input_consumer.commit()

            # Consume Processed Data and Sink to Partitioned Files
            sink_messages = sink_consumer.poll(timeout_ms=100)
            if sink_messages:
                for tp, messages in sink_messages.items():
                    logger.info(f"Sinking batch from partition {tp.partition}...")
                    for message in messages:
                        processed_message_data = message.value
                        source_partition = processed_message_data.get(
                            "source_partition", -1
                        )

                        # Determine output file based on source_partition from original message
                        if source_partition in PARTITIONS_FILE_A:
                            output_file = CSV_FILE_PATH_A
                        elif source_partition in PARTITIONS_FILE_B:
                            output_file = CSV_FILE_PATH_B
                        else:
                            logger.warning(
                                f"Msg with unexpected source partition {source_partition}. Writing to A."
                            )
                            output_file = CSV_FILE_PATH_A

                        write_to_csv(processed_message_data, output_file)
                sink_consumer.commit()

            if not raw_messages and not sink_messages:
                time.sleep(0.1)  # Brief sleep when idle

    except KeyboardInterrupt:
        logger.info("Stopping processor and sink...")
    finally:
        # Cleanup
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
