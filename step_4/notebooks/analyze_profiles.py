# notebooks/analyze_profiles.py
import pstats
from pstats import SortKey
import sys

# Files to analyze, passed as command line arguments or default
DEFAULT_FILES = [
    "producer_sensor.prof",
    "producer_activity.prof",
    "processor_sink.prof",
]
files_to_analyze = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_FILES

# Number of lines to print in stats reports
TOP_N = 15

for filename in files_to_analyze:
    print(f"\n{'='*10} Analyzing: {filename} {'='*10}")
    try:
        stats = pstats.Stats(filename)

        print(f"\n--- Top {TOP_N} by CUMULATIVE TIME (cumtime) ---")
        stats.sort_stats(SortKey.CUMULATIVE).print_stats(TOP_N)

        print(f"\n--- Top {TOP_N} by TOTAL TIME in function (tottime) ---")
        stats.sort_stats(SortKey.TIME).print_stats(TOP_N)

        print(f"\n--- Top {TOP_N} by NUMBER OF CALLS (ncalls) ---")
        stats.sort_stats(SortKey.CALLS).print_stats(TOP_N)

    except FileNotFoundError:
        print(f"ERROR: Profile file not found: {filename}")
    except Exception as e:
        print(f"ERROR: Could not process file {filename}: {e}")

    print(f"{'='*10} End Analysis: {filename} {'='*10}\n")

print("Analysis complete.")
print(
    f"Hint: For visual analysis, run: pip install snakeviz && snakeviz {files_to_analyze[0]}"
)
