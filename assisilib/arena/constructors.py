#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Author   : Rob Mills, BioISI, FCUL.
         : ASSISIbf project

Abstract : Constructor classes of enclosures for agents.


'''

#from math import pi, sin, cos
from math import pi

from transforms import Point
from transforms import rotate_polygon, translate_seq, apply_transform_to_group, xy_from_seq

from minimal_arenas import create_arc_with_width


ORIGIN = (0, 0, 0)


#{{{ Base class
class BaseArena(object):
    def __init__(self, ww=1.0, **kwargs):

        self.ww = ww

        self.bl_bound = (0,0)
        self.tr_bound = (0,0)

        self.segs = []
        self.color      = kwargs.get('color', (0.5, 0.5, 0.5))
        self.label_stub = kwargs.get('label_stub', 'arena')
        self.height     = kwargs.get('height', 1.0)

    # not much point in getter/setter is there
    def set_wall_color(self, clr):
        self.color = clr

    def transform(self, trans):
        ''' apply transform to segments, in place '''
        self.segs = apply_transform_to_group(self.segs, trans)

    def transformed(self, trans):
        '''
        hmm, what does this mean
        apply a transform to a COPY of segments, and return/
        '''
        return apply_transform_to_group(self.segs, trans)

    def get_valid_zone(self):
        return  (self.bl_bound, self.tr_bound)

    def get_valid_zone_rect(self):
        '''
        return parameters xy, xspan, yspan suitable for rendering a rectangle
        by matplotlib.patches.Rectangle (or similar).
        '''
        dx = (self.tr_bound[0] - self.bl_bound[0])
        dy = (self.tr_bound[1] - self.bl_bound[1])
        return self.bl_bound, dx, dy

    def _spawn_polygon(self, simctrl, poly, label,
                       height=1, color=(0,0,1)):
        simctrl.spawn('Physical', label, ORIGIN, polygon=poly, color=color,
                      height=height)


    def spawn(self, simctrl, verb=False, offset=0):
        '''
        spawn the arena in the ASSISI playground instance with handle `simctrl`.
        The segments obtain names with numerical suffix. Optional int argument
        `offset` increments the starting index.
        '''

        for i, poly in enumerate(self.segs):
            label = "{}-{:03d}".format(self.label_stub, i+offset)
            pts = xy_from_seq(poly)

            self._spawn_polygon(simctrl, pts, label, height=self.height, color=self.color)

#}}}

#{{{ StadiumArena
class StadiumArena(BaseArena):
    def __init__(self, width=6.0, length=16.0, arc_steps=9, ww=1.0,
                 bee_len=1.5,
                 **kwargs):
        '''
        A rectangle with semi-circular ends.  This corresponds to one of the
        enclosures used in the Graz bee lab, and is suitable for two CASUs.

        By default, this arena will be positioned horizontally, about (0, 0).
        Transforms can be applied.

        '''
        super(StadiumArena, self).__init__(ww=ww, **kwargs)
        self.width = width
        self.length = length


        # compute geometry
        arc_rad = width / 2.0 - ww / 2.0
        l_middle_seg = length - width # 2 * arc_rad

        # create polygons for the two long/parallel walls
        #wall_long  = ( (0, 0), (l_middle_seg, 0),  (l_middle_seg, ww), (0, ww), (0, 0) )
        lms = l_middle_seg # shorthand
        wall_long  = ( (-lms/2.0, -ww/2.0), (+lms/2.0, -ww/2.0),
                    (+lms/2.0, +ww/2.0), (-lms/2.0, +ww/2.0),
                    (-lms/2.0, -ww/2.0))

        poly_wl     =  [Point(x, y, 0) for (x, y) in wall_long]
        s  = [(0,  -width/2.0+ww/2.0,     0),          poly_wl]
        n  = [(0,  +width/2.0-ww/2.0,     0),          poly_wl]


        # now we need two arcs.
        # centre of the RH arc is ...
        # c_r = [(ex+2)*l , 3*l / 2.0 ]
        # c_l = [(0,        3*l / 2.0 ]
        arc_r = create_arc_with_width(cx=+lms/2.0, cy=0,
                                    radius=arc_rad,
                                    theta_0=pi/2.0, theta_end=-pi/2,
                                    steps=arc_steps, width=ww)
        arc_l = create_arc_with_width(cx=-lms/2.0, cy=0,
                                    radius=arc_rad,
                                    theta_0=pi/2.0, theta_end=3*pi/2.0,
                                    steps=arc_steps, width=ww)

        # compile a list of segments
        segs = []
        for origin, poly in [s, n]:
            # create relevant polygon with correct offset/position
            (xo, yo, theta) = origin
            ctr = Point(poly[0].x, poly[0].y) # rotate segment about its bottom left corner
            seg = rotate_polygon(poly, ctr, theta) # do the rotation
            seg = translate_seq(seg, dx=xo, dy=yo) # now translate the segment
            segs.append(seg)

        segs.extend(arc_r)
        segs.extend(arc_l)

        self.segs = segs


        ### compute the bounds within which agent bees can be spawned ###
        # for simplicity, we assume that the valid zone is only between the
        # parallel section, since random generation with curved bounds is likely
        # going to be a pain (unless we do generate & test - then have to write
        # something to do a 'hit test')
        k = bee_len /2.0 # don't allow bees to be spawned in the wall

        s_x, s_y, s_yaw = s[0]
        n_x, n_y, n_yaw = n[0]
        self.bl_bound = (s_x + poly_wl[0].x + k, s_y + poly_wl[3].y + k )
        self.tr_bound = (n_x + poly_wl[2].x - k, n_y + poly_wl[1].y - k )

#}}}

#{{{ StadiumArena
class CircleArena(BaseArena):
    def __init__(self, radius=15.5, arc_steps=36, ww=1.0, bee_len=1.5,
                 **kwargs):
        '''
        A rectangle with semi-circular ends.  This corresponds to one of the
        enclosures used in the Graz bee lab, and is suitable for two CASUs.

        By default, this arena will be positioned horizontally, about (0, 0).
        Transforms can be applied.

        '''
        super(CircleArena, self).__init__(ww=ww, **kwargs)
        self.radius = radius


        # compute geometry
        arc_rad = self.radius - ww

        # can we do it with a single arc?
        arc_t = create_arc_with_width(cx=0, cy=0, radius=arc_rad, theta_0=0,
                                      theta_end=2*pi,
                                      steps=arc_steps, width=ww)

        # now we need two arcs.
        # centre of the RH arc is ...
        # c_r = [(ex+2)*l , 3*l / 2.0 ]
        # c_l = [(0,        3*l / 2.0 ]
        #arc_r = create_arc_with_width(cx=+lms/2.0, cy=0,
        #                            radius=arc_rad,
        #                            theta_0=pi/2.0, theta_end=-pi/2,
        #                            steps=arc_steps, width=ww)
        #arc_l = create_arc_with_width(cx=-lms/2.0, cy=0,
        #                            radius=arc_rad,
        #                            theta_0=pi/2.0, theta_end=3*pi/2.0,
        #                            steps=arc_steps, width=ww)

        # compile a list of segments
        #segs.extend(arc_r)
        #segs.extend(arc_l)

        self.segs = arc_t


        ### compute the bounds within which agent bees can be spawned ###
        # for simplicity, we define a square inside the circle that is valid.
        k = bee_len /2.0 # don't allow bees to be spawned in the wall

        # the side length of the square inside the cirle is sqrt(2)*r
        _dim = (2.0**0.5 * radius * 0.5 ) - k - ww

        self.bl_bound = (-_dim, -_dim)
        self.tr_bound = (+_dim, +_dim)


#}}}
