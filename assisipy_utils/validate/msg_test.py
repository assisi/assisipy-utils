#!/usr/bin/env python
# -*- coding: utf-8 -*-


from assisipy import casu
import time, os
import datetime
from numpy import array
import argparse
import yaml
import pygraphviz as pgv


# VERSION 0.3

DO_LOG=False
ERR = '\033[41m'
BLU = '\033[34m'
ENDC = '\033[0m'


'''

The basic idea is to send a message along every path in the network (nbg)
to check all paths work

The final result should be collected into a data dir, processed, and validated.


'''

#{{{ graph funcs
def get_outmap(fg, casu, verb=False):
    '''
    given the flattened graph, `fg`, find a map of connections for
    which the node `casu` should emit messages to.

    return a dict whose keys are the destinations and whose values
    are edge labels

    '''
    if casu not in fg:
        raise KeyError

    sendto = {}

    for src, _dest in fg.out_edges(casu):
        # attributes does not have a .get(default=X) so make useable copy
        attr = dict(fg.get_edge(src, _dest).attr)
        lbl = attr.get('label')
        # trim any layer info from the edge src/dest
        dest = str(_dest).split('/')[-1]

        if verb: print "\t--> {} label: {}".format(dest, lbl)
        sendto[dest] = lbl

    return sendto

def get_inmap(fg, casu, default_weight=0.0, verb=False):
    '''
    given the flattened graph, `fg`, find a map of connections for
    which the node `casu` may receive messages from

    return a dict whose keys are the sources and whose values are
    dicts with entries for labels and edgeweight.

    the value of `default_weight` is set on all weights if one is not
    specified in the graph file


    '''
    if casu not in fg:
        raise KeyError

    recvfrom = {}
    # and a map of incoming weights
    if verb: print "expect to receive from..."
    for src, dest in fg.in_edges(casu):
        attr = dict(fg.get_edge(src, dest).attr)
        lbl = attr.get('label', "")
        w = float(attr.get('weight', default_weight))

        if verb: print "\t<-- {} w={:.2f} label: {}".format(src, w, lbl)
        recvfrom[src] = { 'w': w, 'label': lbl }

    return recvfrom




def show_inout(nbg):
    for _casu in nbg.nodes():
        print "\n*** {} ***".format(_casu)

        # need to know who will send to
        # (why? how do the messages work?)
        my_sendto = []
        my_recvfrom = []
        print "Send to..."
        for src, _dest in nbg.out_edges(_casu):
            # attributes set is like a dict but not completely
            # - without a mechansim for get+default
            # so make a copy that is useable.
            attr = dict(nbg.get_edge(src, _dest).attr)
            lbl = attr.get('label')
            # the edge might be multi-layer, so throw away the layer since
            # not needed here
            dest = str(_dest).split('/')[-1]

            print "\t--> {} label: {}".format(dest, lbl)
            my_sendto.append(dest)

        # and a map of incoming weights
        print "expect to receive from..."
        for src, dest in nbg.in_edges(_casu):
            attr = dict(nbg.get_edge(src, dest).attr)
            lbl = attr.get('label')
            w = float(attr.get('weight', 0.0))

            print "\t<-- {} w={:.2f} label: {}".format(src, w, lbl)
            my_recvfrom.append(src)


def flatten_AGraph(nbg, layer_select=None):
    '''
    process a multi-layer CASU interaction graph file and return
    a flattened graph.

    If layer_select is set, only include nodes in the selected layer

    Note: does not support node properties!
    '''
    g = pgv.AGraph(directed=True, strict=False) # allow self-loops.


    for _n in nbg.nodes():
        # trim any layer info off the node
        l, n = _n.split('/')[0:2]
        #print n, _n
        if layer_select is not None and l != layer_select:
            print "[I] excluded node '{}' ('{}') since not in layer '{}'".format(
                n, _n, layer_select)
            continue

        # if we got here, not filtered, so add it
        g.add_node(n)


    for i, (_src, _dest) in enumerate(nbg.edges()):
        # trimmed versions
        ls, s = _src.split('/')[0:2]
        ld, d = _dest.split('/')[0:2]

        # first, filter on layers.  Note: for a messaging test within a single
        # layer, we should only include the edge if both nodes are in tgt layer
        if layer_select is not None:
            if ls != layer_select or ld != layer_select:
                print "[I] excluded edge '{}'-->'{}' since not wholly in layer '{}'".format(
                    s, d, layer_select)

                continue


        # if it doesn't exist already, add edge
        if not (s in g and d in g):
            print "[W] s,d not both present. not adding edge"
            continue
        #else:
        #    print "[I] adding {} -> {} ({} : {})".format(s, d,
        #                                                 s.split('-')[-1],
        #                                                 d.split('-')[-1])

        g.add_edge(s, d)
        #print "now we have {} edges (pre: {}, delta {})\n".format(
        #    pre, post, post-pre)

        # add any attributes to the flattened graph
        attr = dict(nbg.get_edge(_src, _dest).attr)

        e = g.get_edge(s, d)
        for k, v in attr.iteritems():
            e.attr[k]= v

    return g

