# -*- coding: utf-8 -*-

'''
some utilities for use in conjunction with the TopoGeomGraph class
and validation tasks.
'''

import csv

_C_OKBLUE =  '\033[94m'
_C_OKGREEN = '\033[92m'
_C_ENDC = '\033[0m'
_C_ERR  = '\033[1;31m'


#{{{ read logfile
def read_edge_recs(msg_file):
    '''
    read a log file for results indicating the messages that were received
    across the whole system.
    The file can contain rows of different types but these should be structured
    msg_test, <src>, <tgt>, <seq>
    '''
    msgs_ok = []
    if msg_file is not None:
        with open(msg_file) as csvfile:
            rdr = csv.reader(csvfile, delimiter=',')
            for row in rdr:
                if row[0].strip() == "msg_test":

                    if len(row) == 4:
                        msgs_ok.append( (row[1].strip(), row[2].strip()))
    return msgs_ok

def read_node_recs(recs_file):
    '''
    read a log file for results indicating logs for each of the nodes that
    could set and read casus.
    The file can contain rows of different types but these should be structured
    node_set, <src>, <seq>
    node_read, <src>, <seq>
    '''
    # TODO!
    node_write_ok = []
    if recs_file is not None:
        with open(recs_file) as csvfile:
            rdr = csv.reader(csvfile, delimiter=',')
            for row in rdr:
                if row[0].strip() == "node_set" and len(row)>=2:
                    node_write_ok.append(row[1].strip())

    return node_write_ok
#}}}

#{{{ annotate according to log file
def annotate_links_by_msg(DG, msgs_ok):
    '''
    for each node-node link (=edge in the graph), if a message was successfully
    received in the conn_test phase, mark as green. else mark as red.

    changes are made inline
    '''

    # apply a color to each edge according to whether message was rx ok.
    for edge in DG.edges():
        # increase width a bit
        edge.attr['penwidth'] = 2
        # default color (assume fail until seen msg)
        edge.attr['color'] = "red"
        hit = False

        # check whether the edge is linked ok during the test
        _f = str(edge[0].encode('ascii','ignore'))
        _t = str(edge[1].encode('ascii','ignore'))
        for mf, mt in msgs_ok:
            mf = str(mf)
            mt = str(mt)
            if _f == mf and _t == mt:
                #print "hit ", edge
                hit = True
                edge.attr['color'] = "green3"

        if not hit:
            print "[E] failed to traverse ", edge

def annotate_nodes_by_writemsg(DG, node_write_ok):
    '''
    for each node that we could successfully write values to, mark the node in
    DG as green. Else mark as red.

    changes made inline
    '''
    for node in DG.nodes():
        # default color
        node.attr['color'] = 'red'
        node.attr['penwidth'] = 3
        hit = False
        _n = str(node.encode('ascii', 'ignore'))
        for n in node_write_ok:
            if n == _n:
                hit = True
                node.attr['color'] = "green3"

        if not hit:
            print "[E] failed to set values on node {}",format(_n)
#}}}


#{{{ compact_weight_labels
def compact_weight_labels(DG):
    '''
    in-place method to re-write compact edge labels in graph, to include
    "#source => #target" and weight.
    Assumes all three infos exist but ignores gracefully if not present.
    '''
    # annotate graph with edge weights.
    for edge in DG.edges():
        w = edge.attr.get('weight')
        if w is None:
            # no wieght info, nothing to do.
            continue

        # construct a compact label, including the weight
        l_orig = edge.attr.get('label', "")
        # try to extract two digits as src/tgt nodes from the label
        if sum(c.isdigit() for c in l_orig) == 2:
            fr, to = [str(c) for c in l_orig if c.isdigit()]
            l_new = "{}=>{}: {}".format(fr, to, w)
        else:
            l_new  = "{} : {}".format(l_orig, w)

        edge.attr['label'] = l_new
#}}}


#{{{ compute_total_incoming_weights
def compute_total_incoming_weights(DG, expected=None, tol=0.02):
    '''
    Compute sum of incoming weights to each node, and optionally verify that
    each sum is close to an expected value. If `expected` is None, this is skipped.

    '''
    print "[I] per-node inhibition"
    print "{:14}\t{:^10}\t{:^18}".format("node name", "#in edges", "sum inhibn")
    if expected is not None:
        print "{:14}\t{:10}\t".format("", ""),
        print _C_OKGREEN + "{:^18}".format("expected: {}".format(expected)) + _C_ENDC
    print "{:14}\t{:>10}\t{:^18}".format("---------",  "----------", "--------------")

    #"\tname\t#inedges\tsum inhibn"
    errs = 0
    for node in sorted(DG.nodes()):
        in_edges = DG.in_edges(node)
        total = 0.0
        for edge in in_edges:
            w = float(edge.attr['weight'])
            total += w

        s = "{:14}\t{:10}\t".format(node, len(in_edges))
        if expected is not None:
            if abs(total - expected) > tol:
                errs += 1
                s += _C_ERR
            else:
                s += _C_OKGREEN

        s += "{:11}".format(total)
        if expected is not None: s += _C_ENDC

        print s

    if expected is not None:
        if errs > 0:
            s = _C_ERR + "[E] {} of {} nodes have unexpected input sums".format(
                errs, len(DG.nodes())) + _C_ENDC
        else:
            s = _C_OKGREEN + "[I] all {} nodes have expected input sum {}".format(
                len(DG.nodes()), expected) + _C_ENDC

        print "--------- --------- --------- --------- ---------"
        print s
        print "--------- --------- --------- --------- ---------" + "\n"

#}}}

