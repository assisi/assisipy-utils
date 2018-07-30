# assisipy-utils

[![License: LGPL v3](https://img.shields.io/badge/License-LGPL%20v3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.1323580.svg)](https://doi.org/10.5281/zenodo.1323580)


**What is it?** 

This package provides a library of utilities for use with
[`assisi-python`](https://github.com/assisi/assisipy)[[1]](#assisipy-ref) and
[`assisi-playground`](https://github.com/assisi/playground)[[2]](#playground-ref),
primarily for managing and inspecting simulation and lab-based experiments. It
is licenced under LGPLv3. See the LICENSE file For more details.



**How to install**

It is possible to use pip to install directly (without needing to clone this repo):

    $ pip install --user git+https://github.com/assisi/assisipy-utils.git@v0.9.2     

Note that `pip` installs scripts to `~/.local/bin` and if this is not already
on your path you will need to add it, for instance in your `.bashrc` file:

    $ echo 'export PATH=${PATH}:~/.local/bin:' >> ~/.bashrc

or, for system-wide installation (script path should not require modification):

    $ sudo pip install git+https://github.com/assisi/assisipy-utils.git

This is only useful if you already have [`assisi-playground`](https://github.com/assisi/playground) installed. See guide:

http://assisipy.readthedocs.org/en/latest/


**How to use**

See the examples directory for illustrations of:

* spawning arenas, casus, and agents
* executing behavioural controllers for multiple agents 
   * with heterogeneous parameters
   * with heterogeneous controller programs

New tools, as yet without example usage, include:

* stopping all running CASUs easily
* validation of CASU and link specifications visually and by log
* graph augmentation / generation based on deployment specifications


**References**

<a name="#assisipy-ref"></a>[1] Damjan Miklic, Rob Mills, Pedro Mariano, Marsela Polic and Tomislav Haus
(2018, August). Assisipy: Python API for the ASSISIbf project. Zenodo. https://dx.doi.org/10.5281/zenodo.1320079

<a name="#playground-ref"></a>[2] Pedro Mariano, Damjan Miklic and Rob Mills (2018, August). Assisi-playground bio-hybrid system simulator. Zenodo. https://dx.doi.org/10.5281/zenodo.1323609 




