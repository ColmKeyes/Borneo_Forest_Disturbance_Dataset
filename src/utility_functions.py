

# -*- coding: utf-8 -*-
"""
Utility functions for merging tiffs and finding Sentinel-1 SLC  pairs based on file type and date.

@Time    : 2/2024
@Author  : Colm Keyes
@Email   : keyesco@tcd.ie
@File    : utility_functions.py
"""




import rasterio
import numpy as np
import os
import re
from collections import defaultdict

from rasterio.merge import merge


def find_pairs(image_files, file_type):
    pairs = defaultdict(list)
    # Adjusted regex to extract the date from the file name
    pattern = re.compile(rf"S1A_IW_SLC__1SDV_(\d{{8}}).*{file_type}.*_T\d{{2}}\w{{3}}\.tif")

    for image in image_files:
        match = pattern.search(image)
        if match:
            # Use the date as the key
            date = match.group(1)
            pairs[date].append(image)

    # Filter out any keys that don't have exactly 2 images for the same date
    return {k: v for k, v in pairs.items() if len(v) == 2}


def merge_tiles_with_nodata_precedence(tile1_path, tile2_path, output_path='merged.tif', dominant= "first"):
    """
    Merges two Sentinel-1 tiles where the second tile takes precedence only in no-data regions of the first tile.

    Parameters:
    tile1_path (str): Path to the first tile.
    tile2_path (str): Path to the second tile.
    output_path (str): Path for the output merged file.
    """
    # Open the tiles
    # Open the tiles
    with rasterio.open(tile1_path) as src1, rasterio.open(tile2_path) as src2:
        # Merge tiles with specified precedence
        datasets_to_merge = [src1, src2] if dominant == 'first' else [src2, src1]
        merged_image, out_transform = merge(datasets_to_merge, method=dominant)

        # Update the metadata
        out_meta = src1.meta.copy()
        out_meta.update({
            "driver": "GTiff",
            "height": merged_image.shape[1],
            "width": merged_image.shape[2],
            "transform": out_transform
        })

        # Write the merged file
        with rasterio.open(output_path, 'w', **out_meta) as dest:
            dest.write(merged_image)

def merge_image_pairs(directory, tile, file_type):
    image_files = [f for f in os.listdir(directory) if f.endswith('.tif') and tile in f and file_type in f]

    # Find pairs based on the file type and date
    pairs = find_pairs(image_files, file_type)

    # Merge each pair
    for date, pair in pairs.items():
        image_paths = [os.path.join(directory, filename) for filename in pair]
        output_path = os.path.join(directory, f"{date}_{tile}_{file_type}_merged.tif")
        merge_tiles_with_nodata_precedence(image_paths[0], image_paths[1], output_path)
        print(f"Merged: {output_path}")


# tile1= r"E:\Data\Sentinel2_data\30pc_cc\Borneo_June2021_Dec_2023_30pc_cc_stacks_agb_radd_sar\S1A_IW_SLC__1SDV_20231109_pol_VV_VH_backscatter_multilook_window_28_IW2_burst_4_7_T49MCV.tif"
# tile2 = r"E:\Data\Sentinel2_data\30pc_cc\Borneo_June2021_Dec_2023_30pc_cc_stacks_agb_radd_sar\S1A_IW_SLC__1SDV_20231109_pol_VV_VH_backscatter_multilook_window_28_IW1_burst_4_7_T49MCV.tif"
# # Example usage
# output_path = r"E:\Data\Sentinel2_data\30pc_cc\Borneo_June2021_Dec_2023_30pc_cc_stacks_agb_radd_sar\S1A_IW_SLC__1SDV_20231109_pol_VV_VH_backscatter_multilook_window_28_IW12_burst_4_7_T49MCV_merged.tif"
# merge_tiles_with_nodata_precedence(tile1, tile2, output_path)


# Example usage
directory = r"E:\Data\Sentinel2_data\30pc_cc\Borneo_June2021_Dec_2023_30pc_cc_stacks_agb_radd_sar"
tile = "T49MCV"
merge_image_pairs(directory, tile, "backscatter")