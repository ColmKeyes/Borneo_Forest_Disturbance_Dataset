# -*- coding: utf-8 -*-
"""
DatasetManagement class created for preprocessing datasets and basic plotting

@Time    : 7/12/2023 07:49
@Author  : Colm Keyes
@Email   : keyesco@tcd.ie
@File    : preprocessing_pipeline
"""


#
import os
import shutil
import rasterio
import numpy as np
from torch.utils.data import Dataset, random_split
from rasterio.windows import Window
import matplotlib.pyplot as plt
import shutil
import torch
# from sklearn.model_selection import train_test_split

class CustomDataset(Dataset):
    def __init__(self, data_dir, pairs):
        self.data_dir = data_dir
        self.pairs = pairs

    def __len__(self):
        return len(self.pairs)

    def __getitem__(self, idx):
        return self.pairs[idx]

class DatasetManagement:
    def __init__(self, source_dir, train_dir, val_dir, output_folder, tile_size=512, val_split=0.25):
        self.source_dir = source_dir
        self.train_dir = train_dir
        self.val_dir = val_dir
        self.output_folder = output_folder
        self.tile_size = tile_size
        self.val_split = val_split
        self.pairs = []

    def _save_raster(self, data, profile, filename, folder):
        """Helper function to save raster data."""
        output_path = os.path.join(folder, filename)
        num_bands = 1 if len(data.shape) == 2 else data.shape[0]
        profile.update(count=num_bands)
        with rasterio.open(output_path, 'w', **profile) as dst:
            if num_bands == 1:
                dst.write(data, 1)
            else:
                for i in range(num_bands):
                    dst.write(data[i, :, :], i + 1)

    ##########
    ## Crop radd_sen2 stack to 512 tile size
    ##########

    def crop_to_tiles(self, image_path, output_folder):
        with rasterio.open(image_path) as src:
            for j in range(0, src.height, self.tile_size):
                for i in range(0, src.width, self.tile_size):
                    # Save each tile
                    tile_filename = f"{os.path.splitext(os.path.basename(image_path))[0]}_{i}_{j}.tif"
                    tile_path = os.path.join(output_folder, tile_filename)

                    if os.path.exists(tile_path):
                        continue

                    window = Window(i, j, self.tile_size, self.tile_size)
                    if src.height - j < self.tile_size or src.width - i < self.tile_size:
                        continue  # Skip incomplete tiles at the edge

                    tile = src.read(window=window)

                    with rasterio.open(
                            tile_path,
                            'w',
                            driver='GTiff',
                            height=tile.shape[1],
                            width=tile.shape[2],
                            count=src.count,
                            dtype=tile.dtype,
                            crs=src.crs,
                            transform=rasterio.windows.transform(window, src.transform)
                    ) as tile_dst:
                        tile_dst.write(tile)
            src.close()

    ##########
    ## Split 512 tiles into radd and sen2 stacks
    ##########

    def find_unique_tiles(self):
        tile_names = [filename.split('_')[1] for filename in os.listdir(self.source_dir) if filename.endswith('.tif')]
        unique_tiles = {tile for tile in tile_names if tile_names.count(tile) == 2}
        unique_files = [filename for filename in os.listdir(self.source_dir) if any(tile in filename for tile in unique_tiles)]
        return unique_files

    def move_files(self, files, destination):
        for file in files:
            shutil.move(os.path.join(self.source_dir, file), os.path.join(destination, file))


    def split_tiles(self, source_folder):

        for file in os.listdir(source_folder):
            if file.endswith('.tif') and not file.endswith('radd.tif') and not  file.endswith('sentinel.tif') :
                file_path = os.path.join(source_folder, file)

                with rasterio.open(file_path) as src:
                    base_name, _ = os.path.splitext(file)

                    # RADD alerts (first band)
                    radd_filename = base_name + '_radd.tif'

                    # Sentinel-2 bands (remaining bands)
                    sentinel_filename = base_name + '_sentinel.tif'

                    self.pairs.append((os.path.join(source_folder, sentinel_filename), os.path.join(source_folder, radd_filename)))

                    if os.path.exists(f"{source_folder}/{sentinel_filename}") and os.path.exists(f"{source_folder}/{radd_filename}"):
                        continue


                    sentinel_bands = src.read(range(2, src.count + 1))
                    radd_alerts = src.read(1)
                    self._save_raster(sentinel_bands, src.profile, sentinel_filename, source_folder)
                    self._save_raster(radd_alerts, src.profile, radd_filename, source_folder)

                    print(f"rasters saved: {sentinel_filename}, {radd_filename} ")
                    src.close()
                    os.remove(file_path)
                    print(f"Deleted File: {file_path} ")
        return self.pairs
    ##########
    ## Sets radd and sen2 stacks into val and train folders
    ##########

    def split_dataset(self, source_folder, destination_directory ,val_split=0.2):
        # Automatically define train and val directories
        train_dir = os.path.join(destination_directory, 'train')
        val_dir = os.path.join(destination_directory, 'val')
        os.makedirs(train_dir, exist_ok=True)
        os.makedirs(val_dir, exist_ok=True)

        # Building pairs based on the full identifier
        pairs = []
        files = os.listdir(source_folder)
        for file in files:
            if '_radd_labelled' in file or '_sentinel' in file:
                identifier = "_".join(file.split('_')[:-1])  # Adjust based on your naming convention to include pixel values
                pair = None
                if '_radd_labelled' in file:
                    sentinel_version = identifier + '_sentinel.tif'
                    if sentinel_version in files:
                        pair = (os.path.join(source_folder, file), os.path.join(source_folder, sentinel_version))
                elif '_sentinel' in file:
                    radd_version = identifier + '_radd_labelled.tif'
                    if radd_version in files:
                        pair = (os.path.join(source_folder, radd_version), os.path.join(source_folder, file))
                if pair and pair not in pairs:
                    pairs.append(pair)

        # Splitting pairs into train and val sets
        total_size = len(pairs)
        val_size = int(total_size * val_split)
        all_indices = list(range(total_size))
        torch.manual_seed(42)  # For reproducibility
        shuffled_indices = torch.randperm(total_size).tolist()

        train_indices = shuffled_indices[val_size:]
        val_indices = shuffled_indices[:val_size]

        # Move files based on split
        for idx in train_indices:
            for file_path in pairs[idx]:
                shutil.move(file_path, train_dir)
        for idx in val_indices:
            for file_path in pairs[idx]:
                shutil.move(file_path, val_dir)


    def plot_7_bands(self, filename):
        file_path = os.path.join(self.output_folder, filename)
        if not os.path.exists(file_path):
            print(f"File {filename} does not exist in the output directory.")
            return

        band_labels = ['RADD Alert', 'Red Band', 'Green Band', 'Blue Band', 'NIR Band', 'SWIR1 Band', 'SWIR2 Band']

        with rasterio.open(file_path) as src:
            fig, axs = plt.subplots(3, 3, figsize=(20, 18), gridspec_kw={'height_ratios': [1, 1, 1]})
            fig.suptitle(filename, fontsize=16)


            for i in range(6):
                row = i // 3
                col = i % 3
                band = src.read(i + 2)
                band = np.where(band == -9999, np.nan, band)
                vmax = np.nanmax(band)
                im = axs[row, col].imshow(band, cmap='gray', vmin=0, vmax=vmax)
                axs[row, col].set_title(band_labels[i + 1])
                plt.colorbar(im, ax=axs[row, col], fraction=0.046, pad=0.04)


            radd_band = src.read(1)
            radd_band = np.where(radd_band == -9999, np.nan, radd_band)
            vmax = np.nanmax(radd_band)
            im = axs[2, 1].imshow(radd_band, cmap='gray', vmin=0, vmax=vmax)
            axs[2, 1].set_title(band_labels[0])
            plt.colorbar(im, ax=axs[2, 1], fraction=0.046, pad=0.04)

            # Hiding unused subplots
            for i in range(3):
                axs[2, i].axis('off')
            axs[2, 1].axis('on')

            plt.tight_layout(rect=[0, 0.03, 1, 0.95])
            plt.show()
