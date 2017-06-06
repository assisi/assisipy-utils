#!/usr/bin/env python
# -*- coding: utf-8 -*-

desc='''
simple tool to augment a .nbg file with labels and positions

- the .nbg file (dot format) defines the graph topology
- the .arena file defines the positions of the CASUs
- the .assisi file defines the choice of nbg and arena files

This tool brings together the data above, producing a new .nbg file
in dot format, which can be rendered using neato (or fdp) to see
the physical and topological layout together.

'''


import pygraphviz as pgv
import argparse
import yaml, os

from assisipy_utils import tool_version


class TopoGeomGraph(object):
    def __init__(self, project, scale=2.0, outfile=None, verb=False):
        #{{{ initialiser
        self.verb = verb
        ### load specification files
        if self.verb:
            print "[I] loading definitions for {}".format(os.path.basename(project))
        with open(project) as f:
            self.project_spec = yaml.safe_load(f)
            if self.verb:
                print "   [I] loaded assisi defn"


        self.project_root = os.path.dirname(os.path.abspath(project))
        self.scale = scale

        self._phys_layout_loaded = False

        # the arena file has locations
        self.af = self.project_spec.get('arena')
        # the nbg file has edges
        self.gf = self.project_spec.get('nbg')
        self.nbg = os.path.join(self.project_root, self.gf)

        if outfile is None:
            self.outfile = "{}.layout".format(os.path.join(self.project_root, self.gf))
        else:
            self.outfile = outfile
        if self.af is None or self.gf is None:
            raise RuntimeError(
                "[F] cannot annotate graph without both arena and nbg data!")

        with open(os.path.join(self.project_root, self.af)) as f:
            self.arena = yaml.safe_load(f)
            if self.verb:
                print "   [I] loaded .arena file '{}'.".format(self.af), self.arena.keys()

        # load topology (nbg)
        self.DG = pgv.AGraph(self.nbg, directed=True)
        if self.verb:
            print "   [I] loaded .nbg file"
        # generate flattened geometry data
        self._flatten_phys_layout()
        # attach a geometric position to the casu if specified
        self.add_geometric_positions()
    #}}}

    #{{{ add_geometric_positions
    def add_geometric_positions(self):
        if not self._phys_layout_loaded:
            self._flatten_phys_layout()

        if self.verb: print "[I] adding geometric data to graph"
        for _node in self.DG.nodes():
            if self.verb: print "   [I] working on node {}".format(_node)
            # we need to flatten the topo naming as well
            if "/" in _node:
                _aa, nodename = _node.split('/')[0:2]
            else:
                nodename = str(_node)

            if nodename in self.allnodes:
                pose = self.allnodes[nodename].get('pose')
                if pose:
                    s = "{},{}!".format(
                        pose['x']/self.scale, pose['y']/self.scale)
                    # add the attribute to the original topo node (?)
                    _node.attr['pos'] = s
                    if self.verb:
                        print "   [I] added pos {} to node {} ({})".format(s, nodename, _node)
                else:
                    print "   [W] skipping {} ({}) since no data".format(nodename, _node)


    #}}}

    #{{{ flatten physical layout graph (arena)
    def _flatten_phys_layout(self):
        '''
        remove the layers from hierarchy, since pygraphvis does not handle
        layers in a useful way
        '''
        self.allnodes = {}
        for layer in self.arena:
            for c in self.arena[layer]:
                # check whether it already exists
                if c in self.allnodes:
                    raise ValueError("[E] duplicate node names! We cannot flatten graph, aborting")
                self.allnodes[c] = self.arena[layer][c]
        self._phys_layout_loaded = True
    #}}}

    #{{{ write out, and issue info message for generating plot
    def write(self):
        # write out the updated graph to file
        self.DG.write(self.outfile)

        # print message to indicate how to draw an image
        print "[I] render new graph with neato:"
        print "neato -Tpdf -O {}".format(self.outfile)
    #}}}


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

    args = parser.parse_args()
    #}}}

    TGG = TopoGeomGraph(project=args.project, scale=args.scale_factor,
                        outfile=args.outfile, verb=args.verb)
    TGG.write()

    return args, TGG

if __name__ == "__main__":
    a, TGG = main()
