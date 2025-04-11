Experiment 1
Producer sensor
2025-04-09 17:59:36,931 - INFO - --- Timing Results (300 iterations) ---
2025-04-09 17:59:36,931 - INFO - Average loop time: 1.007061 seconds
2025-04-09 17:59:36,931 - INFO - Standard deviation: 0.006623 seconds
2025-04-09 17:59:36,931 - INFO - Min loop time: 1.001168 seconds
2025-04-09 17:59:36,931 - INFO - Max loop time: 1.115192 seconds

processor_sink_timed.py
2025-04-09 17:57:49,264 - INFO - --- Timing Results (200 batches) ---
2025-04-09 17:57:49,264 - INFO - Average batch processing loop time: 0.978555 seconds
2025-04-09 17:57:49,264 - INFO - Standard deviation: 0.162773 seconds
2025-04-09 17:57:49,264 - INFO - Min batch time: 0.007458 seconds
2025-04-09 17:57:49,264 - INFO - Max batch time: 1.106129 seconds

Experiment 2

========== Analyzing: producer_sensor.prof ==========

--- Top 15 by CUMULATIVE TIME (cumtime) ---
Wed Apr  9 18:19:23 2025    producer_sensor.prof

         96540 function calls (94597 primitive calls) in 72.852 seconds

   Ordered by: cumulative time
   List reduced from 1649 to 15 due to restriction <15>

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
    138/1    0.001    0.000   72.852   72.852 {built-in method builtins.exec}
        1    0.000    0.000   72.852   72.852 producer_sensor.py:1(<module>)
        1    0.004    0.004   72.805   72.805 producer_sensor.py:95(main)
       73   72.348    0.991   72.348    0.991 {built-in method time.sleep}
       73    0.002    0.000    0.416    0.006 producer_sensor.py:80(send_data)
       76    0.001    0.000    0.354    0.005 /opt/conda/lib/python3.11/threading.py:604(wait)
       76    0.001    0.000    0.352    0.005 /opt/conda/lib/python3.11/threading.py:288(wait)
      307    0.352    0.001    0.352    0.001 {method 'acquire' of '_thread.lock' objects}
       73    0.001    0.000    0.251    0.003 /opt/conda/lib/python3.11/site-packages/kafka/producer/future.py:59(get)
       73    0.000    0.000    0.250    0.003 /opt/conda/lib/python3.11/site-packages/kafka/producer/future.py:26(wait)
       73    0.006    0.000    0.163    0.002 /opt/conda/lib/python3.11/site-packages/kafka/producer/kafka.py:568(send)
       73    0.001    0.000    0.107    0.001 /opt/conda/lib/python3.11/site-packages/kafka/producer/kafka.py:702(_wait_on_metadata)
    171/5    0.000    0.000    0.047    0.009 <frozen importlib._bootstrap>:1165(_find_and_load)
    171/5    0.000    0.000    0.047    0.009 <frozen importlib._bootstrap>:1120(_find_and_load_unlocked)
    160/5    0.000    0.000    0.047    0.009 <frozen importlib._bootstrap>:666(_load_unlocked)



--- Top 15 by TOTAL TIME in function (tottime) ---
Wed Apr  9 18:19:23 2025    producer_sensor.prof

         96540 function calls (94597 primitive calls) in 72.852 seconds

   Ordered by: internal time
   List reduced from 1649 to 15 due to restriction <15>

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
       73   72.348    0.991   72.348    0.991 {built-in method time.sleep}
      307    0.352    0.001    0.352    0.001 {method 'acquire' of '_thread.lock' objects}
       73    0.006    0.000    0.163    0.002 /opt/conda/lib/python3.11/site-packages/kafka/producer/kafka.py:568(send)
      136    0.005    0.000    0.005    0.000 {built-in method marshal.loads}
       76    0.005    0.000    0.005    0.000 {method 'sendall' of '_socket.socket' objects}
       73    0.004    0.000    0.011    0.000 producer_sensor.py:70(generate_sensor_data)
       73    0.004    0.000    0.004    0.000 /opt/conda/lib/python3.11/json/encoder.py:205(iterencode)
        1    0.004    0.004   72.805   72.805 producer_sensor.py:95(main)
       73    0.004    0.000    0.023    0.000 /opt/conda/lib/python3.11/site-packages/kafka/producer/record_accumulator.py:184(append)
       81    0.004    0.000    0.004    0.000 {method 'write' of '_io.TextIOWrapper' objects}
  673/667    0.003    0.000    0.010    0.000 {built-in method builtins.__build_class__}
       81    0.003    0.000    0.006    0.000 /opt/conda/lib/python3.11/logging/__init__.py:292(__init__)
       76    0.002    0.000    0.002    0.000 /opt/conda/lib/python3.11/threading.py:236(__init__)
  676/638    0.002    0.000    0.003    0.000 {built-in method __new__ of type object at 0xaaaaca237740}
       73    0.002    0.000    0.004    0.000 /opt/conda/lib/python3.11/site-packages/kafka/record/default_records.py:461(append)



