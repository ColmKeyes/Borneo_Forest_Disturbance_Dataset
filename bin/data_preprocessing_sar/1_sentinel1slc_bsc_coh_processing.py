# -*- coding: utf-8 -*-
"""
This script processes SLC data to coherence or backscatter GeoTiffs
"""
"""
@Time    : 18/01/2023 16:02
@Author  : Colm Keyes
@Email   : keyesco@tcd.ie
@File    : Backscatter_Preprocessing
"""
"""
`sentinel1_spacing` represents the pixel spacing of the SLC data.
The window sizes and corresponding pixel spacing values are as follows:
[2,8] (28.08 m), [3,12] (42.12 m), [4,15] (56.16 m),
[9,34] (126.36 m), [14,53] (196.56 m), [18,69] (252.72 m)
window size * sentinel1_spacing = pixel spacing
- This section on calcualting firstly the correct resolution for IW2 and then determining the pixel spacing 

"""
import sys
sys.path.append(r'C:\Users\Lord Colm\PycharmProjects\Sentinel-1-Coherence-pipeline\src')
import sentinel1slc as slc

# Define input parameters
pols = ['VH',"VV"]  # 'VH,VV'
sentinel1_GroundRange_resolution = [14.04, 3.68]  ## this is the slant range resolution, not the ground range.
sentinel1_SlantRange_resolution = [2.7, 22]
iw_swath = 'IW1'
first_burst_index = 4
mode = 'coherence'
last_burst_index = 7
product_type = 'GeoTIFF'
window_size = [[2, 8]]#, [3, 12], [4, 15], [9, 34], [14, 53], [18, 69]]

tile = "T49MCV" #"T50MKE" #"T49MDU"#"T49MHU"#"T49MET" #"T49MCV" #"T50NLF"
SLC_path = f"E:\\Data\\SLC\\Prithvi_borneo_tiles\\{tile}"
path_asf_csv = f"E:\\Data\\SLC\\Prithvi_borneo_tiles\\{tile}\\asf_sbas_pairs_{tile}.csv"
outpath = f"E:\\Data\\Results\\prithvi_sar\\{tile}"
if mode == 'backscatter':
    outpath_window = '_backscatter_multilook_window_'
elif mode == 'coherence':
    outpath_window = '_coherence_window_'

# Loop over polarizations and window sizes
for iy, pols in enumerate(pols):
    for ix, i in enumerate(window_size):
        slc.main(pols,
                 iw_swath,
                 first_burst_index,
                 last_burst_index,
                 window_size[ix],

                 mode=mode,
                 speckle_filter='Lee',
                 speckle_filter_size=[5, 5],
                 product_type=product_type,
                 outpath=outpath + '\\' + str(int(sentinel1_GroundRange_resolution[0] * window_size[ix][0])) + 'm_window'
                         + '\\pol_' + str(pols) + str(outpath_window)
                         + str(int(sentinel1_GroundRange_resolution[0] * window_size[ix][0])),
                 SLC_path=SLC_path,
                 path_asf_csv=path_asf_csv
                 )



