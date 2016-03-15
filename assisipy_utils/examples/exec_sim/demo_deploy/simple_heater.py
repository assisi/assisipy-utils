#!/usr/bin/env python
# -*- coding: utf-8 -*-

# NOTE: THE #! IS CRUCIAL! in the deploy tools, it is agnostic to python
# so could be a different language. (gotcha #1)

from assisipy import casu
import argparse
import time


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('rtc', )
    parser.add_argument('-t', '--temp', type=float, default=None)
    args = parser.parse_args()

    # connect to casu
    c = casu.Casu(rtc_file_name=args.rtc, log=True)
    # set temperature
    if args.temp is None:
        c.temp_standby()
    else:
        c.set_temp(args.temp)
        r = (args.temp - 25.0) / (45.0 - 25.0)
        c.set_diagnostic_led_rgb(r=r, g=0.1, b=0.1)

    # wait until interrupt
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        c.temp_standby()
        c.set_diagnostic_led_rgb(0,0,0)

