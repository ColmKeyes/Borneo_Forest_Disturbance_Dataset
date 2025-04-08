# -*- coding: utf-8 -*-
"""
Updates configuration settings and runs model training.
used to ensure reset of model image norm from datasets with alternative data values

@Time    : 2/2024
@Author  : Colm Keyes
@Email   : keyesco@tcd.ie
@File    : run_config.py
"""

import os
from mmseg.apis import train_segmentor, init_segmentor, inference_segmentor
from mmcv import Config

# Update the config file
cfg_path = r"E:\hls-foundation-os\Experiment_2\updated_config.py"
cfg = Config.fromfile(cfg_path)

# Update data root directory
cfg.data_root = r"E:\Data\Sentinel2_data\30pc_cc\Tiles_512_30pc_cc"

# Update pre-trained weights path
cfg.pretrained_weights_path = r"E:\\Prithvi_100M.pt"

# Update experiment name
cfg.experiment = "Experiment_2"

# Update project directory
cfg.project_dir = "E:\hls-foundation-os"

# Update number of samples per GPU
cfg.samples_per_gpu = 8

# Update image normalization config
cfg.img_norm_cfg = dict(
    means=[190.25926138433516, 429.89401106101735, 263.64892182260917, 2914.742437197362, 1436.1499327360475, 552.0405896092034],
    stds=[147.77000967917303, 181.20171057982083, 215.94822142698277, 560.9504799450765, 380.71293248398223, 229.565368633047],
)

# Update bands
cfg.bands = [0, 1, 2,3,4,5]

# Update classes
cfg.CLASSES = ("Forest", "Disturbed_Forest")

# Update optimizer settings
cfg.optimizer = dict(type="Adam", lr=1.3e-05, betas=(0.9, 0.999))

# Update learning rate scheduler config
cfg.lr_config = dict(
    policy="poly",
    warmup="linear",
    warmup_iters=1500,
    warmup_ratio=1e-06,
    power=1.0,
    min_lr=0.0,
    by_epoch=False
)

# Save the updated config file
#cfg.dump(os.path.join(cfg.project_dir, cfg.experiment, "updated_config.py"))

# Initialize and train the segmentor
model = init_segmentor(cfg, device='cuda:0')
train_segmentor(model, cfg.data.train, cfg)

# For inference, you can use the following
# results = inference_segmentor(model, "/path/to/your/test/image")



