#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
composite arena with barrier.

'''

from assisipy import sim
from assisipy_utils import arena


if __name__ == '__main__':

    simctrl = sim.Control()

    # define an arena wall object
    A = arena.RoundedRectArena(length=25.5, width=16.5, ww=0.5, corner_rad=4.9)
    # and a barrier that constrains a bit the bee locations.
    A2 = arena.RoundedRectBarrier(length=11., width=10., ww=0.5, corner_rad=2.,
                                  label_stub='block', edges='wn')
    T2= arena.Transformation(dx=8.75, dy=-4.75)
    A2.transform(T2)

    # define the poses of some CASUs (all "yaw"/rotations are 0)
    yaw = 0
    c5 = "casu-005", (0,  +4.5, yaw)
    c4 = "casu-004", (0,  -4.5, yaw)
    c2 = "casu-002", (-9, -4.5, yaw)
    c1 = "casu-001", (-9, +4.5, yaw)
    c3 = "casu-003", (+9, +4.5, yaw)

    # spawn each of the CASU objects
    for cname, cpos in [c5, c4, c2, c1, c3]:
        simctrl.spawn('Casu', cname, cpos)

    A.spawn(simctrl)
    A2.spawn(simctrl)
