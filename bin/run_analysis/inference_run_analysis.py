# -*- coding: utf-8 -*-
"""
Run testing on UNet models and evaluate mIoU for each checkpoint.

@Time    : 2/2024
@Author  : Colm Keyes
@Email   : keyesco@tcd.ie
@File    : run_test_command_unet.py
"""



import os
from src.model_analysis import plot_image_triplet

base_output_path = r"E:\PycharmProjects\hls-foundation-os\test_image_results"

model_paths = [

    "Prithvi-100m/best_mIoU_iter_500_minalerts_10000_prithvi_final_run1_op.pth",
    "Prithvi-100m/best_mIoU_iter_500_minalerts_15000_prithvi_final_run1_op.pth",
    "Prithvi-100m_burnscars/best_mIoU_iter_400_minalerts_15000_prithvi_burnscars_final_run1_op.pth",
    "Prithvi-100m_unet/best_mIoU_iter_500_minalerts_15000_unet_final_run1_op.pth",
    "Prithvi-100m_unet/best_mIoU_iter_500_minalerts_10000_unet_final_run1_op.pth",
    "Prithvi-100m_backscatter/best_mIoU_iter_500_minalerts_15000_prithvi_backscatter_final_run1_op.pth",
    "Prithvi-100m_coherence/best_mIoU_iter_400_minalerts_15000_prithvi_coherence_final_run1_op.pth",
    "Prithvi-100m_unet_coherence/best_mIoU_iter_500_minalerts_15000_unet_coherence_final_run1_op.pth",

]
image_basenames = [
    "2023290_T50MKE_agb_radd_fmask_stack_1024_3072",
    "2023276_T49MDU_agb_radd_fmask_stack_2048_1024",
    "2023271_T49MDU_agb_radd_fmask_stack_2048_1024",
    "2023245_T50MKE_agb_radd_fmask_stack_2048_512",
    "2023241_T49MDU_agb_radd_fmask_stack_2048_1024",
    "2023111_T49MET_agb_radd_fmask_stack_512_512",
    "2023076_T49MET_agb_radd_fmask_stack_512_512",
]

save_path = r"E:\PycharmProjects\hls-foundation-os\test_image_results\comparisons"

for model_path in model_paths:
    data_type = ''
    if 'backscatter' in model_path:
        data_type = 'backscatter'
        input_path = r"E:\Data\Sentinel2_data\30pc_cc\Tiles_512_30pc_cc\globalnorm\15000_minalerts_backscatter\test"
        ground_truth_path = input_path
    elif 'coherence' in model_path:
        data_type = 'coherence'
        input_path = r"E:\Data\Sentinel2_data\30pc_cc\Tiles_512_30pc_cc\globalnorm\15000_minalerts_coherence\test"
        ground_truth_path = input_path
    else:
        input_path = r"E:\Data\Sentinel2_data\30pc_cc\Tiles_512_30pc_cc\globalnorm\15000_minalerts\test"
        ground_truth_path = input_path

    model_output_path = os.path.join(base_output_path, os.path.splitext(model_path)[0])
    final_image_path = os.path.join(save_path, os.path.basename(model_output_path))

    os.makedirs(final_image_path, exist_ok=True)

    for image_basename in image_basenames:
        plot_image_triplet(
            input_path=input_path,
            output_path=model_output_path,
            ground_truth_path=ground_truth_path,
            image_basename=image_basename,
            data_type=data_type,
            save_path=final_image_path
        )