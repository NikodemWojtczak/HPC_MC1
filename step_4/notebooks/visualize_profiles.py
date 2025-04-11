#!/usr/bin/env python3
# visualize_profiles.py - Generate static visualizations from Python profiling data
import pstats
import matplotlib.pyplot as plt
import numpy as np
import os

# Profile files to visualize
PROFILE_FILES = ["producer_sensor.prof", "processor_sink.prof"]

# Number of top functions to display
TOP_N = 15


def create_bar_chart(stats, sort_key, title, filename):
    """Create a horizontal bar chart of the top functions."""
    # Sort the stats by the specified key
    sorted_stats = stats.sort_stats(sort_key)

    # Get the top functions
    function_stats = []
    for func, (cc, nc, tt, ct, callers) in sorted_stats.stats.items():
        name = func[2] if len(func) > 2 else str(func)
        if "/" in name:  # For clarity, show only the function name without full path
            name = name.split("/")[-1]
        function_stats.append((name, ct))  # Use cumulative time

    # Sort by cumulative time and get top N
    function_stats.sort(key=lambda x: x[1], reverse=True)
    top_functions = function_stats[:TOP_N]

    # Create a bar chart
    fig, ax = plt.subplots(figsize=(12, 8))

    names = [f"{i+1}. {func}" for i, (func, _) in enumerate(top_functions)]
    values = [time for _, time in top_functions]

    # Plot horizontal bars
    y_pos = np.arange(len(names))
    ax.barh(y_pos, values, align="center")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(names)
    ax.invert_yaxis()  # Labels read top-to-bottom
    ax.set_xlabel("Time (seconds)")
    ax.set_title(title)

    # Add values on the bars
    for i, v in enumerate(values):
        ax.text(v + 0.1, i, f"{v:.2f}s", va="center")

    plt.tight_layout()
    plt.savefig(filename)
    print(f"Saved chart to {filename}")


def visualize_profile(profile_file):
    """Generate visualizations for a single profile file."""
    print(f"\nProcessing {profile_file}...")

    # Load stats from the profile file
    stats = pstats.Stats(profile_file)

    # Base filename for the output charts
    base_name = os.path.splitext(profile_file)[0]

    # Create charts for different metrics
    create_bar_chart(
        stats,
        "cumulative",
        f"Top {TOP_N} Functions by Cumulative Time - {base_name}",
        f"{base_name}_cumtime.png",
    )

    create_bar_chart(
        stats,
        "time",
        f"Top {TOP_N} Functions by Total Time - {base_name}",
        f"{base_name}_tottime.png",
    )

    create_bar_chart(
        stats,
        "calls",
        f"Top {TOP_N} Functions by Number of Calls - {base_name}",
        f"{base_name}_calls.png",
    )


def main():
    """Main function to process all profile files."""
    print("Generating visualizations for profile files...")

    for profile_file in PROFILE_FILES:
        try:
            visualize_profile(profile_file)
        except FileNotFoundError:
            print(f"ERROR: Profile file not found: {profile_file}")
        except Exception as e:
            print(f"ERROR: Could not process file {profile_file}: {e}")

    print(
        "\nVisualization complete. PNG files have been created in the current directory."
    )


if __name__ == "__main__":
    main()