#}}}

class TestMsgChannels(object):
    TSTR_FMT = "%Y/%m/%d-%H:%M:%S-%Z"

    #{{{ init
    def __init__(self, casu_name, logname, delay, nbg, msg_spec=None,
            timeout=50.0, sync_period=10.0, interval=6.0, layer_select=None):

        self._rtc_pth, self._rtc_fname = os.path.split(casu_name)
        if self._rtc_fname.endswith('.rtc'):
            self.name = self._rtc_fname[:-4]
        else:
            self.name = self._rtc_fname

        self.verb = 1
        self.timeout     = timeout
        self.interval    = interval
        self.sync_period = sync_period
        self.layer_select = layer_select
        self.nbg = nbg
        self.read_interactions()

        self.msg_spec = msg_spec
        self.read_msg_spec()
        self.logname = logname
        self.delay_steps = delay

        self._casu = casu.Casu(rtc_file_name=os.path.join(self._rtc_pth, self.name + ".rtc"), log=DO_LOG)
        self.seq = 0

        self.msgs_recv = 0
        self.log_file_name = "{}-msgtest.log".format(self.name)
        self.log_file = open(self.log_file_name, 'w')
        self.log_file.write("# {} msg test on {} started\n".format(
            datetime.datetime.now().strftime(self.TSTR_FMT), self.name) )


    #}}}

    def read_msg_spec(self):
        '''
        a file defines
        - which messages we expect to receive
        - which messages we are to send
        '''
        if self.msg_spec is None:
            return
        pass

    #{{{ read_interactions
    def read_interactions(self):
        g_hier = pgv.AGraph(self.nbg)
        g_flat = flatten_AGraph(g_hier, self.layer_select)
        # since in/out are both derived from the flattened, filtered graph, we
        # don't need to filter these generators as well (for layers)
        self.in_map = get_inmap(g_flat, self.name)
        self.out_map = get_outmap(g_flat, self.name, verb=True)
    #}}}



    #{{{ send_msg
    def send_msg(self, linkname):
        '''
        emit a message to the neighbour defined by `linkname`
        '''

        if linkname in self.out_map.values():
            s = "{}".format(self.seq)
            self._casu.send_message(linkname, s)
            self.seq += 1
    #}}}

    #{{{  (old/borrowed) routines
    def __old_parse_conf(self, conf_file):
        self._conf = {}
        if conf_file is not None:
            with open(conf_file) as f:
                self._conf = yaml.safe_load(f)

        self.use_diag_led = self._conf.get('use_diag_led', True)
        self.verb         = self._conf.get('verbose', 0)

        _ir = self._conf.get('IR', {})
        self.calib_steps  = _ir.get('calib_steps', 10)
        self.calib_gain   = _ir.get('calib_gain', 1.1)
        self.t_interval   = _ir.get('t_interval', 0.1)
        self.min_thresh   = _ir.get('min_thresh', 3.14)

        if self.verb > 4: print "[I] read config from {}".format(conf_file)
    def calibrate_ir(self):
        '''
        read IR sensors several times, take the highest reading seen
        as the threshold (with a multiplier)


        '''
        base_ir_thresholds = array([self.min_thresh] * 7) # default values
        if self.use_diag_led:
            self._casu.set_diagnostic_led_rgb(b=1, r=0, g=0)

        # read sensors
        for stp in xrange(self.calib_steps):
            if self.verb > 4: print "calib step {}".format(stp)
            for i, v in enumerate(self._casu.get_ir_raw_value(casu.ARRAY)):
                if v > base_ir_thresholds[i]:
                    base_ir_thresholds[i] = v

            time.sleep(self.t_interval*0.9)
            if self.use_diag_led:
                self._casu.set_diagnostic_led_rgb(b=0, r=0.1, g=0.1)
            time.sleep(self.t_interval*0.1)
            if self.use_diag_led:
                self._casu.set_diagnostic_led_rgb(b=1, r=0, g=0)


        # compute calibrate values
        self.ir_thresholds = base_ir_thresholds * self.calib_gain
        self.calib_data['IR'] = self.ir_thresholds.tolist()
        if self.verb > 4: print "[I] will dump these values:", self.calib_data['IR']

        self.update_calib_time(time.time())

        # finish procedure
        if self.use_diag_led:
            self._casu.set_diagnostic_led_rgb(b=0, r=0, g=0)
            self._casu.diagnostic_led_standby()


    def __old_write_levels_to_file(self):
        '''
        Write an array of IR levels to calibration file

        '''
        _dump = {self.name:self.calib_data}
        s = yaml.safe_dump(_dump, default_flow_style=False)
        with open(self.logname, "w") as f:
            f.write(s + "\n")
    #}}}

    #{{{ basic_sync_barrier
    def basic_sync_barrier(self):
        '''
        different casus start at quite different times if not on the same beaglebone.
        (also possibly if in a multi-sim or sim+phys setup)
        even the deployment time is non-negligable when >>1 casu

        so wait until a round period before starting
        - assumes all hardware using synchronised clocks -- achieved by ntp
        '''

        d = datetime.datetime.now()
        while d.second % self.sync_period > 1:
            print "{}: remainder is {}".format(
                self.name, self.sync_period - (d.second % self.sync_period)), d.strftime("%c")
            time.sleep(0.9)
            d = datetime.datetime.now()
    #}}}


    def flash(self, n=2, duty=0.5, cycle_len=0.5, clr=(1,0,0)):
        for i in xrange(n):
            # on
            self._casu.set_diagnostic_led_rgb(*clr)
            time.sleep(duty*cycle_len)
            # off
            self._casu.set_diagnostic_led_rgb(r=0, g=0, b=0)
            time.sleep((1.0-duty)*cycle_len)


    def emit_msgs(self):
        # we go through each of our neighbours, send a message
        for phys_dest, linkname in self.out_map.iteritems():
            self.send_msg(linkname)
            print "[I] attempted to send {} to {} ({})".format(
                self.seq -1, linkname, phys_dest)
            # when sending, flash 3x, blue. 25% cycle.
            self.flash(4, duty=0.25, clr=(0,0,1))


        pass

    #{{{ recv_all_incoming
    def recv_all_incoming(self, retry_cnt=0):
        '''lifted from enhacner.'''
        msgs = {}
        try_cnt = 0
        while True:
            msg = self._casu.read_message()

            if msg:
                txt = msg['data'].strip()
                src = msg['sender']
                nb =  float(txt.split()[0])
                msgs[src] = nb

                if self.verb > 0:
                    print "\t[i]<== {3} recv msg ({2} by): '{1}' bees, {4} from {0} {5}".format(
                        msg['sender'], nb, len(msg['data']), self.name, BLU, ENDC)
            else: # buffer emptied, return
                try_cnt += 1
                if try_cnt > retry_cnt: break

        return msgs
    #}}}

    #{{{ top-level routine
    def go(self):
        '''
        top-level routine
        '''
        # 1. go round main loop waiting for a message
        # 2. if time elapsed is enough to be my turn to emit, do so.
        # 3. sleep a bit.


        self.delay_secs = self.interval * self.delay_steps
        self.emitted = False

        # first do a quick get/set test and write to log.
        # to read anything, provided we get a value at all, should be enough?
        # no - because we get a default value before any real data has been
        # received.  So what we really need is to set a specific value, check
        # that when read back it is valid.  diagnostic LED I think.
        _rgb = self._casu.get_diagnostic_led_rgb() # value to restore

        test_rgb = (0.3, 0.7, 0.11)
        s_test = "'(" + ", ".join(str(c) for c in test_rgb) + ")'"
        self._casu.set_diagnostic_led_rgb(*test_rgb)
        time.sleep(2.0) # need to allow for it to be set and re-published.
        read_rgb = self._casu.get_diagnostic_led_rgb()
        s_read  = "'(" + ", ".join(str(c) for c in read_rgb) + ")'"
        time.sleep(0.25)
        self._casu.set_diagnostic_led_rgb(*_rgb) #restore

        # this doesn't say whether it was reading or writing that was a
        # problem... if it doesn't work.
        match = 0
        for s1, r1 in zip(test_rgb, read_rgb):
            if s1 == r1: match += 1

        if match == 3:
            print "[I] {} -- rgb color readback ok ({})".format(self.name, s_read)
            self.log_file.write("node_set,  {}, {}\n".format(self.name, s_test))
            self.log_file.write("node_read, {}, {}\n".format(self.name, s_read))
        else:
            print "[E] {} -- rgb color readback failed (read {}, expecting {})".format(
                self.name, s_read, s_test)


        self.init_time = time.time()



        while True:
            # 1. check for messages
            msgs = self.recv_all_incoming()
            self.msgs_recv += len(msgs)
            # 2. process messages
            if len(msgs):
                print "[I] recvd {} msgs".format(len(msgs))
                for sender, seq in msgs.iteritems():
                    print "\t seq {}, from {}".format(seq, sender)
                    self.flash(n=2, duty=0.5, cycle_len=0.4, clr=(1,0,0))
                    s = "{}, {}, {}".format(sender, self.name, seq)
                    self.log_file.write("msg_test, " + s + "\n")

            # 3. is it my turn to emit?
            now = time.time()
            if self.emitted is False:
                if now - self.init_time > self.delay_secs:
                    # do my emission sequence
                    self.emit_msgs()

                    self.emitted = True
                    elap = time.time() - self.init_time
                    t_remain = self.timeout - elap
                    print "[I] {} emitted all messages. {:.0f}s remain".format(
                        self.name, t_remain)
                    self.flash(n=1, duty=0.9, cycle_len=0.4, clr=(0,0.5,0))


            # 4. sleep a bit
            time.sleep(0.2)
            if now - self.init_time > self.timeout:
                break
        pass
    #}}}


