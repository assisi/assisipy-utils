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

import yaml, os, argparse, sys
import shutil
import subprocess, signal
import datetime, time
import mgmt_utils as utils

from assisipy_utils import tool_version

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

# checks
CHECK_FAILED_FATAL = 1
CHECK_FAILED_WARN  = 3
CHECK_OK = 0




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


def check_files_exist(file_dict, report=False):
    '''
    support function that checks whether files exist
    expects a dictionary, with files as keys; works in place
    returns number of errors/missing files.
    '''
    # mark all as untested
    for fname in file_dict.keys():
        file_dict[fname] = False

    # test whether each one exists.
    for fname in file_dict.keys():
        exists = os.path.isfile(fname)
        file_dict[fname] = bool(exists)


    # report all that are missing.
    e = 0
    for fname, ex in file_dict.iteritems():
        _s = ""
        if report:
            _s += "   [I] {:1} ==> {}".format( int(exists), fname)
        if ex is False:
            #fname = os.path.realpath(os.path.join(pth, fi))
            _s = _C_ERR + "[E] {} does not exist".format(fname) + _C_ENDC
            e += 1
        if len(_s): print _s

    if report:
        if e > 0:
            print "[E] {} of {} files missing.".format(e, len(file_dict))
        #else:
        #    print "[I] {} files specified, all exist.".format(len(file_dict))

    return e

def chunker(seq, size):
    '''
    return an iterator over the sequence with `size` elements in each slice
    from  https://stackoverflow.com/a/434328
    '''
    return (seq[pos:pos + size] for pos in xrange(0, len(seq), size))

#}}}


