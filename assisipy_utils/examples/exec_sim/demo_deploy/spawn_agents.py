#!/usr/bin/env python
# -*- coding: utf-8 -*-

#from math import pi
from assisipy import sim
import argparse
#import random
from assisipy_utils import arena
from assisipy_utils.mgmt import specs
#from assisipy_utils.arena import Transformation
#import yaml

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=
    '''
    Create a circular wall with some casus outside of the wall,
    and spawn bees
    ''')
    parser.add_argument('-n',  '--num-bees', type=int, default=0)
    parser.add_argument('-ol', '--obj-listing', type=str, default=None)
    parser.add_argument('-a', '--arena-file', type=str, default='valid.arena')
    parser.add_argument('-l', '--label', type=str, default='popln1-')
    parser.add_argument('-e', '--exec-script', type=str, required=True,
                        help='name of script to execute for each bee in `bee-file`')
    args = parser.parse_args()

    simctrl = sim.Control()

    obj_file = None
    if args.obj_listing is not None:
        obj_file = open(args.obj_listing, 'w')
        specs.write_header(obj_file)

    # find out where the bees can go
    bl, tr, trans =arena.read_reqs(args.arena_file)
    bee_poses = arena.gen_valid_bee_positions((bl, tr), n=args.num_bees, trans=trans)

    if args.num_bees > 0:
        for i, pts in enumerate(bee_poses):
            pose = pts[0].x, pts[0].y, pts[1]
        #for i in range(1, args.num_bees+1):
            name = '{}-Bee-{:03d}'.format(args.label, i)
            if i < args.num_bees / 2:
                conf = 'gf.conf'
            else:
                conf = 'wf.conf'

            #pose = (random.uniform(-4, 4), random.uniform(-4, 4),
            #        2*pi*random.random())

            simctrl.spawn('Bee', name, pose)
            print 'Spawned bee', name
            if obj_file:
                s = specs.gen_spec_str(name, 'Bee', pose,
                                       args.exec_script, conf,
                                       'tcp://localhost:5556',
                                       'tcp://localhost:5555',
                                       )

                obj_file.write(s + "\n")


    if obj_file:
        obj_file.close()
        print "[I] wrote object listing to {}".format(obj_file.name)


