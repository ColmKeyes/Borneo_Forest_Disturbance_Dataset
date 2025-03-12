# -*- coding: utf-8 -*-
"""
Analise and compare model performance metrics across different runs.

@Time    : 2/2024
@Author  : Colm Keyes
@Email   : keyesco@tcd.ie
@File    : model_run_analysis.py
"""

import matplotlib.pyplot as plt
import os
from src.model_analysis import ModelAnalysis

# Paths to your log files
log_files = {
    "minalerts_10000_prithvi": r"E:\PycharmProjects\hls-foundation-os\Prithvi-100m\best_mIoU_iter_1000_minalerts_10000_prithvi.log.json",
    "minalerts_10000_unet": r"E:\PycharmProjects\hls-foundation-os\Prithvi-100m\best_mIoU_iter_1000_minalerts_10000_unet.log.json",
    "minalerts_10000_prithvi_burnscars": r"E:\PycharmProjects\hls-foundation-os\Prithvi-100m\best_mIoU_iter_1000_minalerts_10000_prithvi_burnscars.log.json",
    "minalerts_12500_prithvi": r"E:\PycharmProjects\hls-foundation-os\Prithvi-100m\best_mIoU_iter_1000_minalerts_12500_prithvi.log.json",
    "minalerts_12500_unet": r"E:\PycharmProjects\hls-foundation-os\Prithvi-100m\best_mIoU_iter_1000_minalerts_12500_unet.log.json",
    "minalerts_12500_prithvi_burnscars": r"E:\PycharmProjects\hls-foundation-os\Prithvi-100m\best_mIoU_iter_900_minalerts_12500_prithvi_burnscars.log.json",
    "minalerts_15000_prithvi": r"E:\PycharmProjects\hls-foundation-os\Prithvi-100m\best_mIoU_iter_1000_minalerts_15000_prithvi.log.json",
    "minalerts_15000_unet": r"E:\PycharmProjects\hls-foundation-os\Prithvi-100m\best_mIoU_iter_900_minalerts_15000_unet.log.json",
    "minalerts_15000_prithvi_burnscars": r"E:\PycharmProjects\hls-foundation-os\Prithvi-100m\best_mIoU_iter_1000_minalerts_15000_prithvi_burnscars.log.json",
}

# Initialize ModelAnalysis objects
analyses = {name: ModelAnalysis(log_file) for name, log_file in log_files.items()}

# Specify the metrics to plot
metrics = ["aAcc", "mIoU", "mAcc", "IoU.Forest", "IoU.Disturbed_Forest", "Acc.Forest", "Acc.Disturbed_Forest"]

# Create a directory for the result images if it doesn't exist
output_dir = r"E:\Data\Results\Prithvi_model_analysis_images"
os.makedirs(output_dir, exist_ok=True)

# Plot metrics
for metric in metrics:
    fig, ax = plt.subplots()
    for name, analysis in analyses.items():
        analysis.plot_metric(metric, ax, label=name.replace('_', ' '))

    ax.set_ylim([0, 1])
    plt.title(metric)
    plt.legend()
    plt.savefig(os.path.join(output_dir, f"{metric}_comparison.png"))
    plt.close()









