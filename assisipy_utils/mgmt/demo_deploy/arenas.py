#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
A simple example of assisilib usage, spawning two oval arenas
(assumes any CASUs required are spawned externally)

'''

from assisipy import sim
from assisipy_utils import arena

if __name__ == '__main__':
    simctrl = sim.Control()
    # in the 9-CASU arena of V3 casus, the centres are 9cm apart, centred at 5
    # 9 8 7
    # 6 5 4
    # 3 2 1
    # ----/ --
    #   <door>
    #
    # this example will use the arenas around 9, 8

    # define an arena wall object
    A = arena.StadiumArena(ww=0.5, label_stub='arena-98')
    T = arena.Transformation(dx=-4.5, dy=+9.0, theta=0.0)
    A.transform(T)
    A.spawn(simctrl)

