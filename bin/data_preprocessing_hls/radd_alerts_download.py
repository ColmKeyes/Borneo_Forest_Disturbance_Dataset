import ee
import geemap
import os
import datetime

ee.Initialize(project="biomass-estimation-439322")

# Define Borneo region coordinates
borneo_coords = [
    [108.8, 7.3], [119.5, 7.3],
    [119.5, -4.2], [108.8, -4.2],
    [108.8, 7.3]
]
roi = ee.Geometry.Polygon(borneo_coords)

# Date range for alerts
start_date = '2000-01-01'
end_date = '2030-12-31'

# Download settings
scale = 30  # meters
local_output_dir = 'data/radd_alerts'

# --- Earth Engine Initialization ---
try:
    # Initialize geemap and Earth Engine
    # geemap.ee_initialize() will attempt to authenticate if needed
    # geemap.ee_initialize()
    print("Earth Engine Initialized Successfully.")
except Exception as e:
    print(f"Error initializing Earth Engine: {e}")
    exit()

# --- Access RADD Data ---
radd_collection_id = 'projects/radar-wur/raddalert/v1'
radd = ee.ImageCollection(radd_collection_id)
print(f"Accessing RADD collection: {radd_collection_id}")

# --- Debugging and Verification ---
# First verify the collection exists and has data
print("\nVerifying RADD collection...")
print(f"Total images in collection: {radd.size().getInfo()}")

# Print first few image IDs to verify access
print("\nSample image IDs in collection:")
for img in radd.limit(5).getInfo()['features']:
    print(img['id'])

# --- Filter and Select Latest Alert ---
print(f"\nFiltering for date range={start_date} to {end_date}")
filtered_radd = radd.filterDate(start_date, end_date) \
                   .filterBounds(roi)

print(f"Images after filtering: {filtered_radd.size().getInfo()}")

# Check available layer types
print("\nAvailable layer types in filtered images:")
layer_types = filtered_radd.aggregate_array('layer').getInfo()
print(set(layer_types))

# Try alternative layer names that might contain alerts
possible_alert_layers = ['alerts', 'alert', 'disturbance', 'change', 'forest_alert']
alert_images = None

for layer_name in possible_alert_layers:
    temp_images = filtered_radd.filter(ee.Filter.eq('layer', layer_name))
    count = temp_images.size().getInfo()
    if count > 0:
        alert_images = temp_images
        print(f"Found {count} alert images using layer name: '{layer_name}'")
        break

if alert_images:
    print(f"Total alert images found: {alert_images.size().getInfo()}")
    # Print available metadata properties for debugging
    sample_img = alert_images.first()
    print("\nSample alert image properties:")
    print(f"ID: {sample_img.id().getInfo()}")
    print(f"Date: {sample_img.date().format('YYYY-MM-dd').getInfo()}")
    print(f"Available properties: {sample_img.propertyNames().getInfo()}")
    latest_radd_alert = alert_images.sort('system:time_end', False).first()
    print('Latest RADD alert image found within the date range:', latest_radd_alert.id().getInfo())

    # Get version date for the description
    try:
        version_date = latest_radd_alert.get('version_date').getInfo()
        filename_base = f'radd_alerts_borneo_v{version_date}'
    except Exception as e:
        print(f"Could not get version_date: {e}")
        filename_base = f'radd_alerts_borneo_{datetime.datetime.now().strftime("%Y%m%d")}'

    # --- Download Locally ---
    # Ensure the local output directory exists
    os.makedirs(local_output_dir, exist_ok=True)
    filename = os.path.join(local_output_dir, f"{filename_base}.tif")

    print(f"Starting download to local file: {filename}")

    # Use geemap.ee_export_image for direct download
    # Note: This function blocks until the download is complete or fails.
    # For large areas, this might take a long time. Consider tiling if needed.
    geemap.download_ee_image(
        image=latest_radd_alert,
        filename=filename,
        region=roi,
        scale=scale,
        crs='EPSG:4326' # Using EPSG:4326 as in the JS example
    )

    print(f"Download complete. File saved to: {filename}")

else:
    print(f"No RADD alert images found for date range '{start_date}' to '{end_date}' in the specified Borneo region.")

# --- Optional: Add Forest Baseline (as in JS example) ---
# If you need the forest baseline layer as well:
# try:
#     forest_baseline = ee.Image(radd.filterMetadata('layer','contains','forest_baseline')
#                                 .filterMetadata('geography','contains',geography).first())
#     print('Forest baseline image:', forest_baseline.id().getInfo())
#     # You could export this separately if needed
#     # task_baseline = geemap.ee_export_image_to_drive(...)
# except Exception as e:
#     print(f"Could not load forest baseline: {e}")

print("Script finished.")
print("Script finished.")