if __name__ == '__main__':
    #{{{ main / interaction with cmdline
    parser = argparse.ArgumentParser()
    parser.add_argument('name', )
    #parser.add_argument('-c', '--conf', type=str, default=None)
    parser.add_argument('-o', '--output', type=str, default=None)
    parser.add_argument('--nbg', type=str, default=None)
    parser.add_argument('--timeout', type=float, default=60.0)
    parser.add_argument('--sync_period', type=float, default=10.0)
    parser.add_argument('--interval', type=float, default=6.0)
    parser.add_argument('--layer', help='Name of single layer to action', default=None)
    parser.add_argument('--delay', type=int, required=True,
                        help="how many periods to wait before emitting")
    args = parser.parse_args()

    c = TestMsgChannels(args.name, logname=args.output, delay=args.delay,
                        nbg=args.nbg, timeout=args.timeout,
                        sync_period=args.sync_period, interval=args.interval,
                        layer_select=args.layer)

    if c.verb > 0: print "Msg test - connected to {}".format(c.name)
    try:
        c.basic_sync_barrier()
        c.go()
    except KeyboardInterrupt:
        c._casu.stop()


    #c.write_levels_to_file()
    OK = (c.msgs_recv == len(c.in_map))
    msg = BLU + "OK" + ENDC
    if not OK: msg = ERR + "ERROR" + ENDC

    s = "# Recvd {} msgs. Expected {}. {}".format(c.msgs_recv, len(c.in_map), msg)
    print s
    c.log_file.write(s + "\n")
    s = "# Msg test '{}' - done. Recvd {} msgs".format(c.name, c.msgs_recv)
    if c.verb > 0: print s
    c.log_file.write(s + "\n")
    # tidy up
    c.log_file.close()
    #}}}
