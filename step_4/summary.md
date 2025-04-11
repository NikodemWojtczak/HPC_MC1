## Experiment 1: Loop Timing Analysis

### Goal
The goal of this experiment was to quantify the typical execution time and variability of the main operational loops for both the Kafka producer and the consumer/sink application.

### Method
The original producer (`producer_sensor.py`) and consumer (`processor_sink.py`) scripts were modified to create timed versions (`*_timed.py`). These scripts used `time.perf_counter()` to measure the duration of each loop/batch and ran for a fixed number of iterations (300 for producer, 200 batches for consumer). The `statistics` module was used to calculate the average time, standard deviation, minimum, and maximum loop times upon completion.

### Results

* **Producer (`producer_sensor_timed.py`):**
    * Average loop time: **1.007061 seconds**
    * Standard deviation: **0.006623 seconds**
    * Min loop time: 1.001168 seconds
    * Max loop time: 1.115192 seconds
* **Consumer/Sink (`processor_sink_timed.py`):**
    * Average batch processing loop time: **0.978555 seconds**
    * Standard deviation: **0.162773 seconds**
    * Min batch time: 0.007458 seconds
    * Max batch time: 1.106129 seconds

### Discussion
The producer results show extremely consistent performance, with the average loop time just slightly above the hardcoded 1-second sleep. The very low standard deviation confirms that the producer's loop duration is almost entirely dictated by `time.sleep(1)`, with minimal overhead from data generation and sending the message (including waiting for acknowledgment).

Unlike the steady producer, the consumer script's speed changed a lot during each loop. On average, a loop took just under one second (0.98s), but sometimes it finished extremely quickly (around 0.01 seconds) and other times it took much longer (up to 1.1 seconds).

This big difference happened because the consumer waits up to 1 second for new messages if none are ready (poll timeout). The slowest loops (around 1.1 seconds) were when it had to wait that full second. The fastest loops (around 0.01 seconds) occurred when messages were already there, showing that the actual work of processing and saving data is very quick.

So, this tells us the consumer code itself runs efficiently, but it frequently has to wait for data to arrive from Kafka. The consumer code isn't the bottleneck; the waiting time is the main factor determining its loop duration in this test.

## Experiment 2: Method Profiling Analysis (cProfile / pstats / Visualization)

### Goal
The goal of this experiment was to identify the specific functions and methods within the original Python scripts that consumed the most execution time (either CPU time or wait time) and which functions were called most frequently. This helps pinpoint computational hotspots or significant waiting periods.

### Method
The original `producer_sensor.py` and `processor_sink.py` scripts were run using Python's `cProfile` module (`python -m cProfile -o ...`) to generate `.prof` data files. These files were then analyzed textually using the `pstats` module, sorting the results by cumulative time (`cumtime`), total time spent within the function (`tottime`), and number of calls (`ncalls`). Additionally, the `.prof` files were converted into PNG call graph visualizations using `gprof2dot` and Graphviz (`dot`) for a visual representation of time distribution.

### Results (Summary from pstats)

* **Producer (`producer_sensor.prof`):**
    * **Top `tottime`:** `{built-in method time.sleep}` (72.3s / 72.8s total runtime) was overwhelmingly dominant. `{method 'acquire' of '_thread.lock' objects}` (0.35s) and `kafka.producer.kafka.py:568(send)` (0.006s) were distant followers.
    * **Top `cumtime`:** Script execution (`exec`, `main`) and `time.sleep` were highest. Waiting for Kafka ack (`future.get`) showed ~0.25s cumulative time over 73 calls.
    * **Top `ncalls`:** Dominated by low-level built-ins like `len`, `isinstance`, `list.append`, string methods, etc.
* **Consumer (`processor_sink.prof`):**
    * **Top `tottime`:** `{built-in method time.sleep}` (52.6s), followed by `{method 'poll' of 'select.epoll' objects}` (21.0s - network I/O wait) and `{method 'acquire' of '_thread.lock' objects}` (6.3s - internal locking/wait).
    * **Top `cumtime`:** Dominated by script execution (`exec`, `main`), `time.sleep`, and then the Kafka polling function stack (`kafka.consumer.group.py:653(poll)`).
    * **Top `ncalls`:** Dominated by internal functions like `time.time`, Kafka metrics methods, built-ins (`max`, `len`), and thread lock exits.

### Discussion
The profiling results strongly reinforce the findings from the loop timing. The **producer** is clearly **sleep-bound**; almost all its time is spent paused in `time.sleep`. The actual Kafka operations consume very little relative time.

The **consumer** profile, based on the provided data showing `time.sleep` as dominant, suggests it was also primarily waiting (either sleeping or waiting for I/O). The next most significant time consumers were the low-level network wait (`epoll.poll` – representing the system efficiently waiting for messages to arrive from Kafka sockets) inherent in `KafkaConsumer.poll()` and internal thread locking (`acquire` – representing threads waiting for access to shared Kafka client resources). Crucially, functions related to the core application logic – `process_message`, `write_to_csv`, JSON parsing (`json.loads`) – **did not appear** among the top time consumers in either profile.

The generated PNG visualizations would visually confirm these findings, showing large blocks corresponding to the sleep or wait functions (`time.sleep`, `epoll.poll`). Together, these results indicate that for this workload, the Python application code itself is efficient, and performance is dictated by the designed sleep interval (producer) and network I/O waits for message arrival (consumer). No significant CPU-bound bottlenecks were identified within the user code.