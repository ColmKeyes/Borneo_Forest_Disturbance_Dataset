Borneo Forest Disturbance Dataset

## Project Overview
This project focuses on validating and improving the quality of a forest disturbance dataset for deep learning applications. The goal is to prepare the dataset for hosting on Huggingface by ensuring proper preprocessing and implementing comprehensive quality metrics.

## Documentation Progress
- [x] Created Agent_summary.md
- [x] Created ARCHITECTURE.md with Mermaid diagram
- [x] Created DOCS.md with file-level documentation and implementation rationale

## Project Structure
```
Borneo_Forest_Disturbance_Dataset/
├── bin/                     # Processing pipeline scripts
│   ├── data_preprocessing_hls/  # RGB data processing
│   ├── data_preprocessing_sar/  # SAR data processing
│   ├── run_analysis/        # Analysis scripts
│   └── run_model/           # Model running scripts
├── src/                     # Core processing modules
│   ├── dataset_management.py
│   ├── hls_stacks_prep.py
│   ├── model_analysis.py
│   ├── model_input_processor.py
│   └── utility_functions.py
├── docs/                    # Documentation files
│   ├── Agent_summary.md
│   ├── ARCHITECTURE.md
│   └── DOCS.md
└── README.md                # Project documentation
```

## Processing Pipelines
1. RGB Data Pipeline (Sentinel-2)
2. SAR Data Pipeline (Sentinel-1)
3. InSAR Data Pipeline (Sentinel-1)

## Tasks
### Completed
- [x] Project overview and requirements analysis
- [x] Initial README creation
- [x] System architecture documentation
- [x] Comprehensive technical documentation

### In Progress
- [ ] RGB pipeline assessment
- [ ] Data quality evaluation implementation

### Pending
- [ ] SAR pipeline assessment
- [ ] InSAR pipeline assessment
- [ ] Model evaluation integration
- [ ] Final documentation updates

## Technical Questions
1. Are there specific quality thresholds for pixel values that should be enforced?
2. Should we implement additional data augmentation steps?
3. What specific metrics are most important for Huggingface dataset hosting?

## Git Setup Instructions

1. Initialize Git repository:
```bash
cd Borneo_Forest_Disturbance_Dataset
git init
```

2. Add all files:
```bash
git add .
```

3. Make initial commit:
```bash
git commit -m "Initial commit: Project setup with documentation and package structure"
```

## Git Commit History
- Initial commit: Created project structure and README
- Documentation update: Added comprehensive documentation files
- Git setup: Added .gitignore and package initialization files
- HLS Preprocessing Update: Updated .gitignore to exclude HLS data directory and pushed updated HLS preprocessing scripts.
