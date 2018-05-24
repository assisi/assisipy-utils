#!/usr/bin/env python
# -*- coding: utf-8 -*-

# VERSION 0.1

import argparse
from assisipy import casu
import time, datetime

DO_LOG=False
TSTR_FMT = "%Y/%m/%d-%H:%M:%S-%Z"

def flash_test(_name, _casu, _order, SYNC_PERIOD=20, INTERVAL=2.0):
    # order defines the offset from the next minute ?
    d = datetime.datetime.now()
    while d.second % SYNC_PERIOD > 1:
        print "{}: remainder is {}".format(_name, SYNC_PERIOD - (d.second % SYNC_PERIOD)), d.strftime("%c")
        time.sleep(0.9)
        d = datetime.datetime.now()


    # now we start at ~same time (without comms, sync barrier etc)
    delay = _order * INTERVAL
    time.sleep(delay)

    # flash, 2x, with 50% duty cycle
    print "{}: flashing now, 50pc cycle".format(_name.upper())
    for i in xrange(2):
        # on
        _casu.set_diagnostic_led_rgb(r=1)
        time.sleep(0.25)
        # off
        _casu.set_diagnostic_led_rgb(r=0, g=0, b=0)
        time.sleep(0.25)
    print "{}: completed flashing.".format(_name)


def writeback_test(_casu, _name, log_file):
    '''
    super simple test of writing state, checking we can do so.
    if successful, data goes to logfile.
    '''

    _rgb = _casu.get_diagnostic_led_rgb() # value to restore

    test_rgb = (0.3, 0.7, 0.11)
    s_test = "'(" + ", ".join(str(c) for c in test_rgb) + ")'"
    _casu.set_diagnostic_led_rgb(*test_rgb)
    time.sleep(2.0) # need to allow for it to be set and re-published.
    read_rgb = _casu.get_diagnostic_led_rgb()
    s_read  = "'(" + ", ".join(str(c) for c in read_rgb) + ")'"
    time.sleep(0.25)
    _casu.set_diagnostic_led_rgb(*_rgb) #restore

    # this doesn't say whether it was reading or writing that was a
    # problem... if it doesn't work.
    match = 0
    for s1, r1 in zip(test_rgb, read_rgb):
        if s1 == r1: match += 1

    if match == 3:
        print "[I] {} -- rgb color readback ok ({})".format(_name, s_read)
        log_file.write("node_set,  {}, {}\n".format(_name, s_test))
        log_file.write("node_read, {}, {}\n".format(_name, s_read))
    else:
        print "[E] {} -- rgb color readback failed (read {}, expecting {})".format(
            _name, s_read, s_test)


def main():
    parser = argparse.ArgumentParser(description='simple tester program to flash casus in an externally-defined order')
    parser.add_argument('rtc', help='')
    parser.add_argument('--order', help='how long a delay before this one starts?', default=1.0, type=float)
    parser.add_argument('--sync_period', type=float, default=10.0)
    parser.add_argument('--interval', type=float, default=2.0)
    args = parser.parse_args()

    # NOTE: we can't actually do this because there is a non-deterministic start! hmm

    # connect to casu
    if args.rtc.endswith('.rtc'):
        _name = args.rtc[:-4]
    else:
        _name = args.rtc

    _casu = casu.Casu(rtc_file_name=_name+'.rtc', log=DO_LOG)

    # first, read sensor values, and write to file
    # TODO (this can be done asynch, but really requires a log to file, then
    # TODO  automatic check on the final results.)
    #sensor_test(_name, _casu)


    with open("{}-msgtest.log".format(_name), 'w') as logfile:
        logfile.write("# {} msg test on {} started\n".format(
            datetime.datetime.now().strftime(TSTR_FMT), _name))

        writeback_test(_casu, _name, logfile)

    # to run a coordinated flash test, with delays appropriate to sync all the casus.
    flash_test(_name, _casu, args.order,
               SYNC_PERIOD=args.sync_period, INTERVAL=args.interval)

    print "=============== ALL done!! ==============="

    #done, return


if __name__ == '__main__':
    main()

