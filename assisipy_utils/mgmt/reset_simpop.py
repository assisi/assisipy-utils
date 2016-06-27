#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
simple tool to reset the position of all agents as per their original spec

for all agents defined in an object listing file

'''

import argparse

import specs
from assisipy_utils import tool_version
from assisipy import sim
import random
from math import pi, sin, cos

def main():
    ''' execute the handler for all agents in one or many agent specification listings '''
    # input
    parser = argparse.ArgumentParser()
    parser.add_argument('-ol', '--obj-listing', type=str, required=True, nargs='+',
            help='files listing all objects spawned in enki simulator (one or more)') # no default
    parser.add_argument('-sa', '--sub-addr', type=str, default="tcp://127.0.0.1:5555")
    parser.add_argument('-pa', '--pub-addr', type=str, default="tcp://127.0.0.1:5556")
    parser.add_argument('-x', type=float, default=None,
                        help='override x,y,r to reset popln to random positions in a circle given by x,y, radius')
    parser.add_argument('-y', type=float, default=None,
                        help='override x,y,r to reset popln to random positions in a circle given by x,y, radius')
    parser.add_argument('-r', type=float, default=None,
                        help='override x,y,r to reset popln to random positions in a circle given by x,y, radius')

    tool_version.ap_ver(parser) # attach package dev version to parser
    parser.add_argument('--verb', type=int, default=0,)
    args = parser.parse_args()
    override_pos = False
    if args.x is not None and args.y is not None and args.r is not None:
        override_pos = True

    # extract info from specs
    agent_data = []
    for grp in args.obj_listing:
        _ad = specs.read_agent_handler_data_yaml(grp)
        agent_data += _ad
    a_names = [d.get('name') for d in agent_data ]
    _longest = len( max(a_names, key=lambda p: len(p)) )


    simctrl = None
    if len(d):
        simctrl = sim.Control(pub_addr=args.pub_addr, sub_addr=args.sub_addr)

        for d in agent_data:
            print "\t{:{fwid}} ({:4}): {:20}".format(
                d.get('name'),
                d.get('type'),
                ", ".join([ "{:+.2f}".format(_e) for _e in d.get('pose') ]),
                fwid=_longest+1
            )
            #print type(d.get('pose')) # seems ok
            if override_pos:
                _r = args.r * random.random()
                theta = 2*pi * random.random()
                x = _r * cos(theta) + args.x
                y = _r * sin(theta) + args.y
                yaw = theta
                pose = (x,y,yaw)

            else:
                pose = d.get('pose')

            simctrl.teleport(d.get('name'), pose)

    return agent_data


if __name__ == '__main__':
   ad = main()
