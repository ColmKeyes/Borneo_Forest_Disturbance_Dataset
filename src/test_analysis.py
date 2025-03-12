# -*- coding: utf-8 -*-
"""
Analise test metrics across multiple runs and calculate average performance.

@Time    : 2/2024
@Author  : Colm Keyes
@Email   : keyesco@tcd.ie
@File    : test_analysis.py
"""

import json
import pandas as pd
import numpy as np

class TestAnalysis:
    def __init__(self, log_files):
        self.log_files = log_files
        self.data = [self.load_log_data(log_file) for log_file in log_files]

    def load_log_data(self, log_file):
        """Load the log data from the JSON file."""
        with open(log_file, 'r') as f:
            return json.load(f)

    def get_average_metrics(self):
        """Calculate the average metrics across multiple runs."""
        metrics_list = [run_data['metric'] for run_data in self.data if 'metric' in run_data]

        # Initialize a dictionary to store the sum and count of the metrics
        sum_metrics = {}
        count_metrics = {}

        # Get the list of all metric names
        if not metrics_list:
            return {}
        metric_names = metrics_list[0].keys()

        # Sum the values for each metric and count the entries
        for metrics in metrics_list:
            for name in metric_names:
                if name in metrics:
                    sum_metrics[name] = sum_metrics.get(name, 0) + metrics[name]
                    count_metrics[name] = count_metrics.get(name, 0) + 1

        # Calculate the average for each metric
        average_metrics = {name: sum_metrics[name] / count_metrics[name] for name in metric_names}

        return average_metrics
