#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
A simple example of assisilib usage, spawning two oval arenas
(assumes any CASUs required are spawned externally)

'''

from assisipy import sim
from assisipy_utils import arena
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-x', type=float, default=0.0)
    parser.add_argument('-y', type=float, default=0.0)
    parser.add_argument('-l', '--label', type=str, default='popln1-')
    parser.add_argument('-o', '--output', type=str, default='valid_area.csv')
    args = parser.parse_args()

    # in the 9-CASU arena of V3 casus, the centres are 9cm apart, centred at 5
    # 9 8 7
    # 6 5 4
    # 3 2 1
    # ----/ --
    #   <door>
    #
    ### this example will use the arenas around 9, 8

    # define an arena wall object
    A = arena.StadiumArena(ww=0.5, label_stub=args.label+"-arena")
    T = arena.Transformation(dx=args.x, dy=args.y, theta=0.0)
    A.transform(T)
    posns_to_write = [x for sublist in A.get_valid_zone() for x in sublist]

    with open(args.output, 'w') as va_file:
        s = ", ".join([str(x) for x in posns_to_write])
        va_file.write(s + "\n")
    va_file.close()
    print "[I] wrote specification to {}".format(va_file.name)

    # now we have a definition, we can spawn the wall segments
    simctrl = sim.Control()
    A.spawn(simctrl)

