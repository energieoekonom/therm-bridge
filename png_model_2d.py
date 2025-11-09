#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 28 13:13:28 2024

@author: economist

Reads png image representing a cross section of material to model
accompanied by a CSV file having grayscale to heat conductivity mappings.

Sample command line:
    png_model_2d.py -pixel_step=10 svg/bridge_plain.png

"""

import sys
import argparse
from pathlib import Path

import img.png_to_matrix as pngm
import img.value_map as pnvm

# import libraries for numerical functions and plotting
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import eqtn.elliptic_system as els

# these lines are only for helping improve the display
import matplotlib_inline.backend_inline
matplotlib_inline.backend_inline.set_matplotlib_formats('pdf', 'png')
plt.rcParams['figure.dpi']= 300
plt.rcParams['savefig.dpi'] = 300

argv = sys.argv[1:]

parser = argparse.ArgumentParser()
parser.add_argument('-pixel_step', type=int, default=10)
parser.add_argument('-print_values_only', type=int, default=0)
parser.add_argument('-csv_dump', type=int, default=0)
parser.add_argument('-T_i', type=float, default=20.0)
parser.add_argument('-T_e', type=float, default=-10.0)
parser.add_argument('pngimage', type=str)

args = parser.parse_args(argv)

def flip_vertical(A):
    """
    flips matrix along axis 0

    Parameters
    ----------
    A : array
        input matrix.

    Returns
    -------
    A_flip : array
        flipped matrix.

    """
    cy = A.shape[0]
    A_flip = A[np.arange(cy)[::-1],:]
    return A_flip

def print_pixel_portions(v,c,vm):
    """
    prints a breakdown of materials mapped in the input image

    Parameters
    ----------
    v : list
        list of luminosity values found in grayscale image.
    c : list
        list of counts of pixels having a luminosity.
    vm : dict
        value map from luminosity to material description.

    Returns
    -------
    None.

    """
    percent = c/sum(c)*100
    for zv,zc in zip(v,percent):
        model = vm[zv]
        fix = ''
        if model.isFix():
            fix = ' fix'
        print(f"{zv:.3f} -> {model.getUValue()}, {model.getDescription()}{fix}: {zc:.2f}%")

def floor_at(image, max):
    image = np.array(image)
    mask = image > max
    image[mask] = max
    return image

def png_model2d(args):
    """
    runs the 2d finite difference model with parameters from command line

    Parameters
    ----------
    args : namespace
        parameters passed from command line.

    Raises
    ------
    ValueError
        unspecified error condition.

    Returns
    -------
    int

    """
    print_values_only = args.print_values_only == 1

    grayimage2d = pngm.read_grayscale_2d(args.pngimage)
    pixelpicked2d = pngm.matrix_to_pix(grayimage2d, args.pixel_step)
    
    v_grayimage2d, c_grayimage2d = np.unique(grayimage2d, return_counts=True)
    v_pixelpicked2d, c_pixelpicked2d = np.unique(pixelpicked2d, return_counts=True)

    if print_values_only:
        with np.printoptions(precision=4, suppress=True):
            print("Colors and counts in image:")
            print(np.vstack((v_grayimage2d, c_grayimage2d)).T)
            print(f"Reduced image / pixel matrix size: {pixelpicked2d.shape}")
            print("Colors and counts in pixelmatrix:")
            print(np.vstack((v_pixelpicked2d,c_pixelpicked2d)).T)
 
    if len(v_grayimage2d) != len(v_pixelpicked2d):
        raise ValueError(f"error in image or pixel picking."
                         f" Did you export with anti-aliasing?"
                         f" Have {len(v_grayimage2d)} values in original,"
                         f" {len(v_pixelpicked2d)} in reduced x {args.pixel_step}")
    
    if print_values_only:
        return 1

    path = Path(args.pngimage)
    imgBaseName = path.stem
    
    wallThickness = pnvm.get_wall_thickness(f"{args.pngimage}.csv")
    
    print(f"Wall thickness [m]: {wallThickness.getPixelValue()}")
    print("")    
    value_map = pnvm.generate_value_map(v_grayimage2d, f"{args.pngimage}.csv")

    print("grayimage wall portions")
    print_pixel_portions(v_grayimage2d, c_grayimage2d, value_map)
    print("")
    print("pixelpicked downscale in comparison")
    print_pixel_portions(v_pixelpicked2d, c_pixelpicked2d, value_map)
        
    ###########################################################
    # now the fun bit: the numerical approximation :)
    ###########################################################
        
    inf_cond = 1e9
    # first, add temperature defining first and last rows to the matrix sized
    # 'image'. These can then be initialized with inner and outer temperatures
    # in the computation and get infinite heat conductivity.
    p2d = pixelpicked2d # handier alias
    p2d = np.insert(p2d, 0, inf_cond, axis=0)
    p2d = np.insert(p2d, p2d.shape[0], inf_cond, axis=0)
    # now replace the luminosities from the image by their mapped
    # heat conductivities.
    p2dm = np.array(p2d)
    for v in value_map.keys():
        mask = p2d == v
        p2dm[mask] = value_map[v].getUValue()
    
    # now set up the equation system
    shape_A = p2dm.size
    (cy,cx) = p2dm.shape

    A = els.fill_system_weights(p2dm)
    els.set_identity(A, cx)
    
    # boundary conditions - per default equations resolve to zero
    # but can set temperature of chosen nodes
    # first row temperatures
    T_i, T_e = args.T_i, args.T_e
    b = els.create_system_results(shape_A, cx, T_i, T_e)
    
    u = np.linalg.solve(A, b)
    u_square = u.reshape((cy,cx))
    
    u_square_flip = flip_vertical(u_square)
    p2dm_flip = flip_vertical(p2dm)
    p2dm_flip_floor = floor_at(p2dm_flip, 1.5)
    
    # https://matplotlib.org/stable/users/explain/colors/colormaps.html
    plt.contourf(p2dm_flip_floor, levels=80, cmap='inferno')
    plt.colorbar()
    plt.savefig(f"{imgBaseName}.mat_contour.png")
    plt.show()

    plt.contourf(u_square_flip, levels=80, cmap='plasma')
    plt.colorbar()
    plt.savefig(f"{imgBaseName}.temp_contour.png")
    plt.show()
    
    if args.csv_dump == 1:
        mat_df = pd.DataFrame(p2dm)
        mat_df.to_csv(f"{imgBaseName}.mat_contour.csv", index=True)
        temp_df = pd.DataFrame(u_square)
        temp_df.to_csv(f"{imgBaseName}.temp_contour.csv", index=True)
            
    return 0
    
    



def main(args):
    ret = png_model2d(args)
    return ret

try:
    v = main(args)
    sys.exit(v)
except Exception as ex:
    print(f"Exception: {ex}")
    print("terminating exit(1)")
    sys.exit(1)

