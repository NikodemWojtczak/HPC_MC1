```
+---------------------+       +---------------------+       +-----------------------+
| producer_sensor.py  | ----> | Kafka Topic:        | ----> |                       |       +-----------------------+       +---------------------+
| (Generates temp/hum)|       | sensor_data         |       |                       | ----> | Kafka Topic:          | ----> |                     |       +------------------------+
+---------------------+       +---------------------+       | processor_sink.py     |       | processed_data        |       |                     | ----> | CSV Files:              |
                                                            | (Consumer part 1:     |       +-----------------------+       | processor_sink.py   |       | - processed_data_sensor.csv |
+---------------------+       +---------------------+       |  Reads sensor_data &  |                                       | (Consumer part 2:   |       | - processed_data_activity.csv|
| producer_activity.py| ----> | Kafka Topic:        | ----> |  user_activity;       |                                       |  Reads              |       +------------------------+
| (Generates clicks)  |       | user_activity       |       |  Processes;           |                                       |  processed_data;    |
+---------------------+       +---------------------+       |  Producer part:       |                                       |  Writes to CSV      |
                                                            |  Sends to             |                                       |  based on data type)|
                                                            |  processed_data)      |                                       |                     |
                                                            +-----------------------+                                       +---------------------+
```

# Component Tasks and Architecture

## What are the tasks of the components?

- **producer_sensor.py**: Simulate sensor devices, generate periodic temperature/humidity readings, and send them to the sensor_data Kafka topic.
- **producer_activity.py**: Simulate user interactions, generate user activity events (clicks, purchases), and send them to the user_activity Kafka topic.
- **Kafka Cluster (Brokers + Topics)**: Receive messages from producers, store them durably and reliably in partitioned topics (sensor_data, user_activity, processed_data), and serve them to consumers. Manages distribution, replication, and fault tolerance.
- **processor_sink.py**:
  - **Processor**: Consume messages from sensor_data and user_activity, apply basic transformations/enrichment (e.g., add status to sensor data, standardize format), and produce the results to the processed_data topic.
  - **Sink**: Consume messages from processed_data and append them to CSV files based on data type (processed_data_sensor.csv for sensor data, processed_data_activity.csv for user activity) for persistent storage and offline analysis.
- **CSV Files**: The final storage files for the processed data, separated by data type.

## Which interfaces do the components have?
- **Producers**: Use the Kafka Producer API (kafka-python) to send messages to specific topics via the Kafka brokers (kafka1:9092, etc.)
- **Processor/Sink**:
  - Uses the Kafka Consumer API (kafka-python) to subscribe to topics (sensor_data, user_activity, processed_data) via consumer groups
  - The Processor component uses the Kafka Producer API to send processed results to the processed_data topic
  - The Sink component uses standard Python file I/O (csv module) to write to the local filesystem (mapped via Docker volume)

## Why did you decide to use these components?

- **Kafka**: Chosen as the core messaging system because it's designed for high-throughput, persistent, scalable streaming data pipelines. It decouples producers from consumers. The project specification requires using Kafka initially.
- **Separate Producers**: Allows independent simulation and scaling of different data sources.
- **Combined Processor/Sink**: For this simple example, combining them reduces the number of running scripts. In a real-world scenario, they might be separate for independent scaling and failure isolation.

## Are there any other design decisions you have made?

- **Topic Naming**: Used descriptive names (sensor_data, user_activity, processed_data).
- **Consumer Groups**: Used distinct group IDs (processor-group, sink-group) to allow independent consumption tracking. Even though combined in one script, using two conceptual consumers with different group IDs demonstrates the pattern. If we ran multiple instances of processor_sink.py, Kafka would balance partitions within each group.
- **Serialization**: Chose JSON for its readability and Python support. Used UTF-8 encoding.
- **Producer acks='all'**: Configured producers to wait for acknowledgment from all in-sync replicas for higher durability guarantees, at the cost of slightly higher latency.
- **Consumer auto_offset_reset='earliest'**: Consumers start reading from the beginning of topics if they are new or their previous offset is lost.

## Which requirements (e.g. libraries, hardware, ...) does a component have?

- **Python Scripts**: Python 3 interpreter, kafka-python library, standard libraries (json, time, datetime, random, csv, os, logging). Minimal CPU/RAM, but depends on message rate and processing complexity. Network access to Kafka brokers.
- **Kafka Cluster (Docker)**: Docker Engine, Docker Compose, sufficient RAM (several GB recommended for 3 brokers + KRaft), CPU, and disk space for the Kafka logs (/tmp/kraft-combined-logs inside containers, managed by Docker). Network connectivity between brokers.
- **Jupyter Container**: Docker, minimal resources, network access.
- **Kafdrop Container**: Docker, minimal resources, network access to Kafka brokers.

## Which features of Kafka do you use and how does this correlate to the cluster/topic settings you choose?

- **Topics**: The fundamental abstraction for categorizing streams of records (sensor_data, user_activity, processed_data). We rely on Kafka to manage these.
- **Publish/Subscribe**: Producers publish to topics, and consumers subscribe. This decouples the components.
- **Persistence**: Kafka stores messages durably on disk (in /tmp/kraft-combined-logs within the containers). Your docker-compose.yml doesn't specify volumes for Kafka logs, meaning they will be lost if the containers are removed. For true persistence, volumes should be added.
- **Consumer Groups**: Used processor-group and sink-group. This allows Kafka to track the read offset for each group independently. It also enables load balancing if multiple instances of a consumer with the same group ID are started (Kafka assigns topic partitions among them).
- **Replication**: Your docker-compose.yml sets KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 3 and KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 3. This applies to internal Kafka topics. When creating our data topics (sensor_data, etc.), Kafka will likely default to a replication factor based on the number of brokers (up to 3 here) or a cluster default (often 1 if not specified). Setting acks='all' in the producer leverages this replication for durability. A replication factor of 3 means data can tolerate the failure of up to 2 brokers.
- **Partitioning**: Although not explicitly configured in the Python code (we let Kafka assign partitions), Kafka partitions topics (defaulting to 1 partition per topic if not specified). This is the unit of parallelism. More partitions allow more consumers within a group to read in parallel (up to the number of partitions). The 3-broker setup allows partitions to be distributed for fault tolerance.

## Describe the Docker setup of your application.

The provided docker-compose.yml defines a multi-container Docker application:

- It sets up a 3-node Kafka cluster (kafka1, kafka2, kafka3) using the kafka image, configured to run in KRaft mode without Zookeeper. They communicate internally on a Docker network.
- It includes a jupyter1 service using the jupyter/scipy-notebook image, providing a JupyterLab environment. It maps the local ./notebooks directory into the container for persistent storage of notebooks and scripts. This container is on the same Docker network, allowing it to reach Kafka brokers using their service names (e.g., kafka1:9092). Port 8888 is exposed for accessing JupyterLab from the host.
- It includes a kafdrop service for web-based Kafka monitoring, configured to connect to the brokers. Port 9000 is exposed for access.
- The Python application components (producer_*.py, processor_sink.py) are not defined as separate services in this docker-compose.yml. They are intended to be run manually, either from the host (if Kafka ports are exposed) or, more conveniently in this setup, from within the jupyter1 container's terminal.
