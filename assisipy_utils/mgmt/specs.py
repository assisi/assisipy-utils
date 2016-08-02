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
from datetime import datetime as dt
from itertools import ifilter


def read_agent_handler_data(fname, ty_filter=None, verb=False):
    '''
    read specification as written, in either yaml or csv.
    this function parses the first line to find the format and
    then calls the specific reader.

    returns a list of dicts, each dict having the following:
        name
        ty
        pose
        pa
        sa
        exec_script
        local_conf
    '''
    # read header
    header = ""

    with open(fname, 'r') as f:
        header = f.readline()

    # now parse it
    # expecting to see something like "# yaml, ver 1, created on date X"
    fmt = None
    if header.startswith('#'):
        elems = [e.strip() for e in header.lstrip('#').split(",")]
        if len(elems) >= 2:
            fmt = elems[0]

    if fmt is None:
        print "[E] data format is unknown. write header correctly or use specific reader"
        raise ValueError

    if fmt == "yaml":
        return read_agent_handler_data_yaml(fname, ty_filter=ty_filter, verb=verb)
    elif fmt == "csv":
        return read_agent_handler_data_csv(fname, ty_filter=ty_filter, verb=verb)
    else:
        print "[E] data format '{}' is not recognised! yaml and csv understood.".format(fmt)
        raise ValueError









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

def read_agent_handler_data_csv(fname, ty_filter=None, verb=False):
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
        R = csv.reader(
            ifilter(lambda row: row[0]!='#', fh),
            delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL,
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



def gen_spec_str_csv(name, obj_type, pose, exec_script, conf,
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

def write_header(f, fmt='latest', ver=2.0):
    '''
    write a simple header to spec file, to allow for easy automatic
    processing of the type.
    '''
    now = dt.now()
    _fmt = "yaml"
    if fmt is 'latest':
        _fmt = "yaml"
    else:
        _fmt = fmt

    f.write("# {}, version {}, spec written at {}\n".format(
        _fmt, ver, now.strftime("%c")))

def gen_spec_str(name, obj_type, pose, exec_script, conf,
                  pub_addr='tcp://localhost:5556',
                  sub_addr='tcp://localhost:5555',
                  ):
    '''
    wrapper for the yaml generator, which is the default since v0.6.

    generate a specification string for an agent. returns a string -- does not
    write directly to file

    '''
    return gen_spec_str_yaml(name, obj_type, pose, exec_script, conf,
                             pub_addr=pub_addr, sub_addr=sub_addr)


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





