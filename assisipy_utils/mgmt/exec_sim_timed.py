#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''

A script that runs various parts of code of a simulation, assuming that
the following elements are present
- playground
- CASUs
- agents, possibly in multiple populations (namely, bees at present)

And the script provides
1. execution of relevant parts
2. hangs up all programs after a pre-specified length
3. data retrieval
And #2 is possible with ctrl-c.


Note: if DO_EXEC is False, a dummy run is performed and instead of true
subprocess objects being spawned, the class FakeProc is used.

Rob Mills - BioISI, FCUL & ASSISIbf - March 2016
Major parts of code following Aug 2015 setup


'''

import yaml, os, argparse, sys, errno
import subprocess, signal
import datetime, time

DO_EXEC = False
DO_TEST = True
#
_C_OKBLUE =  '\033[94m'
_C_ENDC = '\033[0m'
_C_WARNING = '\033[93m'
_C_FAIL = '\033[91m'



#{{{ support funcs
class FakeProc(object):
    '''

    Example usage:
        p1 = wrapped_subproc(DO_EXEC,  some_cmd, stdout=outf,
                shell=True, preexec_fn=os.setsid)

    compare the standard usage of Popen:
        p1 = subprocess.Popen(some_cmd, stdout=outf,
                shell=True, preexec_fn=os.setsid)

    '''
    def __init__(self):
        self.pid = None
        pass
    def wait(self):
        pass

def wrapped_subproc(do=True, *args, **kwargs):
    ''' either call subprocess, or ignore (with warning msg) if do is false'''
    if do:
        p1 = subprocess.Popen(*args, **kwargs)
    else:
        p1 = FakeProc()
        print _C_WARNING + "[WWW] did not execute {}".format(args) + _C_ENDC

    return p1

def mkdir_p(path):
    '''
    emulate 'mkdir -p' -
     create dir recursively; if the path exists, don't error
    '''
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise


#}}}

#{{{ class - simulation handler
class SimHandler(object):
    #{{{ initialiser
    def __init__(self, conf_file, label, rpt, **kwargs):

        # store params
        self.label = label
        self.conf_file   = conf_file
        self.rpt         = rpt

        # parse config file
        with open(self.conf_file) as _f:
            self.config = yaml.safe_load(_f)
        # extract additional config requirements, with defaults
        self.pg_cfg_file = self.config.get('playground_config', None)
        #self.pg_cfg_file = self.config.get('playground_config', 'config/Playground.cfg')
        self.sim_sec = int(float(self.config['simulation_runtime_mins']) * 60.)
        self.calib_timeout = int(self.config.get("calib_timeout", 20))

        # user scripts -- if not defined in conf file, this section will be skipped
        self.TOOL_SPAWN_WALLS = self.config.get('spawn_wall_tool', None)
        self.TOOL_SPAWN_AGENTS          = self.config.get("tool_spawn_agents", None)
        self.TOOL_LAUNCH_AGENT_HANDLERS = self.config.get("tool_launch_agent_handlers", None)

        # other params we use to execute simulation
        self.project_root = os.path.dirname(os.path.abspath(self.conf_file))

        # define tools
        self.TOOL_CASU_EXEC    = 'assisirun.py'
        self.TOOL_SIMULATOR    = "assisi_playground"
        self.TOOL_CASU_SPAWN   = "sim.py"
        self.TOOL_DEPLOY       = "deploy.py"
        self.TOOL_COLLECT_LOGS = "collect_data.py"



        # variables
        self.p_handles = []
        self.f_handles = []

        #
        self._setup_dirs()
    #}}}

    #{{{ process management
    def get_pids(self):
        '''
        every time PIDs are queried, check what p_handles we still have
        alive
        '''
        pids = [_p.pid for _p in self.p_handles]
        return pids

    def _setup_dirs(self):
        # set up all of the parts of a simulation before the main loop.
        _ld = "{}{}_n{}_rpt{}".format(
                self.config['PRJ_FILE'].split('.')[0],
                self.label, self.config['n_bees'], self.rpt)
        self.logdir = os.path.join(self.config['logbase'], _ld)
        self.disp_msg("mkdir {}".format(self.logdir))
        mkdir_p(self.logdir)

    def close_active_processes(self, sig = signal.SIGINT):
        '''
        terminate all active process handles with the signal `sig`
        '''
        self.disp_msg("Closing down persistent procs")

        for p in self.p_handles:
            self.disp_msg("\t pgkill -{} {}".format(sig, p.pid))
            if p.pid is not None:
                os.killpg(p.pid, sig)
    #}}}

    #{{{ output funcs
    def disp_msg(self, msg, level='I'):
        now = datetime.datetime.now()
        print "#[{}] {} > {}".format(level, now.strftime("%H:%M:%S"), msg)
        sys.stdout.flush()

    def disp_cmd_to_exec(self, cmd, level='I', verb=False, bg=False):
        now = datetime.datetime.now()
        _bgs = ""
        if bg: _bgs = "&"
        print "#[{}] {} $  {} {}".format(level, now.strftime("%H:%M:%S"), cmd, _bgs)
        sys.stdout.flush()
    #}}}

    #{{{ main stages of expt execution
    def pre_calib_setup(self, ):
        '''
        This stage involves
        - starting the playground
        - spawning CASUs
        - spawning walls
        - deploying code to the CASUs (this transfers, does not start exec)

        '''

        '''
        All p1 are nonblockign and returned
        all p2 are blocking and no handles kept.
        '''
        wd = os.path.join(self.project_root, self.config['DEPLOY_DIR'])
        self.disp_cmd_to_exec("cd {}".format(wd),)
        os.chdir(wd)

        # non-blocking
        pg_cmd = "{}".format(self.TOOL_SIMULATOR)
        if self.pg_cfg_file is not None:
            pg_cmd += " -c {}".format(
            os.path.join(self.project_root, self.pg_cfg_file))
        self.disp_cmd_to_exec(pg_cmd, )
        p1 = wrapped_subproc(DO_TEST, pg_cmd, stdout=subprocess.PIPE,
                shell=True, preexec_fn=os.setsid)
        self.p_handles.append(p1)

        time.sleep(2.0)
        spwn_cmd = "{} ".format (self.TOOL_SPAWN_WALLS)
        self.disp_cmd_to_exec(spwn_cmd)
        p2 = wrapped_subproc(DO_TEST, spwn_cmd, stdout=subprocess.PIPE, shell=True)
        p2.wait()

        spwn_casus = "{} {}".format(self.TOOL_CASU_SPAWN, self.config['ARENA_FILE'])
        self.disp_cmd_to_exec(spwn_casus)
        p2 = wrapped_subproc(DO_TEST, spwn_casus, stdout=subprocess.PIPE, shell=True)
        p2.wait()

        dply_cmd = "{} {}".format(self.TOOL_DEPLOY, self.config['PRJ_FILE'])
        self.disp_cmd_to_exec(dply_cmd)
        p2 = wrapped_subproc(DO_TEST, dply_cmd, stdout=subprocess.PIPE, shell=True)
        p2.wait()


        self.disp_msg("pre-calib setup complete.")
        pass

    def calib_casus(self):
        '''
        for now not separated, so here we simply start the casu
        program with assisi run, and add the process handle to
        internal list.
        Note: this stage also blocks for `calib_timeout`
        '''
        wd = os.path.join(self.project_root, self.config['DEPLOY_DIR'])
        self.disp_cmd_to_exec("cd {}".format(wd),)
        os.chdir(wd)
        # non-blocking

        casu_cmd = "{} {}".format(self.TOOL_CASU_EXEC, self.config['PRJ_FILE'])
        outf = open(os.path.join(self.logdir, "casu_stdout.log"), 'w')
        self.disp_cmd_to_exec(casu_cmd + "> {}".format(outf.name))
        p1 = wrapped_subproc(DO_TEST,  casu_cmd, stdout=outf,
                shell=True, preexec_fn=os.setsid)
        self.p_handles.append(p1)
        self.f_handles.append(outf)

        self.disp_cmd_to_exec("sleep {}".format(self.calib_timeout))
        time.sleep(self.calib_timeout)
        self.disp_msg("calibration done, ready to spawn bees")


    def run_agents(self, ):
        '''
        This assumes the requirement of spawning and executing all agents from
        two populations. The exec is non-blocking.
        '''
        # this function does a bit more - it spawns the bees afterwards;
        # perhaps we should define spawn at a high level?
        wd = os.path.join(self.project_root, self.config['DEPLOY_DIR'])
        self.disp_cmd_to_exec("cd {}".format(wd),)
        os.chdir(wd)


        for _arena in ['top', 'bot']:
            arena = "spawn_bees_{}.py".format(_arena)
            spwn_cmd = "python scripts/{} -n {} -ip {} --logpath {}".format(
                    arena, self.config['n_bees'], self.config['SIM_HOST_IP'],
                    self.logdir)
            self.disp_cmd_to_exec(spwn_cmd)
            p2 = wrapped_subproc(DO_EXEC, spwn_cmd, stdout=subprocess.PIPE, shell=True)
            p2.wait()

        # nonblocking - run bees
        bee_cmd = "python scripts/launch_bee_behaviours.py"
        bee_cmd += " -e {} --logpath {}".format(
                self.config['bee_behav_script'],
                self.logdir,)
        bee_top = bee_cmd + " -ol {}/bee_locations_top.csv".format(self.logdir,)
        bee_bot = bee_cmd + " -ol {}/bee_locations_bot.csv".format(self.logdir,)

        if 'top_bee_conf' in self.config:
            bee_top += " -lc {}".format(self.config['top_bee_conf'])
        if 'bot_bee_conf' in self.config:
            bee_bot += " -lc {}".format(self.config['bot_bee_conf'])

        self.disp_cmd_to_exec(bee_bot, bg=True)
        p1 = wrapped_subproc(DO_EXEC, bee_bot, stdout=subprocess.PIPE,
                shell=True, preexec_fn=os.setsid)
        self.p_handles.append(p1)

        self.disp_cmd_to_exec(bee_top, bg=True)
        p1 = wrapped_subproc(DO_EXEC, bee_top, stdout=subprocess.PIPE,
                shell=True, preexec_fn=os.setsid)
        self.p_handles.append(p1)



    def wait_for_sim(self):
        '''
        blocking wait for the period defined in config.
        '''
        self.disp_msg("running simulation now,  {}s".format(self.sim_sec), level='W')
        time.sleep(self.sim_sec)
        self.disp_msg("simln done", level='W')


    def close_logs(self):
        self.disp_msg("Closing all log files")
        for lf in self.f_handles:
            self.disp_msg("  closing {}".format(lf.name))
            lf.close()


    def collect_logs(self, verb=0, expected_file_cnt=None):
        '''
        retrieve all of the log files that the experiment or simulation
        produced. If `expected_file_cnt` is defined, count how many logs were
        retrieved and warn if mismatch
        '''
        # 1. retrieve data / logs
        wd = os.path.join(self.project_root, self.config['DEPLOY_DIR'])
        self.disp_cmd_to_exec("cd {}".format(wd),)
        os.chdir(wd)

        # A. run retreiver -- don't hide output
        cll_cmd = "{} {} --logpath {}".format( self.TOOL_COLLECT_LOGS,
            self.config['PRJ_FILE'], self.logdir)
        p2 = wrapped_subproc(DO_EXEC, cll_cmd,
                #stdout=subprocess.pipe, # allow stdout out
                shell=True)
        p2.wait()

        # 2. check #files in log path
        cmd = "find {} -type f | wc -l ".format(self.logdir)

        lines = subprocess.check_output(cmd, shell=True).strip()
        if verb: print lines
        file_cnt = int(lines.split()[0])
        if expected_file_cnt is not None:
            f_msg = "[WARNING; NOT ENUGH LOGFILES!]"
            if file_cnt >= expected_file_cnt: f_msg = "ok"
            self.disp_msg("There are {} files/dirs in {} ({})".format(file_cnt, self.logdir, f_msg))

    #}}}

#}}}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--conf', type=str, default=None, required=True)
    parser.add_argument('-l', '--label', type=str, default='sim_')
    parser.add_argument('-r', '--rpt', type=int, default=None, required=True)
    parser.add_argument('-v', '--verb', type=int, default=0,)
    args = parser.parse_args()
    #

    # manually compute the expected number of log files - it is specific to the
    # simulation.
    #n_casus = 4
    #expected_file_cnt = (
    #        ((config['n_bees']+1) * 2) + # nbees + location file
    #        (n_casus * 3) +              # 3 logs per casu
    #        1                 # one stdout log for all causs
    #        )
    expected_file_cnt = None


    cwd = os.getcwd()
    hdlr = SimHandler(conf_file=args.conf, label=args.label, rpt=args.rpt,)

    try:
        hdlr.pre_calib_setup() # initialise: playground, deploy, walls
        hdlr.calib_casus()     # connect and timeout calibration (blocking)
        hdlr.run_agents()      # spawn agents and connect handlers
        if args.verb:
            hdlr.disp_msg("PIDs of persistent procs are {}".format(hdlr.pids))

        hdlr.wait_for_sim()    # main part to exec simulation
    except KeyboardInterrupt:
        hdlr.disp_msg("simln interrupted -- shutting down")

    hdlr.close_active_processes()


    hdlr.close_logs()

    hdlr.collect_logs(expected_file_cnt=expected_file_cnt)

    os.chdir(cwd) # go back to original location

if __name__ == '__main__':
   main()


