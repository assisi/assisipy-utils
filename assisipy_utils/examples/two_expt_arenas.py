
#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
A simple example of assisilib usage, spawning four CASUs and two oval arenas

'''

from assisipy import sim
from assisipy_utils import arena
from math import pi


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
    #
    # this example will use the arenas around 6,3 and 4, 1
    # this example will use the ring around CASUs 5, 4, 2, 1

    # define the poses of the CASUs (all "yaw"/rotations are 0)
    yaw = 0
    c6 = "casu-006", (-9,  0, yaw)
    c3 = "casu-003", (-9, -9, yaw)

    c4 = "casu-004", (9,  0, yaw)
    c1 = "casu-001", (9, -9, yaw)


    # spawn each of the CASU objects
    for cname, cpos in [c6, c3, c4, c1]:
        simctrl.spawn('Casu', cname, cpos)

    # define an arena wall object
    Al = arena.StadiumArena(ww=0.5, label_stub='arena-63')
    Ar = arena.StadiumArena(ww=0.5, label_stub='arena-41', color=(0.0, 0.2, 0.8))
    # define a transform (centre of 6/3)
    Tl = arena.Transformation(dx=-9.0, dy=-4.5, theta=pi/2.0)
    # (centre of 4/1)
    Tr = arena.Transformation(dx=+9.0, dy=-4.5, theta=pi/2.0)
    Al.transform(Tl)
    Al.spawn(simctrl)
    Ar.transform(Tr)
    # since we didnt#
    Ar.spawn(simctrl, )#offset=100)

    pass
