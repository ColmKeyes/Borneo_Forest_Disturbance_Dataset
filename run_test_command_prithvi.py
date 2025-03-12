# -*- coding: utf-8 -*-
"""
Run testing on prithvi model and evaluate mIoU for each checkpoint.

@Time    : 2/2024
@Author  : Colm Keyes
@Email   : keyesco@tcd.ie
@File    : run_test_command_prithvi.py
"""



import subprocess
import os

models = [

"best_mIoU_iter_400_minalerts_15000_prithvi_burnscars_final_run1_op.pth",

    "best_mIoU_iter_500_minalerts_15000_prithvi_backscatter_final_run1_op.pth",

    "best_mIoU_iter_400_minalerts_15000_prithvi_coherence_final_run1_op.pth",

"best_mIoU_iter_400_minalerts_12500_prithvi_final_run1_op.pth",

]

base_ckpt_paths = {
    'prithvi': r"E:\PycharmProjects\hls-foundation-os\Prithvi-100m",
    'backscatter': r"E:\PycharmProjects\hls-foundation-os\Prithvi-100m_backscatter",
    'coherence': r"E:\PycharmProjects\hls-foundation-os\Prithvi-100m_coherence",
    'burnscars': r"E:\PycharmProjects\hls-foundation-os\Prithvi-100m_burnscars",
}

base_log_dir = r"E:\PycharmProjects\hls-foundation-os\test_logs"

# Config paths for each data type
config_paths = {
    "prithvi": r"E:\hls-foundation-os\configs\forest_disturbances_config.py",
    'backscatter': r"E:\hls-foundation-os\configs\forest_disturbances_config_backscatter.py",
    'coherence': r"E:\hls-foundation-os\configs\forest_disturbances_config_coherence.py",
    'burnscars': r"E:\hls-foundation-os\configs\forest_disturbances_config_burnscars.py",
}


for model in models:
    data_type = 'prithvi'  # Default to 'final' if no specific data type is found in the model name
    if 'backscatter' in model:
        data_type = 'backscatter'
    elif 'coherence' in model:
        data_type = 'coherence'
    elif 'burnscars' in model:
        data_type = 'burnscars'

    # Select the appropriate config file based on the data type
    config_path = config_paths[data_type]
    base_ckpt_path = base_ckpt_paths[data_type]

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
        '--show-dir', model_log_dir,
        '--launcher', 'none'
    ]

    # Execute the command
    print(f"Testing with model: {model} using {data_type} config")
    subprocess.run(command)
    print(f"Finished testing with model: {model}\n")

