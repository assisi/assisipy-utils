Change and release log
======================

0.5.0
-----

* run_multiagent agent handler improvements:
   
    * agent handler execution script permits single or multiple specification
      files
    * minor improvements to output formatting

* exec_sim_timed.py sim manager improvments:

    * allows external definition of spawning area, enabling one wall spawner to
      serve multiple populations if required. 
    * better skipping of stages that are detected not to have sufficient info
      to proceed 
    * additional stage to separate init_agents from run_agents
    * process ID management improved
    * improved coloring of log entries to screen

* tools have git-derived sub-version when in development mode (better
  traceability); this falls back to the package version with regular install.


0.4.0
-----

* added simulation execution manager, with facility for:

    * spawning of agents and arena walls, by population
    * execution of agent behaviours with utils.run_multiagent
    * execution of CASU controllers with assisipy.deploy tools  
    * collection of results 
    * timed execution, with early interrupt via ctrl-c.
    * logging of commandes

* added example usage simulation execution manager

* added example of heterogeneous behavioural controllers

known issues:

* exec_sim_timed.py:

    * exit codes are not processed (success of various operations 
      cannot be known since assisipy does not acknowledge, e.g. 
      spawn of objects)
    * non-local paths are not universally handled well
    * config files for agent behaviour are not optional.
    * planned feature: easily skip stages via config -- e.g. via
      setting to None or undefined on tools, or declaring the stages
      explicitly
    * planned feature: dry-run, which checks that all files indicated 
      are present, and permissions for relevant logpaths are allowed


0.3.0
-----

* changed name of library (assisilib -> assisipy_utils)
* updated examples in line with library name & tested

0.2.0
-----

* spawning and launching of multiple bees / controller programs
* example usage for management of simulating multiple agents

0.1.1
-----

* included usage examples

0.1.0
-----

* initial release, including arena generators and geometric transformations



