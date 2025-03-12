
# -*- coding: utf-8 -*-
"""
Main model outputs to analise model performance metrics and visualise results with plots and confusion matrices.

@Time    : 2/2024
@Author  : Colm Keyes
@Email   : keyesco@tcd.ie
@File    : model_analysis.py
"""




import json
import os
import glob
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Arrow
import matplotlib.patheffects as PathEffects
from rasterio.plot import show
from pyproj import Proj, transform


color_maps = {
    '10000': ['#E69F00', '#F0E442', '#56B4E9'],  # Shades for 10000 minalerts
    '12500': ['#009E73', '#8DD3C7', '#0072B2'],  # Shades for 12500 minalerts
    '15000': ['#D55E00', '#CC79A7', '#999999'],  # Shades for 15000 minalerts
}



class ModelAnalysis:
    def __init__(self, log_file):
        self.log_file = log_file
        self.data = self.load_log_data()

    def load_log_data(self):
        """Load the log data from the JSON file."""
        data = []
        with open(self.log_file, 'r') as f:
            for line in f:
                entry = json.loads(line)
                # Ensure the entry contains 'epoch' and 'mode' keys and mode is 'val'
                if 'epoch' in entry and 'mode' in entry and entry['mode'] == 'val':
                    data.append(entry)
        return data

    def extract_metric(self, metric_name):
        """Extract a specific metric across epochs."""
        return [entry[metric_name] for entry in self.data if metric_name in entry]

    def get_epochs(self):
        """Extract epoch numbers."""
        return [entry['epoch'] for entry in self.data]


    def plot_metric(self, metric_name, ax, label):
        """Plot a specific metric."""
        values = self.extract_metric(metric_name)
        epochs = self.get_epochs()
        ax.plot(epochs, values, label=label)
        ax.set_xlabel('Epoch')
        ax.set_ylabel(metric_name)
        ax.legend()
#



