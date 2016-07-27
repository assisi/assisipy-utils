#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''

A tool to generate new specifications from the existing spec, solely for
running a test program that visually flashes on all of the casus in a
given setup.

This works locally, creating a sandbox

'''

import yaml

import argparse
import os, sys
import shutil

import pygraphviz as pgv



class TestCommConfig(object):
    """
    Class that generates .dep files and sandboxes for the connection validation
    """

    #{{{ initialiser
    def __init__(self, project_file_name, testlinks=True):
        """
        Parses the configuration files and initializes internal data structures.
        """
        self.proj_name = os.path.splitext(os.path.basename(project_file_name))[0]
        self.arena    = {}
        self.dep      = {}
        self.nbg_file = None
        self.TESTLINK = testlinks

        self.project_root = os.path.dirname(os.path.abspath(project_file_name))
        self.sandbox_dir = self.proj_name + '_commconfig' + '_sandbox'

        # save where we are before any changes, because cd is destructive
        # see http://stackoverflow.com/q/24323731
        self.scriptdir = os.path.abspath(os.path.dirname(sys.argv[0])) # see http://stackoverflow.com/a/27414086
        self.prepared = False
        if self.TESTLINK:
            self.test_controller = "msg_test.py"
        else:
            self.test_controller = "flash_test.py"

        self.test_dep_prefix = "_commtest"

        #{{{ read the original specification
        with open(project_file_name) as project_file:
            self.project = yaml.safe_load(project_file)

        self.nbg_file   = self.project.get('nbg')
        self.arena_file = self.project.get('arena')
        # Read the .arena file
        with open(os.path.join(self.project_root, self.arena_file)) as af:
            self.arena = yaml.safe_load(af)

        # Read the deployment file
        with open(os.path.join(self.project_root, self.project['dep'])) as dep_file:
            self.dep = yaml.safe_load(dep_file)

        self.out_project_file = "commtest" + self.proj_name + '.assisi'
        self.out_dep_file     = "commtest" + self.project['dep']
        #}}}

    #}}}

    #{{{ prep_commtest
    def prep(self):
        self.prep_commtest()
        self.prepared = True

    def prep_commtest(self):
        '''
        prepare the commtest code in local folder
        '''
        #{{{ directory setup stuff
        cwd = os.getcwd()
        print('Changing directory to {0}'.format(self.project_root))
        os.chdir(self.project_root)
        print('Preparing commtest deployment config!')

        # Clean up and create new sandbox folder
        sandbox_path = os.path.join(self.project_root, self.sandbox_dir)
        _msg = "created"
        if os.path.exists(sandbox_path):
            _msg = "overwritten"
        print("The folder \n\t{}\n will be {}".format(sandbox_path, _msg))
        try:
            shutil.rmtree(sandbox_path)
        except OSError:
            # The sandbox directory does not exist, no biggie
            pass

        os.mkdir(self.sandbox_dir)
        os.chdir(self.sandbox_dir)
        #}}}

        #{{{ construct a new deployment (dict)
        # this dep file to have entries for all CASUs in
        # original dep, inheriting many params but overriding some
        # and with added args and extra support files for those
        # CASUs with a calibration entry
        i = 0
        main_dep = {}
        for layer in sorted(self.arena):
            main_dep[layer] = {}
            for casu in sorted(self.arena[layer]):
                # find the basic deployment info
                depdata = self.dep[layer][casu]
                testdepinfo = {}
                # required, inherit directly from original
                for k in [ 'hostname', 'user', ]:#'prefix',]:
                    #[ 'controller']:
                    testdepinfo[k] = depdata[k] # fail if not defined


                testdepinfo['controller'] = self.test_controller
                testdepinfo['prefix'] = self.test_dep_prefix

                if self.TESTLINK:
                    # we need to send a few args and also extra files.
                    testdepinfo['args'] = ['--delay {}'.format(i)]
                    i += 1 # we need to compute the number of outlinks, not just
                    # one delay step per casu.
                    testdepinfo['args'] += ['--nbg {}'.format(self.nbg_file)]

                    testdepinfo['extra'] = [self.nbg_file, ]
                    testdepinfo['results'] = ['*.log']

                else:
                    # ignore these ones ### for k in [ 'extra', 'results']
                    # override these
                    testdepinfo['args'] = ['--order {}'.format(i)]
                    i += 1

                main_dep[layer][casu] = testdepinfo
        #}}}

        #{{{ write the constructed dicts to file
        sd = yaml.safe_dump(main_dep, default_flow_style=False)
        with open(self.out_dep_file, 'w')  as outdep:
            outdep.write(sd + "\n")

        # now do the project file - just update the .dep file
        mainproj = dict(self.project)
        mainproj['dep'] = self.out_dep_file

        sp = yaml.safe_dump(mainproj, default_flow_style=False)
        with open(self.out_project_file, 'w')  as outproj:
            outproj.write(sp + "\n")
        #}}}

        #{{{ finally, copy the .arena and .nbg files to the sandbox.
        # - and also the controller. (what is the source? should be the same as the tool;
        #   though i don't know how this works with setuptools)
        dst = os.path.join(self.project_root, self.sandbox_dir)
        src = os.path.join(self.project_root, mainproj['arena'])
        #print "src to dest: \n\t{} \n\t{}".format(src, dst)
        shutil.copy2(src, dst)
        src = os.path.join(self.project_root, mainproj['nbg'])
        #print "src to dest: \n\t{} \n\t{}".format(src, dst)
        shutil.copy2(src, dst)

        src = os.path.join( self.scriptdir, self.test_controller)
        shutil.copy2(src, dst)
        #}}}

        os.chdir(cwd)
    #}}}

    #{{{ check_links
    def check_links(self):
        '''
        a simple check on the links that are defined.
        - are all the links with independent names?
        - are all msg_addrs unique?
        - do all of the terminals exist?  [not sure whether this is a problem for earlier stage?]
        '''
        self._unique_msg_addrs()
        self._unique_link_labels()
        self._generate_msg_links()
    #}}}

    #{{{ _generate_msg_links
    def _generate_msg_links(self):
        '''
        for each link in the graph, put into a list a message --
        seq number, from, to
        '''
        self._msg_list = []
        #i = 0
        pass
    #}}}

    #{{{ _unique_link_labels
    def _unique_link_labels(self):
        # read the nbg graph.
        if self.nbg_file is None:
            print "[W] nbg is undefined, no link checks performed"
            return

        fatal_cnt = 0
        node_cnt = 0
        edge_cnt = 0
        _nf = os.path.join(self.project_root, self.nbg_file)
        G = pgv.AGraph(_nf)
        for node in G.nodes():
            node_cnt += 1
            _lbls = []
            #print node
            for e in G.out_edges(node):
                edge_cnt += 1
                lbl = e.attr.get('label')
                #print "\t", e, lbl
                _lbls.append(lbl)

            # find if any labels are duplicated. (since 64 nodes max in
            # casu nets, altough this is O(list^2), not really significant)
            duplicates = set([x for x in _lbls if _lbls.count(x) > 1])
            #
            if len(duplicates):
                for lbl in duplicates:
                    # find the targets now
                    tgts = []
                    for e in G.out_edges(node):
                        _lbl = e.attr.get('label')
                        if lbl == _lbl:
                            tgts.append(e[1])
                    print "[F] {} has used the msg label '{}' for multiple targets ({})".format(
                        node, lbl, len(tgts))
                    print "\t[", ", ".join(tgts), "]"

                    fatal_cnt += 1


        if fatal_cnt > 0:
            raise ValueError("[F] errors found ({}) in link specification. Aborting.".format(fatal_cnt))
        else:
            print "[I] no duplicate labels found in link specification. " + \
                "\n    Checked {} nodes and {} links".format(node_cnt, edge_cnt)

        return G
    #}}}

    #{{{ _unique_msg_addrs
    def _unique_msg_addrs(self):

        # are msg addr unique for all casus in the whole setup?
        # we can check this from the .arena file
        casu_cnt = 0
        fatal_cnt = 0
        all_addrs = {}
        for arena in self.arena:
            for _casu in self.arena[arena]:
                casu_cnt += 1
                ma = self.arena[arena][_casu].get('msg_addr', None)
                if ma is None:
                    print "[F] {} has no msg_addr defined.".format(_casu)
                    fatal_cnt += 1

                all_addrs[_casu] = ma

        # now we have all the msg_addrs, lets check there are no duplicates
        rev_addrs = {}
        for key, value in all_addrs.items():
            rev_addrs.setdefault(value, set()).add(key)
        # find any duplicates
        dup_addrs = [key for key, v in rev_addrs.items() if len(v) >1]
        if dup_addrs :
            for k in dup_addrs:
                dup_cas = list(rev_addrs[k])
                print "[F] the message address '{}' is used multiple times:".format(k)
                print "\n".join("\t" + e for e in dup_cas)
                fatal_cnt += len(dup_cas)

        self.all_addrs = rev_addrs


        if fatal_cnt > 0:
            raise ValueError("[F] errors found ({}) in CASU port specification. Aborting.".format(fatal_cnt))
        else:
            print "[I] no duplicate msg_addrs found in areana specification. " + \
                "\n    Checked {} casus".format(casu_cnt)

        #}}}

    #{{{ showcmds
    def showcmds(self, annotate):
        # simulation needs - simulator, sim.py deploy, assisirun.py
        print "\n" + "="*75
        print "[I] execute these commands to run full test and graph results"
        print "    (skip simulator and sim.py stages if using only physical casus)"
        print " "*4 + "-"*64

        print "cd {}".format(os.path.join(self.project_root, self.sandbox_dir))
        print "assisi_playground &"
        print "sim.py {}".format(self.out_project_file)
        print "deploy.py {}".format(self.out_project_file)
        print "assisirun.py {}".format(self.out_project_file)

        if annotate:
            print "collect_data.py {}".format(self.out_project_file)
            datadir = "data" + self.test_dep_prefix +  self.proj_name
            msg_file = "msgs.csv"
            print 'find "{}" -type f -name "*msgtest.log" -exec cat {} \; | grep -v ^# > {}'.format(datadir, "{}", msg_file)
            print "show_conntest_results.py {} -m {}".format(self.out_project_file, msg_file)
            #print "label_conn_results.py --nbg {} --arena {} -pf {} -m {}".format(
            #    self.nbg_file, self.arena_file, self.out_project_file, msg_file)
            print "neato -Tpdf {}.layout > results_{}.pdf".format(
                self.nbg_file, "")

        #
        print "="*75
    #}}}


def main():
    parser = argparse.ArgumentParser(description='Generate a deployment setup for calibration of CASUs')
    parser.add_argument('project', help='name of .assisi file specifying the project details.')
    parser.add_argument('--links', type=int, default=1, )
    # TODO: This is fully implemented yet!
    parser.add_argument('--layer', help='Name of single layer to action', default='all')
    parser.add_argument('-na', '--skip-annotate', help='annotate graph or visual test', action='store_true')
    args = parser.parse_args()
    if args.skip_annotate:
        args.annotate = False
    else:
        args.annotate = True

    project = TestCommConfig(args.project, testlinks=args.links)
    project.prep()
    project.check_links()
    project.showcmds(args.annotate)
    return project # for interactive inspection in ipython

if __name__ == '__main__':
    p = main()
