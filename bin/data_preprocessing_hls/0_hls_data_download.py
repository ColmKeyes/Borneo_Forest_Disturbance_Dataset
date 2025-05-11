import os
import time
import datetime
import math
import json
import pandas as pd
import numpy as np
import earthaccess
import geopandas as gpd
from shapely.geometry import Polygon, mapping
from concurrent.futures import ThreadPoolExecutor
import logging
from tqdm import tqdm
import requests
import urllib3
from pathlib import Path

# Suppress insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("earthdata_download.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Output directory
output_dir = '/media/colm-the-conjurer/writable/data/hls'
os.makedirs(output_dir, exist_ok=True)

# EarthData credentials
# You will be prompted for these if not stored in your .netrc file
# Or you can set them here:
# earthaccess.login() #username="Coliflower", password="r*F$QG&7si6kceU")

# Try to log in with stored credentials or prompt if needed
try:
    auth = earthaccess.login(strategy="netrc")
    if auth:
        logger.info("Successfully authenticated with NASA EarthData")
    else:
        logger.warning("Failed to authenticate. You may be prompted for credentials.")
except Exception as e:
    logger.error(f"Authentication error: {str(e)}")
    raise

# Define the Borneo region as a polygon
# (Using a simplified polygon of Borneo)
borneo_polygon = Polygon([
    (108.8, 7.3), (119.5, 7.3),
    (119.5, -4.2), (108.8, -4.2),
    (108.8, 7.3)
])

# Original subsample region
subsample_polygon = Polygon([
    (113.428345, -1.722736), (113.69751, -1.722736),
    (113.69751, -2.095175), (113.428345, -2.095175),
    (113.428345, -1.722736)
])

# Choose which region to use
use_full_borneo = True  # Set to True to process all of Borneo, False for subsample
region_to_use = borneo_polygon if use_full_borneo else subsample_polygon

    # Convert km to approximate degrees (rough approximation)
# Get the bounding box of the region
minx, miny, maxx, maxy = region_to_use.bounds


# Function to divide a region into tiles
def create_grid(polygon, tile_size_km=50):
    """
    Create a grid of smaller polygons from a large polygon

    Args:
        polygon: Shapely Polygon object
        tile_size_km: Approximate size of each tile in kilometers

    Returns:
        List of dicts with 'geometry' (Shapely Polygon) and 'id' (string)
    """
    # Get the bounds of the polygon
    minx, miny, maxx, maxy = polygon.bounds

    # Convert km to approximate degrees (rough approximation)
    tile_size_deg = tile_size_km / 111  # ~111km per degree at equator

    # Calculate number of tiles in each direction
    num_x_tiles = math.ceil((maxx - minx) / tile_size_deg)
    num_y_tiles = math.ceil((maxy - miny) / tile_size_deg)

    logger.info(f"Creating grid with {num_x_tiles}x{num_y_tiles} tiles")

    tiles = []
    for i in range(num_x_tiles):
        for j in range(num_y_tiles):
            x1 = minx + i * tile_size_deg
            y1 = miny + j * tile_size_deg
            x2 = min(minx + (i + 1) * tile_size_deg, maxx)
            y2 = min(miny + (j + 1) * tile_size_deg, maxy)

            tile_poly = Polygon([(x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)])

            # Only include tiles that intersect with the original polygon
            if polygon.intersects(tile_poly):
                tiles.append({
                    'geometry': tile_poly,
                    'id': f'tile_x{i}_y{j}',
                    'bounds': (x1, y1, x2, y2)
                })

    return tiles


# Create tiles
tiles = create_grid(region_to_use, tile_size_km=30)
logger.info(f"Created {len(tiles)} tiles for processing")

# Save tiles as GeoJSON for visualization (optional)
tile_features = []
for tile in tiles:
    tile_features.append({
        "type": "Feature",
        "geometry": mapping(tile['geometry']),
        "properties": {"id": tile['id']}
    })

geojson_output = {
    "type": "FeatureCollection",
    "features": tile_features
}

with open('borneo_tiles.geojson', 'w') as f:
    json.dump(geojson_output, f)
logger.info("Saved tiles as GeoJSON")


