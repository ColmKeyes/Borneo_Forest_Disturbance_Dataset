# Borneo Forest Disturbance Dataset

A comprehensive dataset for detecting and analyzing forest disturbances in Borneo using multi-modal satellite imagery (Sentinel-1 SAR and Sentinel-2 HLS).

## Key Features

- Preprocessed Sentinel-2 HLS imagery with cloud masking
- Integrated RADD forest disturbance alerts
- Processed Sentinel-1 SAR coherence data
- Ready-to-use 512x512 tiles for deep learning
- Comprehensive preprocessing pipeline

## Installation

```bash
git clone https://github.com/ColmKeyes/Borneo_Forest_Disturbance_Dataset.git
cd Borneo_Forest_Disturbance_Dataset
pip install -e .
```

## Data Processing Pipeline

The dataset is processed through three main stages:

1. **HLS Preprocessing** (`bin/data_preprocessing_hls/`):
   - FMask cloud masking
   - Band stacking
   - RADD alert integration
   - Tile generation

2. **SAR Preprocessing** (`bin/data_preprocessing_sar/`):
   - Coherence calculation
   - Terrain correction
   - Temporal stacking

3. **Dataset Preparation** (`src/dataset_management.py`):
   - Train/validation split
   - Quality filtering
   - Metadata generation

## Data Sources

- **HLS Imagery**: NASA Harmonized Landsat Sentinel-2 (HLS) project
- **RADD Alerts**: Wageningen University's Radar for Detecting Deforestation (RADD)
- **SAR Data**: ESA Sentinel-1 missions

## Usage Example

```python
from src.dataset_management import DatasetManagement

# Initialize dataset manager
dm = DatasetManagement(
    source_dir="data/8.2.stacks_radd_forest_fmask",
    output_dir="data/9.Tiles_512"
)

# Process a single HLS stack
dm.crop_to_tiles("2023245_T50MKE_forest_masked_fmask_stack.tif")
```

## Contributing

Contributions are welcome! Please open an issue to discuss proposed changes.

## License

[MIT License](LICENSE)
