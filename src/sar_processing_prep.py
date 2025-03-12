# -*- coding: utf-8 -*-
"""
This script provides preprocessing of Sentinel-1 SAR imagery data for combining with Sen-1 HLS stacks.
"""
"""
@Time    : 23/03/2024 02:06
@Author  : Colm Keyes
@Email   : keyesco@tcd.ie
@File    : sar_processing_prep
"""

import os
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.mask import mask
from shapely.geometry import box, mapping
from pyproj import Transformer
from rasterio.enums import Resampling
import numpy as np
from datetime import datetime, timedelta
import re
from shapely.ops import transform as shapely_transform
from rasterio.coords import BoundingBox


class SARProcessing:
    """
    A class for processing SAR imagery data in preparation for assimilation with Sentinel-2 data.
    """

    def __init__(self, sar_data_path, sen2_stack_path, base_tile_path, output_path,data_type ):
        """
        Args:
            sar_data_path (str): Path to the directory containing SAR data.
            sen2_stack_path (str): Path to the directory containing Sentinel-2 stack data.
            output_path (str): Path to the directory where the processed SAR data will be stored.
        """
        self.sar_data_path = sar_data_path
        self.sen2_stack_path = sen2_stack_path
        self.output_path = output_path
        self.base_tile_path = base_tile_path
        self.data_type = data_type
        self.vh_dir = os.path.join(base_tile_path, "28m_window", "pol_VH_backscatter_multilook_window_28")
        self.vv_dir = os.path.join(base_tile_path, "28m_window", "pol_VV_backscatter_multilook_window_28")

    def join_vv_vh_bands(self,tile_id):
        if self.data_type == 'backscatter':
            vh_subdir = "pol_VH_backscatter_multilook_window_28"
            vv_subdir = "pol_VV_backscatter_multilook_window_28"
        elif self.data_type == 'coherence':
            vh_subdir = "pol_VH_coherence_window_28"
            vv_subdir = "pol_VV_coherence_window_28"
        else:
            raise ValueError("Invalid data type specified. Choose 'backscatter' or 'coherence'.")

        vh_dir = os.path.join(self.base_tile_path, "28m_window", vh_subdir)
        vv_dir = os.path.join(self.base_tile_path, "28m_window", vv_subdir)

        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

        for vh_file in os.listdir(vh_dir):
            if vh_file.endswith('.tif'):
                # Extract the identifier and additional details from the VH filename
                parts = vh_file.split('_')
                identifier = '_'.join(parts[:7])  # Adjusted to: S1A_IW_SLC__1SDV_20230907
                additional_details = '_'.join(parts[7:]).replace('.tif', '')  # Now: pol_VH_backscatter_multilook_window_28_IW2_burst_7_9

                vv_file = vh_file.replace('VH', 'VV')
                vv_file_path = os.path.join(vv_dir, vv_file)

                if os.path.exists(vv_file_path):
                    with rasterio.open(os.path.join(vh_dir, vh_file)) as vh_src, \
                            rasterio.open(vv_file_path) as vv_src:

                        assert vh_src.meta == vv_src.meta, "Metadata mismatch between VH and VV files"

                        vv_data = vv_src.read(1)
                        vh_data = vh_src.read(1)

                        profile = vh_src.meta
                        profile.update(count=2)

                        # Construct the output filename with the additional details
                        output_filename = f"{identifier}_VV_{additional_details}_{tile_id}.tif"
                        output_path = os.path.join(self.output_path, output_filename)

                        if os.path.exists(output_path):
                            print(f"File {output_filename} already exists. Skipping...")
                            continue

                        with rasterio.open(output_path, 'w', **profile) as dst:
                            dst.write(vv_data, 1)
                            dst.write(vh_data, 2)

                        print(f"Combined VV-VH {self.data_type} file saved to {output_filename}")
                else:
                    print(f"No corresponding VV file found for {vh_file}")

    def find_closest_sar_file(self, sen2_file, sar_files, tile_id):
        # Adjust the regex based on data_type
        if self.data_type == 'coherence':
            pattern = re.compile(r'coherence_window_28_IW\d_burst_\d_\d_T\d{2}[A-Z]{3}\.tif$')
        elif self.data_type == 'backscatter':
            pattern = re.compile(r'backscatter_multilook_window_28_IW\d_burst_\d_\d_T\d{2}[A-Z]{3}\.tif$')

        # Extract the date from the Sentinel-2 filename
        sen2_date_str = sen2_file.split('_')[0]
        year = int(sen2_date_str[:4])
        day_of_year = int(sen2_date_str[4:])
        sen2_date = datetime(year, 1, 1) + timedelta(days=day_of_year - 1)

        potential_matches = []
        for sar_file in sar_files:
            if pattern.search(sar_file) and tile_id in sar_file:
                # Extract and parse the date from the SAR filename
                sar_date_str = sar_file.split('_')[-13]  # adjust based on your filename format
                sar_date = datetime.strptime(sar_date_str, '%Y%m%d')

                if sar_date <= sen2_date:
                    date_diff = (sen2_date - sar_date).days
                    potential_matches.append((sar_file, date_diff))

        # Sort potential matches by date difference
        potential_matches.sort(key=lambda x: x[1])
        return [match[0] for match in potential_matches]  # Return a list of SAR files sorted by closeness

        # Sort potential matches by date difference
        potential_matches.sort(key=lambda x: x[1])
        return [match[0] for match in potential_matches]  # Return a list of SAR files sorted by closeness

    def find_corresponding_files(self, tile_id):
        sen2_files = [os.path.join(self.sen2_stack_path, filename) for filename in os.listdir(self.sen2_stack_path)
                      if tile_id in filename]

        sar_files = [os.path.join(self.output_path, filename) for filename in os.listdir(self.output_path)
                     if tile_id in self.sar_data_path and filename.endswith('.tif')]

        matched_files = []
        for sen2_file in sen2_files:
            closest_sar_files = self.find_closest_sar_file(os.path.basename(sen2_file), sar_files,tile_id)
            for sar_file in closest_sar_files:
                with rasterio.open(sen2_file) as sen2, rasterio.open(sar_file) as sar:
                    # Transform SAR data from EPSG:4326 to EPSG:32650 to match Sentinel-2's CRS
                    transformer_to_sen2_crs = Transformer.from_crs(sar.crs, sen2.crs, always_xy=True)
                    sar_bounds_transformed = shapely_transform(transformer_to_sen2_crs.transform, box(*sar.bounds))
                    sen2_bounds = box(*sen2.bounds)

                    if sen2_bounds.intersects(sar_bounds_transformed):
                        matched_files.append((sen2_file, sar_file))
                        break  # Stop looking for matches once an overlap is found
                    else:
                        print(f"No geographic overlap for {os.path.basename(sen2_file)} in provided SAR files.")

        return matched_files

    
    def resample_sar_to_30m(self, sar_file_path, sen2_file_path, output_file_path):
        with rasterio.open(sar_file_path) as sar_src, rasterio.open(sen2_file_path) as sen2_src:
            # Transform source CRS to Sentinel-2 CRS
            transform, width, height = calculate_default_transform(
                sar_src.crs, sen2_src.crs, sar_src.width, sar_src.height, *sar_src.bounds, resolution=(30.0, 30.0))

            # Update metadata for the destination dataset
            out_meta = sar_src.meta.copy()
            out_meta.update({
                'crs': sen2_src.crs,
                'transform': transform,
                'width': width,
                'height': height,
                'nodata': sar_src.nodata  # Preserve the original NoData value
            })

            # Perform the reprojection and resampling
            with rasterio.open(output_file_path, 'w', **out_meta) as dst:
                for i in range(1, sar_src.count + 1):
                    reproject(
                        source=rasterio.band(sar_src, i),
                        destination=rasterio.band(dst, i),
                        src_transform=sar_src.transform,
                        src_crs=sar_src.crs,
                        dst_transform=transform,
                        dst_crs=sen2_src.crs,
                        resampling=Resampling.nearest)

        # os.remove(sar_file_path)
            return output_file_path



    def replace_sen2_bands_with_sar(self, sen2_file_path, cropped_sar_path):
        """
        Replaces the 6th and 7th bands in the Sentinel-2 stack with SAR data, only in the area covered by the SAR data.
        """

        with rasterio.open(sen2_file_path) as sen2_dataset, rasterio.open(cropped_sar_path) as sar_dataset:
            sen2_meta = sen2_dataset.meta.copy()
            assert sar_dataset.count == 2, "SAR data should have 2 bands to replace the 6th and 7th Sentinel-2 bands."
            output_file_name = os.path.basename(sen2_file_path).replace('.tif', '_sar.tif')
            output_file_path = os.path.join(self.output_path, output_file_name)

            with rasterio.open(output_file_path, 'w', **sen2_meta) as dest:
                for i in range(1, 6):
                    dest.write(sen2_dataset.read(i), i)

                # Apply scaling if necessary
                scale_factor = 1#10000  # Define the scale factor based on your data's needs

                # Read and scale the SAR data
                sar_data_1 = sar_dataset.read(1) * scale_factor
                sar_data_2 = sar_dataset.read(2) * scale_factor

                # Write the scaled SAR data to bands 6 and 7
                dest.write(sar_data_1.astype(sen2_meta['dtype']), 6)
                dest.write(sar_data_2.astype(sen2_meta['dtype']), 7)

                for i in range(8, sen2_dataset.count + 1):
                    dest.write(sen2_dataset.read(i), i)

                print(f"Replaced Sentinel-2 bands with scaled SAR data at {output_file_name}")
                return output_file_path

    def crop_sar_to_sen2(self, resampled_sar_path, sen2_file_path):
        """
        Crops the resampled SAR data to match the extent of a Sentinel-2 stack.
        """
        with rasterio.open(sen2_file_path) as sen2_dataset, rasterio.open(resampled_sar_path) as sar_dataset:
            sen2_bounds = sen2_dataset.bounds

            # Get the geometry of the Sentinel-2 bounding box
            sen2_geometry = box(*sen2_bounds)

            # Perform cropping
            sar_cropped, transform = mask(sar_dataset, [mapping(sen2_geometry)], crop=True)
            output_file_name = os.path.basename(resampled_sar_path).replace('.tif', '_cropped.tif')
            output_file_path = os.path.join(self.output_path, output_file_name)

            if os.path.exists(output_file_path):
                print(f"File {output_file_name} already exists. Skipping...")
                return output_file_path

            # Update the profile for the cropped image
            output_profile = sar_dataset.profile.copy()
            output_profile.update({
                'height': sar_cropped.shape[1],
                'width': sar_cropped.shape[2],
                'transform': transform,
                'count': sar_dataset.count
            })

            with rasterio.open(output_file_path, 'w', **output_profile) as dest:
                dest.write(sar_cropped)


            return output_file_path

    def crop_single_stack(self, sentinel_stack_path, single_image_path, output_path):

        ##############################
        ## SAR DATA VERSION
        ##############################
        with rasterio.open(sentinel_stack_path) as sentinel_stack, rasterio.open(single_image_path) as image_raster:
            sentinel_bounds = sentinel_stack.bounds
            sentinel_crs = sentinel_stack.crs
            image_bounds = image_raster.bounds
            image_crs = image_raster.crs

            # Extract the relevant parts of the file name from the sentinel_stack_path
            #tile, date = os.path.basename(sentinel_stack_path).split('_')[0].split('.')
            if self.data_type == "coherence":
                date1 = os.path.basename(sentinel_stack_path).split('_')[5]
                date2 = os.path.basename(sentinel_stack_path).split('_')[6]
                date = f"coh_{date1}_{date2}"
            elif self.data_type == "backscatter":    
                date = f"bsc_{os.path.basename(sentinel_stack_path).split('_')[5]}"
                    
            #identifier = f"{parts[0]}_{parts[1]}"

            # Assuming the base name of the single_image_path is 'resampled_radd_alerts_int16_compressed.tif'
            basename = os.path.basename(single_image_path)
            date_str = basename.split('_')[0]
            date_obj = datetime.strptime(date_str, '%Y%j')
            formatted_date = date_obj.strftime('%Y%m%d')
            suffix = basename.replace(date_str, formatted_date)

            # Combine the identifier and suffix to form the output file name
            output_file_name = f"{date}_sen2_{suffix}"#f"{date}_{tile}_{suffix}"
            output_file_path = os.path.join(output_path, output_file_name)

            if os.path.exists(output_file_path):
                print(f"File {output_file_name} already exists. Skipping cropping.")
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
            ########
            ## only valid when values are present. values 3 have been preselected in data acquisition to be 3. 
            # image_cropped.mask[0] = (image_cropped.data[0] != 3)

            # Update the profile for the cropped image
            output_profile = image_raster.profile.copy()
            output_profile.update({
                'height': image_cropped.shape[1],
                'width': image_cropped.shape[2],
                'transform': transform,
                'count' : image_raster.count  #1 ##is 1 for a single band crop
            })

            with rasterio.open(output_file_path, 'w', **output_profile) as dest:
                for band in range(1, image_raster.count + 1):
                    dest.write(image_cropped[band-1], band)
                print(f"written {output_file_name}")

            return output_file_path

