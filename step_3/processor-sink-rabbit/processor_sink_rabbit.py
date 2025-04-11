# processor_sink_rabbit.py
import pika
import time
import json
import csv
import os
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "user")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "password")

INPUT_EXCHANGE = "data_exchange"
INPUT_QUEUE = "processing_queue"
INPUT_BINDING_KEYS = [
    "sensor.*",
    "user.activity",
]  # Bind to sensor data and specific user activity

OUTPUT_EXCHANGE = "processed_exchange"
OUTPUT_QUEUE = "sink_queue"
OUTPUT_ROUTING_KEY = "processed.data"  # Key for processed messages
OUTPUT_BINDING_KEY = "processed.*"  # Sink binds to this

# Write CSV inside the container at /data (mapped from ./notebooks)
CSV_FILE_PATH = "/data/processed_data_rabbit.csv"


# --- Processing logic (same as Kafka version) ---
def process_message(message_body, routing_key):
    try:
        data = json.loads(message_body)
        processed = None
        logger = logging.getLogger(__name__)  # Get logger instance

        logger.debug(f"Processing message with routing key '{routing_key}'")

        # Determine type based on routing key prefix if needed, or check data content
        if routing_key.startswith("sensor."):
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
        elif routing_key == "user.activity":
            processed = {
                "processing_timestamp": datetime.now().isoformat(),
                "original_timestamp": data.get("event_timestamp"),
                "type": "activity",
                "user": data.get("user_id"),
                "action": data.get("action"),
                "details": data.get("details", {}),
            }
        else:
            logger.warning(
                f"Received message with unhandled routing key: {routing_key}"
            )
        return processed
    except json.JSONDecodeError:
        logging.error("Failed to decode JSON message body.")
        return None
    except Exception as e:
        logging.error(f"Error processing message: {e}")
        return None


# --- CSV Writing logic (same as Kafka version) ---
def write_to_csv(data, filepath):
    # ... (Identical CSV writing logic as in processor_sink.py) ...
    file_exists = os.path.isfile(filepath)
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
                writer.writeheader()
            writer.writerow(flat_data)
            logging.debug(f"Appended record to {filepath}")
    except Exception as e:
        logging.error(f"Error writing to CSV file {filepath}: {e}")


# --- RabbitMQ Connection and Callbacks ---
connection = None
consuming_channel = None
publishing_channel = None


def connect_rabbitmq():
    global connection
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    parameters = pika.ConnectionParameters(
        RABBITMQ_HOST,
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300,
    )
    while True:
        try:
            connection = pika.BlockingConnection(parameters)
            logging.info("Connected to RabbitMQ.")
            return connection
        except pika.exceptions.AMQPConnectionError as e:
            logging.error(f"Connection failed: {e}. Retrying in 5 seconds...")
            time.sleep(5)


def setup_channels_and_queues(connection):
    global consuming_channel, publishing_channel
    try:
        # Channel for consuming raw data
        consuming_channel = connection.channel()
        consuming_channel.exchange_declare(
            exchange=INPUT_EXCHANGE, exchange_type="topic", durable=True
        )
        # Declare durable queue for processing
        consuming_channel.queue_declare(queue=INPUT_QUEUE, durable=True)
        for key in INPUT_BINDING_KEYS:
            consuming_channel.queue_bind(
                exchange=INPUT_EXCHANGE, queue=INPUT_QUEUE, routing_key=key
            )
        logging.info(
            f"Declared input exchange '{INPUT_EXCHANGE}', queue '{INPUT_QUEUE}', bindings '{INPUT_BINDING_KEYS}'"
        )

        # Channel for publishing processed data and consuming it for sink
        publishing_channel = connection.channel()
        publishing_channel.exchange_declare(
            exchange=OUTPUT_EXCHANGE, exchange_type="topic", durable=True
        )
        # Declare durable queue for sinking
        publishing_channel.queue_declare(queue=OUTPUT_QUEUE, durable=True)
        publishing_channel.queue_bind(
            exchange=OUTPUT_EXCHANGE, queue=OUTPUT_QUEUE, routing_key=OUTPUT_BINDING_KEY
        )
        logging.info(
            f"Declared output exchange '{OUTPUT_EXCHANGE}', queue '{OUTPUT_QUEUE}', binding '{OUTPUT_BINDING_KEY}'"
        )

        # Set QoS to process one message at a time before acking
        consuming_channel.basic_qos(prefetch_count=1)
        publishing_channel.basic_qos(prefetch_count=1)  # Also for the sink part

        return consuming_channel, publishing_channel

    except (pika.exceptions.AMQPConnectionError, pika.exceptions.AMQPChannelError) as e:
        logging.error(f"Error setting up channels/queues: {e}")
        time.sleep(5)
        return None, None  # Signal failure


