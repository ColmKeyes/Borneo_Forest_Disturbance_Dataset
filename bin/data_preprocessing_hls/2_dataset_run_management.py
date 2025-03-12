# -*- coding: utf-8 -*-
"""
"""
"""
@Time    : 6/12/2024 00:01
@Author  : Colm Keyes
@Email   : keyesco@tcd.ie
@File    : dataset_run_management
"""

import os
from src.dataset_management import DatasetManagement
from src.model_input_processor import Loader


source_dir = r"E:\Data\Sentinel2_data\30pc_cc\Borneo_June2021_Dec_2023_30pc_cc_stacks_agb_radd_forest_fmask"
train_dir = r"E:\Data\Sentinel2_data\30pc_cc\Tiles_512_30pc_cc\training"
train_dir_narrow = r"E:\Data\Sentinel2_data\30pc_cc\Tiles_512_30pc_cc\training_narrow"
val_dir = r"E:\Data\Sentinel2_data\30pc_cc\Tiles_512_30pc_cc\validation"
val_dir_narrow = r"E:\Data\Sentinel2_data\30pc_cc\Tiles_512_30pc_cc\validation_narrow"
output_dir = r"E:\Data\Sentinel2_data\30pc_cc\Tiles_512_30pc_cc"  # Directory to store cropped tiles

globalnorm_dir = r"E:\Data\Sentinel2_data\30pc_cc\Tiles_512_30pc_cc\globalnorm"
globalnorm_10000_dir = f"{globalnorm_dir}\\10000_minalerts"
globalnorm_12500_dir = f"{globalnorm_dir}\\12500_minalerts"
suffix = "_radd_fmask_stack.tif"
tile_size = 512

# Instantiate the DatasetManagement class with an additional output_dir parameter
data_manager = DatasetManagement(source_dir, train_dir, val_dir, output_dir, tile_size)
model_funcs = Loader(output_dir,  train_dir, val_dir, output_dir,tile_size)
if __name__ == '__main__':


    #############
    ## Step 9: Filter images based on minimal labels requirements. typical limits: 1000-5000.
    #############
    # alert_stacks = model_funcs.filter_stacks(output_dir,suffix, 1,15000)#5000)#1000) # set to 0 for current distribution
    # distribution = model_funcs.calculate_alert_distribution(alert_stacks,5)
    # print(distribution)

    #############
    ## Step 10: Crop sen2_agb_radd_forest_stacks into 512x512 tiles for model input
    #############
    test_sites = ["2023076_T49MET", "2023111_T49MET", "2023241_T49MDU","2023245_T50MKE", "2023271_T49MDU", "2023276_T49MDU","2023290_T50MKE"]
    for file in os.listdir(source_dir):
        if file.endswith('_radd_fmask_stack.tif'):
            if any(site in file for site in test_sites):
                image_path = os.path.join(source_dir, file)
                data_manager.crop_to_tiles(image_path,output_dir)
                print(f"cropping finished: {file}")

    #############
    ## Step 11: Re-Filter tiled images based on minimal labels requirements. typical limits: 1000-5000.
    #############

    # alert_stacks = model_funcs.filter_stacks(val_dir_narrow,1,7500)#output_dir, 1,0)#1000)
    # distribution = model_funcs.calculate_alert_distribution(alert_stacks,20)
    # print(distribution)



    #############
    ## step 12, split tiles into radd and sentinel2
    #############

    pairs = data_manager.split_tiles(output_dir) #globalnorm_dir) #output_dir)

    #############
    ## step 13, alter labels
    #############
    #
    # model_funcs.alter_radd_data_to_label(output_dir)

    #############
    ## step 14, split tiles into train_val_test
    #############
    # destination_directory = output_dir#globalnorm_12500_dir
    # data_manager.split_dataset(output_dir, destination_directory)#,pairs)







    #############
    ## utilites
    ## some plots
    #############

    # for file in os.listdir(train_dir):

        ## Plot all bands
    ## nmno need for full path.
    #output_dir_image = os.path.join(output_dir,"2021210_T50NNK_agb_radd_fmask_stack_1024_0_radd_modified_sentinel.tif")
    # data_manager.plot_7_bands("2021210_T50NNK_agb_radd_fmask_stack_1024_0_radd_modified_sentinel.tif")







