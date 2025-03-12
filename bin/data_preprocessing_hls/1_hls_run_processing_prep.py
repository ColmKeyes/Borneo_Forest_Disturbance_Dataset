# -*- coding: utf-8 -*-
"""
This script provides analysis and preprocessing of Sentinel-2 HLS imagery data.
"""
"""
@Time    : 07/12/2023 07:58
@Author  : Colm Keyes
@Email   : keyesco@tcd.ie
@File    : HLS-Data-Preprocessing-Analysis
"""


import os
# import geopandas as gpd
import warnings
import rasterio
warnings.simplefilter(action='ignore', category=FutureWarning)
import pandas as pd
import numpy as np
##################
## compress images
##################
## gdal_translate -a_nodata 0 -co "COMPRESS=LZW" resampled_radd_alerts.tif resampled_radd_alerts_int16_compressed.tif
##################
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
from src.hls_stacks_prep import prep as HLSstacks
# from utils import [additional relevant utility functions or classes if any]
if __name__ == '__main__':


    # Set variables
    sentinel2_path = r'E:\Data\Sentinel2_data\30pc_cc\Borneo_June2021_Dec_2023_30pc_cc'
    stack_path_list = r'E:\Data\Sentinel2_data\30pc_cc\Borneo_June2021_Dec_2023_30pc_cc_stacks'
    bands = ['B02', 'B03', 'B04', 'B08', 'B11', 'B12']  # Sentinel-2 bands to include
    # shp = gpd.read_file('[Path to optional shapefile]')  # Optional geospatial boundary
    land_cover_path = r"E:\Data\CMS_AGB_Landcover_Indonesia_1645\CMS_AGB_Landcover_Indonesia_1645\data\land_cover"
    radd_alert_path = r"E:\Data\Radd_Alerts_Borneo"
    cropped_land_cover_path = r"E:\Data\Sentinel2_data\30pc_cc\Land_Cover_Borneo_Cropped_30pc_cc"
    cropped_radd_alert_path = r"E:\Data\Sentinel2_data\30pc_cc\Radd_Alerts_Borneo_Cropped_30pc_cc"
    merged_radd_alerts = f"{radd_alert_path}\\merged_radd_alerts_qgis_int16_compressed.tif"
    # combined_radd_sen2_stack_path = r"E:\Data\Sentinel2_data\30pc_cc\Borneo_June2021_Dec_2023_30pc_cc_stacks_radd"
    fmaskwarped_folder = r'E:\Data\Sentinel2_data\30pc_cc\fmaskwarped'
    #fmask_applied_folder = r"E:\Data\Sentinel2_data\30pc_cc\Borneo_June2021_Dec_2023_30pc_cc_stacks_radd_fmask_corrected"
    fmask_stack_folder = r"E:\Data\Sentinel2_data\30pc_cc\Borneo_June2021_Dec_2023_30pc_cc_stacks_agb_radd_forest_fmask"
    hansen_folder = "E:\Data\Hansen_treecover_lossyear"
    agb_stack_folder = r"E:\Data\Sentinel2_data\30pc_cc\Borneo_June2021_Dec_2023_30pc_cc_stacks_agb"
    sen2_agb_radd_stack_path = r"E:\Data\Sentinel2_data\30pc_cc\Borneo_June2021_Dec_2023_30pc_cc_stacks_agb_radd"
    agb_class_file = "E:\Data\CMS_AGB_Landcover_Indonesia_1645\CMS_AGB_Landcover_Indonesia_1645\data\land_cover\Kalimantan_land_cover.tif"
    forest_stacks_folder = r"E:\Data\Sentinel2_data\30pc_cc\Borneo_June2021_Dec_2023_30pc_cc_stacks_agb_radd_forest"
    # Initialize HLSstacks object
    hls_data = HLSstacks(sentinel2_path, stack_path_list, bands, radd_alert_path, land_cover_path)#, shp)


    #################
    ## Step 1: Resample Radd Alerts to Sen2 res
    #################
    # resample radd alerts to 30m
    #hls_data.resample_radd_alerts(merged_radd_alerts)




    #################
    ## Step 2: Write Sen2 images to Stack
    #################
    # Process and stack Sentinel-2 imagery
    # hls_data.write_hls_rasterio_stack()


    ##########
    # Step 3: Crop radd alerts to Sen2 stacks.
    #########
    for sentinel2_file in os.listdir(stack_path_list):
        if sentinel2_file.endswith('.tif'):
            sentinel2_file_path = os.path.join(stack_path_list, sentinel2_file)
    #
    #         # Call crop_images_to_stacks for each Sentinel-2 file
            hls_data.crop_single_stack(sentinel2_file_path,
                                       r"E:\Data\Radd_Alerts_Borneo\resampled_merged_radd_alerts_qgis_int16_compressed_30m.tif", cropped_radd_alert_path)



    ###########
    ## Step 4: Crop AGB Land Cover to Sen2 stacks
    ###########
    ## Have the data already processed, but doesnt quite azs is for land_cover
    # for sentinel2_file in os.listdir(stack_path_list):
    #     if sentinel2_file.endswith('.tif'):
    #         sentinel2_file_path = os.path.join(stack_path_list, sentinel2_file)
    #
    #         # Call crop_images_to_stacks for each Sentinel-2 file
    #         hls_data.crop_single_stack(sentinel2_file_path,
    #                                    os.path.join(land_cover_path, "Kalimantan_land_cover.tif"), cropped_land_cover_path)


    ##########
    ## Step 5: add AGB LULC to Sen2 stacks
    ##########
    #hls_data.merge_with_agb(cropped_land_cover_path,agb_stack_folder)


    ##########
    ## Step 6: GDALwarp and add RADD Alert labels to Sen2 stacks
    ##########

    # for sentinel2_file in os.listdir(agb_stack_folder):
    #     if sentinel2_file.endswith('.tif') and not sentinel2_file.endswith("reordered.tif"):
    #         sentinel2_file_path = os.path.join(agb_stack_folder, sentinel2_file)
    #         tile, date = sentinel2_file.split('_')[0].split(".")
    #
    #         # Paths for the reordered stack and the final output
    #         reordered_file = os.path.join(agb_stack_folder, f"{date}_{tile}_stack_reordered.tif")
    #         output_file = os.path.join(sen2_agb_radd_stack_path, f"{date}_{tile}_agb_radd_stack.tif")
    #
    #         # Skip processing if the output file already exists
    #         if os.path.exists(output_file):
    #             print(f"Output file {output_file} already exists. Skipping...")
    #             continue
    #
    #         # Reorder bands and add a blank band, skip if reordered file already exists
    #         if not os.path.exists(reordered_file):
    #             hls_data.reorder_and_add_blank_band(sentinel2_file_path, reordered_file)
    #
    #         # Corresponding RADD alerts file path
    #         radd_file = os.path.join(cropped_radd_alert_path, f"{date}_{tile}_resampled_merged_radd_alerts_qgis_int16_compressed_30m.tif")
    #
    #         # Check if the reordered file and RADD file exist
    #         if os.path.exists(reordered_file) and os.path.exists(radd_file):
    #             # Warp the RADD alerts onto the first band of the reordered stack
    #             hls_data.warp_rasters([reordered_file, radd_file], output_file)
    #             print(f"Warped and merged raster saved to {output_file}")
    #             os.remove(reordered_file)
    #             print(f"removed redundant reordered file {reordered_file}")
    #         else:
    #             print(f"already exists: {output_file}")



    ##########
    ## Step 7: Mask Sen2_agb_radd stacks by Hansen Forest Loss. Remove disturbances detected prior to RADD start date (2021)
    ##########

    # hls_data.forest_loss_mask(sen2_agb_radd_stack_path,hansen_folder,forest_stacks_folder)


    ##########
    ## Step 8: Apply Fmask to sentinel-2 stacks, removing clouds and cloud shadows
    ##########

    # Process each Sentinel-2 stack file with the corresponding FMask file
    # for fmask_file in os.listdir(sentinel2_path):
    #     if fmask_file.endswith('.Fmask.tif'):
    #         date = fmask_file.split('.')[3][:7]
    #         tile = fmask_file.split('.')[2]
    #         sentinel_file = f"{date}_{tile}_agb_radd_stack.tif"
    #         sentinel_stack_path = os.path.join(forest_stacks_folder, sentinel_file)
    #         fmask_path = os.path.join(sentinel2_path, fmask_file)
    #         fmaskwarped_file = os.path.join(fmaskwarped_folder,f"{date}_{tile}_fmaskwarped.tif" )
    #         fmask_stack_file = os.path.join(fmask_stack_folder, sentinel_file.replace("_stack.tif", "_fmask_stack.tif"))
    #
    #         if not os.path.exists(fmaskwarped_file):
    #             hls_data.warp_rasters([fmask_path,sentinel_stack_path ], fmaskwarped_file)  #[sentinel_stack_path, fmask_path], fmaskwarped_file)
    #
    #
    #         if os.path.exists(sentinel_stack_path) and os.path.exists(fmask_path):
    #             hls_data.apply_fmask(sentinel_stack_path, fmaskwarped_file, fmask_stack_file)
    #
    #
    #