def plot_image_triplet(input_path, output_path, ground_truth_path, image_basename, data_type, save_path):

    unnormalised_image_path = r"E:\Data\Sentinel2_data\30pc_cc\Tiles_512_30pc_cc" # for printing non-normalised rgb.
    suffix = ''
    if data_type == 'backscatter':
        suffix = '_bsc_masked_normalized'
    elif data_type == 'coherence':
        suffix = '_coh_masked_normalized'


    run_number = ''
    for part in save_path.split('_'):
        if part.startswith('run'):
            run_number = part
            break

    inProj = Proj(init='epsg:32650')
    outProj = Proj(init='epsg:4326')
    # Transform the corners of the image to lat/long
    left, bottom = transform(inProj, outProj, 230536.5095550618, -107359.60842863785)
    right, top = transform(inProj, outProj, 245873.9621862365, -92022.15579746317)


    input_image = os.path.join(input_path, f"{image_basename}_sentinel_agb_normalized{suffix}.tif")
    unnormalised_image = os.path.join(unnormalised_image_path, f"{image_basename}_sentinel.tif")
    output_image = os.path.join(output_path, f"{image_basename}_sentinel_agb_normalized{suffix}_pred_{run_number}_op.tif")
    ground_truth_image = os.path.join(ground_truth_path, f"{image_basename}_radd_labelled_agb.tif")

    class_cmap = ListedColormap(['lightblue', 'orange', 'grey'])
    class_cmap_gt = ListedColormap(['lightblue', 'red', 'grey'])

    difference_cmap = ListedColormap(['orange', "lightblue", 'grey'])
    sar_map = plt.cm.gray

    colorlist = ["grey","lightblue",  "red", "blue", "orange"]  # Colors for NoData, TN, FN, FP, TP
    cmap = ListedColormap(colorlist)
    leg_handles = [Line2D([0], [0], color=color, lw=4) for color in colorlist]
    leg_labels = [ "No Data","TN", "FN", "FP", "TP"]




    fig, axs = plt.subplots(1, 4, figsize=(30, 8), sharex=True, sharey=True)

    with rasterio.open(input_image) as src:
        if data_type in ["backscatter", "coherence"]:
            # For backscatter or coherence, create a composite image using band 5 and band 6
            band1 = src.read(5)
            band2 = src.read(6)

            # Create a composite image
            composite = np.stack((band1, band2, band1), axis=0)  # Stacking along the first axis (color channel)
            composite = composite.astype(float)
            # composite /= composite.max()  # Normalize to [0, 1] range
            p99 = np.percentile(composite, 99)  # Get the 99th percentile
            composite = np.clip(composite, 0, p99) / p99
            axs[0].imshow(composite.transpose(1, 2, 0), cmap="gray", extent=[left, right, bottom, top])  # Transpose for imshow
            axs[0].set_title(f'{data_type.capitalize()} Bands Composite', fontsize=28)
            # Display the composite image

        else:
            # Handle non-backscatter and non-coherence data types
            with rasterio.open(unnormalised_image) as src:

                input_rgb = src.read([1, 2, 3])
                # input_rgb = np.clip(input_rgb / 0.1, 0, 1)
                # max_value = np.nanmax(input_rgb)
                # input_rgb = input_rgb / max_value
                p99 = np.percentile(input_rgb, 99)
                input_rgb = np.clip(input_rgb, 0, p99) / p99

                axs[0].imshow(input_rgb.transpose(1, 2, 0),vmin=0, vmax=1, extent=[left, right, bottom, top])  #vmin=0, vmax=2, Display RGB image
                axs[0].set_title('Input RGB', fontsize=28)
    # with rasterio.open(input_image) as src:
    #     if data_type in ["backscatter", "coherence"]:
    #         # For backscatter or coherence, display band 5 and band 6 separately
    #         band1 = src.read(5)
    #         band2 = src.read(6)
    #         axs[0].imshow(band1, cmap='gray', extent=[left, right, bottom, top])
    #         axs[0].set_title(f'{data_type.capitalize()} Band 1')
    #     else:
    #         input_rgb = src.read([1, 2, 3])
    #         input_rgb = np.clip(input_rgb / 0.1, 0, 1)
    #         axs[0].imshow(input_rgb.transpose(1, 2, 0), extent=[left, right, bottom, top])
    #         axs[0].set_title('Input RGB')


    with rasterio.open(output_image) as src:
        output_data = src.read(1).astype(float)
        output_data[output_data == -1] = np.nan

    with rasterio.open(ground_truth_image) as src:
        gt_data = src.read(1).astype(float)
        gt_data[gt_data == -9999] = np.nan

    # Calculate TN,FN,TP,FP.
    cont = np.zeros_like(output_data, dtype=np.int16)  # Assuming output_data is already defined
    cont[output_data == -9999] = 0  # NoData
    cont[(gt_data == 0) & (output_data == 0)] = 1  # TN: True Negative
    cont[(gt_data == 1) & (output_data == 0)] = 2  # FN: False Negative
    cont[(gt_data == 0) & (output_data == 1)] = 3  # FP: False Positive
    cont[(gt_data == 1) & (output_data == 1)] = 4  # TP: True Positive



    difference_map = np.where(np.isnan(output_data) | np.isnan(gt_data), 2, 1 - np.abs(gt_data - output_data))

    # fig.suptitle('Prithvi 15k', fontsize=20)

    show_class_data(output_data, axs[1], class_cmap, 'Output U-Net', [left, right, bottom, top])
    show_class_data(gt_data, axs[2], class_cmap_gt, 'Labels', [left, right, bottom, top])


    axs[0].set_xlabel('Longitude', fontsize=28)
    axs[0].set_ylabel('Latitude', fontsize=28)
    axs[0].tick_params(axis='both', labelsize=16)  # Adjusting the size of the tick labels
    # axs[3].imshow(difference_map, cmap=difference_cmap, vmin=0, vmax=2, extent=[left, right, bottom, top])
    # axs[3].set_title('Difference Map', fontsize=28)
    # axs[3].set_xlabel('Longitude', fontsize=28)
    # axs[3].set_ylabel('Latitude', fontsize=28)
    # axs[3].tick_params(axis='both', labelsize=16)  # Adjusting the size of the tick labels
    axs[3].imshow(cont, cmap=cmap, vmin=0, vmax=4, interpolation="nearest", extent=[left, right, bottom, top])
    axs[3].set_title('Confusion Matrix Map', fontsize=24)
    axs[3].set_xlabel('Longitude', fontsize=28)
    axs[3].set_ylabel('Latitude', fontsize=28)
    axs[3].tick_params(axis='both', labelsize=16)
    # axs[3].legend(handles=leg_handles, labels=leg_labels, loc='upper right', fontsize=12)

    add_legend(axs[1], class_cmap, ['Non-Disturbed', 'Disturbed', 'No Data'], fontsize=22)
    add_legend(axs[2], class_cmap_gt, ['Non-Disturbed', 'Disturbed', 'No Data'],fontsize=22)
    # add_legend(axs[3], difference_cmap, ['Difference', 'No Difference', 'No Data'],fontsize=22)
    add_legend(axs[3], cmap, leg_labels, fontsize=22)

    output_filename = os.path.join(save_path, f"{image_basename}_comparison.png")
    plt.tight_layout()
    plt.savefig(output_filename, bbox_inches='tight')
    plt.close()

    print(f"File saved at {output_filename}")

def show_class_data(data, ax, cmap, title, extent):
    mapped_data = np.full(data.shape, 2)  # Default to no data
    mapped_data[data == 0] = 0  # Non-disturbed
    mapped_data[data == 1] = 1  # Disturbed
    ax.imshow(mapped_data, cmap=cmap, extent=extent)
    ax.set_title(title, fontsize=28)
    ax.set_xlabel('Longitude', fontsize=28)
    ax.set_ylabel('Latitude', fontsize=28)
    ax.tick_params(axis='both', labelsize=16)
    ax.axis('on')

def add_legend(ax, cmap, labels, fontsize=14):  # Added fontsize parameter with a default value
    patches = [plt.Rectangle((0, 0), 1, 1, color=cmap(i)) for i in range(len(labels))]
    ax.legend(handles=patches, labels=labels, loc='upper right', fontsize=fontsize)

