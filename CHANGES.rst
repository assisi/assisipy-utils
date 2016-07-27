Change and release log
======================

0.7.0
-----

New implementations

* added a graph class (and tool) that combines topological and geometric info
  (from nbg and arena files) to produce a new output graph.  The class is 
  extensible and can be used in validation procedures, such as to annotate 
  edges that have had successful message transmissions detected.  Some are 
  provided in the `assisipy_utils.validate` module.

* added validator of a deployment specification: this tool generates a new 
  deployment based on an existing deployment spec, that performs simple 
  flashing and messaging tests on the deployment targets, and by means of 
  logfiles it also validates the success or failure of each individual test.



Issues resolved

* 

New known bugs

* 

0.6.0
-----

* exec_sim_timed.py sim manager improvments:

  * archiving source or config files
  * directory creation is now logged
  
* mgmt/specs:

  * implemented a yaml-based agent handler data reader and writer (with 
    the same interface as the csv-based version, but files are more readable
    and also extensible in the case that more information is required by 
    alternative processes)  

  * added `exec_phys_timed`, a script that manages physical-only experiments.
    These are far simpler than a simulated run, since no agents/walls/simulator
    are spawned. It handles the deployment toolsuite, archiving of results, and
    experiment length. It is installed as a script.

  * added `cmdlog.sh`, a simple script to strip off meta-info on command logs,
    to ease re-running of an experiment from the log

  * added `reset_popln` to facilitate moving all agents back to their
    originally-specified positions. This is useful in interactive modelling
    (casus, or agents, or both)

* arena:

  * implemented RoundedRectArena, similar to the stadium but more general since
    there can be a flat section on the L/R walls as well as the T/B walls if
    desired
  * included simple rendering helpers for drawing components in `matplotlib`
    (as opposed to spawning in the playground)

Known issues:

* if a key is undefined in the yaml specwriter, it is written (& read) as the 
  string 'null', and not as a None.  Strip out any invalid key/value pairs at 
  generation time; consider whether defaults at read time are wise.


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



