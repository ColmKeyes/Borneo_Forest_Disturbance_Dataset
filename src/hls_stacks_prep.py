
# -*- coding: utf-8 -*-
"""
This script provides a class and methods for preprocessing Sentinel-2 imagery data.
The main functionalities include band selection and stacking for further analysis and model input.
"""
"""
@Time    : 7/12/2023 07:49
@Author  : Colm Keyes
@Email   : keyesco@tcd.ie
@File    : preprocessing_pipeline
"""


import numpy as np
import numpy.ma as ma
import os
from matplotlib.pyplot import pause
from matplotlib.lines import Line2D
import matplotlib.animation as animation
import pandas as pd
# import rioxarray
# import xarray
import rasterio
import rasterio.plot
from rasterio.warp import calculate_default_transform ,reproject
from rasterio.windows import get_data_window, transform
from rasterio.enums import Resampling
from rasterio.mask import mask
from rasterio.windows import from_bounds
from rasterio.io import MemoryFile
from rasterio.merge import merge
from shapely.geometry import box,mapping
from shapely.ops import transform as shapely_transform
import pyproj
from pyproj import Transformer
from functools import partial
# from geocube.api.core import make_geocube
from datetime import datetime
import matplotlib.pyplot as plt
# from meteostat import Daily
# from statsmodels.tsa.seasonal import seasonal_decompose
import re
import warnings
from collections import defaultdict
import json
from functools import partial
import os
import pyproj
import rasterio
from rasterio import MemoryFile
from rasterio.transform import from_bounds, Affine
from rasterio.warp import calculate_default_transform, reproject, Resampling
from shapely.geometry import box
from shapely.ops import transform as shapely_transform
from osgeo import gdal
from osgeo_utils import gdal_merge as gm
import glob


warnings.simplefilter(action='ignore', category=FutureWarning)

#plt.style.use('dark_background')


pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

