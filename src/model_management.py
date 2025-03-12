# -*- coding: utf-8 -*-
"""
This script provides analysis and preprocessing of Sentinel-2 HLS imagery data.

@Time    : 19/03/2023 23:20
@Author  : Colm Keyes,
@Email   : keyesco@tcd.ie
@File    : model_management
"""
####################
## Resetting Model Weights
####################

import torch

def reset_weights(model_dict, layer_name, device='cpu'):
    """Reset the weights of a specific layer and keep the dimensions."""
    for name, param in model_dict.items():
        if layer_name in name:
            print(f"Original shape of {name}: {param.shape}")
            model_dict[name] = torch.randn(param.shape).to(device)
            print(f"Updated shape of {name}: {model_dict[name].shape}")
    return model_dict

def compare_checkpoints(original_checkpoint_path, updated_checkpoint_path):
    """Compare the weights of two checkpoints and display detailed changes."""
    original_checkpoint = torch.load(original_checkpoint_path, map_location='cpu')
    updated_checkpoint = torch.load(updated_checkpoint_path, map_location='cpu')

    for key in original_checkpoint['state_dict']:
        if key in updated_checkpoint['state_dict']:
            original_value = original_checkpoint['state_dict'][key]
            updated_value = updated_checkpoint['state_dict'][key]
            # Ensure we compare tensors of the same shape
            if original_value.shape != updated_value.shape:
                print(f"Shape mismatch for: {key}")
                print(f"Original shape: {original_value.shape}")
                print(f"Updated shape: {updated_value.shape}")
            elif not torch.equal(original_value, updated_value):
                print(f"Value changed for: {key}")
                # Display a subset of the tensor values for comparison
                print(f"Original value sample: {original_value.flatten()[:10]}")
                print(f"Updated value sample: {updated_value.flatten()[:10]}")

# Load the checkpoint
checkpoint_path = r'E:\burn_scars_Prithvi_100M.pth'
checkpoint = torch.load(checkpoint_path, map_location='cpu')

# Reset weights for specific layers
# layers_to_reset = ['decode_head.conv_seg.weight', 'decode_head.conv_seg.bias']
# for layer in layers_to_reset:
#     checkpoint['state_dict'] = reset_weights(checkpoint['state_dict'], layer)

# Save the updated checkpoint
updated_checkpoint_path = r'E:\burn_scars_Prithvi_100M_reset.pth'
# torch.save(checkpoint, updated_checkpoint_path)

# Compare the original and updated checkpoints
compare_checkpoints(checkpoint_path, updated_checkpoint_path)