# -*- coding: utf-8 -*-
"""
This script contains functions for processing and preparing data for the Prithvi-100m model, focusing on tasks such as cropping large satellite images into smaller tiles.

@Time    : 07/12/2023 10:21
@Author  : Colm Keyes
@Email   : keyesco@tcd.ie
@File    : model_functions.py
"""

import rasterio

import numpy as np
import os
import rasterio.warp
from rasterio.warp import calculate_default_transform, reproject, Resampling
from shapely.geometry import box
from shapely.ops import transform as shapely_transform
from osgeo import gdal
import json
import re
import matplotlib.pyplot as plt
# from mmseg.datasets import CustomDataset
# from mmseg.datasets.builder import PIPELINES
import datetime as dt
from datetime import datetime

class Loader:


    def __init__(self, source_dir, train_dir, val_dir, output_folder, tile_size=512):
            """
            Args:
                path (list): List of file paths to Sentinel-2 imagery.
                stack_path_list (str): Path to directory where output raster stacks will be stored.
                bands (list): List of Sentinel-2 band names to include in the stack (e.g., ['B02', 'B03', 'B04', 'B08', 'B11', 'B12']).
                shp (geopandas.GeoDataFrame, optional): GeoDataFrame containing study area polygon.

            Attributes:
                cube (None or xarray.DataArray): Multi-dimensional, named array for storing data.
            """

            # Initialize class variables

            self.tile_size = tile_size
            self.source_dir = source_dir
            self.train_dir = train_dir
            self.val_dir = val_dir
            self.output_folder = output_folder
            self.nodata_value = -9999
            # Initialize a list to store titles of processed files (optional)


    def write_hls_rasterio_stack(self):
        """
        Write folder of Sentinel-2 GeoTIFFs, corresponding Fmask, to a GeoTIFF stack file.
        """

        for file in os.listdir(self.sentinel2_path):
            if any(band in file for band in self.bands) and file.endswith('.tif'):
                sentinel_file = os.path.join(self.sentinel2_path, file)

                # Corresponding Fmask file
                fmask_file_name = '.'.join(file.split('.')[:-2]) + '.Fmask.tif'
                fmask_file = os.path.join(self.sentinel2_path, fmask_file_name)

                if not os.path.exists(fmask_file):
                    continue  # Skip if corresponding Fmask file does not exist

                # Files to be stacked (only Sentinel-2 bands and Fmask)
                files = [sentinel_file, fmask_file]

                # Read the first image to setup profile
                with rasterio.open(sentinel_file) as src_image:
                    dst_crs = src_image.crs
                    dst_transform, dst_width, dst_height = calculate_default_transform(
                        src_image.crs, dst_crs, src_image.width, src_image.height, *src_image.bounds)

                    # Create a profile for the stack
                    dst_profile = src_image.profile.copy()
                    dst_profile.update({
                        "driver": "GTiff",
                        "count": len(files),
                        "crs": dst_crs,
                        "transform": dst_transform,
                        "width": dst_width,
                        "height": dst_height
                    })

                    # Create stack directory if it doesn't exist
                    if not os.path.exists(self.stack_path_list):
                        os.makedirs(self.stack_path_list)

                    stack_file = os.path.join(self.stack_path_list, f'{os.path.splitext(file)[0]}_stack.tif')
                    with rasterio.open(stack_file, 'w', **dst_profile) as dst:
                        for i, file_path in enumerate(files, start=1):
                            with rasterio.open(file_path) as src:
                                data = src.read(1)  # Read the first band
                                dst.write(data, i)

    import rasterio

    def count_radd_alerts(self, tif_file):
        with rasterio.open(tif_file) as src:
            # Assuming RADD alerts are in the first band
            band1 = src.read(1)
            # Count non-zero (alert) pixels
            alert_count = (band1 > 0).sum()
            return alert_count

    # Example usage
    # tif_file = 'path/to/your/radd_alerts.tif'
    # alert_count = count_radd_alerts(tif_file)
    # print(f"Number of RADD alerts: {alert_count}")

    def alter_radd_data_to_label(self, sentinel_stack_path):
        # Convert the Sentinel stack date string to a datetime object
        #sentinel_stack_date = datetime.datetime.strptime(sentinel_stack_date_str, "%Y%j").date()

        for sentinel_stack in os.listdir(sentinel_stack_path):
            # if sentinel_stack.endswith('.tif') and not sentinel_stack.endswith('_radd.tif') and not sentinel_stack.endswith("sentinel.tif"):#sentinel_stack.endswith('_radd_modified.tif') and not sentinel_stack.endswith(""):
            if sentinel_stack.endswith('_radd.tif'):    # Extract the date from the filename
                sentinel_date_str = sentinel_stack.split('_')[0]
                sentinel_date = dt.datetime.strptime(sentinel_date_str, "%Y%j").date()

                sentinel_date_yydoy = int(datetime.strftime(sentinel_date, "%y%j"))

                stack_path = os.path.join(sentinel_stack_path, sentinel_stack)

                with rasterio.open(stack_path) as src:
                    profile = src.profile
                    #src.nodata = -9999
                    radd_alerts = src.read(1)  # RADD alerts are assumed to be in the first band
                    sentinel_data = src.read()[1:]  # Sentinel-2 data spans bands 2 to 7
                    profile = src.profile

                    # Assuming your RADD alerts contain date information encoded in a specific way
                    # For demonstration, we create a mask for alerts beyond the Sentinel date (this part needs your actual implementation)
                    future_events_mask = radd_alerts > sentinel_date_yydoy

                    # tile, date = os.path.basename(sentinel_stack_path).split('_')[0].split('.')

                    nodata_value = -9999

                    # Apply the future events mask to set these alerts to nodata
                    radd_alerts[future_events_mask] = nodata_value

                    # Convert remaining values greater than 0 to 1 (RADD alerts to binary)
                    radd_alerts[radd_alerts > 0] = 1

                    # Ensure the profile is updated with the correct nodata value
                    profile.update(nodata=nodata_value)

                    # Save the modified stack with updated RADD alerts
                    output_filename = sentinel_stack.replace('.tif', '_labelled.tif')
                    output_path = os.path.join(sentinel_stack_path, output_filename)
                    with rasterio.open(output_path, 'w', **profile) as dst:
                        dst.write(radd_alerts, 1)  # Write modified RADD alerts to band 1
                        for i, band in enumerate(sentinel_data, start=2):  # Write original Sentinel-2 data back
                            dst.write(band, i)
                    src.close()
                os.remove(stack_path)
                print(f"Done applying radd future_mask, Wrote to: {output_path}, Deleted: {stack_path}")





    def filter_stacks(self, stack_directory, suffix, alert_label_value, min_alert_pixels=0):
        """
        Filters stacks based on the count of RADD alert labels.

        Args:
            alert_label_value (int): Pixel value that represents a RADD alert.
            min_alert_pixels (int): Minimum number of alert pixels required to keep a stack.
        """
        alert_counts = []
        file_names = []
        for file in os.listdir(stack_directory):
            # if file.endswith("fmask_stack.tif") or (stack_directory.endswith("Tiles_512_30pc_cc") and file.endswith(".tif") and not file.endswith("radd.tif") and not file.endswith("sentinel.tif")):
            if file.endswith(suffix): #"radd_modified_radd_agb.tif"): #"_radd_labelled_agb.tif"):

                file_path = os.path.join(stack_directory, file)

                with rasterio.open(file_path) as src:
                    radd_alerts = src.read(1)  # Assuming the RADD alert band is the first band
                    alert_count = np.count_nonzero(radd_alerts > 0)  ### alert_label_value)
                    print(f"file:{file}, alert count: {alert_count}")
                    alert_counts.append(alert_count)
                    file_names.append(file)  # Keep track of the file names

                    src.close()
                    if alert_count < min_alert_pixels:
                        base_name = file.replace(suffix, '')
                        for suffix in ['_radd_.tif', '_radd.tif', '_sentinel.tif',"_sentinel_agb_normalized.tif", suffix]:
                            file_to_delete = os.path.join(stack_directory, f"{base_name}{suffix}")  # Ensure to add the suffix when deleting
                            if os.path.exists(file_to_delete):
                                os.remove(file_to_delete)
                                print(f"Removed file {file_to_delete}")

                        print(f"Removed stack {file} due to insufficient RADD alerts:{alert_count}.")

        # Find and print the file with the maximum alerts
        if alert_counts:  # Ensure there are alert counts to process
            max_alert_count = max(alert_counts)
            max_index = alert_counts.index(max_alert_count)
            max_alert_file = file_names[max_index]

            min_alert_count = min(alert_counts)
            min_index = alert_counts.index(min_alert_count)
            min_alert_file = file_names[min_index]

            print(f"The file with the maximum alerts is '{max_alert_file}' with {max_alert_count} alerts.")
            print(f"The file with the minimum alerts is '{min_alert_file}' with {min_alert_count} alerts.")
        else:
            print("No alert counts to process.")



        return alert_counts


    def filter_stacks_and_radd_by_AGB(self, input_folder, output_folder, valid_classes=[2, 3, 4, 5], nodata_value=-9999):
        """
        Filters Sentinel stacks and corresponding RADD alert files by AGB land classification.
#     # 1 = Intact Lowland Forest
#     # 2 = Intact Montane Forest
#     # 3 = Secondary and Degraded Forest
#     # 4 = Peat Swamp Forest
#     # 5 = Mangrove Forest
#     # 6 = Swamp Scrublands
#     # 7 = Crops/Agriculture
#     # 8 = Tree Plantations
#     # 9 = Urban/Settlement
#     # 10 = Scrublands
#     # 11 = Inland Water
        Args:
            input_folder (str): Path to the folder containing Sentinel and RADD files.
            output_folder (str): Path to the folder where filtered files will be saved.
            valid_classes (list): AGB class values to retain.
            nodata_value (int): No-data value for filtered pixels.
        """

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        for filename in os.listdir(input_folder):
            if filename.endswith('sentinel.tif'):
                sentinel_file_path = os.path.join(input_folder, filename)

                with rasterio.open(sentinel_file_path) as sentinel_src:
                    agb_band = sentinel_src.read(7)  # Assuming AGB band is the 7th band

                    radd_filename = filename.replace('_sentinel.tif', '_radd_labelled.tif')
                    radd_file_path = os.path.join(input_folder, radd_filename)

                    # Check if any of the valid classes are present in the AGB band
                    if not np.any(np.isin(agb_band, valid_classes)):
                        print(f"removing {radd_filename, sentinel_file_path} as it does not contain any of the valid AGB classes.")
                        # radd_src.close()
                        sentinel_src.close()
                        if os.path.exists(radd_file_path):
                            os.remove(radd_file_path)
                        os.remove(sentinel_file_path)

                        continue  # Skip this file

                    agb_mask = np.isin(agb_band, valid_classes)

                    # Process Sentinel file
                    output_sentinel_filename = f"{filename.replace('.tif', '')}_agb.tif"
                    output_sentinel_path = os.path.join(output_folder, output_sentinel_filename)
                    self.apply_mask_and_save(sentinel_src, agb_mask, output_sentinel_path, nodata_value)

                    # Check and process corresponding RADD file if it exists

                    if os.path.exists(radd_file_path):
                        with rasterio.open(radd_file_path) as radd_src:
                            output_radd_filename = f"{radd_filename.replace('.tif', '')}_agb.tif"
                            output_radd_path = os.path.join(output_folder, output_radd_filename)
                            self.apply_mask_and_save(radd_src, agb_mask, output_radd_path, nodata_value)

                            radd_src.close()
                        os.remove(radd_file_path)
                    sentinel_src.close()
                os.remove(sentinel_file_path)

    def apply_mask_and_save(self, src, mask, output_path, nodata_value):
        """
        Applies a mask to the source dataset and saves the result to the specified output path.
        Args:
            src (rasterio.io.DatasetReader): Source dataset.
            mask (numpy.ndarray): Mask to apply.
            output_path (str): Path to save the masked dataset.
            nodata_value (int): No-data value for masked pixels.
        """
        meta = src.meta.copy()
        meta.update(nodata=nodata_value, dtype=rasterio.float32)

        with rasterio.open(output_path, 'w', **meta) as dst:
            for i in range(1, src.count + 1):
                data = src.read(i).astype(rasterio.float32)
                masked_data = np.where(mask, data, nodata_value)
                dst.write(masked_data, i)


        print(f"Processed file saved as: {output_path}, Deleted File: {src}")



    def calculate_alert_distribution(self, alert_counts, num_groups=5):
        """
        Calculates the distribution of alert counts into equal groups.

        Args:
            alert_counts (list): List of alert counts from RADD alert bands.
            num_groups (int): Number of groups to divide the alert counts into.

        Returns:
            dict: A dictionary with the range as keys and count of alerts in each range as values.
        """
        max_alert_count = max(alert_counts)
        max_index = alert_counts.index(max_alert_count)
        min_alert_count = min(alert_counts)
        min_index = alert_counts.index(min_alert_count)
        print(f"{max_index} is the max alert_count index, {max(alert_counts)} is the max counts.")
        print(f"{min_index} is the min alert_count index, {min(alert_counts)} is the min counts.")
        min_alert_count = min(alert_counts)
        range_size = (max_alert_count - min_alert_count) / num_groups
        distribution = {}

        for i in range(num_groups):
            lower_bound = min_alert_count + i * range_size
            upper_bound = lower_bound + range_size
            if i == num_groups - 1:
                # Ensure the last group includes the max value
                upper_bound = max_alert_count + 1

            # Count how many alerts fall into this range
            count = sum(lower_bound <= count <= upper_bound for count in alert_counts)
            distribution[f"{lower_bound:.2f}-{upper_bound:.2f}"] = count



        return distribution


    def calculate_band_statistics(self, directories, nan_value=-9999):
        """
        Calculates the mean and standard deviation of each Sentinel band,
        excluding specified NaN values.

        Args:
            directories (list): List of directories to process.
            nan_value (int): Value to be treated as NaN and excluded from calculations.

        Returns:
            dict: Dictionary containing means and stds for each band.
        """
        band_sums = []
        band_squares = []
        band_counts = []
        initialized = False

        for directory in directories:
            for file in os.listdir(directory):
                if file.endswith('_sentinel_normalized.tif'):
                    file_path = os.path.join(directory, file)

                    with rasterio.open(file_path) as src:
                        bands = src.read()

                        if not initialized:
                            # Initialize sum, sum of squares, and count arrays
                            band_sums = [np.zeros(band.shape) for band in bands]
                            band_squares = [np.zeros(band.shape) for band in bands]
                            band_counts = [0 for _ in bands]
                            initialized = True

                        for i, band in enumerate(bands):
                            valid_mask = band != nan_value
                            band_sums[i] += np.where(valid_mask, band, 0)
                            band_squares[i] += np.where(valid_mask, np.square(band), 0)
                            band_counts[i] += np.count_nonzero(valid_mask)

        means = [np.sum(band_sum) / band_count if band_count > 0 else 0 for band_sum, band_count in zip(band_sums, band_counts)]
        stds = [np.sqrt(max(np.sum(band_square) / band_count - mean ** 2, 0)) if band_count > 0 else 0 for band_square, band_count, mean in zip(band_squares, band_counts, means)]

        return {"means": means, "stds": stds}

    def compute_global_min_max(self, input_folder, bands=[1, 2, 3, 4, 5, 6]):
        global_min = np.full(len(bands), np.inf)
        global_max = np.full(len(bands), -np.inf)

        for filename in os.listdir(input_folder):
            if filename.endswith('_sentinel_agb.tif'):
                filepath = os.path.join(input_folder, filename)
                with rasterio.open(filepath) as src:
                    for i, band_idx in enumerate(bands):
                        band = src.read(band_idx).astype(np.float32)
                        valid_mask = band > 0  # Assuming negative values are not valid
                        valid_pixels = band[valid_mask]
                        if valid_pixels.size > 0:  # Ensure there are valid pixels
                            global_min[i] = min(np.min(valid_pixels), global_min[i])
                            global_max[i] = max(np.max(valid_pixels), global_max[i])

        return global_min, global_max

    def normalize_images_global(self, input_folder, output_folder, global_min, global_max, bands=[1, 2, 3, 4, 5, 6]):
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        for filename in os.listdir(input_folder):
            if filename.endswith('_sentinel_agb.tif'):
                input_path = os.path.join(input_folder, filename)
                output_path = os.path.join(output_folder, os.path.splitext(filename)[0] + '_normalized.tif')

                with rasterio.open(input_path) as src:
                    meta = src.meta.copy()
                    meta.update(dtype=rasterio.float32)  # Ensure output data type is float32

                    with rasterio.open(output_path, 'w', **meta) as dst:
                        for i in range(1, src.count + 1):  # Include all bands, adjusting loop to iterate through all bands
                            if i in bands:
                                band = src.read(i).astype(np.float32)
                                valid_mask = (band != self.nodata_value) & (band >= 0)
                                # Scale to 0-1 range using global min and max
                                scaled_band = np.where(valid_mask, (band - global_min[i - 1]) / (global_max[i - 1] - global_min[i - 1]), self.nodata_value)
                                dst.write(scaled_band, i)
                            elif i == 7:  # Handle the 7th band if needed
                                classification_band = src.read(i).astype(np.float32)
                                dst.write(classification_band, i)

                    src.close()
                os.remove(input_path)
                print(f"Normalized file saved as: {output_path}, Deleted: {input_path}")


    def compute_global_mean_std(self, input_folder, bands=[1, 2, 3, 4, 5, 6]):
        sum_means = np.zeros(len(bands))
        sum_variances = np.zeros(len(bands))
        total_pixels = 0

        for filename in os.listdir(input_folder):
            if not filename.endswith('_sentinel_agb_normalized.tif'):
                continue  # Skip non-sentinel files
            filepath = os.path.join(input_folder, filename)
            with rasterio.open(filepath) as src:
                for i, band_idx in enumerate(bands):
                    band = src.read(band_idx).astype(np.float32)
                    valid_mask = band > 0  # Assuming negative values are not valid
                    valid_pixels = band[valid_mask]
                    sum_means[i] += valid_pixels.mean()
                    sum_variances[i] += valid_pixels.var()
                    total_pixels += valid_pixels.size

        global_means = sum_means / len(os.listdir(input_folder))
        global_stds = np.sqrt(sum_variances / len(os.listdir(input_folder)))

        return global_means, global_stds

    #
    # def normalize_images_global(self, input_folder,output_folder, global_means, global_stds, bands=[1, 2, 3, 4, 5, 6]):
    #     if not os.path.exists(output_folder):
    #         os.makedirs(output_folder)
    #
    #     for filename in os.listdir(input_folder):
    #         if filename.endswith('modified_sentinel_agb.tif'):
    #             input_path = os.path.join(input_folder, filename)
    #             output_path = os.path.join(output_folder, os.path.splitext(filename)[0] + '_normalized.tif')
    #
    #             with rasterio.open(input_path) as src:
    #                 meta = src.meta.copy()
    #                 meta.update(dtype=rasterio.float32)  # Ensure output data type is float32
    #
    #                 with rasterio.open(output_path, 'w', **meta) as dst:
    #                     for i in range(1, src.count + 1):  # Include all bands, adjusting loop to iterate through all bands
    #                         if i in bands:
    #                             # Normalize specified bands
    #                             band = src.read(i).astype(np.float32)
    #                             valid_mask = (band != self.nodata_value) & (band >= 0)
    #                             normalized_band = np.where(valid_mask, (band - global_means[i - 1]) / global_stds[i - 1], self.nodata_value)
    #                             dst.write(normalized_band, i)
    #                         elif i == 7:  # Assuming the 7th band is the classification band
    #                             # Directly write the 7th band without normalization
    #                             classification_band = src.read(i).astype(np.float32)
    #                             dst.write(classification_band, i)
    #
    #             print(f"Normalized file saved as: {output_path}")



    def normalize_single_file_rasterio(self, file_path, nodata_value=-9999):
        """
        Normalizes the first 6 bands of a Sentinel-2 data file to a range of 0-1,
        excluding no-data and values below zero. The 7th band, assumed to be a LULC classification band,
        is added without normalization. The output data is written as float32
        to a new file with '_normalized' suffix.

        Args:
            file_path (str): Path to the Sentinel-2 data file.
            nodata_value (int): Value to be treated as 'no data' and excluded from normalization.
        """
        if file_path.endswith('_sentinel.tif'):
            output_path = os.path.splitext(file_path)[0] + '_normalized.tif'

            with rasterio.open(file_path) as src:
                meta = src.meta
                meta.update(dtype=rasterio.float32)

                with rasterio.open(output_path, 'w', **meta) as dst:
                    for i in range(1, src.count + 1):  # Process all bands
                        band = src.read(i).astype(np.float32)

                        if i <= 6:  # Normalize the first 6 bands
                            valid_mask = (band != nodata_value) & (band >= 0)
                            band_masked = np.ma.masked_array(band, ~valid_mask)

                            if np.ma.is_masked(band_masked):
                                min_val = band_masked.min()
                                max_val = band_masked.max()

                                # Normalize valid data
                                band_normalized = (band_masked - min_val) / (max_val - min_val)
                                band_normalized.fill_value = nodata_value
                                dst.write_band(i, band_normalized.filled())

                        else:  # Directly add the 7th band without normalization
                            dst.write_band(i, band)
            os.remove(file_path)
            print(f"Normalized file saved as: {output_path}")

    def plot_metrics_from_log(self, log_filename):
        # Regular expression patterns
        performance_pattern = re.compile(
            r"Iter\(val\) \[\d+\]\s+aAcc: ([\d.]+), mIoU: ([\d.]+), mAcc: ([\d.]+), "
            r"IoU.Unburnt land: ([\d.]+), IoU.Burn scar: ([\d.]+), "
            r"Acc.Unburnt land: ([\d.]+), Acc.Burn scar: ([\d.]+)"
        )

        training_pattern = re.compile(
            r"Iter \[\d+/\d+\]\s+lr: [\d.e-]+, .+decode.loss_dice: ([\d.]+), "
            r"decode.acc_seg: ([\d.]+), aux.loss_dice: ([\d.]+), "
            r"aux.acc_seg: ([\d.]+), loss: ([\d.]+)"
        )

        # Initialize lists for performance metrics
        aAccs, mIoUs, mAccs = [], [], []
        IoU_unburnt, IoU_burn, Acc_unburnt, Acc_burn = [], [], [], []

        # Initialize lists for training metrics
        decode_loss_dices, decode_acc_segs = [], []
        aux_loss_dices, aux_acc_segs, total_losses = [], [], []

        # Read the log file and parse the metrics
        if not os.path.exists(log_filename):
            print(f"Log file {log_filename} not found.")
            return

        with open(log_filename, 'r') as file:
            for line in file:
                perf_match = performance_pattern.search(line)
                train_match = training_pattern.search(line)

                if perf_match:
                    aAccs.append(float(perf_match.group(1)))
                    mIoUs.append(float(perf_match.group(2)))
                    mAccs.append(float(perf_match.group(3)))
                    IoU_unburnt.append(float(perf_match.group(4)))
                    IoU_burn.append(float(perf_match.group(5)))
                    Acc_unburnt.append(float(perf_match.group(6)))
                    Acc_burn.append(float(perf_match.group(7)))

                if train_match:
                    decode_loss_dices.append(float(train_match.group(1)))
                    decode_acc_segs.append(float(train_match.group(2)))
                    aux_loss_dices.append(float(train_match.group(3)))
                    aux_acc_segs.append(float(train_match.group(4)))
                    total_losses.append(float(train_match.group(5)))

        # Plotting
        plt.figure(figsize=(15, 20))

        # Plot performance metrics
        plt.subplot(5, 1, 1)
        plt.plot(mIoUs, label='mIoU')


        plt.plot(aAccs, label='aAcc')
        plt.plot(mAccs, label='mAcc')
        plt.plot(IoU_unburnt, label='IoU Unburnt Land')
        plt.plot(IoU_burn, label='IoU Burn Scar')
        plt.plot(Acc_unburnt, label='Acc Unburnt Land')
        plt.plot(Acc_burn, label='Acc Burn Scar')
        plt.xlabel('Iteration')
        plt.ylabel('Performance Metrics')
        plt.title('Performance Metrics Over Iterations')
        plt.legend()

        # Plot training metrics - Decode Loss Dice
        plt.subplot(5, 1, 2)
        plt.plot(decode_loss_dices, label='Decode Loss Dice')
        plt.xlabel('Iteration')
        plt.ylabel('Decode Loss Dice')
        plt.title('Decode Loss Dice Over Iterations')
        plt.legend()

        # Plot training metrics - Decode Accuracy Segment
        plt.subplot(5, 1, 3)
        plt.plot(decode_acc_segs, label='Decode Accuracy Segment')
        plt.xlabel('Iteration')
        plt.ylabel('Decode Accuracy Segment')
        plt.title('Decode Accuracy Segment Over Iterations')
        plt.legend()

        # Plot training metrics - Aux Loss Dice & Aux Accuracy Segment
        plt.subplot(5, 1, 4)
        plt.plot(aux_loss_dices, label='Aux Loss Dice')
        plt.plot(aux_acc_segs, label='Aux Accuracy Segment')
        plt.xlabel('Iteration')
        plt.ylabel('Aux Metrics')
        plt.title('Auxiliary Metrics Over Iterations')
        plt.legend()

        # Plot training metrics - Total Loss
        plt.subplot(5, 1, 5)
        plt.plot(total_losses, label='Total Loss')
        plt.xlabel('Iteration')
        plt.ylabel('Total Loss')
        plt.title('Total Loss Over Iterations')
        plt.legend()

        plt.tight_layout()
        plt.show()

    def plot_bands(self, sentinel_path, radd_path):
        band_labels = ['RADD Alert', 'Red Band', 'Green Band', 'Blue Band', 'NIR Band', 'SWIR1 Band', 'SWIR2 Band']

        # Initialize plot
        fig, axs = plt.subplots(2, 4, figsize=(24, 12), sharex =True, sharey = True)  # Adjust for 8 subplots
        fig.suptitle('Combined Bands Visualization', fontsize=16)

        # Plot RADD band
        with rasterio.open(radd_path) as src:
            radd_band = src.read(1)  # Assuming RADD data is in the first band
            radd_band = np.where(radd_band == -9999, np.nan, radd_band)
            im = axs[0, 0].imshow(radd_band, cmap='gray', vmin=0, vmax=np.nanmax(radd_band))
            axs[0, 0].set_title(band_labels[0])
            plt.colorbar(im, ax=axs[0, 0], fraction=0.046, pad=0.04)

        # Plot Sentinel bands
        with rasterio.open(sentinel_path) as src:
            for i in range(1, 7):  # Six Sentinel bands
                band = src.read(i)
                band = np.where(band == -9999, np.nan, band)
                row, col = divmod(i, 4)
                im = axs[row, col].imshow(band, cmap='gray', vmin=0, vmax=np.nanmax(band))
                axs[row, col].set_title(band_labels[i])
                plt.colorbar(im, ax=axs[row, col], fraction=0.046, pad=0.04)

        # Hide unused subplot
        axs[1, 3].axis('off')
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        # plt.show()
        plt.pause(10)


    def find_pairs(self, directory, sentinel_suffix="_sentinel.tif", radd_suffix="_radd.tif"):
        files = os.listdir(directory)
        sentinel_files = [f for f in files if f.endswith(sentinel_suffix)]
        radd_files = [f for f in files if f.endswith(radd_suffix)]

        pairs = []
        for sen_file in sentinel_files:
            base_name = sen_file.replace(sentinel_suffix, "")
            matching_radd = base_name + radd_suffix
            if matching_radd in radd_files:
                pairs.append((sen_file, matching_radd))
        return pairs

    def replace_nodata_values(self, input_filepath, output_filepath, old_nodata_value=-9999, new_nodata_value=np.nan):

        with rasterio.open(input_filepath) as src:
            # Read the entire array
            data = src.read()

            # Replace -9999 with new_nodata_value for all bands
            data[data == old_nodata_value] = new_nodata_value

            # Copy the metadata
            new_meta = src.meta.copy()
            # Update the metadata with new nodata value
            new_meta.update(nodata=new_nodata_value)

            with rasterio.open(output_filepath, 'w', **new_meta) as dst:
                dst.write(data)


