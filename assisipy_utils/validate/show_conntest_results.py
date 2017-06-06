#!/usr/bin/env python
# -*- coding: utf-8 -*-

desc='''
A simple tool to augment a .nbg file with labels, positions, and edge 
weights, and compute the incoming edge weight total, for each node.

This is an example usage of the validate.TopoGeomGraph class, extending to:
    - annotate with edge weights
    - parse results of a `conn_test` messaging test
    - color the final graph according to success/failure of all
      the tests
'''
from assisipy_utils import validate
from assisipy_utils import tool_version

import argparse


def main():
    #{{{ cmd line args
    parser = argparse.ArgumentParser(
            description=desc,
            #description="simple tool to augment a .nbg file with labels and positions",
        formatter_class=argparse.RawTextHelpFormatter)
    tool_version.ap_ver(parser) # attach package dev version to parser
    parser.add_argument('project', help='name of .assisi file specifying the project details.')
    parser.add_argument('-s', '--scale-factor', type=float, default=3.0,
                        help="scaling factor for layout. 3.0 works well for"
                        "a 9-CASU array")
    parser.add_argument('-o', '--outfile', help='name to generate output graph in', default=None)
    parser.add_argument('-v', '--verb', action='store_true', help="be verbose")
    parser.add_argument("-m", "--msg_file", type=str, default=None,
                        help="csv of msging test results")

    args = parser.parse_args()
    #}}}

    TGG = validate.TopoGeomGraph(project=args.project, scale=args.scale_factor,
                                 outfile=args.outfile)

    # annotate graph with edge weights.
    validate.compact_weight_labels(TGG.DG)

    # read messages recvd from summary file, and node activations
    msgs_ok       = validate.read_edge_recs(args.msg_file)
    node_write_ok = validate.read_node_recs(args.msg_file)

    # color the links and nodes to report success/failure of tests
    validate.annotate_links_by_msg(TGG.DG, msgs_ok)
    validate.annotate_nodes_by_writemsg(TGG.DG, node_write_ok)

    # generate new graph, with extra info.
    TGG.write()

    return args, TGG

if __name__ == "__main__":
    a, TGG = main()
