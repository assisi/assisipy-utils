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

DO_EXEC = True
DO_TEST = True
#
_C_OKBLUE =  '\033[94m'
_C_OKGREEN = '\033[92m'
_C_ENDC = '\033[0m'
_C_WARNING = '\033[93m'
_C_FAIL = '\033[91m'
_C_TEST = '\033[2;32;40m'
_C_ERR  = '\033[1;31m'


SEVERITY = {
    'I' : _C_OKBLUE,
    'W' : _C_WARNING,
    'F' : _C_FAIL,
    'E' : _C_ERR,
}


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
        self.TOOL_EXEC_AGENTS = self.config.get("tool_exec_agents", None)

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
        self._cmd_idx = 0

        #
        self._setup_dirs()
        self._setup_cmdlog()
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
        _ld = "{}-{}_rpt{}".format(
                self.config['PRJ_FILE'].split('.')[0],
                self.label, self.rpt)
        self.logdir = os.path.join(self.config['logbase'], _ld)
        self.disp_msg("mkdir {}".format(self.logdir))
        mkdir_p(self.logdir)
        self.procdir = os.path.join(self.logdir, 'proc')
        mkdir_p(self.procdir)

    def _setup_cmdlog(self):
        # open a logfile, for all commands executed to be entered.
        # borrowed log format from casu
        now_str = datetime.datetime.now().__str__().split('.')[0]
        now_str = now_str.replace(' ','-').replace(':','-')

        self._cmdlog = open(
            os.path.join(self.logdir, "commands-{}.log".format(now_str)),
            'w', 0 # bufsize=0 for unbuffered, =1 for line buffered)
        )

    def _add_pid_file(self, p1):
        '''
        keep track of all pids started by a given simulation, in case of
        crash, to know which processes to stop
        '''
        fn = os.path.join(self.procdir, "{}".format(p1.pid))
        now_str = datetime.datetime.now().__str__().split('.')[0]
        now_str = now_str.replace(' ','-').replace(':','-')
        with open(fn, 'w') as f:
            f.write("{}".format(now_str))

        f.close()

    def _remove_pid_file(self, p1):
        '''
        when we close a process, remove the pid file
        '''
        fn = os.path.join(self.procdir, "{}".format(p1.pid))
        if os.path.exists(fn):
            os.remove(fn)
            self.disp_msg("removed PID file {}".format(p1.pid))
        else:
            self.disp_msg("could not remove PID file for proc {}".format(p1.pid), level='D')


    # a bit of debug - write all active PIDs before closing them
    def check_stillactive_pids(self):
        raise  # TODO: implement! what was I working on...
        pass




    def close_active_processes(self, sig = signal.SIGINT):
        '''
        terminate all active process handles with the signal `sig`
        '''
        self.disp_msg("Closing down persistent procs")
        self.check_stillactive_pids()

        for p in self.p_handles:
            self.disp_msg("\t pgkill -{} {}".format(sig, p.pid))
            if p.pid is not None:
                os.killpg(p.pid, sig)
                self._remove_pid_file(p)


    def cd(self, pth):
        ''' convenience wrapper for ch dir since used so frequently '''
        self.disp_cmd_to_exec("cd {}".format(pth))
        os.chdir(pth)

    #}}}

    #{{{ output funcs
    def disp_msg(self, msg, level='I', clr=True):
        now = datetime.datetime.now()
        if clr:
            pre = SEVERITY.get(level, '')
            post = _C_ENDC
        else:
            pre = ""
            post = ""
        print "#{}[{}]{} {} > {}{}{}".format(pre, level, post,
            now.strftime("%H:%M:%S"), pre, msg, post)
        sys.stdout.flush()

    def disp_cmd_to_exec(self, cmd, level='I', verb=False, bg=False):
        now = datetime.datetime.now()
        _bgs = ""
        if bg: _bgs = "&"
        cmd_str = "#[{}] {} {:3} $  {} {}".format(
            level, now.strftime("%H:%M:%S"), self._cmd_idx, cmd, _bgs)
        print _C_TEST + cmd_str + _C_ENDC
        self._cmdlog.write(cmd_str + "\n")
        #print _C_TEST + "#[{}] {} $  {} {}".format(level, now.strftime("%H:%M:%S"), cmd, _bgs) + _C_ENDC
        sys.stdout.flush()
        self._cmd_idx += 1

    def done(self):
        if self._cmdlog is not None and self._cmdlog.closed is False:
            self._cmdlog.close()
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
        self.cd(wd)

        # non-blocking
        pg_cmd = "{}".format(self.TOOL_SIMULATOR)
        if self.pg_cfg_file is not None:
            pg_cmd += " -c {}".format(
            os.path.join(self.project_root, self.pg_cfg_file))
        self.disp_cmd_to_exec(pg_cmd, bg=True)
        p1 = wrapped_subproc(DO_TEST, pg_cmd, stdout=subprocess.PIPE,
                shell=True, preexec_fn=os.setsid)
        self.p_handles.append(p1)
        self._add_pid_file(p1)

        # sleep a bit for simulator to launch before attempting to connect to it
        self.disp_cmd_to_exec("sleep {}".format(2.0))
        time.sleep(2.0)

        # we do walls here for each population
        for pop, data in self.config['agents'].items():
            _ws = data.get('wall_spawner', None)
            if _ws is None:
                continue # skip to next population

            arena_bounds_file = os.path.join(
                self.logdir, "{}-arenalims.arena".format(pop))
            data['arena_bounds_file'] = arena_bounds_file

            spwn_cmd = "{} -l {} -o {}".format(_ws, pop, arena_bounds_file)
            self.disp_cmd_to_exec(spwn_cmd)
            p2 = wrapped_subproc(DO_TEST, spwn_cmd, stdout=subprocess.PIPE, shell=True)
            p2.wait()


        spwn_casus = "{} {}".format(self.TOOL_CASU_SPAWN, self.config['PRJ_FILE'])
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
        self.cd(wd)
        # non-blocking

        casu_cmd = "{} {}".format(self.TOOL_CASU_EXEC, self.config['PRJ_FILE'])
        outf = open(os.path.join(self.logdir, "casu_stdout.log"), 'w')
        self.disp_cmd_to_exec(casu_cmd + "> {}".format(outf.name))
        p1 = wrapped_subproc(DO_TEST,  casu_cmd, stdout=outf,
                shell=True, preexec_fn=os.setsid)
        self.p_handles.append(p1)
        self._add_pid_file(p1)
        self.f_handles.append(outf)

        self.disp_cmd_to_exec("sleep {}".format(self.calib_timeout))
        time.sleep(self.calib_timeout)
        self.disp_msg("calibration done, ready to spawn agents")


    def init_agents(self, ):
        '''
        This stage spawns agents from all populations as defined in config.
        The spawning is blocking.
        '''
        # this function does a bit more - it spawns the bees afterwards;
        # perhaps we should define spawn at a high level?
        wd = os.path.join(self.project_root, self.config['DEPLOY_DIR'])
        self.cd(wd)

        spawn_count = 0

        # we spawn all the agents for here for each population (blocking)
        for pop, data in self.config['agents'].items():
            _as = data.get('spawner', None)
            if _as is None:
                continue # skip to next population

            _ab_file = data.get('arena_bounds_file')
            if _ab_file is None:
                # without this file, the automatic spawner cannot proceed,
                # but it is possible that assumptions are written-in somewhere
                # so should allow for progress if this is really desired?
                self.disp_msg( (_C_WARNING +
                                """Missing arena bounds specification for popln
                                {}.  Skipping spawning stage for {} agents.
                                """.format(pop, data.get('size', -1)) + _C_ENDC ),
                               level='W')
                continue


            obj_listing = os.path.join(self.logdir, "{}-listing.csv".format(pop))
            data['obj_listing'] = obj_listing
            spwn_cmd = "{} -l {} -ol {} -a {} -n {} -e {}".format(
                _as, pop, obj_listing, data['arena_bounds_file'],
                data['size'],
                data.get('behav_script', "None"),)
            self.disp_cmd_to_exec(spwn_cmd)
            p2 = wrapped_subproc(DO_TEST, spwn_cmd, stdout=subprocess.PIPE, shell=True)
            p2.wait()
            data['agents_spawned'] = True
            spawn_count += 1

        self.disp_msg("Agents spawned from {} populations. Ready to exec.".format(spawn_count))

    def run_agents(self, ):
        '''
        This assumes the requirement of executing hanlders for all agents from
        all populations. The exec is non-blocking.
        '''

        # execute all agent behaviour scripts
        wd = os.path.join(self.project_root, self.config['DEPLOY_DIR'])
        self.cd(wd)
        for pop, data in self.config['agents'].items():
            _ab = data.get('behav_script', None)
            _spawned = data.get('agents_spawned', False)
            if _ab is None:
                if _spawned:
                    # emit a warning that this population will not be executed,
                    # despite having been spawned
                    self.disp_msg( """popln {} was spawned, but no behavioural
                                  handler defined.  Check specification if this
                                  is not desired.""".format(pop), level='W')

                continue # skip to next population

            if not _spawned:
                # currently do not permit external spawners, so skip exec of this
                # population, for any reason that the spawn has not happened.
                self.disp_msg( (_C_WARNING +
                                """popln {} was not spawned, so cannot guarantee
                                that agents exist. Skipping behavioural handlers.
                                """.format(pop) + _C_ENDC ),
                               level='W')
                continue

            #
            agent_cmd = "{} -ol {} --logpath {}".format(
                self.TOOL_EXEC_AGENTS, data['obj_listing'], self.logdir,)
            self.disp_cmd_to_exec(agent_cmd, bg=True)
            p1 = wrapped_subproc(DO_TEST, agent_cmd, stdout=subprocess.PIPE,
                                 shell=True, preexec_fn=os.setsid)
            self.p_handles.append(p1)
            self._add_pid_file(p1)





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
        self.cd(wd)

        # A. run retreiver -- don't hide output
        cll_cmd = "{} {} --logpath {}".format( self.TOOL_COLLECT_LOGS,
            self.config['PRJ_FILE'], self.logdir)
        self.disp_cmd_to_exec(cll_cmd)
        p2 = wrapped_subproc(DO_EXEC, cll_cmd,
                #stdout=subprocess.pipe, # allow stdout out
                shell=True)
        p2.wait()

        # 2. check #files in log path
        if expected_file_cnt is not None:
            cmd = "find {} -type f | wc -l ".format(self.logdir)

            lines = subprocess.check_output(cmd, shell=True).strip()
            if verb: print lines
            file_cnt = int(lines.split()[0])
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
        hdlr.init_agents()     # spawn agents
        hdlr.run_agents()      # connect handlers to agents
        if args.verb:
            hdlr.disp_msg("PIDs of persistent procs are {}".format(hdlr.pids))

        hdlr.wait_for_sim()    # main part to exec simulation
    except KeyboardInterrupt:
        hdlr.disp_msg("simln interrupted -- shutting down")


    hdlr.close_active_processes()
    hdlr.close_logs()
    hdlr.collect_logs(expected_file_cnt=expected_file_cnt)

    hdlr.cd(cwd) # go back to original location

    hdlr.disp_msg("------------- Simulation finished! -------------")
    hdlr.disp_msg(_C_OKBLUE + "Results are in {}".format(hdlr.logdir) + _C_ENDC)
    hdlr.disp_msg("------------- -------------------- -------------")
    hdlr.done()

if __name__ == '__main__':
   main()


