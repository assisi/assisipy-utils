#!/usr/bin/env python
# -*- coding: utf-8 -*-

# simple script to attach to all casus in a given deployment
# and emit a casu.stop() message to them.

import argparse, yaml, os
from assisipy import casu

def main():
    parser = argparse.ArgumentParser(description='stop all casus in a given depployment')
    parser.add_argument('project', help='name of .assisi file specifying the proejct')
    parser.add_argument('--layer', help='Name of single layer to deploy', default=None)

    args = parser.parse_args()

    proj = {}
    dep  = {}
    with open(args.project) as f:
        proj = yaml.safe_load(f)

    root = os.path.dirname(os.path.abspath(args.project))
    proj_name = os.path.splitext(os.path.basename(args.project))[0]
    sandbox_dir = proj_name + '_sandbox'
    depspec = proj.get('dep')
    if depspec is not None:

        with open( os.path.join(root, depspec)) as f:
            dep = yaml.safe_load(f)



    for layer in dep:
        if args.layer is None or layer == args.layer:
            print "[I] processing layer {}".format(layer)
            for _casu in dep[layer]:
                rtc = os.path.join(sandbox_dir, layer, _casu, '{}.rtc'.format(_casu))
                c = casu.Casu(rtc_file_name=rtc)
                c.stop()
                print "[I] stopped casu {}".format(_casu)



        else:
            print "[W] skipping layer {}".format(layer)


if __name__ == '__main__':
    main()
