# -*- coding: utf-8 -*-
"""
Simple SageMaker-compatible inference script. inference_entry_point.py.

#######
## Introduction
#######
- This script reads arguments from command line or environment variables.
- Replaces local paths with container paths.
- Calls model_inference.py for actual inference.
"""

import argparse
import os
import subprocess

#######
## 1. Parse Arguments
#######
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint_name", type=str, default="best_mIoU_iter_400_coherence.pth",
                        help="Name of the checkpoint file.")
    parser.add_argument("--config_name", type=str, default="forest_disturbances_config_coherence.py",
                        help="Name of the config file.")
    parser.add_argument("--input_path", type=str, default="/opt/ml/input/data/test",
                        help="Where the inference input data is stored in the container.")
    parser.add_argument("--output_path", type=str, default="/opt/ml/output/inference_results",
                        help="Where results should be written inside the container.")
    parser.add_argument("--bands", type=str, default="[0,1,2,3,4,5]",
                        help="Which bands to include.")
    return parser.parse_args()

#######
## 2. Main Inference Logic
#######
def run_inference(args):
    # Construct the container-based paths
    ckpt_path = os.path.join("/opt/ml/input/data", args.checkpoint_name)
    config_path = os.path.join("/opt/ml/input/data", args.config_name)
    model_output_path = args.output_path

    if not os.path.exists(model_output_path):
        os.makedirs(model_output_path)

    command = [
        "python", "model_inference.py",
        "-config", config_path,
        "-ckpt", ckpt_path,
        "-input", args.input_path,
        "-output", model_output_path,
        "-input_type", "tif",
        "-bands", args.bands,
    ]

    print("Running inference with command:", " ".join(command))
    subprocess.run(command, check=True)
    print("Inference complete. Results saved to:", model_output_path)

#######
## 3. Entry Point
#######
if __name__ == "__main__":
    args = parse_args()
    run_inference(args)
