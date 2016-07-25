#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
example usage of the validate.TopoGeomGraph class, extending to
annotate with edge weights.

'''

import argparse
from assisipy_utils import validate


if __name__ == "__main__":
    #{{{ cmd line args
    parser = argparse.ArgumentParser(
        description="simple tool to augment a .nbg file with labels, "
                    "positions, and edge weights")
    parser.add_argument('project', help='name of .assisi file specifying the project details.')
    parser.add_argument('-s', '--scale-factor', type=float, default=3.0,
                        help="scaling factor for layout. 3.0 works well for"
                        "a 9-CASU array")
    parser.add_argument('-o', '--outfile', help='name to generate output graph in', default=None)
    parser.add_argument('-v', '--verb', action='store_true', help="be verbose")

    args = parser.parse_args()
    #}}}

    TGG = validate.TopoGeomGraph(project=args.project, scale=args.scale_factor,
                                 outfile=args.outfile)

    # annotate graph with edge weights.
    for edge in TGG.DG.edges():
        w = edge.attr.get('weight')
        if w is None:
            # no wieght info, nothing to do.
            continue

        # construct a compact label, including the weight
        l_orig = edge.attr.get('label', "")
        l_new  = "{} : {}".format(l_orig, w)
        edge.attr['label'] = l_new


    # generate new graph, with extra info.
    TGG.write()
