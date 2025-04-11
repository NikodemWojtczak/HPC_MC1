# Experiment 1: Stability Analysis (Single Broker) Report

## Goal

The primary goal of this experiment was to demonstrate the impact of reducing the number of brokers on the **stability and fault tolerance** of the Kafka cluster, directly comparing its resilience to the multi-broker baseline setup.

## Setup & Actions

1.  **Baseline Observation:**
    * The baseline configuration used a 3-node Kafka cluster (`kafka1`, `kafka2`, `kafka3`).
    * Testing confirmed this baseline setup was fault-tolerant: stopping one of the three brokers allowed the producers and consumers to continue operating after potential leader re-election, thanks to data replication (assuming Replication Factor > 1).
2.  **Experiment Configuration:**
    * The `docker-compose-experiment_1.yml` file was modified to run **only the `kafka1` service**. Services `kafka2` and `kafka3` were removed.
    * Necessary configuration adjustments were made (e.g., `KAFKA_CONTROLLER_QUORUM_VOTERS` updated for `kafka1` only).
3.  **Execution & Test:**
    * The single-broker (`kafka1`) cluster was started along with Jupyter and Kafdrop.
    * Producer and consumer scripts were run, connecting successfully to the single broker.
    * The key test involved stopping the only running broker: `docker compose stop kafka1`.

## Observations

* The application ran without issues when connected to the single `kafka1` broker.
* When the single `kafka1` broker was stopped, **all Kafka-related operations failed immediately** for both producers and consumers.
* Producers could no longer send messages (likely resulting in connection errors or timeouts).
* Consumers could no longer fetch messages and stalled or threw connection errors.
* This behavior was distinctly different from the baseline, where stopping one broker did not halt the application.

## Conclusion & Comparison to Baseline

* **Key Difference vs. Baseline:** **Fault Tolerance / Stability**.
* **Finding:** The baseline's 3-broker architecture provided essential resilience against single-node failure due to its distributed nature and data replication. In stark contrast, the single-broker setup **eliminated all fault tolerance**, creating a critical single point of failure.
* **Outcome:** This experiment clearly demonstrated that reducing the cluster to a single node fundamentally changes its stability profile compared to the baseline. It highlights why multiple brokers and appropriate replication factors are critical configurations for achieving the high availability and resilience that Kafka is known for, confirming that the baseline's multi-broker design was essential for its observed stability.

# Experiment 2: Parallel Processing & Split Output Report

## Goal

The primary goal was to demonstrate and observe Kafka's processing scalability achieved through topic partitioning and the use of multiple parallel consumer instances within the same consumer group. A secondary goal was to implement and verify a method for managing the output of this parallel processing by directing results to different files based on the source Kafka partition, using a single consumer script codebase.

## Setup & Actions

1.  **Cluster:** A 3-node Kafka cluster (using KRaft) was utilized, as defined in the `docker-compose.yml` from the Part 1.
2.  **Topics:** The relevant Kafka topics (`sensor_data`, `user_activity`, `processed_data`) were explicitly created with **6 partitions** each and a **replication factor of 3**.
    ```bash
    # Example creation command (run for each topic):
    docker exec kafka1 kafka-topics --bootstrap-server kafka1:9092 --create --topic sensor_data --partitions 6 --replication-factor 3
    ```
3.  **Code:**
    * The original producer scripts (`producer_sensor.py`, etc.) were used to generate data.
    * A modified consumer script, `processor_sink_partitioned_output.py`, was used. This script was designed to:
        * Consume raw messages and note their source partition.
        * Include the `source_partition` in the message sent to the `processed_data` topic.
        * Consume from `processed_data` and determine the output file path based on the `source_partition` field (partitions 0-2 to `processed_split_A.csv`, partitions 3-5 to `processed_split_B.csv`).
4.  **Execution:**
    * Producers were started to populate the input topics.
    * Multiple instances (e.g., 2 or 3) of the `processor_sink_partitioned_output.py` script were launched concurrently, ensuring they used the same consumer group IDs.

## Observations

* Multiple consumer instances were confirmed to be running simultaneously.
* Log analysis from individual consumer instances showed that Kafka correctly assigned multiple partitions to each instance (e.g., one instance handled partitions 0, 1, 4, 5, while others handled 2, 3).
    ```
    # Example Log Snippet from one instance:
    2025-04-11 07:20:44,677 - INFO - Processing batch from partition 4...
    2025-04-11 07:20:48,215 - INFO - Sinking batch from partition 0...
    2025-04-11 07:20:50,728 - INFO - Processing batch from partition 5...
    2025-04-11 07:20:52,850 - INFO - Sinking batch from partition 1...
    ```
## Conclusion

* This experiment successfully demonstrated **parallel message processing** across multiple consumer instances, showcasing Kafka's core scalability mechanism.
* The modified logic successfully **split the processed output into multiple files** based on data origin (partition), illustrating a method for managing results from distributed work.
* Overall, this experiment highlighted Kafka's ability to scale processing horizontally through partitioning and consumer groups, and demonstrated a practical approach to handling the output from such parallel execution.