"""
Terminal commands for running model inference and training

@Time    : 2/2024
@Author  : Colm Keyes
@Email   : keyesco@tcd.ie
@File    : model_inference_terminal_commands.py
"""

# set PL_TORCH_DISTRIBUTED_BACKEND = gloo
# set NCCL_DEBUG=INFO
#
# mim train mmsegmentation --help
# mim train mmsegmentation --launcher none --gpus 1 configs/burn_scars.py
# mim train mmsegmentation --launcher pytorch --gpus 1 configs/burn_scars.py
# mim train mmsegmentation --launcher none --gpu 0 configs/burn_scars.py
#
#
#
# python model_inference.py -config "C:/Users/Lord Colm/PycharmProjects/hls-foundation-os/configs/burn_scars.py" -ckpt "E:/PycharmProjects/hls-fo
# undation-os/experiment 1/best_mIoU_iter_900.pth" -input "C:/Users/Lord Colm/Downloads/S2B_MSIL2A_20230828T210929_N0509_R057_T04QGJ_20230828T230535.SAFE/GRANULE/L2A_T04QGJ_A033831_20230828T210926/IMG_D
# ATA/" -output "C:/Users/Lord Colm/Downloads/S2B_MSIL2A_20230828T210929_N0509_R057_T04QGJ_20230828T230535.SAFE/GRANULE/L2A_T04QGJ_A033831_20230828T210926/IMG_DATA/" -input_type tif -bands "[0,1,2,3,4,5
# ]" -out_channels = 1
#
#
#
# python model_inference.py -config "E:/hls-foundation-os/configs/forest_distrubances_config.py" -ckpt "E:/PycharmProjects/hls-foundation-os/Prithvi-100m/best_mIoU_iter_30.pth" -input "E:\Data\Sentinel2_data\30pc_cc\Tiles_512_30pc_cc\\inference_test" -output "E:/" -input_type tif -bands "[0,1,2,3,4,5]"
#
#