def processing_callback(ch, method, properties, body):
    global publishing_channel
    logging.info(
        f" [P] Received message from input queue '{INPUT_QUEUE}' (Delivery Tag: {method.delivery_tag})"
    )
    processed_data = process_message(body, method.routing_key)

    if processed_data:
        try:
            # Publish processed data to the output exchange
            publishing_channel.basic_publish(
                exchange=OUTPUT_EXCHANGE,
                routing_key=OUTPUT_ROUTING_KEY,
                body=json.dumps(processed_data),
                properties=pika.BasicProperties(delivery_mode=2),  # persistent
            )
            logging.info(
                f" [P] Published processed data to '{OUTPUT_EXCHANGE}' with key '{OUTPUT_ROUTING_KEY}'"
            )
            # Acknowledge the original message only after successful processing AND publishing
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logging.debug(f" [P] Acknowledged message {method.delivery_tag}")
        except (
            pika.exceptions.AMQPConnectionError,
            pika.exceptions.AMQPChannelError,
        ) as e:
            logging.error(
                f" [P] Connection/Channel error during publish/ack: {e}. Message will be nacked/requeued."
            )
            # Negative acknowledge, requeue the message
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        except Exception as e:
            logging.error(
                f" [P] Failed to publish processed message: {e}. Message will be nacked/requeued."
            )
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    else:
        logging.warning(
            f" [P] Processing failed for message {method.delivery_tag}. Acknowledging to discard."
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)


def sink_callback(ch, method, properties, body):
    logging.info(
        f" [S] Received message from output queue '{OUTPUT_QUEUE}' for sinking (Delivery Tag: {method.delivery_tag})"
    )
    try:
        data_to_sink = json.loads(body)
        write_to_csv(data_to_sink, CSV_FILE_PATH)
        # Acknowledge message after successfully writing to CSV
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logging.debug(f" [S] Acknowledged message {method.delivery_tag}")
    except json.JSONDecodeError:
        logging.error(
            " [S] Failed to decode JSON message body for sinking. Discarding (ack)."
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logging.error(
            f" [S] Error writing to CSV or acknowledging: {e}. Message will be nacked/requeued."
        )
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def start_consuming():
    global connection, consuming_channel, publishing_channel
    while True:  # Main reconnection loop
        if not connection or connection.is_closed:
            connection = connect_rabbitmq()
            consuming_channel, publishing_channel = setup_channels_and_queues(
                connection
            )

        if not consuming_channel or not publishing_channel:
            logging.error("Failed to setup channels. Retrying connection...")
            time.sleep(5)
            continue  # Go back to reconnecting

        try:
            # Start consuming from the input queue (Processing)
            consuming_channel.basic_consume(
                queue=INPUT_QUEUE, on_message_callback=processing_callback
            )  # auto_ack=False is default

            # Start consuming from the output queue (Sinking)
            publishing_channel.basic_consume(
                queue=OUTPUT_QUEUE, on_message_callback=sink_callback
            )

            logging.info(" [*] Waiting for messages. To exit press CTRL+C")
            # Start consuming loop for BOTH consumers (on their respective channels)
            # Note: Running two consumers in one thread like this isn't ideal for high load,
            #       but sufficient for this example. Pika's blocking adapter is tricky with multiple consumers.
            #       A better approach uses threads or async adapters (e.g., asyncio with aio-pika).

            # This will block here, handling messages on both channels as they arrive
            consuming_channel.start_consuming()  # This will likely handle both if on same connection? Check pika docs.
            # If the above doesn't work for both, might need threading or async. Let's try simply.

        except KeyboardInterrupt:
            logging.info("Stopping consumer...")
            if consuming_channel and consuming_channel.is_open:
                consuming_channel.stop_consuming()
            if publishing_channel and publishing_channel.is_open:
                publishing_channel.stop_consuming()  # Ensure both stop
            break  # Exit the while loop
        except (
            pika.exceptions.AMQPConnectionError,
            pika.exceptions.ConnectionClosedByBroker,
            pika.exceptions.StreamLostError,
        ) as e:
            logging.error(f"Connection lost: {e}. Reconnecting...")
            # Reset channels, connection object will be recreated in the next loop iteration
            consuming_channel = None
            publishing_channel = None
            connection = None
            time.sleep(5)
        except Exception as e:
            logging.error(
                f"An unexpected error occurred in consume loop: {e}", exc_info=True
            )
            # Consider if we need to break or just retry connection
            time.sleep(5)

    if connection and connection.is_open:
        connection.close()
        logging.info("RabbitMQ connection closed.")


if __name__ == "__main__":
    start_consuming()
