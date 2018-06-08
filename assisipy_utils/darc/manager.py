from __future__ import print_function

import argparse
import yaml

import graph

BEE_ARENA = 'bee-arena'
MANAGER_LAYER = 'fish-tank'
MANAGER_NODE = '{}/cats'.format (MANAGER_LAYER)

class DARC_Manager:
    def __init__ (self, _project, arena_file_name, config_file_name):
        self.project = _project
        self._assisi_filename, self._arena_filename, self._dep_filename, self._nbg_filename = ['{}.{}'.format (self.project, extension) for extension in ['assisi', 'arena', 'dep', 'nbg'] ]
        with open (arena_file_name, 'r') as fd:
            self.arena = yaml.safe_load (fd)
        with open (config_file_name, 'r') as fd:
            self.config = yaml.safe_load (fd)
        self.used_casus = [
            c
            for label in self.config ['controllers']
            for c in self.config ['controllers'][label]['casus'] ]
        self.graph = graph.Graph (self.config)
        self.base_worker_port = 90000

    def create_files (self):
        self.__create_assisi_file ()
        self.__create_arena_file ()
        self.__create_dep_file ()
        self.__create_nbg_file ()

    def create_workers_file (self):
        contents = {
            'workers': []
        }
        for layer in self.arena:
            for casu_label in self.arena [layer]:
                if self.__is_casu_used (casu_label):
                    data = {
                        field : self.arena [layer][casu_label][field]
                        for field in ['sub_addr', 'pub_addr', 'msg_addr']
                    }
                    ## BIG ASSUMPTION HERE
                    casu_number = int (casu_label [-3:])
                    data ['casu_number'] = int (casu_label [-3:])
                    hostname = self.__casu_hostname (casu_number)
                    data ['wrk_addr'] = 'tcp://{}:{}'.format (hostname, self.base_worker_port + casu_number)
                    contents ['workers'].append (data)
                else:
                    print ('[II] Physical casu {} is not used'.format (casu_label))
        with open ('{}.workers'.format (self.project), 'w') as fd:
            yaml.dump (contents, fd, default_flow_style = False)
            fd.close ()

    def casu_key (self, number):
        return 'casu-{:03d}'.format (number)

    def __create_assisi_file (self):
        with open (self._assisi_filename, 'w') as fd:
            yaml.dump ({'arena' : self._arena_filename}, fd, default_flow_style = False)
            yaml.dump ({'dep' : self._dep_filename}, fd, default_flow_style = False)
            yaml.dump ({'nbg' : self._nbg_filename}, fd, default_flow_style = False)
            fd.close ()
        print ('[I] Created assisi file for project {}'.format (self.project))

    def __create_arena_file (self):
        contents = {}
        for layer in self.arena:
            for casu_label in self.arena [layer]:
                if self.__is_casu_used (casu_label):
                    if layer not in contents:
                        contents [layer] = {}
                    contents [layer][casu_label] = {
                        field : self.arena [layer][casu_label][field]
                        for field in ['sub_addr', 'pub_addr', 'msg_addr']
                    }
                else:
                    print ('[II] Physical casu {} is not used'.format (casu_label))
        with open (self._arena_filename, 'w') as fd:
            yaml.dump (contents, fd, default_flow_style = False)
            fd.close ()
        print ('[I] Created arena file for project {}'.format (self.project))

    def __create_dep_file (self):
        contents = {
            BEE_ARENA : {}
        }
        for controller in self.config ['controllers'].values ():
            for casu in controller ['casus']:
                hostname = self.__casu_hostname (casu)
                if hostname is not None:
                    args = []
                    if self.config ['deploy'].get ('args', {}).get ('add_casu_number', False):
                        args.append (casu)
                    if self.config ['deploy'].get ('args', {}).get ('add_worker_address', False):
                        args.append ('tcp://{}:{}'.format (hostname, self.base_worker_port + casu))
                    args.extend (controller ['args'])
                    print (args)
                    contents [BEE_ARENA][self.casu_key (casu)] = {
                        'controller' : controller ['main']
                        , 'extra'      : [x for x in controller ['extra']]
                        , 'args'       : args #[x for x in controller ['args']]
                        , 'hostname'   : hostname
                        , 'user'       : self.config ['deploy']['user']
                        , 'prefix'     : self.config ['deploy']['prefix']
                        , 'results'    : [x for x in controller ['results']]
                    }
                else:
                    print ('[W] There is no physical casu {}!!!'.format (casu))
        with open (self._dep_filename, 'w') as fd:
            yaml.dump (contents, fd, default_flow_style = False)
            fd.close ()
        print ('[I] Created dep file for project {}'.format (self.project))

    def __create_nbg_file (self):
        self.graph.create_neighbourhood_dot ().write (self._nbg_filename)
        print ('[I] Created nbg file for project {}'.format (self.project))

    def __is_casu_used (self, casu_label):
        ## BIG ASSUMPTION HERE
        casu_number = int (casu_label [-3:])
        return casu_number in self.used_casus

    def __casu_hostname (self, casu):
        key = self.casu_key (casu)
        for layer in self.arena:
            for casu_label in self.arena [layer]:
                if casu_label == key:
                    ## BIG ASSUMPTION HERE
                    result = self.arena [layer][casu_label]['sub_addr']
                    result = result [6:] #remove tcp://
                    result = result.split (':') [0]
                    return result
        return None

def main ():
    __create_example_config ()
    args = process_arguments ()
    darcm = DARC_Manager (args.project, args.arena, args.config)
    darcm.create_files ()
    darcm.create_workers_file ()
    return None

def process_arguments ():
    parser = argparse.ArgumentParser (
        description = 'Deploy, ASSISIS run and collect data manager.  Creates the assisi, dep, and nbg files given information about which programs run on each CASUs and which ones talk to each other')
    parser.add_argument (
        '--arena', '-a',
        metavar = 'FILENAME',
        type = str,
        required = True,
        help = 'Filename containing the description of available CASUs and their sockets'
    )
    parser.add_argument (
        '--config', '-c',
        metavar = 'FILENAME',
        type = str,
        required = True,
        help = 'Filename containing information which controllers to run in each CASUs and their connections'
    )
    parser.add_argument (
        '--project', '-p',
        metavar = 'P',
        type = str,
        default = 'project',
        help = 'Label used in the name of the assisi, dep, arena, and nbg files'
    )
    return parser.parse_args ()

def __create_example_config ():
    with open ('test.config', 'w') as fd:
        yaml.dump ({
            'controllers' : {
                'domset' : {
                    'main' : '/home/user/binary',
                    'extra' : ['/home/user/lib_1.py', '/home/user/utils.py'],
                    'args' : ['--verbose'] ,
#                    'results' : ['*.csv', '*.log'] ,
                    'results' : [] ,
                    'casus': [1, 2, 31]
                    }
                },
            'deploy': {
                'user' : 'pedro',
                'prefix' : 'folder/exp',
                'args': {
                    'add_casu_number': True,
                    'add_worker_address': True
                }
            },
            'graph': {
                'node_CASUs': {
                    'n1': [21, 22],
                    'n2': [23, 24],
                    'n3': [25, 26]
                },
                'edges': [['n1', 'n2'], ['n2', 'n3'], ['n3', 'n1']]
            }
        }, fd, default_flow_style = False)

if __name__ == '__main__':
    main ()
