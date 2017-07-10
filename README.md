# assisipy-utils

**What is it?** 

Library of utilities for use with [`assisi-python`](https://github.com/larics/assisi-python) and [`assisi-playground`](https://github.com/larics/assisi-playground) 


**How to install**

It is possible to use pip to install directly (without needing to clone this repo):

    $ pip install --user git+https://github.com/assisi/assisipy-utils.git@v0.8.0     

Note that `pip` installs scripts to `~/.local/bin` and if this is not already
on your path you will need to add it, for instance in your `.bashrc` file:

    $ echo 'export PATH=${PATH}:~/.local/bin:' >> ~/.bashrc

or, for system-wide installation (script path should not require modification):

    $ sudo pip install git+https://github.com/assisi/assisipy-utils.git

This is only useful if you already have [`assisi-playground`](https://github.com/larics/assisi-playground) installed. See:

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

