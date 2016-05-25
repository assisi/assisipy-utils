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

import yaml
import csv
import copy

def read_agent_handler_data_yaml(fname, ty_filter=None, verb=False):
    '''
    read specification as written in yaml

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
    _y = {}
    with open(fname) as f:
        _y = yaml.safe_load(f)

    data = []
    for k, v in _y.iteritems():
        ty = v.get('type')
        if ty_filter is not None and ty.lower() != ty_filter:
            continue
        else:
            d = copy.deepcopy(v)
            d['name'] = k
            data.append(d)

    return data

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
                'pose'        : [float(x), float(y), float(theta)],
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


def write_spec_file(fname, speclist ):
    '''
    writes a list of specification lines to a specfile.
    '''
    with open(fname, 'w') as f:
        for s in speclist:
            f.write(s+"\n")
    # done

def gen_spec_str_yaml(name, obj_type, pose, exec_script, conf,
                  pub_addr='tcp://localhost:5556',
                  sub_addr='tcp://localhost:5555',
                  ):
    '''
    generate a specification string for an agent. returns a string -- does not
    write directly to file
    '''
    d = {}
    d[name] = {
    'type'          : obj_type,
    'pose'          : list(pose),
    'exec_script'   : exec_script,
    'conf'          : conf,
        'pub_addr'  : pub_addr,
        'sub_addr'  : sub_addr,
    }

    s = yaml.safe_dump(d)
    return s





