Simulation management tool -- demo
==================================

**Rationale**:
Many tools are used in the execution of a simulation -- the simulator;
the setup of agents, casus, arenas; the handlers for behaviour of each
agent and casu controller; and data retreival.  This tool attempts to
consistently manage this suite, with capacity to execute for a fixed 
period and also handle interrupts.


**Basic usage**:
Assuming that the python package is installed via `pip`, the command should be
available on the path. Thus, just type

    $ exec_sim_timed -c demo.conf -r 1

**Changing what is executed**:
Inside demo.conf, the setup is configured.  Key points of modification will 
include:
- `simulation_runtime_mins` (how long the simulation runs for before timing out)
- `logbase` (where the results and other working files will be saved)
- `agents`  (controls the number, location, and size of agent populations in 
             a simulation; see inside the .conf file for further detail)


**What the example does**:
This example shows three populations of bees simulated in separate arenas. The
behaviour is a very simple wandering, defined in `basic_bee_fwd.py`.  There are
different parameters (colors here) set through the additional agent config, as
taken from the beeconf example in the same package.  The CASUs are setup using
the deployment tools; one arena has some CASUs present that simply set to a
given temperature that is fixed throughout a simulation.

At present, the locations for each script should be local to the deployment
directory, although this should change in future releases.

**Assumptions made re: existence of setup by the execution tool**:
- top-level config file
- a subdirectory with:
    - an .assisi project file (deployment toolsuite)
    - a  .dep deployment specification (deployment toolsuite)
    - an .arena casu position graph (deployment toolsuite)
    - an agent spawner script, generating specs compatible with `run_multiagent`
    - an arena spawner script
    - an agent behaviour script, compatible with the `run_multiagent` tool
    - a  casu behaviour script, compatible with `assisirun.py`


**Gathering many results**:
This wrapper can itself be called in a loop, for instance, using the shell commands:

    $ for r in `seq 1 10` ; do exec_sim_timed -c demo.conf -r ${r} ; done





