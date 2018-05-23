#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''

A script that runs various parts of code of an experiment that uses
only physical setup (i.e. no simulated components).

And the script provides
1. execution of relevant parts
2. hangs up all programs after a pre-specified length
3. data retrieval
And #2 is possible with ctrl-c.

Note: if DO_EXEC is False, a dummy run is performed and instead of true
subprocess objects being spawned, the class FakeProc is used.

Rob Mills - BioISI, FCUL & ASSISIbf - May 2016

'''


from exec_sim_timed import SimHandler
from exec_sim_timed import _C_ENDC, _C_OKBLUE
from assisipy_utils import tool_version
import argparse, os
import subprocess


def main():
    parser = argparse.ArgumentParser()
    tool_version.ap_ver(parser) # attach package dev version to parser
    parser.add_argument('-c', '--conf', type=str, default=None, required=True)
    parser.add_argument('-l', '--label', type=str, default='sim_')
    parser.add_argument('-r', '--rpt', type=int, default=None, required=True)
    parser.add_argument('--allow-overwrite', action='store_true')
    parser.add_argument('-S', '--dry-run', action='store_true')
    parser.add_argument('--verb', type=int, default=0,)
    args = parser.parse_args()
    #

    cwd = os.getcwd()
    hdlr = SimHandler(conf_file=args.conf, label=args.label, rpt=args.rpt,
                      allow_overwrite=args.allow_overwrite, dry_run=args.dry_run)
    hdlr.expt_type = "experiment"

    if args.dry_run:
        print "[I] all done with checks."
        return

    try:

        try:
            hdlr.phys_pre_calib_setup() # initialise - jst deployment and checks
            hdlr.calib_casus()     # connect and timeout calibration (blocking)
            if args.verb:
                hdlr.disp_msg("PIDs of persistent procs are {}".format(hdlr.pids))

            hdlr.wait_for_expt()    # wait for experiment to complete
        except KeyboardInterrupt:
            hdlr.disp_msg("simln interrupted -- shutting down")


        hdlr.close_active_processes()
        hdlr.close_logs()
        hdlr.collect_logs()

        hdlr.cd(cwd) # go back to original location

        hdlr.disp_msg("------------- Experiment finished! -------------")
        hdlr.disp_msg(_C_OKBLUE + "Results are in {}".format(hdlr.logdir) + _C_ENDC)
        hdlr.disp_msg("------------- -------------------- -------------")
        hdlr.done()

    finally:
        # try to clean up the terminal even if assisirun broke it.
        hdlr.disp_cmd_to_exec("stty sane", prestore=True)
        subprocess.call(["stty", "sane"])

if __name__ == '__main__':
   main()

