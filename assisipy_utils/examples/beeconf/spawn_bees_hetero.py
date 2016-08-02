#!/usr/bin/env python
# -*- coding: utf-8 -*-

from math import pi
from assisipy import sim
import argparse
import random
from assisipy_utils import arena
from assisipy_utils.mgmt import specs


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=
    '''
    Create a circular wall with some casus outside of the wall,
    and spawn bees
    ''')
    parser.add_argument('-n',  '--num-bees', type=int, default=0)
    parser.add_argument('-r',  '--radius', type=float, default=12)
    parser.add_argument('-ol', '--obj-listing', type=str, default=None)
    #parser.add_argument('-e', '--exec-script', type=str, required=True,
    #                    help='name of script to execute for each bee in `bee-file`')
    args = parser.parse_args()

    simctrl = sim.Control()

    obj_file = None
    if args.obj_listing is not None:
        obj_file = open(args.obj_listing, 'w')
        specs.write_header(obj_file)

    if args.num_bees > 0:
        for i in range(1, args.num_bees+1):
            if i < args.num_bees / 2:
                conf = 'gf.conf'
            else:
                conf = 'wf.conf'

            if i % 2 == 0:
                exec_script = "basic_bee_fwd.py"
            else:
                exec_script = "basic_bee_bwd.py"

            name = 'Bee-{:03d}'.format(i)

            pose = (random.uniform(-4, 4), random.uniform(-4, 4),
                    2*pi*random.random())

            if obj_file: # write specification to file for easy exec mgmt
                s = specs.gen_spec_str(name, 'Bee', pose,
                                       exec_script, conf,
                                       'tcp://localhost:5556',
                                       'tcp://localhost:5555',
                                       )

                obj_file.write(s + "\n")

            simctrl.spawn('Bee', name, pose)
            print 'Spawned bee', name



    A = arena.CircleArena(radius=args.radius)
    A.spawn(simctrl)

    if obj_file:
        obj_file.close()
        print "[I] wrote object listing to {}".format(obj_file.name)


