#!/usr/bin/env python

'''
This module provides the package version (e.g. 1.2.0) and also the
git commit hash, such that a tool can report its version easily and accurately.

It also provides an argparse object add_argument to add this in.

'''

import argparse
import re
import os.path

# read the version file, if it exists
_verfile = "dev_version.txt"

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))
verfile = os.path.join(__location__, _verfile)


def find_version(*file_paths):
    # source: https://github.com/jeffknupp/sandman/blob/develop/setup.py
    version_file = os.path.realpath(os.path.join(__location__, "..", "__init__.py"))
    v_buf = open(version_file, 'r')
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              v_buf.read(), re.M)
    if version_match:
        return version_match.group(1)
    else:
        return "alien.."

# use the package version as a fallback / default, if we are not doing dev work
# (and thus the library considered will not have a dev_version.txt)
GIT_VERSION = find_version()

if os.path.isfile(verfile):
    try:
        with open(verfile, 'r') as f:
            _ver = f.read().strip()
        GIT_VERSION = _ver
    except IOError:
        GIT_VERSION = "alien2"

# provide the argparse info

def ap_ver(parser=None):
    #print "in generator:", GIT_VERSION
    elog = "tool version: {}".format(GIT_VERSION)
    if parser is None:
        parser = argparse.ArgumentParser(epilog=elog)
    else:
        try:
            parser.epilog += elog
        except (AttributeError, TypeError):
            parser.epilog = elog



    parser.add_argument('-V', '--version', action='version',
                        version=GIT_VERSION)

    return parser


if __name__ == '__main__':
    parser = ap_ver()
    parser.parse_args()

    print "Version details: {} \n  (from file '{}')".format(GIT_VERSION, verfile)
