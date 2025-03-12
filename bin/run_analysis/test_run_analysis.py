
# -*- coding: utf-8 -*-
"""
Analise and summarize test run metrics from multiple model logs.

@Time    : 2/2024
@Author  : Colm Keyes
@Email   : keyesco@tcd.ie
@File    : test_run_analysis.py
"""


import os
import glob
import pandas as pd
from src.test_analysis import TestAnalysis
import pandas as pd
import re
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

def get_base_model_name(dir_name):
    # Split the directory name and keep the model type and minalerts
    if not dir_name.startswith('best'):
        return None

    # Initialize a list to hold the parts of the base name
    base_parts = []

    # Iterate through each part of the directory name
    parts = dir_name.split('_')
    for part in parts:
        # Check if the part is numeric or a run identifier
        if part.isnumeric() or part.startswith('run'):
            continue
        # Check if the part is related to the iteration number
        if 'iter' in part:
            continue
        # For the minalerts part, keep it as is
        if 'minalerts' in part:
            # Find the next part, which is the numeric value for minalerts
            minalerts_index = parts.index(part) + 1
            if minalerts_index < len(parts) and parts[minalerts_index].isnumeric():
                base_parts.append(f"{part}_{parts[minalerts_index]}")
                continue
        # For other parts, add them to the base parts
        base_parts.append(part)

    # Join the parts to form the base model name
    base_model_name = '_'.join(base_parts)
    return base_model_name

# Directory containing all log directories
base_log_dir = r"E:\PycharmProjects\hls-foundation-os\test_logs"

# Initialize a dictionary to group log files by their base model names
model_logs = {}

# Gather all JSON files and group them by their base model name
for model_dir in os.listdir(base_log_dir):
    model_log_dir = os.path.join(base_log_dir, model_dir)
    if os.path.isdir(model_log_dir) and model_dir.startswith('best'):
        base_model_name = get_base_model_name(model_dir)
        if base_model_name:
            json_files = glob.glob(os.path.join(model_log_dir, '*.json'))
            if base_model_name in model_logs:
                model_logs[base_model_name].extend(json_files)
            else:
                model_logs[base_model_name] = json_files

# Process the grouped log files and calculate average metrics
all_metrics = []

for base_model, log_files in model_logs.items():
    print(f"Analyzing {base_model}")
    analysis = TestAnalysis(log_files)  # Ensure TestAnalysis can handle multiple log files
    metrics = analysis.get_average_metrics()
    if metrics:  # Check if metrics were successfully calculated
        metrics['model'] = base_model  # Label the metrics with the model identifier
        all_metrics.append(metrics)

# Create a DataFrame from the metrics and save or display as needed
df = pd.DataFrame(all_metrics)
df.set_index('model', inplace=True)
print(df)

# Save the DataFrame to a CSV file
csv_file = os.path.join(base_log_dir, 'model_metrics_summary.csv')
df.to_csv(csv_file)
print(f"Metrics saved to {csv_file}")
#