--- Top 15 by NUMBER OF CALLS (ncalls) ---
Wed Apr  9 18:19:23 2025    producer_sensor.prof

         96540 function calls (94597 primitive calls) in 72.852 seconds

   Ordered by: call count
   List reduced from 1649 to 15 due to restriction <15>

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
5822/5619    0.001    0.000    0.001    0.000 {built-in method builtins.len}
     4603    0.001    0.000    0.001    0.000 {built-in method builtins.isinstance}
     3553    0.000    0.000    0.000    0.000 {method 'append' of 'list' objects}
     3476    0.000    0.000    0.000    0.000 {method 'rstrip' of 'str' objects}
     2580    0.000    0.000    0.000    0.000 {method 'startswith' of 'str' objects}
     1996    0.000    0.000    0.000    0.000 {method 'join' of 'str' objects}
     1885    0.001    0.000    0.001    0.000 {built-in method builtins.getattr}
     1697    0.000    0.000    0.000    0.000 <frozen importlib._bootstrap>:244(_verbose_message)
1674/1669    0.000    0.000    0.000    0.000 {built-in method builtins.hasattr}
     1602    0.001    0.000    0.001    0.000 <frozen importlib._bootstrap_external>:128(<listcomp>)
     1602    0.001    0.000    0.002    0.000 <frozen importlib._bootstrap_external>:126(_path_join)
     1466    0.000    0.000    0.000    0.000 {method 'isupper' of 'str' objects}
     1258    0.000    0.000    0.000    0.000 /opt/conda/lib/python3.11/re/_parser.py:164(__getitem__)
     1156    0.000    0.000    0.000    0.000 {method 'get' of 'dict' objects}
     1120    0.000    0.000    0.000    0.000 /opt/conda/lib/python3.11/re/_parser.py:233(__next)


========== End Analysis: producer_sensor.prof ==========


========== Analyzing: producer_activity.prof ==========
ERROR: Profile file not found: producer_activity.prof
========== End Analysis: producer_activity.prof ==========


========== Analyzing: processor_sink.prof ==========

--- Top 15 by CUMULATIVE TIME (cumtime) ---
Wed Apr  9 18:19:30 2025    processor_sink.prof

         1366446 function calls (1357398 primitive calls) in 81.491 seconds

   Ordered by: cumulative time
   List reduced from 1981 to 15 due to restriction <15>

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
    139/1    0.001    0.000   81.492   81.492 {built-in method builtins.exec}
        1    0.000    0.000   81.492   81.492 processor_sink.py:1(<module>)
        1    0.011    0.011   81.447   81.447 processor_sink.py:151(main)
      109   52.561    0.482   52.561    0.482 {built-in method time.sleep}
      357    0.011    0.000   22.252    0.062 /opt/conda/lib/python3.11/site-packages/kafka/consumer/group.py:653(poll)
     2911    0.022    0.000   22.232    0.008 /opt/conda/lib/python3.11/site-packages/kafka/consumer/group.py:702(_poll_once)
     3374    0.034    0.000   21.651    0.006 /opt/conda/lib/python3.11/site-packages/kafka/client_async.py:625(poll)
     3540    0.039    0.000   21.514    0.006 /opt/conda/lib/python3.11/site-packages/kafka/client_async.py:713(_poll)
     3540    0.015    0.000   21.062    0.006 /opt/conda/lib/python3.11/selectors.py:451(select)
     3540   21.044    0.006   21.044    0.006 {method 'poll' of 'select.epoll' objects}
     1525    6.282    0.004    6.282    0.004 {method 'acquire' of '_thread.lock' objects}
        2    0.000    0.000    6.020    3.010 /opt/conda/lib/python3.11/site-packages/kafka/consumer/group.py:477(close)
        2    0.000    0.000    6.017    3.008 /opt/conda/lib/python3.11/site-packages/kafka/coordinator/consumer.py:443(close)
        2    0.000    0.000    6.011    3.006 /opt/conda/lib/python3.11/site-packages/kafka/coordinator/base.py:805(close)
        4    0.000    0.000    6.003    1.501 /opt/conda/lib/python3.11/site-packages/kafka/coordinator/base.py:791(_close_heartbeat_thread)



