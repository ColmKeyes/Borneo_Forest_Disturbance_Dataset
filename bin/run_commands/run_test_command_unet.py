# -*- coding: utf-8 -*-
"""
Run testing on UNet models and evaluate mIoU for each checkpoint.

@Time    : 2/2024
@Author  : Colm Keyes
@Email   : keyesco@tcd.ie
@File    : run_test_command_unet.py
"""



import subprocess
import os

models = [

"best_mIoU_iter_500_minalerts_15000_unet_coherence_final_run1_op.pth",

    "best_mIoU_iter_500_minalerts_15000_unet_backscatter_final_run1_op.pth",

    "best_mIoU_iter_500_minalerts_12500_unet_final_run1_op.pth",

]

base_ckpt_path = r"E:\PycharmProjects\hls-foundation-os\Prithvi-100m_unet"
base_log_dir = r"E:\PycharmProjects\hls-foundation-os\test_logs"
config_path = r"E:\hls-foundation-os\configs\forest_disturbances_config_unet.py"

for model in models:
    # Construct checkpoint path
    checkpoint_path = os.path.join(base_ckpt_path, model)

    # Create a specific log directory for each model
    model_log_dir = os.path.join(base_log_dir, os.path.splitext(model)[0])
    if not os.path.exists(model_log_dir):
        os.makedirs(model_log_dir)

    # Define the command to run the mmseg testing script for the current model
    command = [
        'python',
        r'c:\anaconda3\envs\prithvi-100m\lib\site-packages\mmseg\.mim\tools\test.py',
        config_path,
        checkpoint_path,
        '--out', os.path.join(model_log_dir, 'results.pkl'),
        '--eval', 'mIoU',
        '--work-dir', model_log_dir,
        '--launcher', 'none'
    ]

    # Execute the command
    print(f"Testing with model: {model}")
    subprocess.run(command)
    print(f"Finished testing with model: {model}\n")

