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
## gdal_translate -a_nodata 0 -co "COMPRESS=LZW" /path/to/resampled_radd_alerts.tif /path/to/resampled_radd_alerts_int16_compressed.tif
##################
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
from src.hls_stacks_prep import prep as HLSstacks
# from utils import [additional relevant utility functions or classes if any]
if __name__ == '__main__':
    """Main execution block for HLS data preprocessing"""
    # try:
    #     # Set variables
    #     base_path = '/home/colm-the-conjurer/VSCode/workspace/Borneo_Forest_Disturbance_Dataset/bin/data_preprocessing_hls/data'
    # except Exception as e:
    #     print(f"Error initializing paths: {e}")
    #     raise
    
    # Sensor-specific paths


    # Band configurations
    s30_bands = ['B02', 'B03', 'B04', 'B08', 'B11', 'B12']  # Sentinel-2 bands
    l30_bands = ['B02', 'B03', 'B04', 'B05', 'B06', 'B07']  # Landsat bands


    # shp = gpd.read_file(os.path.join(base_path, 'shapefile.shp'))  # Optional geospatial boundary
    base_path = '/home/colm-the-conjurer/VSCode/workspace/Borneo_Forest_Disturbance_Dataset/bin/data_preprocessing_hls/data'
    sensors = [
        {'type': 'S30', 'path': base_path, 'bands': s30_bands},
        {'type': 'L30', 'path': base_path, 'bands': l30_bands}]
    stack_path_list = os.path.join(base_path, 'hls/stacks')
    land_cover_path = os.path.join(base_path, 'land_cover')
    radd_alert_path = os.path.join(base_path, 'radd_alerts')
    cropped_land_cover_path = os.path.join(base_path, 'cropped_land_cover')
    cropped_radd_alert_path = os.path.join(radd_alert_path, 'cropped_radd_alerts')
    merged_radd_alerts = os.path.join(radd_alert_path, 'merged_radd_alerts_qgis_int16_compressed.tif')
    # combined_radd_sen2_stack_path = os.path.join(base_path, 'stacks_radd')
    fmaskwarped_folder = os.path.join(base_path, 'fmaskwarped')
    #fmask_applied_folder = os.path.join(base_path, 'stacks_radd_fmask_corrected')
    fmask_stack_folder = os.path.join(base_path, 'stacks_agb_radd_forest_fmask')
    hansen_folder = os.path.join(base_path, 'hansen_treecover')
    agb_stack_folder = os.path.join(base_path, 'stacks_agb')
    sen2_agb_radd_stack_path = os.path.join(base_path, 'stacks_agb_radd')
    agb_class_file = os.path.join(land_cover_path, 'Kalimantan_land_cover.tif')
    forest_stacks_folder = os.path.join(base_path, 'stacks_agb_radd_forest')
    # Initialize HLSstacks objects for both sensors
    hls_processors = []
    for sensor in sensors:
        hls_data = HLSstacks(
            sensor['path'], 
            stack_path_list, 
            sensor['bands'], 
            radd_alert_path, 
            land_cover_path,
            sensor_type=sensor['type']
        )
        hls_processors.append(hls_data)

    directories = [
        stack_path_list,
        land_cover_path,
        radd_alert_path,
        cropped_land_cover_path,
        cropped_radd_alert_path,
        fmaskwarped_folder,
        fmask_stack_folder,
        hansen_folder,
        agb_stack_folder,
        sen2_agb_radd_stack_path,
        forest_stacks_folder
    ]

    for d in directories:
        os.makedirs(d, exist_ok=True)
        print(f"Directory ensured: {d}")

    #################
    ## Step 1: Resample Radd Alerts to match sensor resolution (30m)
    #################
    # resample radd alerts to 30m (only need to do once)
    #hls_processors[0].resample_radd_alerts(merged_radd_alerts)




    #################
    ## Step 2: Write HLS images to Stack (both L30 and S30)
    #################
    # for processor in hls_processors:
    #     # Process and stack imagery for each sensor
    #     processor.write_hls_rasterio_stack()


    ##########
    # Step 3: Crop radd alerts to HLS stacks (both L30 and S30)
    #########
    # for hls_file in os.listdir(stack_path_list):
    #     if hls_file.endswith('_stack.tif'):
    #         hls_file_path = os.path.join(stack_path_list, hls_file)
    #
    #         # Determine which processor to use based on sensor type in filename
    #         sensor_type = 'S30' if 'S30' in hls_file else 'L30'
    #         processor = next(p for p in hls_processors if p.sensor_type == sensor_type)
    #
    #         processor.crop_single_stack(
    #             hls_file_path,
    #             os.path.join(radd_alert_path, 'radd_alerts_borneo_v2025-03-30.tif'),  #'resampled_merged_radd_alerts_qgis_int16_compressed_30m.tif'),
    #             cropped_radd_alert_path
    #         )



    ###########
    ## IGNORING THIS STEP FOR NOW.
    ## Step 4: Crop AGB Land Cover to Sen2 stacks
    ###########
    ## Have the data already processed, but doesnt quite azs is for land_cover
    # for sentinel2_file in os.listdir(stack_path_list):
    #     if sentinel2_file.endswith('.tif'):
    #         sentinel2_file_path = os.path.join(stack_path_list, sentinel2_file)
    #
    #         # Call crop_images_to_stacks for each Sentinel-2 file
    #         hls_data.crop_single_stack(sentinel2_file_path,
    #                                    os.path.join(land_cover_path, 'Kalimantan_land_cover.tif'), cropped_land_cover_path)


    ##########
    ## Step 5: add AGB LULC to Sen2 stacks
    ##########
    #hls_data.merge_with_agb(cropped_land_cover_path,agb_stack_folder)


    ##########
    ## Step 6: GDALwarp and add RADD Alert labels to Sen2 stacks
    ##########

    for sentinel2_file in os.listdir(agb_stack_folder):
        if sentinel2_file.endswith('.tif') and not sentinel2_file.endswith("reordered.tif"):
            sentinel2_file_path = os.path.join(agb_stack_folder, sentinel2_file)
            tile, date = sentinel2_file.split('_')[0].split(".")

            # Paths for the reordered stack and the final output
            reordered_file = os.path.join(agb_stack_folder, f"{date}_{tile}_stack_reordered.tif")
            output_file = os.path.join(sen2_agb_radd_stack_path, f"{date}_{tile}_agb_radd_stack.tif")

            # Skip processing if the output file already exists
            if os.path.exists(output_file):
                print(f"Output file {output_file} already exists. Skipping...")
                continue

            # Reorder bands and add a blank band, skip if reordered file already exists
            if not os.path.exists(reordered_file):
                hls_data.reorder_and_add_blank_band(sentinel2_file_path, reordered_file)

            # Corresponding RADD alerts file path
            radd_file = os.path.join(cropped_radd_alert_path, f"{date}_{tile}_resampled_merged_radd_alerts_qgis_int16_compressed_30m.tif")

            # Check if the reordered file and RADD file exist
            if os.path.exists(reordered_file) and os.path.exists(radd_file):
                # Warp the RADD alerts onto the first band of the reordered stack
                hls_data.warp_rasters([reordered_file, radd_file], output_file)
                print(f"Warped and merged raster saved to {output_file}")
                os.remove(reordered_file)
                print(f"removed redundant reordered file {reordered_file}")
            else:
                print(f"already exists: {output_file}")



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
