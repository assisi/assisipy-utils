'''
A setuptools script that follows recommendations (where relevant) from:
  https://github.com/pypa/sampleproject/blob/master/setup.py
  https://github.com/jeffknupp/sandman/blob/develop/setup.py
  http://pythonhosted.org/setuptools/setuptools.html


Note: to ensure that the description file is available in the target,
(needed when setup.py is executed, either manually or by easy_install/pip)
the MANIFEST.in file is used.
package_data and data_files are ignored by setuptools when compiling
source distributions!

Note: for the entry points to work, the rhs expects the target to be a
function in a module, that takes no arguments:
http://stackoverflow.com/q/2853088
Luckily, argparse somehow access sys.argv from wherever they are created
so arguments need to be passed to that entry point func.
The four tools used in deployment scenarios have these entry points set up.

'''


from setuptools import setup, find_packages
import codecs
import os
import re

here = os.path.abspath(os.path.dirname(__file__))

def read(*parts):
    # source: https://github.com/jeffknupp/sandman/blob/develop/setup.py
    # intentionally *not* adding an encoding option to open
    return codecs.open(os.path.join(here, *parts), 'r').read()

def find_version(*file_paths):
    # source: https://github.com/jeffknupp/sandman/blob/develop/setup.py
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

long_description = read('DESCRIPTION.rst')

# setting up entry points to code within the python package - hopefully..
console_scripts = [
    ['exec_sim_timed = assisipy_utils.mgmt.exec_sim_timed:main'],
    ['run_multiagent = assisipy_utils.mgmt.run_multiagent:main'],
]



setup(
    name="assisipy_utils",
    version=find_version('assisipy_utils', '__init__.py'),
    packages=find_packages(exclude=["doc"]),

    description="Utilities for simulations with ASSISI-playground.",
    long_description=long_description,

    # The project URL.
    url='http://assisi-project.eu/',

    # Author details
    author='Rob Mills, FCUL',
    author_email='rob.mills@fc.ul.pt',

    license='LGPL',

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: Artificial Life',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Programming Language :: Python :: 2.7'
    ],

    keywords='assisi, assisibf, collective systems',

    # Run-time dependencies (will be installed by pip)
    #install_requires = ['assisipy >=0.9'], # working with dev version so disable req for now
    install_requires = [],

    entry_points     = {
        'console_scripts': console_scripts,
    },

    #package_dir  = {'assisipy_utils' : 'assisipy_utils'},
    package_data = {'assisipy_utils' : ['examples/*.py',
                                   'examples/beeconf/*',
                                   ], },




)
