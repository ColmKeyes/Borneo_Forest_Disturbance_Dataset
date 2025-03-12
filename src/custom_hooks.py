# -*- coding: utf-8 -*-
"""
Custom Hooks for Visualization
"""
"""
@Time    : 25/01/2024 22:23
@Author  : Colm Keyes
@Email   : keyesco@tcd.ie
@File    : custom_hooks
"""

import mmcv
import numpy as np
from mmengine.registry import HOOKS
from mmengine.hooks import Hook
# from mmseg.core.hook import
from mmcv.runner import Hook, HOOKS
import matplotlib.pyplot as plt
# from mmcv.utils.registry import

@HOOKS.register_module()
class PlotIterationHook(Hook):
    def __init__(self, interval=100):
        self.interval = interval

    # def every_n_iters(self, runner, n):
    #     return (runner.iter + 1) % n == 0 if n > 0 else False

    def after_train_iter(self, runner):
        if (runner.iter + 1) % self.interval == 0:
            # Fetch data and output from runner
            data_batch = runner.data_batch
            model_output = runner.outputs

            img = data_batch['img'].data[0].cpu().numpy()
            img = img.transpose(1, 2, 0)  # Assuming PyTorch format (C, H, W) to (H, W, C)


            # Plotting
            plt.figure(figsize=(12, 6))
            plt.subplot(1, 2, 1)
            plt.imshow(img)
            plt.title(f'Input Image at Iteration {runner.iter}')

