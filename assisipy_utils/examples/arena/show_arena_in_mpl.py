#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
A simple example of assisilib usage, with arenas shown in a matplotlib
visualisation (for testing of shapes, figures that are not from screenshots, etc)


'''

from math import pi
from assisipy_utils import arena
import matplotlib.pyplot as plt

from assisipy_utils.arena import rendering

if __name__ == '__main__':

    plt.figure(1); plt.clf()
    fig, ax = plt.subplots(1,1,num=1)

    # define an arena wall object
    A = arena.RoundedRectArena(length=25.5, width=16.5, ww=0.5, corner_rad=4.9)
    A2 = arena.RoundedRectBarrier(length=11., width=10., ww=0.5, corner_rad=2.,
                                  label_stub='block', edges='wn')
    T2= arena.Transformation(dx=8.75, dy=-4.75)
    A2.transform(T2)

    rendering.render_arena(A.segs, ax=ax, fc='0.5')
    rendering.render_arena(A2.segs, ax=ax, fc='r')

    yaw = pi
    casu_poses = []
    for (x,y) in [(x,y) for x in [-9, 0, 9] for y in [-4.5, +4.5] ]:
            p = arena.transforms.Point(x, y, 0)
            casu_poses.append( (p, yaw))

    # special setup, with only 5 - remove the last one
    del casu_poses[4]

    rendering.render_CASUs(casu_poses, ax=ax)


    ax.set_xlim(-20, +20)
    ax.set_ylim(-20, +20)
    ax.set_aspect('equal')

    ax.grid('on')
    plt.show()
