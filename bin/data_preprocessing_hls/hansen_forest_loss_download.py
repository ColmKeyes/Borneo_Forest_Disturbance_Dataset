#!/usr/bin/env python
import ee
import geemap
import os
import math
import rasterio
from rasterio.merge import merge


def subdivide_bbox(xmin, ymin, xmax, ymax, max_tile_width, max_tile_height):
    """Subdivide a bounding box into tiles that do not exceed max_tile_width/height."""
    x_tiles = math.ceil((xmax - xmin) / max_tile_width)
    y_tiles = math.ceil((ymax - ymin) / max_tile_height)
    tiles = []
    for i in range(x_tiles):
        for j in range(y_tiles):
            tile_xmin = xmin + i * max_tile_width
            tile_xmax = min(xmin + (i + 1) * max_tile_width, xmax)
            tile_ymin = ymin + j * max_tile_height
            tile_ymax = min(ymin + (j + 1) * max_tile_height, ymax)
            tiles.append((tile_xmin, tile_ymin, tile_xmax, tile_ymax))
    return tiles


def export_tile(image, tile_region, scale, crs, outfile):
    """
    Export the given image (an ee.Image) for a tile region to outfile.
    This function is blocking.
    """
    print(f"Exporting tile to {outfile} with region: {tile_region.coordinates().getInfo()}")
    geemap.ee_export_image(
        image,
        outfile,
        scale=scale,
        region=tile_region,
        crs=crs,
        file_per_band=False
    )
    print(f"Exported {outfile}")


def main():
    # Initialize Earth Engine with your project.
    ee.Initialize(project="biomass-estimation-439322")

    # Define the Borneo ROI coordinates and create an EE polygon.
    borneo_coords = [
        [108.8, 7.3], [119.5, 7.3],
        [119.5, -4.2], [108.8, -4.2],
        [108.8, 7.3]
    ]
    roi = ee.Geometry.Polygon(borneo_coords)

    # Get the bounding box of the ROI.
    bbox = roi.bounds().getInfo()['coordinates'][0]
    # bbox is a list of coordinates: [[xmin, ymin], [xmax, ymin], [xmax, ymax], [xmin, ymax], [xmin, ymin]]
    xmin, ymin = bbox[0]
    xmax, ymax = bbox[2]

    # Define maximum tile size in degrees.
    # At 30 m resolution, 32768 pixels correspond roughly to 983 km; at the equator 1° ~ 111 km,
    # so maximum size in degrees ~983000/111000 ≈ 8.86°.
    max_tile_width = 12
    max_tile_height = 12

    # Subdivide the bounding box into tiles.
    tiles = subdivide_bbox(xmin, ymin, xmax, ymax, max_tile_width, max_tile_height)
    print(f"Subdivided ROI into {len(tiles)} tiles.")

    # Load the Hansen dataset and select the 'lossyear' band.
    hansen_img = ee.Image('UMD/hansen/global_forest_change_2023_v1_11').select('lossyear')

    # Create output directories.
    base_dir = os.path.join("data", "hansen_treecover")
    tiles_dir = os.path.join(base_dir, "tiles")
    os.makedirs(tiles_dir, exist_ok=True)

    # Export settings.
    scale = 30  # 30 m resolution
    crs = 'EPSG:4326'

    # Export each tile and collect filenames.
    tile_files = []
    for idx, tile_bbox in enumerate(tiles):
        tile_region = ee.Geometry.Rectangle(tile_bbox)
        outfile = os.path.join(tiles_dir, f"hansen_loss_tile_{idx}.tif")
        export_tile(hansen_img, tile_region, scale, crs, outfile)
        tile_files.append(outfile)

    # Mosaic the downloaded tiles together.
    src_files_to_mosaic = []
    for fp in tile_files:
        src = rasterio.open(fp)
        src_files_to_mosaic.append(src)

    print("Merging tiles...")
    mosaic, out_trans = merge(src_files_to_mosaic)

    # Take the profile from one of the tiles, update with mosaic dimensions and transform.
    out_meta = src_files_to_mosaic[0].meta.copy()
    out_meta.update({
        "driver": "GTiff",
        "height": mosaic.shape[1],
        "width": mosaic.shape[2],
        "transform": out_trans,
        "count": mosaic.shape[0]
    })

    # Write the mosaic to a new file within the 'data/hansen_treecover' folder.
    mosaic_out = os.path.join(base_dir, "hansen_tree_loss_mosaic.tif")
    with rasterio.open(mosaic_out, "w", **out_meta) as dest:
        dest.write(mosaic)

    print(f"Mosaic completed and saved to {mosaic_out}")

    # Close the source files.
    for src in src_files_to_mosaic:
        src.close()


if __name__ == "__main__":
    main()
