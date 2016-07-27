#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
example usage of the validate.TopoGeomGraph class, extending to:
    - annotate with edge weights
    - verify the total sum of incoming weights is consistent


'''

import argparse
from assisipy_utils import validate
from assisipy_utils.validate import libgraph


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
    validate.compact_weight_labels(TGG.DG)
    # validation -- what is the summed input weight per node?
    validate.compute_total_incoming_weights(TGG.DG, expected=-1.0,)

    # generate new graph, with extra info.
    TGG.write()
