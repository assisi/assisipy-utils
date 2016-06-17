#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Author   : Rob Mills, BioISI, FCUL.
         : ASSISIbf project

Abstract : Simple library to enable/aid rendering of arena elements in
         : matplotlib rather than in the assisi playground directly.
         :
         : Typical usage includes in conjunction with analysis
'''


from matplotlib.patches import Polygon #, Rectangle
import matplotlib.pyplot as plt


def poly_from_seq(seq, **kwargs):
    # assumes that seq is a list of Point elements (see transforms.Point)
    pts = [(p.x, p.y) for p in seq]
    return Polygon(pts, **kwargs)

def render_arena(arena, ax=None, fc='b'):
    if ax is None:
        ax = plt.gca()
    for seg in arena:
        patch = poly_from_seq(seg, facecolor=fc, edgecolor='k')
        ax.add_patch(patch)

def render_CASUs(casu_poses, ax=None, fc='w', mew=3):
    if ax is None:
        ax = plt.gca()
    h = []
    for (p, yaw) in casu_poses:
        # print "scattering point at", p.x, p.y
        h.append (ax.scatter(x=p.x, y=p.y, marker='h', s=400, c=fc, linewidth=mew))
    return h