class prep:
    """
    A class for processing Sentinel-2 imagery data in preperation for assimilation by the Prithvi-100m model.
    """

    def __init__(self, sentinel2_path, stack_path_list, bands, radd_alert_path, land_cover_path, shp=None, sensor_type='S30'):
        """
        Args:
            path (list): List of file paths to HLS imagery.
            stack_path_list (str): Path to directory where output raster stacks will be stored.
            bands (list): List of band names to include in the stack.
                         For S30: ['B02', 'B03', 'B04', 'B08', 'B11', 'B12']
                         For L30: ['B02', 'B03', 'B04', 'B05', 'B06', 'B07']
            shp (geopandas.GeoDataFrame, optional): GeoDataFrame containing study area polygon.
            sensor_type (str): Either 'S30' (Sentinel-2) or 'L30' (Landsat-8/9)

        Attributes:
            cube (None or xarray.DataArray): Multi-dimensional, named array for storing data.
        """

        # Initialize class variables
        self.sentinel2_path = sentinel2_path
        self.stack_path_list = stack_path_list
        self.bands = bands
        self.shp = shp
        self.cube = None
        self.sensor_type = sensor_type

        # Band mapping between L30 and S30
        self.band_mapping = {
            'L30': {'B02': 'B02', 'B03': 'B03', 'B04': 'B04', 
                   'B05': 'B8A', 'B06': 'B11', 'B07': 'B12'},
            'S30': {'B02': 'B02', 'B03': 'B03', 'B04': 'B04',
                   'B8A': 'B8A', 'B11': 'B11', 'B12': 'B12'}
        }

        self.radd_alert_path = radd_alert_path
        self.land_cover_path = land_cover_path

        # Initialize a list to store titles of processed files (optional)
        self.titles = []

    """"""""
    # Core Functionalities
    """"""""

    def resample_radd_alerts(self, merged_radd_alerts):
        """
        Resamples 'merged_radd_alerts.tif' to match the resolution of a Sentinel-2 image.
        """

        # Use the first Sentinel-2 image to determine the target CRS
        sentinel_files = [f for f in os.listdir(self.sentinel2_path) if f.endswith('.tif')]
        if not sentinel_files:
            raise ValueError("No Sentinel-2 images found in the specified path.")

        sentinel_path = os.path.join(self.sentinel2_path, sentinel_files[0])
        with rasterio.open(sentinel_path) as sentinel_dataset:
            sentinel_crs = sentinel_dataset.crs

        # Open the merged RADD alerts image
        with rasterio.open(merged_radd_alerts) as merged_radd_dataset:
            # Manually set the desired output resolution (30m)
            desired_resolution = (30.0, 30.0)

            # Calculate the new transform
            transform, width, height = calculate_default_transform(
                merged_radd_dataset.crs, sentinel_crs,
                merged_radd_dataset.width, merged_radd_dataset.height,
                *merged_radd_dataset.bounds,
                resolution=desired_resolution
            )

            # Define metadata for the resampled dataset
            out_meta = merged_radd_dataset.meta.copy()
            out_meta.update({
                "driver": "GTiff",
                "height": height,
                "width": width,
                "transform": transform,
                "crs": sentinel_crs,
                "compress": "LZW",
                "dtype": 'int16'
            })

            # Perform the resampling
            resampled_radd_path = os.path.join(self.radd_alert_path, 'resampled_merged_radd_alerts_qgis_int16_compressed_30m.tif')
            with rasterio.open(resampled_radd_path, 'w', **out_meta) as dest:
                for i in range(1, merged_radd_dataset.count + 1):
                    reproject(
                        source=rasterio.band(merged_radd_dataset, i),
                        destination=rasterio.band(dest, i),
                        src_transform=merged_radd_dataset.transform,
                        src_crs=merged_radd_dataset.crs,
                        dst_transform=transform,
                        dst_crs=sentinel_crs,
                        resampling=Resampling.nearest
                    )

        return resampled_radd_path

    def crop_single_stack(self, sentinel_stack_path, single_image_path, output_path):

        ##############################
        ## AGB LAND CLASSIFICATION VERSION
        ##############################
        with rasterio.open(sentinel_stack_path) as sentinel_stack, rasterio.open(single_image_path) as image_raster:
            sentinel_bounds = sentinel_stack.bounds
            sentinel_crs = sentinel_stack.crs
            image_bounds = image_raster.bounds
            image_crs = image_raster.crs

            # Extract the relevant parts of the file name from the sentinel_stack_path
            tile, date = os.path.basename(sentinel_stack_path).split('_')[0].split('.')
            # date = os.path.basename(sentinel_stack_path).split('_')[0].split('.')

            #identifier = f"{parts[0]}_{parts[1]}"

            # Assuming the base name of the single_image_path is 'resampled_radd_alerts_int16_compressed.tif'
            suffix = os.path.basename(single_image_path)

            # Combine the identifier and suffix to form the output file name
            output_file_name = f"{date}_{tile}_{suffix}"
            output_file_path = os.path.join(output_path, output_file_name)

            if os.path.exists(output_file_path):
                print(f"File {output_file_path} already exists. Skipping cropping.")
                return output_file_path # Skip the rest of the function


            # Create transformers to WGS 84 (EPSG:4326)
            transformer_to_wgs84_sentinel = Transformer.from_crs(sentinel_crs, 'EPSG:4326', always_xy=True)
            transformer_to_wgs84_image = Transformer.from_crs(image_crs, 'EPSG:4326', always_xy=True)

            # Define the functions for coordinate transformation
            def transform_to_wgs84_sentinel(x, y):
                return transformer_to_wgs84_sentinel.transform(x, y)

            def transform_to_wgs84_image(x, y):
                return transformer_to_wgs84_image.transform(x, y)

            # Transform sentinel bounds and image bounds to WGS 84
            sentinel_box_wgs84 = shapely_transform(transform_to_wgs84_sentinel, box(*sentinel_bounds))
            image_box_wgs84 = shapely_transform(transform_to_wgs84_image, box(image_bounds.left, image_bounds.bottom, image_bounds.right, image_bounds.top))

            if not sentinel_box_wgs84.intersects(image_box_wgs84):
                print("doesn't intersect in WGS 84")
                return  # Optionally skip further processing

            transformer_to_image_crs = Transformer.from_crs('EPSG:4326', image_crs, always_xy=True)

            def transform_to_image_crs(x, y):
                return transformer_to_image_crs.transform(x, y)

            # Transform sentinel_box_wgs84 back to the image raster's CRS
            sentinel_box_image_crs = shapely_transform(transform_to_image_crs, sentinel_box_wgs84)

            # Now sentinel_box_image_crs is in the same CRS as the image raster
            # Proceed with masking using sentinel_box_image_crs
            image_cropped, transform = mask(image_raster, [sentinel_box_image_crs], crop=True, filled=False, pad=False, nodata=0)

            # Mask or clip the image raster to the area of the Sentinel-2 stack, specifying the nodata value and transform
            #mage_cropped, transform = mask(image_raster, [sentinel_box_wgs84], crop=True, filled=False, pad=False, nodata=0)

            ########
            ## Radd alerts contain values 2 and 3. 2 for uncertain events, 3 for hihgly certain events. we choose only certain events.
            ## We will see the difference in values between 2 and 3 only in radd alerts this time.
            ########
            # image_cropped.mask[0] = (image_cropped.data[0] != 3)

            # Update the profile for the cropped image
            output_profile = image_raster.profile.copy()
            output_profile.update({
                'height': image_cropped.shape[1],
                'width': image_cropped.shape[2],
                'transform': transform,
                'count' : image_cropped.shape[0]  #1 ##is 1 for a single band crop
            })




            with rasterio.open(output_file_path, 'w', **output_profile) as dest:
                dest.write(image_cropped[0], 1)
                dest.write(image_cropped[1], 2)
                print(f"written {output_file_path}")
            return output_file_path

    def write_hls_rasterio_stack(self):
        """
        Write folder of HLS GeoTIFFs (either L30 or S30) to a GeoTIFF stack file.
        """
        # Create a dictionary to hold file paths for each tile-date combination
        tile_date_files = {}


        # Get all tile folders (e.g. tile_x0_y0, tile_x0_y1, etc.)
        if not os.path.exists(self.sentinel2_path):
            raise FileNotFoundError(f"Path {self.sentinel2_path} does not exist")
            
        tile_folders = [f for f in os.listdir(self.sentinel2_path) if f.startswith('tile_')]
        
        for tile_folder in tile_folders:
            tile_path = os.path.join(self.sentinel2_path, tile_folder)

            # if self.sensor_type == "S30":
            #     tile_path = os.path.join(tile_path, 'S30')
            # elif self.sensor_type == "L30":
            #     tile_path = os.path.join(tile_path, 'L30')

            # Look for sensor-specific folder within each tile
            sensor_path = os.path.join(tile_path, self.sensor_type)
            print(f"Assessing {sensor_path}...")
            if not os.path.exists(sensor_path):
                print(f"No {self.sensor_type} data found in {tile_path}")
                continue
                
            # Ensure the sensor path exists and contains data
            if not os.listdir(sensor_path):
                print(f"Empty {self.sensor_type} folder in {tile_path}")
                continue
                
            # Collect all band files into the dictionary
            for file in os.listdir(sensor_path):
                if file.endswith('.tif'):
                    # Extract relevant parts based on sensor type
                    parts = file.split('.')
                    if self.sensor_type == 'S30':
                        # S30 format: HLS.S30.T{tile}.{date}T{time}.v2.0.B{band}.tif
                        if len(parts) >= 6 and parts[0] == 'HLS' and parts[1] == 'S30':
                            tile_date_key = f'{parts[2]}.{parts[3][:7]}'  # Tile and Date
                            band = parts[6]  # Extract band number from 'B02' etc
                    elif self.sensor_type == 'L30':
                        # L30 format: HLS.L30.T{tile}.{date}T{time}.v2.0.B{band}.tif
                        if len(parts) >= 6 and parts[0] == 'HLS' and parts[1] == 'L30':
                            tile_date_key = f'{parts[2]}.{parts[3][:7]}'  # Tile and Date
                            band = parts[6]  # Extract band number from 'B02' etc
                    else:
                        continue

                    # Only process if band is in our target bands
                    if f'{band}' in self.bands:
                        if tile_date_key not in tile_date_files:
                            tile_date_files[tile_date_key] = {}
                        tile_date_files[tile_date_key][f'{band}'] = os.path.join(sensor_path, file)

        # Process each tile-date set of files
        for tile_date, band_files in tile_date_files.items():
            # Skip if not all bands are present
            if len(band_files) != len(self.bands):
                print(f"Skipping {tile_date} - missing bands (have {len(band_files)}, need {len(self.bands)})")
                continue

            # Sort files according to band order specified in self.bands
            files = [band_files[band] for band in self.bands]

            # Read metadata of first file
            with rasterio.open(files[0]) as src0:
                meta = src0.meta

            # Update meta to reflect the number of layers
            meta.update(count=len(files))

            stack_dir = 'bin/data_preprocessing_hls/data/hls/stacks'
            os.makedirs(stack_dir, exist_ok=True)

            # Ensure output directory exists
            os.makedirs(self.stack_path_list, exist_ok=True)
            
            # Write the stack
            stack_file_path = os.path.join(self.stack_path_list, f'{tile_date}_{self.sensor_type}_stack.tif')
            if os.path.exists(stack_file_path):
                print(
                    f"File {os.path.basename(stack_file_path)} already exists in folder {self.stack_path_list}. Skipping creation.")
            else:
                with rasterio.open(stack_file_path, 'w', **meta) as dst:
                    for id, layer in enumerate(files, start=1):
                        with rasterio.open(layer) as src1:
                            dst.write_band(id, src1.read(1))
                print(f"File {os.path.basename(stack_file_path)} created in folder {self.stack_path_list}")

    def merge_with_agb(self, agb_path, output_path):
        for sentinel_file in os.listdir(self.stack_path_list):
            if sentinel_file.endswith('_stack.tif'):
                sentinel_stack_path = os.path.join(self.stack_path_list, sentinel_file)

                # Extract components from filename (now includes sensor type)
                parts = sentinel_file.split('_')
                tile_date = parts[0]  # e.g. "T22VEQ.2021001"
                sensor = parts[1]      # "L30" or "S30"

                # Find the corresponding AGB file based on tile and date
                agb_file_name = f"{tile_date}_Kalimantan_land_cover.tif"
                agb_file_path = os.path.join(agb_path, agb_file_name)

                if not os.path.exists(agb_file_path):
                    print(f"AGB file {agb_file_path} not found for {sentinel_file}. Skipping.")
                    continue

                with rasterio.open(sentinel_stack_path) as sentinel_stack, rasterio.open(agb_file_path) as agb:
                    # Ensure AGB data is read with the same shape as the HLS stack
                    agb_data = agb.read(
                        out_shape=(1, sentinel_stack.height, sentinel_stack.width),
                        resampling=Resampling.nearest
                    )

                    # Stack AGB data as an additional band to HLS data
                    stacked_data = np.concatenate((sentinel_stack.read(), agb_data), axis=0)

                    # Update the profile for the output file
                    output_profile = sentinel_stack.profile.copy()
                    output_profile.update(count=stacked_data.shape[0])

                    # Write the stacked data to a new file with sensor type preserved
                    output_file_name = sentinel_file.replace('_stack.tif', f'_{sensor}_agb_stack.tif')
                    output_file_path = os.path.join(output_path, output_file_name)
                    with rasterio.open(output_file_path, 'w', **output_profile) as dst:
                        dst.write(stacked_data)

    def forest_loss_mask(self, sentinel_stacks, forest_loss_path, output_path, reference_year=2021):
        # Check if forest loss directory exists and has files
        # if not os.path.exists(forest_loss_path) or not os.listdir(forest_loss_path):
        #     print(f"No forest loss files found in {forest_loss_path}. Skipping forest loss masking.")
        #     return

        for sentinel_file in os.listdir(sentinel_stacks):
            output_file_name = sentinel_file.replace('_radd_stack.tif', '_forest_masked_stack.tif')
            output_file_path = os.path.join(output_path, output_file_name)
            if os.path.exists(output_file_path):
                print(f"{output_file_name} already exists, skipping.")
                continue
            if sentinel_file.endswith('_radd_stack.tif'):
                sentinel_stack_path = os.path.join(sentinel_stacks, sentinel_file)

                with rasterio.open(sentinel_stack_path) as sentinel_stack:
                    sentinel_data = sentinel_stack.read()
                    sentinel_crs = sentinel_stack.crs
                    output_profile = sentinel_stack.profile.copy()

                    # Initialize mask tracking
                    mask_applied = False

                    for forest_loss_file in os.listdir(forest_loss_path):
                        if forest_loss_file.endswith(".tif") and 'lossyear' in forest_loss_file:
                            forest_loss_file_path = os.path.join(forest_loss_path, forest_loss_file)
                            with rasterio.open(forest_loss_file_path) as forest_loss:
                                forest_loss_data = np.zeros((1, sentinel_stack.height, sentinel_stack.width), dtype=rasterio.float32)
                                reproject(
                                    source=rasterio.band(forest_loss, 1),
                                    destination=forest_loss_data[0],
                                    src_transform=forest_loss.transform,
                                    src_crs=forest_loss.crs,
                                    dst_transform=sentinel_stack.transform,
                                    dst_crs=sentinel_crs,
                                    resampling=Resampling.nearest)

                                # Apply forest loss mask
                                current_year = reference_year - 2000
                                mask_condition = (forest_loss_data[0] > 0) & (forest_loss_data[0] < current_year)
                                sentinel_data[:, mask_condition] = sentinel_stack.nodata
                                mask_applied = True

                    if mask_applied:
                        output_profile = sentinel_stack.profile.copy()

                        with rasterio.open(output_file_path, 'w', **output_profile) as dst:
                            dst.write(sentinel_data)
                        print(f"Forest loss mask applied and saved to {output_file_path}")
                    else:
                        print(f"No valid forest loss files found for {sentinel_file}")

    """"""""
    # Utility Functionalities
    """"""""
    def clip_to_extent(self, src_file, target_file, output_file):
        """
        Clips src_file to the extent of target_file.

        :param src_file: File path of the source image to be clipped.
        :param target_file: File path of the target image for the clipping extent.
        :param output_file: File path for the output clipped image.
        """
        # Open the target image and get its bounding box
        with rasterio.open(target_file) as target_src:
            target_bounds = target_src.bounds

        # Create a bounding box geometry
        bbox = box(*target_bounds)
        geo = [bbox.__geo_interface__]

        # Open the source image and clip it using the bounding box
        with rasterio.open(src_file) as src:
            out_image, out_transform = mask(dataset=src, shapes=geo, crop=True)
            out_meta = src.meta.copy()

            # Update the metadata to match the clipped data
            out_meta.update({"driver": "GTiff",
                             "height": out_image.shape[1],
                             "width": out_image.shape[2],
                             "transform": out_transform})

            # Write the clipped image
            with rasterio.open(output_file, "w", **out_meta) as dest:
                dest.write(out_image)

    def reorder_and_add_blank_bands(self, input_file, output_file):
        with rasterio.open(input_file) as src:
            # Update the metadata: total bands = number of HLS bands (src.count, typically 6) + 2 extra bands
            meta = src.meta.copy()
            meta.update(count=src.count + 2)

            with rasterio.open(output_file, 'w', **meta) as dst:
                # Create a blank band (using the shape of band 1) that will be used for both extra bands
                blank_band = src.read(1) * 0

                # Write the extra blank bands with proper descriptions:
                dst.write(blank_band, 1)
                dst.set_band_description(1, "alert")
                dst.write(blank_band, 2)
                dst.set_band_description(2, "date")

                # Retrieve HLS band descriptions from self.bands (which holds ['B02', 'B03', ...])
                # If the source already contains descriptions, you might choose to check them first.
                for band in range(1, src.count + 1):
                    data = src.read(band)
                    # Write each HLS band starting at band index 3 in the new output file
                    dst.write(data, band + 2)
                    # Use self.bands to set the description for each HLS band
                    description = self.bands[band - 1] if band - 1 < len(self.bands) else f"Band {band}"
                    dst.set_band_description(band + 2, description)

                # Update per-band statistics for the "date" band (band 2), not affected in qgis sadly.
                # dst.update_tags(2, STATISTICS_MINIMUM='22000', STATISTICS_MAXIMUM='25000')
                print(f"Written reordered file with extra bands to {output_file}")
        return output_file


    def apply_fmask(self, sentinel_stack_path, fmask_path, output_file):
        import numpy as np
        import rasterio

        CLOUD_BIT = 1 << 1
        CLOUD_SHADOW_BIT = 1 << 3

        # (you can drop all the glob logic here since you already have the warped Fmask)
        if not os.path.exists(fmask_path):
            print(f"Fmask not found: {fmask_path}")
            return

        with rasterio.open(sentinel_stack_path) as ss, rasterio.open(fmask_path) as fm:
            # Now ss.read() and fm.read(1) will both be (3696, 3696), so masking will work
            fmask_data = fm.read(1)
            cloud_mask = (fmask_data & CLOUD_BIT) != 0
            shadow_mask = (fmask_data & CLOUD_SHADOW_BIT) != 0
            combined_mask = cloud_mask | shadow_mask

            stack_data = ss.read()
            nodata_val = ss.nodata if ss.nodata is not None else -9999

            # Apply mask
            masked = np.where(
                combined_mask[None, :, :],
                nodata_val,
                stack_data
            ).astype(rasterio.float32)

            profile = ss.profile.copy()
            profile.update(dtype=rasterio.float32, nodata=nodata_val)

            with rasterio.open(output_file, 'w', **profile) as dst:
                dst.write(masked)

        print(f"Written masked output: {output_file}")

    # def apply_fmask(self, sentinel_stack_path, sentinel2_path, output_file):
    #     import numpy as np
    #     import rasterio
    #
    #     CLOUD_BIT = 1 << 1  # Bit 1 for clouds
    #     CLOUD_SHADOW_BIT = 1 << 3  # Bit 3 for cloud shadow
    #
    #     # Extract date and tile from stack filename.
    #     # New naming example: "2021185_T50NPH_forest_masked_stack.tif"
    #     stack_name = os.path.basename(sentinel_stack_path)
    #     parts = stack_name.split('_')
    #     if len(parts) < 2:
    #         print(f"Filename format not recognized: {stack_name}")
    #         return
    #     date = parts[0]  # e.g., "2021185"
    #     tile = parts[1]  # e.g., "T50NPH"
    #
    #     # Try both sensor options (S30 and L30) to find the Fmask file.
    #     fmask_path = None
    #     candidate = os.path.join(sentinel2_path, f'HLS.{self.sensor_type}.{tile}_{date}.v2.0.Fmask.tif')
    #     if os.path.exists(candidate):
    #         fmask_path = candidate
    #         print(f"applying fmask to {candidate}")
    #
    #
    #
    #     if not fmask_path:
    #         print(
    #             f"Fmask file not found for tile {tile} on date {date} in either sensor folder. Skipping cloud masking.")
    #         return
    #
    #     with rasterio.open(sentinel_stack_path) as sentinel_stack, rasterio.open(fmask_path) as fmask:
    #         fmask_data = fmask.read(1)
    #
    #         # Cloud and cloud shadow masks.
    #         cloud_mask = (fmask_data & CLOUD_BIT) != 0
    #         cloud_shadow_mask = (fmask_data & CLOUD_SHADOW_BIT) != 0
    #         combined_mask = cloud_mask | cloud_shadow_mask
    #
    #         # Prepare an array to hold the masked data.
    #         masked_data = np.zeros_like(sentinel_stack.read(), dtype=rasterio.float32)
    #
    #         # Use nodata value from the stack or default.
    #         nodata_value = sentinel_stack.nodata if sentinel_stack.nodata is not None else -9999
    #
    #         for band in range(sentinel_stack.count):
    #             band_data = sentinel_stack.read(band + 1)
    #             masked_data[band, :, :] = np.where(combined_mask, nodata_value, band_data)
    #
    #         # Update the profile for writing output.
    #         output_profile = sentinel_stack.profile.copy()
    #         output_profile.update(dtype=rasterio.float32, nodata=nodata_value)
    #
    #         with rasterio.open(output_file, 'w', **output_profile) as dest:
    #             dest.write(masked_data)


    # def apply_fmask(self, sentinel_stack_path, sentinel2_path, output_file):
    #     CLOUD_BIT = 1 << 1  # Bit 1 for clouds
    #     CLOUD_SHADOW_BIT = 1 << 3  # Bit 3 for cloud shadow
    #
    #     # Extract tile and sensor from stack filename (format: TXXVEQ.YYYYDDD_S30_stack.tif)
    #     stack_name = os.path.basename(sentinel_stack_path)
    #     parts = stack_name.split('_')
    #     tile_date = parts[0]  # e.g. "T22VEQ.2021001"
    #     sensor = parts[1]     # "S30" or "L30"
    #     tile = tile_date.split('.')[0]  # e.g. "T22VEQ"
    #
    #     # Construct path to Fmask file
    #     # tile_path = os.path.join(sentinel2_path, f'tile_{tile.lower()}')
    #     fmask_path = os.path.join(sentinel2_path, sensor, f'HLS.{sensor}.{tile_date}.v2.0.Fmask.tif')
    #
    #     if not os.path.exists(fmask_path):
    #         print(f"Fmask file not found at {fmask_path}. Skipping cloud masking.")
    #         return
    #
    #     with rasterio.open(sentinel_stack_path) as sentinel_stack, rasterio.open(fmask_path) as fmask:
    #         fmask_data = fmask.read(1)
    #
    #         # Cloud and cloud shadow masks
    #         cloud_mask = (fmask_data & CLOUD_BIT) != 0
    #         cloud_shadow_mask = (fmask_data & CLOUD_SHADOW_BIT) != 0
    #         combined_mask = cloud_mask | cloud_shadow_mask
    #
    #         # Prepare an array to hold the masked data
    #         masked_data = np.zeros_like(sentinel_stack.read(), dtype=rasterio.float32)
    #
    #         # Apply mask and fill with nodata value
    #         nodata_value = sentinel_stack.nodata if sentinel_stack.nodata is not None else -9999
    #
    #         for band in range(sentinel_stack.count):
    #             band_data = sentinel_stack.read(band + 1)
    #             masked_data[band, :, :] = np.where(combined_mask, nodata_value, band_data)
    #
    #         # Update the profile for writing output
    #         output_profile = sentinel_stack.profile.copy()
    #         output_profile.update(dtype=rasterio.float32, nodata=nodata_value)
    #
    #         with rasterio.open(output_file, 'w', **output_profile) as dest:
    #             dest.write(masked_data)


    """"""""
    # Data Wrangling Functionalities
    """"""""

    def warp_rasters(self, input_files, output_file, src_nodata=None, dst_nodata=None):
        # Determine band count for each input and sort descending
        band_counts = []
        for fp in input_files:
            ds = gdal.Open(fp)
            if ds is None:
                raise FileNotFoundError(f"Cannot open source file: {fp}")
            band_counts.append((ds.RasterCount, fp))
            ds = None  # close dataset

        # Sort so that the dataset with the most bands comes first
        sorted_files = [fp for _, fp in sorted(band_counts, key=lambda x: x[0], reverse=True)]

        # Now GDAL will create the destination with the band count of the first source
        warp_options = gdal.WarpOptions(
            format='GTiff',
            srcNodata=src_nodata,
            dstNodata=dst_nodata,
            multithread=True
        )

        gdal.Warp(
            destNameOrDestDS=output_file,
            srcDSOrSrcDSTab=sorted_files,
            options=warp_options
        )

    # def warp_rasters(self, input_files, output_file, src_nodata=None, dst_nodata=None):
    #     # Warp options
    #     warp_options = gdal.WarpOptions(format='GTiff',
    #                                     srcNodata=src_nodata,
    #                                     dstNodata=dst_nodata,
    #                                     multithread=True)
    #
    #     # Perform the warp
    #     gdal.Warp(destNameOrDestDS=output_file,
    #               srcDSOrSrcDSTab=input_files,
    #               options=warp_options)
