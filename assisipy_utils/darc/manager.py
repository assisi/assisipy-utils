from __future__ import print_function

import argparse
import yaml

import assisipy.deploy
import assisipy.assisirun
import assisipy.collect_data

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

    def run (self, destination):
        d = assisipy.deploy.Deploy (self._assisi_filename)
        d.prepare ()
        d.deploy ()
        ar = assisipy.assisirun.AssisiRun (self._assisi_filename)
        ar.run ()
        self.monitor ()
        dc = assisipy.collect_data.DataCollector (self._assisi_filename, logpath = destination)
        dc.collect ()

    def monitor (self):
        raw_input ('Press ENTER to collect data from CASUs')

    def create_workers_file (self):
        not_used_CASUs = []
        contents = {
            'workers': []
        }
        for layer in self.arena:
            for casu_label in self.arena [layer]:
                casu_number = DARC_Manager.__casu_number_4_label (casu_label)
                if self.__is_casu_used (casu_label):
                    data = {
                        field : self.arena [layer][casu_label][field]
                        for field in ['sub_addr', 'pub_addr', 'msg_addr']
                    }
                    data ['casu_number'] = casu_number
                    hostname = self.__casu_hostname (casu_number)
                    data ['wrk_addr'] = 'tcp://{}:{}'.format (hostname, self.base_worker_port + casu_number)
                    contents ['workers'].append (data)
                else:
                    not_used_CASUs.append (casu_number)
        if len (not_used_CASUs) > 0:
            not_used_CASUs.sort ()
            print ('[III] Physical casus not used: {}'.format (not_used_CASUs))
        with open ('{}.workers'.format (self.project), 'w') as fd:
            yaml.dump (contents, fd, default_flow_style = False)
            fd.close ()
        print ('[II] Created workers file')

    def casu_key (self, number):
        return 'casu-{:03d}'.format (number)

    @staticmethod
    def __casu_number_4_label (casu_label):
        ## BIG ASSUMPTION HERE
        return int (casu_label [-3:])

    def __create_assisi_file (self):
        with open (self._assisi_filename, 'w') as fd:
            yaml.dump ({'arena' : self._arena_filename}, fd, default_flow_style = False)
            yaml.dump ({'dep' : self._dep_filename}, fd, default_flow_style = False)
            yaml.dump ({'nbg' : self._nbg_filename}, fd, default_flow_style = False)
            fd.close ()
        print ('[I] Created assisi file for project {}'.format (self.project))

    def __create_arena_file (self):
        not_used_CASUs = []
        contents = {}
        for layer in self.arena:
            for casu_label in self.arena [layer]:
                if self.__is_casu_used (casu_label):
                    if layer not in contents:
                        contents [layer] = {}
                    contents [layer][casu_label] = {
                        field : self.arena [layer][casu_label][field]
                        for field in ['sub_addr', 'pub_addr', 'msg_addr', 'pose']
                    }
                else:
                    not_used_CASUs.append (DARC_Manager.__casu_number_4_label (casu_label))
        if len (not_used_CASUs) > 0:
            not_used_CASUs.sort ()
            print ('[II] Physical casus not used: {}'.format (not_used_CASUs))
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
    args = process_arguments ()
    darcm = DARC_Manager (args.project, args.arena, args.config)
    darcm.create_files ()
    if args.legacy:
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
    parser.add_argument (
        '--legacy',
        action = 'store_true',
        help = 'Also generate the workers file'
    )
    return parser.parse_args ()

if __name__ == '__main__':
    main ()