# Function to search and download HLS data for a single tile
def process_tile_hls(tile, collection_type, start_date, end_date, cloud_cover=10, max_results=50000):
    """
    Search and download HLS data for a specific tile

    Args:
        tile: Dict with 'geometry', 'id', and 'bounds'
        collection_type: 'L30' for Landsat or 'S30' for Sentinel
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        cloud_cover: Maximum cloud cover percentage
        max_results: Maximum number of results to download
    """
    tile_id = tile['id']
    bounds = tile['bounds']
    print(f"Processing {collection_type} for tile {tile['id']}")
    x1, y1, x2, y2 = bounds

    # Create directory for this tile
    tile_dir = os.path.join(output_dir, tile_id, collection_type)
    os.makedirs(tile_dir, exist_ok=True)

    # Create a log file for this tile
    tile_log = os.path.join(tile_dir, f"{tile_id}_{collection_type}_log.txt")
    with open(tile_log, 'a') as log:
        log.write(f"Processing started at {datetime.datetime.now()}\n")
        log.write(f"Region: {bounds}\n")

    # Determine which collection to search
    if collection_type == 'S30':
        collection_id = 'C2021957785-LPCLOUD'  # HLS Sentinel-2 collection
        short_name = 'HLSS30'
    elif collection_type == 'L30':
        collection_id = 'C2021957429-LPCLOUD'  # HLS Landsat collection
        short_name = 'HLSL30'
    else:
        logger.error(f"Unknown collection type: {collection_type}")
        return

    try:
        # Search for granules
        logger.info(f"Searching for {collection_type} data in tile {tile_id}")

        # Use earthaccess to search for data
        results = earthaccess.search_data(
            short_name=short_name,
            cloud_cover=(0, cloud_cover),
            temporal=(start_date, end_date),
            bounding_box=(x1, y1, x2, y2),
            count=max_results
        )

        num_results = len(results)
        logger.info(f"Found {num_results} {collection_type} granules for tile {tile_id}")

        with open(tile_log, 'a') as log:
            log.write(f"Found {num_results} granules\n")

        if num_results == 0:
            return

        # Save metadata about the results
        metadata_list = []
        for gran in results:
            metadata_list.append({
                'id': getattr(gran, 'uuid', None),
                'title': getattr(gran, 'native-id', None),  # Using 'native-id' as title
                'time_start': getattr(gran, 'revision-date', None),  # Using 'revision-date' for time
                'cloud_cover': getattr(gran, 'cloud_hosted', None),
                'collection_id': getattr(gran, 'collection-concept-id', None),
                'granule_ur': getattr(gran, 'native-id', None)
            })

        metadata_df = pd.DataFrame(metadata_list)
        metadata_path = os.path.join(tile_dir, f"{tile_id}_{collection_type}_metadata.csv")
        metadata_df.to_csv(metadata_path, index=False)

        # Download the granules
    # Download the granules
        # Download the granules
        import glob

        # Build list of granules that actually need downloading
        granules_to_download = []
        for granule in results:
            title = getattr(granule, 'native-id', getattr(granule, 'uuid', str(granule)))
            pattern = os.path.join(tile_dir, f"{title}*.tif")
            if glob.glob(pattern):
                logger.info(f"Granule {title} already on disk. Skipping.")
            else:
                granules_to_download.append((granule, title))

        if not granules_to_download:         logger.info("All granules already present for this tile. No download needed.")
        else:
            logger.info(f"Downloading {len(granules_to_download)}/{num_results} new granules...")
            # Extract just the granule objects for download()
            download_list = [g for g, t in granules_to_download]
            try:
                downloaded_files = earthaccess.download(
                    download_list,
                    local_path=tile_dir
                )
                logger.info(f"Download finished. Files: {downloaded_files}")
                # Optionally log each title
                with open(tile_log, 'a') as log:
                    for _, title in granules_to_download:
                        log.write(f"Downloaded {title} at {datetime.datetime.now()}\n")
            except Exception as e:
                logger.error(f"Error downloading granules: {e}")
                with open(tile_log, 'a') as log:
                    log.write(f"ERROR downloading batch: {e}\n")

            # Inner try/except just for the download step
            try:
                downloaded_files = earthaccess.download(
                    [granule],
                    local_path=tile_dir
                )

                if downloaded_files:
                    logger.info(f"Successfully downloaded {title}")
                    with open(tile_log, 'a') as log:
                        log.write(f"Successfully downloaded {title}\n")
                        log.write(f"Files: {downloaded_files}\n")
                else:
                    logger.warning(f"No files downloaded for {title}")
                    with open(tile_log, 'a') as log:
                        log.write(f"No files downloaded for {title}\n")

                time.sleep(2)

            except Exception as e:
                logger.error(f"Error downloading {title}: {str(e)}")
                with open(tile_log, 'a') as log:
                    log.write(f"ERROR downloading {title}: {str(e)}\n")

    except Exception as e:
        logger.error(f"Error processing {collection_type} for tile {tile_id}: {str(e)}")
        with open(tile_log, 'a') as log:
            log.write(f"ERROR: {str(e)}\n")

    #     for i, granule in enumerate(results):
    #         granule_id = getattr(granule, 'uuid', str(granule))
    #         title = getattr(granule, 'native-id', granule_id)            # Check if already downloaded
    #         expected_path = os.path.join(tile_dir, title)
    #         if os.path.exists(expected_path):
    #             logger.info(f"Granule {title} already downloaded. Skipping.")
    #             continue
    #
    #         logger.info(f"Downloading granule {i + 1}/{num_results}: {title}")
    #         with open(tile_log, 'a') as log:
    #             log.write(f"Downloading {title} at {datetime.datetime.now()}\n")
    #
    #         try:
    #             # Download the granule
    #             downloaded_files = earthaccess.download(
    #                 [granule],
    #                 local_path=tile_dir
    #             )
    #
    #             if downloaded_files:
    #                 logger.info(f"Successfully downloaded {title}")
    #                 with open(tile_log, 'a') as log:
    #                     log.write(f"Successfully downloaded {title}\n")
    #                     log.write(f"Files: {downloaded_files}\n")
    #             else:
    #                 logger.warning(f"No files downloaded for {title}")
    #                 with open(tile_log, 'a') as log:
    #                     log.write(f"No files downloaded for {title}\n")
    #
    #             # Add a small delay between downloads
    #             time.sleep(2)
    #
    #         except Exception as e:
    #             logger.error(f"Error downloading {title}: {str(e)}")
    #             with open(tile_log, 'a') as log:
    #                 log.write(f"ERROR downloading {title}: {str(e)}\n")
    #
    # except Exception as e:
    #     logger.error(f"Error processing {collection_type} for tile {tile_id}: {str(e)}")
    #     with open(tile_log, 'a') as log:
    #         log.write(f"ERROR: {str(e)}\n")


