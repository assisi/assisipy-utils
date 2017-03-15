import os


def which(program):
    '''
    equivalent of the unix command `which`; either returns a full path
    to the program sought, or nothing (None) if the tool is not available
    '''
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None

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

def extract_scriptname(cmdline):
    '''
    given a command to be run within the specfile, it will either take the
    form of -
      "<tool> <script> [args+]"
    or, when the script has a hash-bang and is directly executable -
      "<script> [args+]"

    this func extracts the <script> token, for tools [python, sh, bash, perl]

    '''
    known_script_langs = ['python', 'sh', 'bash', 'perl']
    fields = cmdline.split()
    if len(fields) in [0, 1]:
        return cmdline
    else:
        t = fields[0]
        if t in known_script_langs:
            return fields[1]
        else:
            return fields[0]




