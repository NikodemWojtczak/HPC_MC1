# notebooks/processor_sink_timed.py
import time
import json
import csv
import os
from kafka import KafkaConsumer, KafkaProducer
import logging
from datetime import datetime
import statistics  # Added for timing analysis

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Kafka Configuration
KAFKA_BROKERS_INTERNAL = ["kafka1:9092", "kafka2:9092", "kafka3:9092"]
INPUT_TOPICS = ["sensor_data", "user_activity"]
OUTPUT_TOPIC = "processed_data"
CONSUMER_GROUP_ID = "processor-group-timed"  # Use different group ID if needed
SINK_CONSUMER_GROUP_ID = "sink-group-timed"
CSV_FILE_PATH = "/home/jovyan/processed_data_timed.csv"  # Use different file maybe


# --- create_consumer, create_producer, process_message, write_to_csv (Identical to original processor_sink.py) ---
# (Copy those functions here from your original processor_sink.py)
# Make sure write_to_csv uses the new CSV_FILE_PATH variable if you changed it
def create_consumer(topics, group_id):
    """Creates and returns a KafkaConsumer instance."""
    # (Same as original)
    try:
        consumer = KafkaConsumer(
            *topics,  # Unpack the list of topics
            bootstrap_servers=KAFKA_BROKERS_INTERNAL,
            group_id=group_id,
            auto_offset_reset="earliest",
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            consumer_timeout_ms=1000,  # Important for timing loop
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
    # (Same as original)
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
    # (Same as original)
    topic = message.topic
    data = message.value
    processed = None
    # ... (rest of processing logic) ...
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
            "details": data.get("details", {}),
        }
    else:
        logger.warning(f"Received message from unknown topic: {topic}")
    return processed


def send_processed_data(producer, topic, data):
    """Sends processed data to the output Kafka topic."""
    # (Same as original)
    if data is None:
        return False
    try:
        future = producer.send(topic, value=data)
        future.get(timeout=10)
        # logger.debug(f"Sent processed message to topic '{topic}'") # Optional: reduce logging
        return True
    except Exception as e:
        logger.error(f"Error sending processed message: {e}")
        return False


def write_to_csv(data, filepath):
    """Appends processed data to a CSV file."""
    # (Same as original, ensure filepath variable is correct)
    file_exists = os.path.isfile(filepath)
    flat_data = {}
    # ... (flattening logic) ...
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
                writer.writeheader()
            writer.writerow(flat_data)
            # logger.debug(f"Appended record to {filepath}") # Optional: reduce logging
    except Exception as e:
        logger.error(f"Error writing to CSV file {filepath}: {e}")


# --- End of copied functions ---


def main():
    # Setup consumers and producer
    input_consumer = create_consumer(INPUT_TOPICS, CONSUMER_GROUP_ID)
    output_producer = create_producer()
    sink_consumer = create_consumer([OUTPUT_TOPIC], SINK_CONSUMER_GROUP_ID)

    if not input_consumer or not output_producer or not sink_consumer:
        logger.error("Initialization failed. Exiting.")
        return

    batches_to_process = 200  # Number of batches (poll loops) to time
    batch_processing_times = []  # List to store duration of each batch processing loop
    batches_processed = 0

    logger.info(f"Starting timed run (approx {batches_to_process} batches)...")
    logger.info(
        f"Input topics: {INPUT_TOPICS}, Output topic: {OUTPUT_TOPIC}, Sink file: {CSV_FILE_PATH}"
    )

    try:
        while batches_processed < batches_to_process:
            batch_start_time = time.perf_counter()  # Start timer for the batch loop

            # --- Poll for raw messages ---
            raw_messages = input_consumer.poll(
                timeout_ms=1000
            )  # Poll for up to 1 second
            processed_count_in_batch = 0
            work_done_in_batch = False
            if raw_messages:
                work_done_in_batch = True
                for topic_partition, messages in raw_messages.items():
                    for message in messages:
                        processed_data = process_message(message)
                        if processed_data:
                            if send_processed_data(
                                output_producer, OUTPUT_TOPIC, processed_data
                            ):
                                processed_count_in_batch += 1
                input_consumer.commit()

            # --- Poll for processed messages for sink ---
            sink_messages = sink_consumer.poll(timeout_ms=100)  # Shorter poll for sink
            written_count_in_batch = 0
            if sink_messages:
                work_done_in_batch = True
                for topic_partition, messages in sink_messages.items():
                    for message in messages:
                        write_to_csv(message.value, CSV_FILE_PATH)
                        written_count_in_batch += 1
                sink_consumer.commit()

            batch_end_time = time.perf_counter()  # End timer for the batch loop

            # Record time for the batch loop
            batch_processing_times.append(batch_end_time - batch_start_time)
            batches_processed += 1

            if work_done_in_batch:
                logger.info(
                    f"Processed batch {batches_processed}/{batches_to_process} (P:{processed_count_in_batch}, S:{written_count_in_batch}) in {batch_end_time - batch_start_time:.4f}s"
                )
            else:
                logger.info(
                    f"Idle batch {batches_processed}/{batches_to_process} loop took {batch_end_time - batch_start_time:.4f}s"
                )

    except KeyboardInterrupt:
        logger.info("Stopping processor and sink...")
    finally:
        # --- Calculate and print statistics ---
        if batch_processing_times:
            avg_time = statistics.mean(batch_processing_times)
            std_dev = (
                statistics.stdev(batch_processing_times)
                if len(batch_processing_times) > 1
                else 0
            )
            logger.info(
                f"--- Timing Results ({len(batch_processing_times)} batches) ---"
            )
            logger.info(f"Average batch processing loop time: {avg_time:.6f} seconds")
            logger.info(f"Standard deviation: {std_dev:.6f} seconds")
            logger.info(f"Min batch time: {min(batch_processing_times):.6f} seconds")
            logger.info(f"Max batch time: {max(batch_processing_times):.6f} seconds")
        else:
            logger.warning("No batch processing times recorded.")

        # --- Cleanup ---
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
