#!/usr/bin/env python
# -*- coding: utf-8 -*-

from math import sin, cos
from matplotlib.patches import Polygon, Rectangle

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

def translate_point(p, dx=0, dy=0):
    ''' translate point by the delta position dx, dy'''
    return Point(p.x + dx, p.y + dy, p.z)

def translate_seq(seq, dx=0, dy=0):
    ''' move several points by delta pos dx, dy. assumes input is a list of points'''
    return [translate_point(p, dx, dy) for p in seq]

def poly_from_seq(seq, **kwargs):
    pts = [(p.x, p.y) for p in seq]
    return Polygon(pts, **kwargs)

def xy_from_seq(seq):
    return [(p.x, p.y) for p in seq]

def find_ctr_seq(seq):
    # a lazy way to find the centre - assume shape is convex, and just find
    # the middle of the extremes.  It will give us something to start with,
    # but won't hold for complex shapes
    if not len(seq): return Point()

    # take first point as the extreme
    min_x = max_x = seq[0].x
    min_y = max_y = seq[0].y

    # then see if any improve on it
    for p in seq:
        if p.x < min_x: min_x = p.x
        if p.x > max_x: max_x = p.x
        if p.y < min_y: min_y = p.y
        if p.y > max_y: max_y = p.y

    cx = max_x - ( 0.5 * (max_x - min_x))
    cy = max_y - ( 0.5 * (max_y - min_y))
    return Point(cx, cy, 0)

def rotate_point_about_other(p, other, theta=0):
    ''' rotate point about the point 'other', by theta radians '''
    # first translate the point back to the origin
    # vector from origin to this point
    tx =  (p.x - other.x)
    ty =  (p.y - other.y)
    #print "ctr of rotation: ({:.3f}, {:.3f})".format(other.x, other.y)
    #print "point to rotate: ({:.3f}, {:.3f})".format(tx, ty)
    #P = Point(p.x, p.y, p.z)
    #P = translate_point(P, -tx, -ty)
    #print "point at origin: ({:.3f}, {:.3f})".format(P.x, P.y)
    # then rotate it by theta degrees
    Q = Point()
    Q.x = (tx * cos(theta)) - (ty * sin(theta)) + other.x
    Q.y = (tx * sin(theta)) + (ty * cos(theta)) + other.y
    ## now translate back
    #R = translate_point(Q, tx, ty)
    #print "rotated : ({:.3f}, {:.3f})".format(Q.x, Q.y)
    return Q

def rotate_polygon(poly, ctr, theta):
    ''' return a sequence of points rotated about the position 'ctr' '''
    return [rotate_point_about_other(p, ctr, theta) for p in poly]

def rotate_group_about_ctr(poly_group, theta, ctr=None):
    ''' find the centre of the group and rotate all elements about the ctr'''
    # find centre of all points in the group into one list,
    if ctr is None:
        ctr = find_ctr_seq([item for sublist in poly_group for item in sublist])
    rotated_poly_group = []
    for poly in poly_group:
        r_seg = [ rotate_point_about_other(p, ctr, theta) for p in poly]
        rotated_poly_group.append(r_seg)

    return rotated_poly_group

def translate_group(poly_group, dx=0, dy=0):
    return [translate_seq(seg, dx=dx, dy=dy) for seg in poly_group]


def apply_transform_to_group(poly_group, trans):
    '''
    transforms can include a translation and a rotation, as defined by
    `trans`, a Transformation instance.

    the rotation is applied first, about the centre of the group, and then
    the whole rotated group is translated.
    '''
    return (translate_group(
        rotate_group_about_ctr(poly_group, trans.theta),
        dx=trans.dx, dy=trans.dy)
    )


def rotate_point(p, theta=0):
    ''' rotate point about the origin, by theta radians '''
    # well if we are already in global coordinates, then translating to
    # the origin is going to be the same for all points and nothing happens
    # so lets see if we simply rotate all the points - does that give us
    # the right new shape?
    P = Point(p.x, p.y, p.z)
    # then rotate it by theta degrees
    Q = Point()
    Q.x = P.x * cos(theta) + P.y * sin(theta)
    Q.y = P.y * cos(theta) - P.x * sin(theta)
    return Q

#{{{ a very simple point class
class Point(object):
    '''
    simple 3d point container/representation allows addition of positions
    and not much more'''
    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z

    def abs(self):
        ''' return magnitude of length of vector from origin'''
        return (self.x**2 + self.y**2 + self.z**2 )**0.5

    def __add__(self, other):
        return Point(
                x=self.x + other.x,
                y=self.y + other.y,
                z=self.z + other.z)

    def __sub__(self, other):
        return Point(
                x=self.x - other.x,
                y=self.y - other.y,
                z=self.z - other.z)
    def __str__(self):
        return "Point at ({:{fmt}},{:{fmt}},{:{fmt}})".format(self.x, self.y, self.z, fmt='6.3f')

    def __repr__(self):
        return self.__str__()

#}}}

#{{{ simple transformation container class
class Transformation(object):
    '''
    simple container object to consistently store parameters relating
    to a transformation
    '''
    def __init__(self, dx=0, dy=0, theta=0):
        self.dx      = dx
        self.dy      = dy
        self.theta = theta

    def __str__(self):
        s =  "Transformation: Rotate by {{:{fmt}} and translate "
        "by ({:{fmt}}, {:{fmt}})".format(self.theta, self.dx, self.dy)
#}}}
