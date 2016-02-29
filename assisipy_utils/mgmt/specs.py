#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
simple library functions to write and read agent specifications.
They are recorded in CSV form, with one line per agent. The spec includes:
    - agent name
    - agent object type ('Bee', 'Fish', etc)
    - pose (x, y, theta)
    - server addresses (publish and subscribe addresses)
    - behavioural script to execute
    - config file (parameters passsed to behavioural script)

'''

import csv


def read_agent_handler_data(fname, ty_filter=None, verb=False):
    '''
    uses specification parser that is maintained with writer!
    (which provides structured data)

    returns a list of dicts, each dict having the following:
        name
        ty
        pose
        pa
        sa
        exec_script
        local_conf

    '''
    data = []

    # first read whole file
    _specs = []
    with open(fname, 'r') as fh:
        R = csv.reader(fh, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL,
                skipinitialspace=True)
        for row in R:
            if len(row) != 9:
                print "[W] incomplete specification."
            _specs.append(row)

    # now parse each spec into a dictionary
    for (ty, name, x, y, theta, pub_addr, sub_addr, exec_script, conf)  in _specs:
        if ty_filter is not None and ty.lower() != ty_filter:
            continue
        else:
            _d = {
                'name'        : name,
                'type'        : ty,
                'pose'        : (x, y, theta),
                'pub_addr'    : pub_addr,
                'sub_addr'    : sub_addr,
                'exec_script' : exec_script,
                'conf'        : conf,
            }

            data.append(_d)

    return data


def gen_spec_str(name, obj_type, pose, exec_script, conf,
                  pub_addr='tcp://localhost:5556',
                  sub_addr='tcp://localhost:5555',
                  ):
    '''
    generate a specification string for an agent. returns a string -- does not
    write directly to file
    '''
    x,y,yaw = pose
    s = ", ".join(
        [str(field) for field in [obj_type, name, x, y, yaw, pub_addr, sub_addr, exec_script, conf]
         ])
    return s





