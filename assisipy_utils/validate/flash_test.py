#!/usr/bin/env python
# -*- coding: utf-8 -*-

# VERSION 0.1

import argparse
from assisipy import casu
import time, datetime

DO_LOG=False
SYNC_PERIOD = 20 # maybe a minute is better but for testing in sim shorter ok
INTERVAL = 2.0

def flash_test(_name, _casu, _order):
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


def main():
    parser = argparse.ArgumentParser(description='simple tester program to flash casus in an externally-defined order')
    parser.add_argument('rtc', help='')
    parser.add_argument('--order', help='how long a delay before this one starts?', default=1.0, type=float)
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

    # to run a coordinated flash test, with delays appropriate to sync all the casus.
    flash_test(_name, _casu, args.order)

    #done, return


if __name__ == '__main__':
    main()

