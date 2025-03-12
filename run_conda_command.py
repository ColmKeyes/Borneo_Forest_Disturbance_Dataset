
# -*- coding: utf-8 -*-
"""
Iterates through configuration files and runs training for each config model.

@Time    : 2/2024
@Author  : Colm Keyes
@Email   : keyesco@tcd.ie
@File    : run_conda_command.py
"""

import os
from mim.commands.train import train

# Set the necessary environment variable for CUDA
os.environ["CUDA_LAUNCH_BLOCKING"] = "1"

# Define the base parameters for training
package_name = 'mmsegmentation'
base_config_path = "E:\\hls-foundation-os\\configs"
config_files = [
    "forest_disturbances_config.py",
    "forest_disturbances_config_burnscars.py",
    "forest_disturbances_config_backscatter.py",
    "forest_disturbances_config_coherence.py",
    "forest_disturbances_config_unet_backscatter.py",
    "forest_disturbances_config_unet_coherence.py",
    "forest_disturbances_config_unet.py",


]
num_gpus = 1

# Iterate through the configuration files and run training for each
for config_file in config_files:
    config_path = os.path.join(base_config_path, config_file)

    # Ensure the configuration file exists before attempting to train
    if os.path.exists(config_path):
        print(f"Starting training with configuration: {config_file}")
        success, message = train(package=package_name, config=config_path, gpus=num_gpus)

        # Check the result
        if success:
            print(f"Training completed successfully for {config_file}.")
        else:
            print(f"Training failed for {config_file}: {message}")
    else:
        print(f"Configuration file not found: {config_path}")