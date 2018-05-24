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


from matplotlib.patches import Polygon, Rectangle
import matplotlib.pyplot as plt
from transforms import Point, translate_group, rotate_group_about_ctr


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

def valid_area_to_rect(bounds, angle=0, **kwargs):
    ''' just checking that I got the bounds in the right place post-transforms'''
    bl, tr = bounds
    # rectangle form is "bottom left, width, height
    width  = tr[0] - bl[0]
    height = tr[1] - bl[1]

    # for some reason the age of MPL makes a difference (maybe?) as to whether
    # rectangle can take an angle or not
    #return Rectangle(bl, width=width, height=height, angle=angle, **kwargs)
    return Rectangle(bl, width=width, height=height, **kwargs)

def trans_valid_area_to_rect(bounds, trans, **kwargs):
    ''' elaborated version that provides a rect in the transformed position '''
    bl = Point(*bounds[0])
    tr = Point(*bounds[1])
    # apply transformation to the bounds
    poly = [bl, Point(bl.x, tr.y), tr, Point(tr.x, bl.y)]
    seq = [poly, ]
    # transform the polygon
    seq_tr = translate_group(
            rotate_group_about_ctr(seq, trans.theta), trans.dx, trans.dy
            )
    return poly_from_seq(seq_tr[0], **kwargs)

