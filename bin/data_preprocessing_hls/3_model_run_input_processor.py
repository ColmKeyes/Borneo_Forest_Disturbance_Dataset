"""
@Time    : [Time of Creation, e.g., 07/12/2023 10:00]
@Author  : Colm Keyes
@Email   : keyesco@tcd.ie
@File    : 3_model_run_input_processor.py
"""

import rasterio
from rasterio.windows import Window
import numpy as np
import os
from src.model_input_processor import Loader

output_folder = r"E:\Data\Sentinel2_data\30pc_cc\Tiles_512_30pc_cc"
combined_radd_sen2_stack_path = r"E:\Data\Sentinel2_data\30pc_cc\Borneo_June2020_Jan2023_30pc_cc_stacks_radd"
stack_path_list = r'E:\Data\Sentinel2_data\30pc_cc\Borneo_June2020_Jan2023_30pc_cc_stacks_radd'
source_dir = r"E:\Data\Sentinel2_data\30pc_cc\Borneo_June2020_Jan2023_30pc_cc_stacks_radd_fmask_corrected"
train_dir = r"E:\Data\Sentinel2_data\30pc_cc\Tiles_512_30pc_cc\training"
train_narrow_dir = r"E:\Data\Sentinel2_data\30pc_cc\Tiles_512_30pc_cc\training_narrow"

train_narrow_folder_test = r"E:\Data\Sentinel2_data\30pc_cc\Tiles_512_30pc_cc\training_narrow\test"
val_dir = r"E:\Data\Sentinel2_data\30pc_cc\Tiles_512_30pc_cc\validation"
val_narrow_dir = r"E:\Data\Sentinel2_data\30pc_cc\Tiles_512_30pc_cc\validation_narrow"
val_narrow_dir_test = r"E:\Data\Sentinel2_data\30pc_cc\Tiles_512_30pc_cc\validation_narrow\test"
test_dir = r"E:\Data\Sentinel2_data\30pc_cc\Tiles_512_30pc_cc\test"
output_dir = r"E:\Data\Sentinel2_data\30pc_cc\Tiles_512_30pc_cc"
train_globnorm_10000 = r"E:\Data\Sentinel2_data\30pc_cc\Tiles_512_30pc_cc\globalnorm\10000_minalerts\train"
test_globnorm_10000 = r"E:\Data\Sentinel2_data\30pc_cc\Tiles_512_30pc_cc\globalnorm\10000_minalerts\test"
val_globnorm_10000 = r"E:\Data\Sentinel2_data\30pc_cc\Tiles_512_30pc_cc\globalnorm\10000_minalerts\val"
train_globnorm_12500 = r"E:\Data\Sentinel2_data\30pc_cc\Tiles_512_30pc_cc\globalnorm\12500_minalerts\train"
val_globnorm_12500 = r"E:\Data\Sentinel2_data\30pc_cc\Tiles_512_30pc_cc\globalnorm\12500_minalerts\val"
train_globnorm_15000 = r"E:\Data\Sentinel2_data\30pc_cc\Tiles_512_30pc_cc\globalnorm\15000_minalerts\train"
val_globnorm_15000 = r"E:\Data\Sentinel2_data\30pc_cc\Tiles_512_30pc_cc\globalnorm\15000_minalerts\val"
train_nofilter = r"E:\Data\Sentinel2_data\30pc_cc\Tiles_512_30pc_cc\no_filter\train"
val_nofilter = r"E:\Data\Sentinel2_data\30pc_cc\Tiles_512_30pc_cc\no_filter\val"
tile_size = 512

if __name__ == '__main__':
    model_funcs = Loader(output_folder,  train_dir, val_dir, output_folder,tile_size)

    # for sentinel2_file in os.listdir(combined_radd_sen2_stack_path):
    #     if sentinel2_file.endswith('.tif'):
    #         sentinel2_file_path = os.path.join(stack_path_list, sentinel2_file)
    #         model_funcs.write_hls_rasterio_stack()

    # checkpoint_dir = r'E:\PycharmProjects\hls-foundation-os\Prithvi100m'
    # model_funcs.plot_training_progress(checkpoint_dir)


    for dirs in [train_nofilter,val_nofilter]:#[train_globnorm_15000,val_globnorm_15000]: #[train_globnorm_12500,val_globnorm_12500]:
        input_file = dirs
        output_file = dirs


        #######
        ## Step 14: Filter by AGB land classification
        #######

        valid_classes = [2, 3, 4, 5]  # Intact Montane Forest, Secondary and Degraded Forest, Peat Swamp Forest, Mangrove Forest
        nodata_value = -9999
        model_funcs.filter_stacks_and_radd_by_AGB(input_file, output_file) #,valid_classes, nodata_value)#val_narrow_dir_test)

        #######
        ## Step 15: Global Normalisation
        #######
        #

        global_min, global_max = model_funcs.compute_global_min_max(input_file)
        model_funcs.normalize_images_global(input_file,output_file, global_min, global_max)
        new_global_means, new_global_stds = model_funcs.compute_global_mean_std(input_file)
        print(f"min: {global_min}, new means: {new_global_means}")
        print(f"max: {global_max}, new stds: {new_global_stds}")



        #######
        ## Step 16: Filter images based on minimal labels requirement
        #######
        ### choose stack to filter direction by
        ###
        suffix = "_radd_labelled_agb.tif" #"radd_modified_radd_agb.tif"

        alert_stacks = model_funcs.filter_stacks(input_file,suffix, 1,100)
        distribution = model_funcs.calculate_alert_distribution(alert_stacks,20)
        print(distribution)



    ######
    ## examples and utilites
    #####

    #model_funcs.normalize_single_file_rasterio(r"E:\Data\Sentinel2_data\30pc_cc\Tiles_512_30pc_cc\training\corrected_HLS.S30.T49MFU.2022083T023551.v2.0.Fmask_3072_1024_sentinel.tif")


    ########
    ## continuously plot bands
    ########
    # pairs = model_funcs.find_pairs(train_dir)
    #
    # for sen_file, radd_file in pairs:
    #     sen_path = os.path.join(train_dir, sen_file)
    #     radd_path = os.path.join(train_dir, radd_file)
    #     model_funcs.plot_bands(sen_path, radd_path)


    #######
    ## plot model variables
    #######

    #model_funcs.plot_metrics_from_log(r"E:\PycharmProjects\hls-foundation-os\Prithvi100m\20240115_183444.log")

    # for folder in [train_dir,val_dir]:
    #     for file in os.listdir(folder):
    #         input_filepath = os.path.join(folder, file)
    #         model_funcs.normalize_single_file_rasterio(input_filepath)




    #####
    ## count number
    #####
