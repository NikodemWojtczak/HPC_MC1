# producer_sensor_rabbit.py
import pika
import time
import json
import random
import os
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

RABBITMQ_HOST = os.getenv(
    "RABBITMQ_HOST", "localhost"
)  # Use localhost if running outside Docker
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "user")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "password")
EXCHANGE_NAME = "data_exchange"
ROUTING_KEY = "user.activity"  # Example routing key


def connect_rabbitmq():
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


def generate_sensor_data():
    # Same data generation logic as before
    return {
        "timestamp": datetime.now().isoformat(),
        "sensor_id": f"sensor_{random.randint(1, 5)}",
        "temperature_celsius": round(random.uniform(18.0, 25.0), 2),
        "humidity_percent": round(random.uniform(40.0, 60.0), 2),
    }


def main():
    connection = connect_rabbitmq()
    channel = connection.channel()

    # Declare a durable topic exchange
    channel.exchange_declare(
        exchange=EXCHANGE_NAME, exchange_type="topic", durable=True
    )
    logging.info(f"Declared exchange '{EXCHANGE_NAME}'")

    logging.info(
        f"Starting data generation for exchange '{EXCHANGE_NAME}' with key '{ROUTING_KEY}'. Press Ctrl+C to stop."
    )

    try:
        while True:
            data = generate_sensor_data()
            message_body = json.dumps(data)

            try:
                channel.basic_publish(
                    exchange=EXCHANGE_NAME,
                    routing_key=ROUTING_KEY,
                    body=message_body,
                    properties=pika.BasicProperties(
                        delivery_mode=2,  # make message persistent
                    ),
                )
                logging.info(f"Sent: {data}")
            except (
                pika.exceptions.AMQPConnectionError,
                pika.exceptions.AMQPChannelError,
            ) as e:
                logging.error(f"Connection/Channel error: {e}. Reconnecting...")
                connection = connect_rabbitmq()
                channel = connection.channel()
                # Re-declare exchange just in case
                channel.exchange_declare(
                    exchange=EXCHANGE_NAME, exchange_type="topic", durable=True
                )
                # Consider resending the last message or implementing a retry mechanism
            except Exception as e:
                logging.error(f"Failed to send message: {e}")
                time.sleep(1)  # Wait before retrying publish

            time.sleep(1)  # Send every 1 second

    except KeyboardInterrupt:
        logging.info("Stopping producer...")
    finally:
        if connection and connection.is_open:
            connection.close()
            logging.info("RabbitMQ connection closed.")


if __name__ == "__main__":
    main()
