#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
An EXTREMELY basic wrapper for bee behaviour, just to test
the handling of heterogeneity via config files.

No movement is implemented, only a change of color

'''

from assisipy import bee
import os, yaml
import time
import random
from assisilib.common import beelib


#{{{ BasicBee
class BasicBee(object):
    '''
    implementation of the behavoural model BeeClust as per Schmickl 2008.
    using Enki/assisipy bee interface; including extension to agitation by air.
    '''
    #{{{ initialiser
    def __init__(self, bee_name, logfile, pub_addr, sub_addr, conf_file=None,
                 verb=False):

        # process the input arguments and config file.
        self.bee_name = bee_name
        if conf_file is not None:
            with open(conf_file, 'r') as f:
                conf = yaml.safe_load(f)
        else:
            conf = {}
        self.override_fwd_clr           = conf.get('override_fwd_clr', False)
        self._fwd_clr                   = conf.get('fwd_clr', (0.3,0.3,0.3))
        self.verb = verb

        if self.verb:
            print "attempting to connect to bee with name %s" % bee_name
            print "\tpub_addr:{}".format(pub_addr)
            print "\tsub_addr:{}".format(sub_addr)

        '''
        instantiates a assisipy.bee object but not derived from bee (At present)
        default settings are 2nd argument, if not set by config file
        '''
        self.mybee = bee.Bee(name=self.bee_name, pub_addr=pub_addr,
                             sub_addr=sub_addr)

        # easiest way to show something about the bee state is through colour
        self.CLR_FWD  = (0.93, 0.79, 0)
        self.CLR_COLL_OBJ  = (0, 0, 1)
        self.CLR_COLL_BEE  = (0, 1, 0)
        self.CLR_WAIT  = (0.93, 0.0, 0)

        if self.override_fwd_clr:
            # special color for this bee from config file
            c = [float(n) for  n in self._fwd_clr.strip('()').split(',')]
            self.CLR_FWD = c

        self.mybee.set_color(*self.CLR_FWD)
    #}}}

    def behav(self):
        ''' this example currently has no 'behaviour' implemented!'''
        time.sleep(0.5)

    def stop(self):
        '''
        stop the bee and reset the color
        '''
        self.mybee.set_vel(0, 0)
        self.mybee.set_color() # default arguments -> yellow.

#}}}

if __name__ == "__main__":
    # handle command-line arguments
    parser = beelib.default_parser()
    args = parser.parse_args()

    random.seed()
    # set up the bee behaviour, including attaching to simulator
    logfile = os.path.join(args.logpath, "bee_track-{}.csv".format(args.bee_name))
    the_bee = BasicBee(
        bee_name=args.bee_name, logfile = logfile,
        pub_addr=args.pub_addr, sub_addr=args.sub_addr,
        conf_file=args.conf_file,)

    # run handler until keyboard interrupt. (or other SIGINT)
    try:
        while True:
            time.sleep(0.05)
            the_bee.behav()
    except KeyboardInterrupt:
        print "shutting down bee {}".format(args.bee_name)
        the_bee.stop()

