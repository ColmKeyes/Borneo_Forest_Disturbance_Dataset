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
    base_path = "/home/colm-the-conjurer/VSCode/workspace/Borneo_Forest_Disturbance_Dataset/bin/data_preprocessing_hls/data"
    base_path_2 = "/media/colm-the-conjurer/Disk_2/data/hls"
    sensors = [
        {'type': 'S30', 'path': base_path_2, 'bands': s30_bands},
        {'type': 'L30', 'path': base_path_2, 'bands': l30_bands}]
    stack_path_list = os.path.join(base_path, '2.stacks')
    land_cover_path = os.path.join(base_path, 'land_cover')
    radd_alert_path = os.path.join(base_path, '3.radd_alerts')
    cropped_land_cover_path = os.path.join(base_path, 'cropped_land_cover')
    cropped_radd_alert_path = os.path.join(radd_alert_path, '3.cropped_radd_alerts')
    merged_radd_alerts = os.path.join(radd_alert_path, 'merged_radd_alerts_qgis_int16_compressed.tif')
    combined_radd_sen2_stack_path = os.path.join(base_path, '6.stacks_radd')
    fmaskwarped_folder = os.path.join(base_path, '8.1.fmaskwarped')
    #fmask_applied_folder = os.path.join(base_path, 'stacks_radd_fmask_corrected')
    fmask_stack_folder = os.path.join(base_path, '8.2.stacks_radd_forest_fmask')
    hansen_folder = os.path.join(base_path, 'hansen_treecover')
    # agb_stack_folder = os.path.join(base_path, 'stacks_agb')
    # sen2_agb_radd_stack_path = os.path.join(base_path, 'stacks_agb_radd')
    agb_class_file = os.path.join(land_cover_path, 'Kalimantan_land_cover.tif')
    forest_stacks_folder = os.path.join(base_path, '7.stacks_radd_forest')
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
        forest_stacks_folder
    ]

    for d in directories:
        os.makedirs(d, exist_ok=True)
        print(f"Directory ensured: {d}")


    #################
    ## Step 1 (optional): Resample Radd Alerts to match sensor resolution (30m)
    #################
    # resample radd alerts to 30m (only need to do once)
    #hls_processors[0].resample_radd_alerts(merged_radd_alerts)




    #################
    ## Step 2: Write HLS images to Stack (both L30 and S30)
    #################
    # for processor in hls_processors:
    # #     # Process and stack imagery for each sensor
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
    #
    #

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
    ## Step 6: GDALwarp and add RADD Alert labels to HLS stacks (using paths from Step 3)
    ##########
    # stacks_radd_path =  combined_radd_sen2_stack_path#os.path.join(base_path, 'stacks_radd')
    # os.makedirs(stacks_radd_path, exist_ok=True)
    #
    # for hls_file in os.listdir(stack_path_list):
    #     if hls_file.endswith('_stack.tif') and not hls_file.endswith("reordered.tif"):
    #         hls_file_path = os.path.join(stack_path_list, hls_file)
    #         tile, date = hls_file.split('_')[0].split(".")
    #
    #         # Paths for the reordered stack and the final output
    #         reordered_file = os.path.join(stack_path_list, f"{date}_{tile}_stack_reordered.tif")
    #         output_file = os.path.join(stacks_radd_path, f"{date}_{tile}_radd_stack.tif")
    #
    #         # Skip processing if the output file already exists
    #         if os.path.exists(output_file):
    #             print(f"Output file {output_file} already exists. Skipping...")
    #             continue
    #
    #         # Reorder bands and add a blank band, skip if reordered file already exists
    #         if not os.path.exists(reordered_file):
    #             hls_data.reorder_and_add_blank_bands(hls_file_path, reordered_file)
    #
    #         # Corresponding RADD alerts file path
    #         radd_file = os.path.join(cropped_radd_alert_path, f"{date}_{tile}_radd_alerts_borneo_v2025-03-30.tif")
    #
    #         # Check if the reordered file and RADD file exist
    #         if os.path.exists(reordered_file) and os.path.exists(radd_file):
    #             # Warp the RADD alerts onto the first band of the reordered stack
    #             hls_data.warp_rasters([reordered_file, radd_file], output_file)
    #             print(f"Warped and merged raster saved to {output_file}")
    #             os.remove(reordered_file)
    #             print(f"removed redundant reordered file {reordered_file}")
    #         else:
    #             print(f"already exists, or file path incorrect: {output_file}")



    ##########
    ## Step 7: Mask Sen2_agb_radd stacks by Hansen Forest Loss. Remove disturbances detected prior to RADD start date (2021)
    ##########

    # hls_data.forest_loss_mask(combined_radd_sen2_stack_path,hansen_folder,forest_stacks_folder)


    ##########
    ## Step 8: Apply Fmask to sentinel-2 stacks, removing clouds and cloud shadows
    ##########

    # Process each Sentinel-2 stack file with the corresponding FMask file
    for processor in hls_processors:
        # Find all tile directories for this sensor
        sensor_tiles_path = os.path.join(base_path_2)
        for tile_dir in os.listdir(sensor_tiles_path):
            # Ignore non-tile directories (e.g., ignore the "stacks" folder)
            if not os.path.isdir(os.path.join(sensor_tiles_path, tile_dir)) or tile_dir == "stacks":
                continue

            # Build sensor path within each tile directory (e.g. .../tile_x21_y28/S30)
            sensor_path = os.path.join(sensor_tiles_path, tile_dir, processor.sensor_type)
            if not os.path.exists(sensor_path):
                continue

            for fmask_file in os.listdir(sensor_path):
                if fmask_file.endswith('.Fmask.tif'):
                    parts = fmask_file.split('.')
                    tile = parts[2]
                    date = parts[3][:7]

                    # For L30, use the naming convention: <date>_<tile>_L30_forest_masked_stack.tif.
                    # For S30, use the existing naming convention: <tile>.<date>_S30_forest_stack.tif.
                    sentinel_file = f"{date}_{tile}_forest_masked_stack.tif"


                    sentinel_stack_path = os.path.join(forest_stacks_folder, sentinel_file)

                    fmask_path = os.path.join(sensor_path, fmask_file)
                    fmaskwarped_file = os.path.join(fmaskwarped_folder, f"{tile}_{date}_fmaskwarped.tif")
                    # fmask_stack_file keeps the same naming as earlier based on the "standard" convention.
                    fmask_stack_file = os.path.join(fmask_stack_folder,
                                                    sentinel_file.replace("_stack.tif", "_fmask_stack.tif"))

                    # Check that both required files exist before processing
                    if os.path.exists(sentinel_stack_path) and os.path.exists(fmask_path) and not os.path.exists(fmask_stack_file):
                        if not os.path.exists(fmaskwarped_file):
                            processor.warp_rasters([fmask_path, sentinel_stack_path], fmaskwarped_file)
                        processor.apply_fmask(sentinel_stack_path, fmaskwarped_file, fmask_stack_file)
                    else:
                        # print(f"Missing required files for tile {tile} on date {date}:")
                        if not os.path.exists(sentinel_stack_path):
                            print(f"  Sentinel stack missing: {sentinel_stack_path}")
                        if not os.path.exists(fmask_path):
                            print(f"  Fmask file missing: {fmask_path}")
                        if os.path.exists(fmask_stack_file):
                            print(f" Fmask processed stack already exists: {fmask_stack_file}, skipping...")


    # for processor in hls_processors:
    #     # Find all tile directories for this sensor
    #     sensor_tiles_path = os.path.join(base_path, 'hls')
    #     for tile_dir in os.listdir(sensor_tiles_path):
    #         # Ignore non-tile directories (e.g., ignore the "stacks" folder)
    #         if not os.path.isdir(os.path.join(sensor_tiles_path, tile_dir)) or tile_dir == "stacks":
    #             continue
    #         # Append sensor type to sensor path so we locate the Fmask files (e.g., S30 or L30 subfolder)
    #         sensor_path = os.path.join(sensor_tiles_path, tile_dir, processor.sensor_type)
    #         if not os.path.exists(sensor_path):
    #             continue
    #         for fmask_file in os.listdir(sensor_path):
    #             if fmask_file.endswith('.Fmask.tif'):
    #                 parts = fmask_file.split('.')
    #                 tile = parts[2]
    #                 date = parts[3][:7]
    #                 sentinel_file = f"{tile}.{date}_{processor.sensor_type}_forest_stack.tif"
    #                 sentinel_stack_path = os.path.join(forest_stacks_folder, sentinel_file)
    #                 fmask_path = os.path.join(sensor_path, fmask_file)
    #                 fmaskwarped_file = os.path.join(fmaskwarped_folder, f"{tile}_{date}_fmaskwarped.tif")
    #                 fmask_stack_file = os.path.join(fmask_stack_folder,
    #                                                 sentinel_file.replace("_stack.tif", "_fmask_stack.tif"))
    #
    #                 if not os.path.exists(fmaskwarped_file):
    #                     processor.warp_rasters([fmask_path, sentinel_stack_path], fmaskwarped_file)
    #
    #                 if os.path.exists(sentinel_stack_path) and os.path.exists(fmask_path):
    #                     processor.apply_fmask(sentinel_stack_path, sensor_path, fmask_stack_file)

    # for processor in hls_processors:
    #     # Find all tile directories for this sensor
    #     sensor_tiles_path = os.path.join(base_path, 'hls')
    #     for tile_dir in os.listdir(sensor_tiles_path):
    #         if not os.path.isdir(os.path.join(sensor_tiles_path, tile_dir)): needs to ignore the stacks folder, the only other folder in the hls folder bar tiles
    #             continue
    #         sensor_path = os.path.join(sensor_tiles_path, tile_dir, processor.sensor_type)
    #         if not os.path.exists(sensor_path):
    #             continue
    #         for fmask_file in os.listdir(sensor_path): needs s30 or l30 added to sensor path to get fmasks
    #             if fmask_file.endswith('.Fmask.tif'):
    #                 parts = fmask_file.split('.')
    #                 tile = parts[2]
    #                 date = parts[3][:7]
    #                 sentinel_file = f"{tile}.{date}_{processor.sensor_type}_forest_stack.tif"
    #                 sentinel_stack_path = os.path.join(forest_stacks_folder, sentinel_file)
    #                 fmask_path = os.path.join(sensor_path, fmask_file)
    #                 fmaskwarped_file = os.path.join(fmaskwarped_folder, f"{tile}_{date}_fmaskwarped.tif")
    #                 fmask_stack_file = os.path.join(fmask_stack_folder, sentinel_file.replace("_stack.tif", "_fmask_stack.tif"))
    #
    #                 if not os.path.exists(fmaskwarped_file):
    #                     processor.warp_rasters([fmask_path, sentinel_stack_path], fmaskwarped_file)
    #
    #                 if os.path.exists(sentinel_stack_path) and os.path.exists(fmask_path):
    #                     processor.apply_fmask(sentinel_stack_path, sensor_path, fmask_stack_file)
