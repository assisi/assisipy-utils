#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
A simple example of assisilib usage, spawning four CASUs and a circular
arena.

'''

from assisipy import sim
from assisilib import arena


if __name__ == '__main__':
    simctrl = sim.Control()

    # in the 9-CASU arena of V3 casus, the centres are 9cm apart, with a
    # reference of (0,0) for casu 5
    #
    # 9 8 7
    # 6 5 4
    # 3 2 1
    # ----/ --
    #   <door>
    #
    #
    # this example will use the ring around CASUs 5, 4, 2, 1

    # define the poses of the CASUs (all "yaw"/rotations are 0)
    yaw = 0
    c5 = "casu-005", (0,  0, yaw)
    c4 = "casu-004", (9,  0, yaw)
    c2 = "casu-002", (0, -9, yaw)
    c1 = "casu-001", (9, -9, yaw)


    # spawn each of the CASU objects
    for cname, cpos in [c5, c4, c2, c1]:
        simctrl.spawn('Casu', cname, cpos)

    # define an arena wall object
    A = arena.CircleArena(radius=11.0, ww=0.5)
    # define a transform (centre of the 4 casus)
    T = arena.Transformation(dx=4.5, dy=-4.5)
    A.transform(T)
    A.spawn(simctrl)

    pass
