# -*- coding: utf-8 -*-
"""
Run training for a UNet model.

@Time    : 2/2024
@Author  : Colm Keyes
@Email   : keyesco@tcd.ie
@File    : run_unet_model_command.py
"""


import subprocess
import os
import mim
os.environ["CUDA_LAUNCH_BLOCKING"] = "1"
import torch
# Command and arguments
# command = "mim"
# args = ["train", "mmsegmentation", "--launcher", "none", "--gpus", "1", "E:\hls-foundation-os\configs/forest_distrubances_config.py"]

# Running the command
# subprocess.run([command] + args)



from mim.commands.train import train

# Define the parameters for training
package_name = 'mmsegmentation'
config_path = "E:\hls-foundation-os\configs/unet_forest_disturbance_config.py"
num_gpus = 1

# Call the train function
success, message = train(package=package_name, config=config_path, gpus=num_gpus)

# Check the result
if success:
    print("Training completed successfully.")
else:
    print(f"Training failed: {message}")

#from mim.commands.test import t