--- Top 15 by TOTAL TIME in function (tottime) ---
Wed Apr  9 18:19:30 2025    processor_sink.prof

         1366446 function calls (1357398 primitive calls) in 81.491 seconds

   Ordered by: internal time
   List reduced from 1981 to 15 due to restriction <15>

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
      109   52.561    0.482   52.561    0.482 {built-in method time.sleep}
     3540   21.044    0.006   21.044    0.006 {method 'poll' of 'select.epoll' objects}
     1525    6.282    0.004    6.282    0.004 {method 'acquire' of '_thread.lock' objects}
      614    0.070    0.000    0.070    0.000 {method 'send' of '_socket.socket' objects}
     1843    0.069    0.000    0.069    0.000 {built-in method posix.stat}
      704    0.052    0.000    0.052    0.000 {method '__exit__' of '_io._IOBase' objects}
12223/9709    0.049    0.000    0.189    0.000 /opt/conda/lib/python3.11/site-packages/kafka/metrics/stats/sensor.py:59(record)
    29921    0.045    0.000    0.093    0.000 /opt/conda/lib/python3.11/site-packages/kafka/metrics/stats/sampled_stat.py:40(record)
      567    0.041    0.000    0.041    0.000 {built-in method io.open}
     3540    0.039    0.000   21.514    0.006 /opt/conda/lib/python3.11/site-packages/kafka/client_async.py:713(_poll)
      940    0.035    0.000    0.035    0.000 /opt/conda/lib/python3.11/site-packages/kafka/record/_crc32c.py:100(crc_update)
     3374    0.034    0.000   21.651    0.006 /opt/conda/lib/python3.11/site-packages/kafka/client_async.py:625(poll)
     2907    0.030    0.000    0.107    0.000 /opt/conda/lib/python3.11/site-packages/kafka/consumer/fetcher.py:577(_create_fetch_requests)
    16283    0.028    0.000    0.043    0.000 /opt/conda/lib/python3.11/site-packages/kafka/conn.py:1199(next_ifr_request_timeout_ms)
    12223    0.025    0.000    0.033    0.000 /opt/conda/lib/python3.11/site-packages/kafka/metrics/stats/sensor.py:82(_check_quotas)



--- Top 15 by NUMBER OF CALLS (ncalls) ---
Wed Apr  9 18:19:30 2025    processor_sink.prof

         1366446 function calls (1357398 primitive calls) in 81.491 seconds

   Ordered by: call count
   List reduced from 1981 to 15 due to restriction <15>

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
    93967    0.013    0.000    0.013    0.000 {built-in method time.time}
    59842    0.008    0.000    0.008    0.000 /opt/conda/lib/python3.11/site-packages/kafka/metrics/kafka_metric.py:27(config)
    56578    0.015    0.000    0.015    0.000 {built-in method builtins.max}
48436/48233    0.008    0.000    0.008    0.000 {built-in method builtins.len}
    29991    0.015    0.000    0.016    0.000 /opt/conda/lib/python3.11/site-packages/kafka/metrics/stats/sampled_stat.py:54(current)
    29921    0.017    0.000    0.017    0.000 /opt/conda/lib/python3.11/site-packages/kafka/metrics/stats/sampled_stat.py:101(is_complete)
    29921    0.045    0.000    0.093    0.000 /opt/conda/lib/python3.11/site-packages/kafka/metrics/stats/sampled_stat.py:40(record)
    29289    0.011    0.000    0.013    0.000 {built-in method builtins.min}
    28446    0.011    0.000    0.011    0.000 {method '__exit__' of '_thread.RLock' objects}
    26353    0.005    0.000    0.006    0.000 {built-in method builtins.isinstance}
    24747    0.004    0.000    0.004    0.000 {method 'get' of 'dict' objects}
    24209    0.005    0.000    0.005    0.000 {method '__exit__' of '_thread.lock' objects}
    17973    0.004    0.000    0.004    0.000 {built-in method builtins.iter}
    16672    0.003    0.000    0.003    0.000 {method 'values' of 'dict' objects}
    16283    0.028    0.000    0.043    0.000 /opt/conda/lib/python3.11/site-packages/kafka/conn.py:1199(next_ifr_request_timeout_ms)


========== End Analysis: processor_sink.prof ==========