# Function to extract bands from HLS data
def extract_bands(tile_dir, collection_type):
    """
    Extract specific bands from HLS data

    Args:
        tile_dir: Directory containing HLS data
        collection_type: 'L30' for Landsat or 'S30' for Sentinel
    """
    # This is a placeholder function for post-processing
    # Implement according to your specific requirements
    logger.info(f"Extracting bands from {collection_type} data in {tile_dir}")
    # Implementation depends on the specific format of downloaded data


# Main processing function
def main():
    # Define date range
    start_date = '2021-07-01'
    end_date = '2024-12-31'

    # Create a summary file
    summary_file = os.path.join(output_dir, "download_summary.txt")
    with open(summary_file, 'w') as f:
        f.write(f"Download initiated at {datetime.datetime.now()}\n")
        f.write(f"Region: {'Full Borneo' if use_full_borneo else 'Subsample'}\n")
        f.write(f"Number of tiles: {len(tiles)}\n")
        f.write(f"Date range: {start_date} to {end_date}\n\n")

    # Define the collection types to process
    collection_types = ['L30', 'S30']  # L30 for Landsat, S30 for Sentinel

    # Set to True to use parallel processing
    use_parallel = False

    for ctype in collection_types:
        logger.info(f"Processing {ctype} collection")

        if use_parallel:
            # Process tiles in parallel with a limited number of workers
            with ThreadPoolExecutor(max_workers=2) as executor:
                list(executor.map(
                    lambda tile: process_tile_hls(
                        tile, ctype, start_date, end_date, cloud_cover=10, max_results=50000
                    ),
                    tiles
                ))
        else:
            # Process tiles sequentially
            for i, tile in enumerate(tiles):
                logger.info(f"Processing {ctype} data for tile {i + 1}/{len(tiles)}: {tile['id']}")

                process_tile_hls(
                    tile, ctype, start_date, end_date, cloud_cover=10, max_results=50000
                )

                # Add delay between tiles to avoid overwhelming the API
                # if i < len(tiles) - 1:
                #     time.sleep(5)  # 5 second delay between tiles

    # Update summary
    with open(summary_file, 'a') as f:
        f.write(f"Download completed at {datetime.datetime.now()}\n")


if __name__ == "__main__":
    main()