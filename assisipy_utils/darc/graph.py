import pygraphviz
import yaml

from manager import BEE_ARENA, MANAGER_LAYER, MANAGER_NODE

class CASU:
    def __init__(self, number):
        self.number = number

    def key (self):
        return '{}/casu-{:03d}'.format (BEE_ARENA, self.number)

    def label (self):
        return '{:03d}'.format (self.number)

class Node:
    def __init__ (self, number, node_CASUs, CASUs):
        self.id = number
        self.CASUs = {c : CASUs [c] for c in node_CASUs}
        print (self.CASUs)

class Edge:
    def __init__ (self, nodes, dict_nodes):
        self.nodes = (dict_nodes [nodes [0]], dict_nodes [nodes [1]])
        print (self.nodes)

class Graph:
    def __init__ (self, parameter):
        if isinstance (parameter, dict):
            yaml_graph = parameter ['graph']
        else:
            raise Exception ('Unexpected argument type to Graph constructor {}'.format (parameter))
        self.CASUs = {c : CASU (c) for n in yaml_graph ['node_CASUs'] for c in yaml_graph ['node_CASUs'][n]}
        self.nodes = {n : Node (n, yaml_graph ['node_CASUs'][n], self.CASUs) for n in yaml_graph ['node_CASUs']}
        self.edges = [Edge (ns, self.nodes) for ns in yaml_graph ['edges']]

    def create_neighbourhood_dot (self):
        result = pygraphviz.AGraph (directed = True)
        manager_layer = result.add_subgraph (name = MANAGER_LAYER)
        bee_arena_layer = result.add_subgraph (name = BEE_ARENA)
        for c in self.CASUs.values ():
            manager_layer.add_edge (
                MANAGER_NODE,
                c.key (),
                label = 'casu-{}'.format (c.label ())
            )
            bee_arena_layer.add_edge (
                c.key (),
                MANAGER_NODE,
                label = "cats"
            )
        for n in self.nodes.values ():
            for c1 in n.CASUs.values ():
                for c2 in n.CASUs.values ():
                    if c1 != c2:
                        bee_arena_layer.add_edge (
                            c1.key (),
                            c2.key (),
                            label = 'casu-{}-{}'.format (c1.label (), c2.label ())
                        )
        return result
