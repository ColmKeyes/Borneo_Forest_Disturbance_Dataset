# -*- coding: utf-8 -*-
"""
Produce inference from checkpoint-model pairs.

@Time    : 2/2024
@Author  : Colm Keyes
@Email   : keyesco@tcd.ie
@File    : run_inference_command.py
"""


import subprocess
import os

base_ckpt_path = r"E:\PycharmProjects\hls-foundation-os"
base_output_path = r"E:\PycharmProjects\hls-foundation-os\test_image_results"
base_config_path = r"E:\hls-foundation-os\configs"
base_input_path = r"E:\Data\Sentinel2_data\30pc_cc\Tiles_512_30pc_cc\globalnorm"

model_config_pairs = [

    ("Prithvi-100m_coherence/best_mIoU_iter_400_minalerts_15000_prithvi_coherence_final_run1_op.pth", "forest_disturbances_config_coherence.py"),
    ("Prithvi-100m_coherence/best_mIoU_iter_400_minalerts_15000_prithvi_coherence_final_run2_op.pth", "forest_disturbances_config_coherence.py"),
    ("Prithvi-100m_coherence/best_mIoU_iter_500_minalerts_15000_prithvi_coherence_final_run3_op.pth", "forest_disturbances_config_coherence.py"),
    ("Prithvi-100m_backscatter/best_mIoU_iter_500_minalerts_15000_prithvi_backscatter_final_run1_op.pth", "forest_disturbances_config_backscatter.py"),
    ("Prithvi-100m_backscatter/best_mIoU_iter_500_minalerts_15000_prithvi_backscatter_final_run2_op.pth", "forest_disturbances_config_backscatter.py"),
    ("Prithvi-100m_backscatter/best_mIoU_iter_500_minalerts_15000_prithvi_backscatter_final_run3_op.pth", "forest_disturbances_config_backscatter.py"),

    ("Prithvi-100m_unet_coherence/best_mIoU_iter_500_minalerts_15000_unet_coherence_final_run1_op.pth", "forest_disturbances_config_unet_coherence.py"),
    ("Prithvi-100m_unet_coherence/best_mIoU_iter_500_minalerts_15000_unet_coherence_final_run1_op.pth", "forest_disturbances_config_unet_coherence.py"),
    ("Prithvi-100m_unet_coherence/best_mIoU_iter_500_minalerts_15000_unet_coherence_final_run1_op.pth", "forest_disturbances_config_unet_coherence.py"),
    ("Prithvi-100m_unet_backscatter/best_mIoU_iter_500_minalerts_15000_unet_backscatter_final_run1_op.pth", "forest_disturbances_config_unet_backscatter.py"),
    ("Prithvi-100m_unet_backscatter/best_mIoU_iter_400_minalerts_15000_unet_backscatter_final_run1_op.pth", "forest_disturbances_config_unet_backscatter.py"),
    ("Prithvi-100m_unet_backscatter/best_mIoU_iter_500_minalerts_15000_unet_backscatter_final_run1_op.pth", "forest_disturbances_config_unet_backscatter.py"),

]

input_type = "tif"
bands = "[0,1,2,3,4,5]"
out_channels = 1

for model, config in model_config_pairs:
    # Construct checkpoint path
    ckpt_path = os.path.join(base_ckpt_path, model)

    # Select input path based on model type
    if "backscatter" in model:
        input_path = os.path.join(base_input_path, "15000_minalerts_backscatter/test/")
    elif "coherence" in model:
        input_path = os.path.join(base_input_path, "15000_minalerts_coherence/test/")
    else:
        input_path = os.path.join(base_input_path, "15000_minalerts/test/")

    # Define config path
    config_path = os.path.join(base_config_path, config)

    # Create a specific output directory for each model
    model_output_path = os.path.join(base_output_path, os.path.splitext(model)[0])
    if not os.path.exists(model_output_path):
        os.makedirs(model_output_path)

    # Construct the command
    command = [
        'python', 'model_inference.py',
        '-config', config_path,
        '-ckpt', ckpt_path,
        '-input', input_path,
        '-output', model_output_path,
        '-input_type', input_type,
        '-bands', bands,
    ]

    # Run the command
    subprocess.run(command)