#{{{ class - simulation handler
class SimHandler(object):
    #{{{ initialiser
    def __init__(self, conf_file, label, rpt, **kwargs):
        '''
        dry-run does the following:
            - generates all sandboxes as if to run all (specified) programs
            - test that all source files exist
            - verify the logdir is writeable

        '''

        # store params
        self.label = label
        self.conf_file   = conf_file
        self.rpt         = rpt
        self.expt_type   = "simulation"
        self.allow_overwrite = kwargs.get('allow_overwrite', False)
        self.dry_run = kwargs.get('dry_run', False)
        self.verb    = kwargs.get('verb', 0)

        self._deployed = False
        self._expt_run = False

        # parse config file
        with open(self.conf_file) as _f:
            self.config = yaml.safe_load(_f)

        # handle potentially empty arguments
        for key in ['agents',] :
            v = self.config.get(key, {})
            if v is None: self.config[key] = {}

        # extract additional config requirements, with defaults
        self.pg_cfg_file = self.config.get('playground_config', None)
        #self.pg_cfg_file = self.config.get('playground_config', 'config/Playground.cfg')
        self.sim_sec = int(float(self.config['simulation_runtime_mins']) * 60.)
        self.calib_timeout = int(self.config.get("calib_timeout", 20))

        # user scripts -- if not defined in conf file, this section will be skipped
        self.TOOL_EXEC_AGENTS = self.config.get("tool_exec_agents", None)

        # define tools - hard-coded!!! TODO: supply from where?
        self.TOOL_CASU_EXEC    = 'assisirun.py'
        self.TOOL_SIMULATOR    = self.config.get("SIMULATOR", "assisi_playground")
        self.TOOL_CASU_SPAWN   = "sim.py"
        self.TOOL_DEPLOY       = self.config.get("DEPLOY_TOOL", "deploy.py")
        self.TOOL_COLLECT_LOGS = self.config.get("COLLECT_LOG_TOOL", "collect_data.py")


        self.ARCHIVE_BEHAV_SCRIPT = True
        self.ARCHIVE_SPAWNER      = True

        self.project_root = os.path.dirname(
            os.path.abspath(os.path.expanduser(self.conf_file)))

        self._check_sim_addrspec()
        # branch ere:
        # 1. if dry-run, then we just check files exist etc
        # 2. otherwise, create archives, logfiles, etc
        if self.dry_run:
            self.check_deployment_exists()
            # parse the dep file itself. (.nbg and .arena files don't specify other files)
            self.validate_depfile(True)

            # check existence of tools(?) and args
            self.check_tools_exist(report=True)
            self.check_toolargs_exist(report=True)
            self.check_agent_tools(report=True)

            # not sure how to exit the initialiser?
            return


        self._setup_archives()
        # other params we use to execute simulation


        # variables
        self.p_handles = []
        self.f_handles = []

        self._cmd_idx = 0
        self._pre_cmdlog = [] # store any commands before log is opened

        # check whether the logdir exists already
        self._check_and_mk_logdir()
        self._setup_dirs()
        self._setup_cmdlog()

        self._arch_depconf()

    def _check_sim_addrspec(self, ):
        '''
        if defined in config, include custom address for simulator
        '''
        self.CUSTOM_ADDRS = False
        self.custom_subaddr = None
        self.custom_pubaddr = None
        if "SIM_HOST" in self.config:
            ip = self.config['SIM_HOST'].get('addr')
            sp = self.config['SIM_HOST'].get('sub')
            pp = self.config['SIM_HOST'].get('pub')
            if ip is None or sp is None or pp is None:
                raise RuntimeError("[F] incomplete specification of sim_host")
            self.CUSTOM_ADDRS = True

            self.custom_pubaddr = "tcp://{}:{}".format(ip, pp)
            self.custom_subaddr = "tcp://{}:{}".format(ip, sp)

            if self.verb >1:
                self.disp_msg("using custom simulator pubaddr: {}".format(self.custom_pubaddr))
                self.disp_msg("using custom simulator subaddr: {}".format(self.custom_subaddr))


        pass

    def _setup_archives(self):
        # default is to archive all, for now
        # but anything in config can override
        self.selected_archives = {
            'deploy_sandbox' : True,
            #'' : True
        }

        cfg_arch = self.config.get('archives', {})
        for ctg, v in cfg_arch.iteritems():
            self.selected_archives[ctg] = v


    #}}}

    #{{{ process management
    def get_pids(self):
        '''
        every time PIDs are queried, check what p_handles we still have
        alive
        '''
        pids = [_p.pid for _p in self.p_handles]
        return pids

    def _check_and_mk_logdir(self):
        _ld = "{}-{}_rpt{}".format(
                self.config['PRJ_FILE'].split('.')[0],
                self.label, self.rpt)
        logbase = os.path.expanduser(self.config['logbase'])
        logdir = os.path.join(logbase, _ld)
        #logdir = os.path.join(self.config['logbase'], _ld)

        if os.path.exists(logdir):
            if not self.allow_overwrite:
                msg = _C_FAIL + "[F] logpath already exists." + _C_ENDC
                msg += "\n\t{}".format(logdir)
                msg += _C_FAIL + "\nconsider the --allow-overwrite option" +\
                    "if you meant to reuse the path" + _C_ENDC

                raise RuntimeError(msg)
            else: # emit an info message that we are overwriting path.
                msg = "re-using path {} since --allow-overwrite is enabled".format(logdir)
                self.disp_msg(msg)

        # if it doesn't exist, or --allow-overwrite is set, proceed with this
        # as the logdir
        self.logdir = logdir



    def _setup_dirs(self):
        # set up all of the parts of a simulation before the main loop.
        self.mkdir(self.logdir, prestore=True)
        self.procdir = os.path.join(self.logdir, 'proc')
        self.mkdir(self.procdir, prestore=True)
        self.archdir = os.path.join(self.logdir, 'archive')
        self.mkdir(self.archdir, prestore=True)
        self.stagelogdir = os.path.join(self.logdir, 'stage_logs')
        self.mkdir(self.stagelogdir, prestore=True)
        #

        self.pg_img_dir = None # default case
        #if 'playground_args' in self.config:
        _pg_args = self.config.get('playground_args', [])
        if any(["img_path" in _ for _ in _pg_args]):
            # we expect the pg to emit images and will then create a
            # directory for it; also declare this as the parameter.
            self.pg_img_dir = os.path.join(self.logdir, "snapshots")
            self.mkdir(self.pg_img_dir, prestore=True)


    def _setup_cmdlog(self):
        # open a logfile, for all commands executed to be entered.
        # borrowed log format from casu
        now_str = datetime.datetime.now().__str__().split('.')[0]
        now_str = now_str.replace(' ','-').replace(':','-')

        self._cmdlog = open(
            os.path.join(self.logdir, "commands-{}.log".format(now_str)),
            'w', 0 # bufsize=0 for unbuffered, =1 for line buffered)
        )
        for cmd_str in self._pre_cmdlog:
            self._cmdlog.write(cmd_str + "\n")

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
        w_cnt = 0
        pids = [p.pid for p in self.p_handles]
        _s_p = " ".join([str(_p) for _p in pids])
        self.disp_msg('Currently active processes are: {}'.format(_s_p))
        for pid in pids:
            # check whether there is a file corresponding to this still?
            fn = os.path.join(self.procdir, "{}".format(pid))
            if not os.path.exists(fn):
                self.disp_msg("file for {} does not exist!".format(pid), level='W')
                w_cnt += 1

        if w_cnt >0:
            self.disp_msg("{} problems encountered!".format(w_cnt), level='W')

        return w_cnt


    def _arch_dep_sandbox(self):
        '''
        copy the sandbox made by deploy tool into archive.
        '''
        if self._deployed:
            depdir = os.path.join(self.project_root, self.config['DEPLOY_DIR'])
            prj_name = os.path.splitext(os.path.basename(self.config['PRJ_FILE']))[0]
            sandbox_dir = prj_name + '_sandbox'
            src = os.path.join(depdir, sandbox_dir)
            dst = os.path.join(self.archdir, "sandbox_dep")# sandbox_dir)
            #print _C_ERR + "[I] will copy \n\tfrom {}\n\tto {}  ".format(src, dst)
            try:
                self.copytree(src, dst)
            except IOError as e:
                print "[W] data not found?", e
        else:
            print "[W] called at a bad time."


        #self._deparchdir = os.path.join(self.archdir, 'dep')
    #defcopytree(self, src, dst, symlinks=False, ignore=None)
        pass

    def _arch_depconf(self):
        '''
        copy all of the config files from deployment into the archive
        '''

        self._deparchdir = os.path.join(self.archdir, 'dep')
        self.mkdir(self._deparchdir)
        files = []

        pf = os.path.join(self.project_root, self.config['DEPLOY_DIR'], self.config['PRJ_FILE'])

        with open(pf) as project_file:
            project = yaml.safe_load(project_file)
            for key in ['arena', 'dep', 'nbg']:
                _f = project.get(key, None)
                if _f is not None:
                    src = os.path.join(self.project_root, self.config['DEPLOY_DIR'], _f)
                    files.append(src)


        for f in [self.conf_file, pf] + files :
            if os.path.exists(f):
                self.copyfile(f, dest=self._deparchdir)
            else:
                print "[W] skipping {} since does not exist".format(f)




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

    def mkdir(self, pth, prestore=False):
        ''' convenience wrapper to ensure mkdirs are logged '''
        self.disp_cmd_to_exec("mkdir -p {}".format(pth), prestore=prestore)
        utils.mkdir_p(pth)

    def copyfile(self, src, dest):
        self.disp_cmd_to_exec("cp -p {} {}".format(src, dest))
        shutil.copy2(src, dest)

    def copytree(self, src, dst, symlinks=False, ignore=None):
        ''' copy a directory, recursively'''
        self.disp_cmd_to_exec("cp -pr {} {}".format(src, dst))
        # see http://stackoverflow.com/a/12514470
        # and also https://stackoverflow.com/a/13814557
        if not os.path.exists(dst):
            os.makedirs(dst)
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if os.path.isdir(s):
                try:
                    shutil.copytree(s, d, symlinks, ignore)
                except (shutil.Error, OSError) as e:
                    self.disp_msg("problem with copying tree {} to {} \n\t{}".format(src, dst, e), level='W')
                    pass
            else:
                shutil.copy2(s, d)

    #{{{ process stage outputs
    def write_stage_stdout_log(self, out, stagename, this_pid):
        '''
        emit to file the standard output from a given stage
        '''
        _fn = os.path.join(
            self.stagelogdir, '{}.{}.stdout'.format(stagename, this_pid))
        with open(_fn, 'w') as f:
            f.writelines(out)

    def process_stage_error_log(self, err, stagename, this_pid, ):
        '''
        if there is output in stderr, 1) write to stagelog, and 2_ parse
        the stderr output from a given subprocess execution.
        If there are errors indicated in the output, count and report how
        many (use blank lines to separate)
        '''
        if err is not None and len(err):
            _fn = os.path.join(
                self.stagelogdir, '{}.{}.stderr'.format(stagename, this_pid))
            with open(_fn, 'w') as f:
                f.writelines(err)

            ei, E = utils.chunk_text_by_blankline(err)
            level = 'W'
            if "error" in err.lower(): level = 'E'
            self.disp_msg(
                "{} warning/error entries in '{}' stage".format(ei, stagename),
                level=level)
            if self.verb > 0:
                for k, v in E.items():
                    print "{}:\t".format(k), _C_WARNING + "\n".join(v) + _C_ENDC
        pass



    #}}}

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

    def disp_cmd_to_exec(self, cmd, level='I', verb=False, bg=False, prestore=False):
        now = datetime.datetime.now()
        _bgs = ""
        if bg: _bgs = "&"
        cmd_str = "#[{}] {} {:3} $  {} {}".format(
            level, now.strftime("%H:%M:%S"), self._cmd_idx, cmd, _bgs)
        print _C_TEST + cmd_str + _C_ENDC
        if prestore:
            self._pre_cmdlog.append(cmd_str)
        else:
            self._cmdlog.write(cmd_str + "\n")
            #print _C_TEST + "#[{}] {} $  {} {}".format(level, now.strftime("%H:%M:%S"), cmd, _bgs) + _C_ENDC
            sys.stdout.flush()
        self._cmd_idx += 1

    def done(self):
        if self._cmdlog is not None and self._cmdlog.closed is False:
            self._cmdlog.close()
    #}}}

    #{{{ validation
    def check_deployment_exists(self):
        '''
        check that the deployment working dir exists, and that the key
        deployment files exist (And are readable?)
        '''
        check_passed = CHECK_OK
        # 1. depdir exists?
        wd = os.path.join(self.project_root, self.config['DEPLOY_DIR'])
        if not os.path.isdir(wd):
            self.disp_msg("[F] deployment dir does not exist!: {}".format(wd),
                          level='F')
            return CHECK_FAILED_FATAL

        #self.cd(wd) # needed?
        # 2. project file. This one is essential too.
        pf = os.path.join(self.project_root, self.config['DEPLOY_DIR'], self.config['PRJ_FILE'])
        if not os.path.isfile(pf):
            self.disp_msg("[F] assisi project file does not exist!: {}".format(pf),
                          level='F')
            return CHECK_FAILED_FATAL

        # 3. now read the spec for key files.
        files = []
        self.depfile = None

        with open(pf) as project_file:
            project = yaml.safe_load(project_file)
            for key in ['arena', 'dep', 'nbg']:
                _f = project.get(key, None)
                if _f is not None:
                    src = os.path.join(self.project_root, self.config['DEPLOY_DIR'], _f)
                    files.append(src)
                    if key is 'dep':
                        self.depfile = src

                else:
                    self.disp_msg("[W] {} file is not specified.".format(key), level='W')
                    check_passed = CHECK_FAILED_WARN


        # 4. for all specified files, check they exist
        for f in [self.conf_file, pf] + files :
            if not os.path.exists(f):
                self.disp_msg("[F] specified deployment file does not exist {}".format(f),
                              level='F')
                check_passed = CHECK_FAILED_FATAL

        return check_passed

    #{{{ validate_depfile
    def validate_depfile(self, report=False):
        '''
        read an assisi deployment .dep file, check that the relevant files are
        all exist.
        this should be tested from the path ...
        and check all files in the parameters CONTROLLER and EXTRA (list)

        '''
        if self.depfile is None:
            return CHECK_FAILED_WARN

        d = yaml.load(open(self.depfile))
        i = 0
        # construct dictionary of dependency files, with full path
        # note: references are relative to depfile location
        pth = os.path.dirname(os.path.realpath(self.depfile))
        files = {}
        for arena in d.keys():
            for casu in d[arena].keys():
                ctrlr = d[arena][casu].get('controller', None)
                extra = d[arena][casu].get('extra', [])
                if ctrlr is not None:
                    _f = os.path.realpath(os.path.join(pth, ctrlr))
                    files[_f] = False
                    i += 1
                for fi in extra:
                    _f = os.path.realpath(os.path.join(pth, fi))
                    files[_f] = False
                    i += 1

        if report:
            print "[ ] checking existence of referred files in depfile... "
        e = check_files_exist(files, report=report)

        # how many files are missing
        _s = "[I] references to {} files ({} unique) in depfile '{}'.".format(
            i, len(files), os.path.basename(self.depfile) )

        if e > 0:
            _s = _C_ERR + _s + "!! {} files not found!!".format(e) + _C_ENDC
        else:
            _s = _C_OKGREEN + _s + _C_ENDC

        if report or e > 0:
            print _s
        return e
    #}}}

    #{{{ check_tools_exist
    def check_toolargs_exist(self, report=False):
        if report:
            print "[ ] checking existence of files in tool args..."
        files = {}
        i = 0
        # self.pg_cfg_file is used with the assisi_playground
        if self.pg_cfg_file is not None:
            # assisi conf file should be relative to proj root
            _f = os.path.join(self.project_root, self.pg_cfg_file)
            files[_f] = False
            i += 1

        e = check_files_exist(files, report=report)

        # how many files are missing
        _s = "[I] references to {} files ({} unique) in tool args.".format(
            i, len(files), )
        if e > 0:
            _s = _C_ERR + _s + "!! {} files not found!!".format(e) + _C_ENDC
        else:
            _s = _C_OKGREEN + _s + _C_ENDC

        if report or e > 0:
            print _s
        return e

    def check_tools_exist(self, report=False):
        # tools
        if report:
            print "[ ] checking tools on path..."
        tool_list = [
            self.TOOL_EXEC_AGENTS, self.TOOL_CASU_EXEC, self.TOOL_SIMULATOR,
            self.TOOL_CASU_SPAWN, self.TOOL_DEPLOY, self.TOOL_COLLECT_LOGS]
        missing_tools = []

        for tool in tool_list:
            if tool is not None:
                res = utils.which(tool)
                if res is None:
                    missing_tools.append(tool)
                    self.disp_msg(
                        "  tool {} is not on path. Overall exec may not run".format(tool),
                        level='W')
                else:
                    if report:
                        print "   [I] {} OK".format(tool)

        if report:
            if len(missing_tools) == 0:
                print _C_OKGREEN + \
                    "[I] all {} tools available on path".format(len(tool_list)) \
                    + _C_ENDC
            else:
                print _C_WARNING + \
                    "[W] {} tools unavailable on path".format(len(missing_tools)) \
                    + _C_ENDC


    #}}}

    #{{{ check_agent_tools
    def check_agent_tools(self, report=False):
        '''
        for each population, check the tools and files defined all exist
        '''

        wd = os.path.join(self.project_root, self.config['DEPLOY_DIR'])

        # every pop spec could have
        # - a behav_script (this should be a relative or abs path, python file)
        # - archives, a list of config files, etc
        # - a wall spawner, (execution command line, )
        # - an agent spawner.
        print "[ ] checking existence of files and scripts in agent spec '{}' ...".format(self.conf_file)

        files = {}
        i = 0
        _ag_data = self.config.get('agents', {}) # if nothing defined, ignore.
        for pop, data in _ag_data.items():
            # behav script:
            bs = data.get('behav_script', None)
            if bs is not None:
                f = os.path.realpath(os.path.join(wd, bs))
                files[f] = False
                i += 1

            archs = data.get('archives', [])
            for a in archs:
                f = os.path.realpath(os.path.join(wd, a))
                files[f] = False
                i += 1

            # wall spawner and spawner are commands, referring to user-scripts
            for key in ['wall_spawner', 'spawner']:
                cmd = data.get(key, None)
                if cmd is not None:
                    exe = utils.extract_scriptname(cmd)
                    f = os.path.realpath(os.path.join(wd, exe))
                    files[f] = False
                    i += 1

        # now check all teh files exist and report.
        e = check_files_exist(files, report=report)
        # how many files are missing
        _s = "[I] references to {} files ({} unique) in agent spec.".format(
            i, len(files), )
        if e > 0:
            _s = _C_ERR + _s + "!! {} files not found!!".format(e) + _C_ENDC
        else:
            _s = _C_OKGREEN + _s + _C_ENDC

        if report or e > 0:
            print _s
        return e

    #}}}

    #}}}

    #{{{ main stages of expt execution
    #{{{ sim -only version for pre_calib_setup
    def pre_calib_setup(self, ): #noqa
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

        if self.pg_img_dir is not None:
            pg_cmd += " --Output.img_path {}".format(
                self.pg_img_dir)
        # pass on any extra args to playground
        _pg_args = self.config.get('playground_args', [])
        for (arg, val) in chunker(_pg_args, 2):
            if arg == "--Output.img_path":
                continue
            pg_cmd += " {} {} ".format(arg, val)

        # add in switches for custom addresses if defined
        if self.CUSTOM_ADDRS:
            pg_cmd += " --pub_addr {} --sub_addr {} ".format(
                self.custom_pubaddr, self.custom_subaddr)



        self.disp_cmd_to_exec(pg_cmd, bg=True)
        # setup files for logging output.
        _stage = os.path.splitext(os.path.basename(self.TOOL_SIMULATOR))[0]
        f_simulator_stdout = open(
            os.path.join( self.stagelogdir, "{}.stdout".format(_stage)), 'w')
        f_simulator_stderr = open(
            os.path.join( self.stagelogdir, "{}.stderr".format(_stage)), 'w')

        p1 = wrapped_subproc(DO_TEST, pg_cmd, stdout=f_simulator_stdout,
                             stderr=f_simulator_stderr,
                             shell=True, preexec_fn=os.setsid)
        self.p_handles.append(p1)
        self._add_pid_file(p1)
        self.f_handles.append(f_simulator_stdout)
        self.f_handles.append(f_simulator_stderr)

        # sleep a bit for simulator to launch before attempting to connect to it
        self.disp_cmd_to_exec("sleep {}".format(2.0))
        time.sleep(2.0)

        #{{{ we spawn walls here for each population
        _ag_data = self.config.get('agents', {})
        for pop, data in _ag_data.items():
        #for pop, data in self.config['agents'].items():
            _ws = data.get('wall_spawner', None)
            _spec = data.get('wall_spec', None)
            if _ws is None:
                if _spec is None: # nothing defined, OK but skip
                    continue # skip to next population
                else: # specfile defined, OK
                    # we can continue, we just enter the spec into db. (another
                    # popln or tool has (or will have) handled generating spec)

                    data['arena_bounds_file'] = os.path.join(self.logdir, _spec)
                    continue
            else:
                if _spec is not None: # BOTH defined -- clash
                    raise RuntimeError, "[E] cannot proceed with BOTH a wall spawning progam and a specfile declared: conflicting config"
                else: # spawner defined, specfile undef, OK, run it
                    pass

            arena_bounds_file = os.path.join(
                self.logdir, "{}-arenalims.arena".format(pop))
            data['arena_bounds_file'] = arena_bounds_file

            spwn_cmd = "{} -l {} -o {}".format(_ws, pop, arena_bounds_file)
            # add in switches for custom addresses if defined (note that
            # the HOST subaddr is the client/tool *pub* addr)
            if self.CUSTOM_ADDRS:
                spwn_cmd += " --pub-addr {} --sub-addr {} ".format(
                    self.custom_subaddr, self.custom_pubaddr)
            self.disp_cmd_to_exec(spwn_cmd)
            p2 = wrapped_subproc(DO_TEST, spwn_cmd, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, shell=True)
            p2.wait()

            this_pid = p2.pid
            out, err = p2.communicate()
            _stage = "spawn_walls_{}".format(pop)
            self.write_stage_stdout_log( out, _stage, this_pid)
            self.process_stage_error_log(err, _stage, this_pid)

            if self.ARCHIVE_SPAWNER and _ws is not None:
                if os.path.isfile(_ws):
                    pth = os.path.join(self.archdir, pop)
                    self.mkdir(pth)
                    self.copyfile(_ws, pth)
        #}}}

        #{{{ spawn the casus
        #spwn_casus = "{} {}".format(self.TOOL_CASU_SPAWN, self.config['PRJ_FILE'])
        # TODO: until PR#39 is accepted, this needs to give the .arena file!
        a_file = None
        with open(self.config['PRJ_FILE']) as project_file:
            project = yaml.safe_load(project_file)
            a_file = project.get('arena', None)

        if a_file is not None:
            spwn_casus = "{} {}".format(self.TOOL_CASU_SPAWN, a_file)
            sim_extra = self.config.get('sim_args', "")
            spwn_casus += " " + sim_extra

            # add in switches for custom addresses if defined (note that
            # the HOST subaddr is the client/tool *pub* addr)
            if self.CUSTOM_ADDRS:
                spwn_casus += " --address {} --sub-addr {} ".format(
                    self.custom_subaddr, self.custom_pubaddr)

            self.disp_cmd_to_exec(spwn_casus)
            p2 = wrapped_subproc(
                DO_TEST, spwn_casus, shell=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,)
            p2.wait()
            this_pid = p2.pid
            out, err = p2.communicate()
            self.write_stage_stdout_log( out, "sim", this_pid)
            self.process_stage_error_log(err, "sim", this_pid)

        #}}}

        self.deploy()

        self.disp_msg("pre-calib setup complete.")
    #}}}
    #{{{ phys-only version for pre_calib_setup
    def phys_pre_calib_setup(self, ):
        '''
        This stage involves
        - (check the CASUs exist? check timing of CASUs login via ntp?)
        - deploying code to the CASUs (this transfers, does not start exec)

        '''

        '''
        All p1 are nonblockign and returned
        all p2 are blocking and no handles kept.
        '''
        # we do walls here for each population
        if 'agents' in self.config:
            for pop, data in self.config['agents'].items():
                raise RuntimeError, "[E] not expecting any simulated components!"

        self.deploy()
        self.disp_msg("pre-calib setup complete.")
    #}}}

    def deploy(self):
        '''
        '''
        wd = os.path.join(self.project_root, self.config['DEPLOY_DIR'])
        self.cd(wd)
        dply_cmd = "{} {}".format(self.TOOL_DEPLOY, self.config['PRJ_FILE'])
        self.disp_cmd_to_exec(dply_cmd)
        p2 = wrapped_subproc(DO_TEST, dply_cmd, shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, )

        p2.wait()
        this_pid = p2.pid
        out, err = p2.communicate()
        # rest goes to logfile.
        self.write_stage_stdout_log( out, "deploy", this_pid)
        self.process_stage_error_log(err, "deploy", this_pid)

        self._deployed = True

        self.disp_msg("deployment complete.")
        if self.selected_archives.get('deploy_sandbox', False):
            time.sleep(0.5)
            self.disp_msg('attempting to archive the deployment config')
            self._arch_dep_sandbox()
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

        # we can't know pid before the process is started; accept this one as-is
        std_err_file = open(os.path.join(self.stagelogdir, "assisirun.stderr"), 'w')

        self.disp_cmd_to_exec(casu_cmd + "> {}".format(outf.name))
        p1 = wrapped_subproc(DO_TEST,  casu_cmd, stdout=outf, stderr=std_err_file,
                shell=True, preexec_fn=os.setsid)
        self.p_handles.append(p1)
        self._add_pid_file(p1)
        self.f_handles.append(outf)
        self.f_handles.append(std_err_file)

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
        _ag_data = self.config.get('agents', {})
        for pop, data in _ag_data.items():
        #for pop, data in self.config['agents'].items():
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
            # add in switches for custom addresses if defined (note that
            # the HOST subaddr is the client/tool *pub* addr)
            if self.CUSTOM_ADDRS:
                spwn_cmd += " --pub-addr {} --sub-addr {} ".format(
                    self.custom_subaddr, self.custom_pubaddr)
            self.disp_cmd_to_exec(spwn_cmd)
            p2 = wrapped_subproc(DO_TEST, spwn_cmd, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, shell=True)
            p2.wait()
            this_pid = p2.pid
            out, err = p2.communicate()
            _stage = "spawn_agents_{}".format(pop)
            self.write_stage_stdout_log( out, _stage, this_pid)
            self.process_stage_error_log(err, _stage, this_pid)
            data['agents_spawned'] = True
            spawn_count += 1

        self.disp_msg("Agents spawned from {} populations. Ready to exec.".format(spawn_count))

    def run_agents(self, ):
        '''
        This assumes the requirement of executing hanlders for all agents from
        all populations. The exec is non-blocking.
        '''

        # execute all agent behaviour scripts
        # first, gather all agents to be run
        wd = os.path.join(self.project_root, self.config['DEPLOY_DIR'])
        self.cd(wd)
        exec_listings = []
        _ag_data = self.config.get('agents', {})
        for pop, data in _ag_data.items():
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
            exec_listings.append( data['obj_listing'])
            # any archives then put into log folder
            _archs = data.get('archives', [])
            if self.ARCHIVE_BEHAV_SCRIPT:
                _archs += [_ab]
            for f in _archs:
                pth = os.path.join(self.archdir, pop)
                self.mkdir(pth)
                self.copyfile(f, pth)


        # then run all with a single handler
        if len(exec_listings):
            _el = " ".join(str(_e) for _e in exec_listings)
            agent_cmd = "{} -ol {} --logpath {}".format(
                self.TOOL_EXEC_AGENTS, _el, self.logdir,)
                #self.TOOL_EXEC_AGENTS, data['obj_listing'], self.logdir,)

            #
            # setup files for logging output.
            _stage = os.path.splitext(os.path.basename(self.TOOL_EXEC_AGENTS))[0]
            f_stdout = open(
                os.path.join( self.stagelogdir, "{}.stdout".format(_stage)), 'w')
            f_stderr = open(
                os.path.join( self.stagelogdir, "{}.stderr".format(_stage)), 'w')

            self.disp_cmd_to_exec(agent_cmd, bg=True)
            p1 = wrapped_subproc(DO_TEST, agent_cmd, stdout=f_stdout,
                                 stderr=f_stderr, shell=True, preexec_fn=os.setsid)
            self.p_handles.append(p1)
            self._add_pid_file(p1)
            self.f_handles.append(f_stdout)
            self.f_handles.append(f_stderr)

    def wait_for_expt(self):
        ''' logical rename for other non-simulation based users of this class'''
        self.wait_for_sim()

    def wait_for_sim(self):
        '''
        blocking wait for the period defined in config.
        '''

        now = datetime.datetime.now()
        fin = now + datetime.timedelta(0, self.sim_sec)
        self.disp_msg("running {} now,  for {}s. Expect completion at {}".format(
            self.expt_type, self.sim_sec, fin.strftime("%H:%M:%S") ), level='W')
        time.sleep(self.sim_sec)
        self.disp_msg("{} done".format(self.expt_type), level='W')


    def close_logs(self):
        self.disp_msg("Closing all log files")
        for lf in self.f_handles:
            self.disp_msg("  closing {}".format(lf.name))
            lf.close()


    def collect_logs(self, expected_file_cnt=None):
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
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             shell=True)
        p2.wait() # execute command
        this_pid = p2.pid
        # now capture the output,
        out, err = p2.communicate()
        # rest goes to logfile.
        self.write_stage_stdout_log( out, "collect_logs", this_pid)
        self.process_stage_error_log(err, "collect_logs", this_pid)

        #TODO:  display a summary; accumulate warnings and error count


        # 2. check #files in log path
        if expected_file_cnt is not None:
            cmd = "find {} -type f | wc -l ".format(self.logdir)

            lines = subprocess.check_output(cmd, shell=True).strip()
            if self.verb: print lines
            file_cnt = int(lines.split()[0])
            f_msg = "[WARNING; NOT ENUGH LOGFILES!]"
            if file_cnt >= expected_file_cnt: f_msg = "ok"
            self.disp_msg("There are {} files/dirs in {} ({})".format(file_cnt, self.logdir, f_msg))

    #}}}

#}}}

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
    hdlr = SimHandler(conf_file=args.conf, label=args.label, rpt=args.rpt,
                      allow_overwrite=args.allow_overwrite, dry_run=args.dry_run,
                      verb=args.verb)
    if args.dry_run:
        print "[I] all done with checks."
        return

    try:
        hdlr.pre_calib_setup() # initialise: playground, deploy, walls
        hdlr.calib_casus()     # connect and timeout calibration (blocking)
        hdlr.init_agents()     # spawn agents
        hdlr.run_agents()      # connect handlers to agents
        if args.verb:
            hdlr.disp_msg("PIDs of persistent procs are {}".format(hdlr.get_pids()))

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


