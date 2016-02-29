#!/bin/sh

# What does this example do?
# - the primary aim is to demonstrate how to execute multiple different
#   agent behaviours simultaneously.  It also provides an example for how
#   to structure an (extremely) simple agent behaviour
#
# 1. runs the playground
# 2. spawns several agents, also a wall. Logged in a spec listing
#    - note that the 1st half get config file 1, 2nd half get config file 2
#    - note that even indices get one behaviour (fwd), odd get other (bwd)
#    - together, we should have 4 different agent "types". (The differences
#      here are trivial and a bit meaningless, and should only be taken as
#      illustrative)
# 3. runs behavioural program for all agents in the listing, via 
#    differing agent behaviour and config files -- heterogeneity.

### set up the few parts to run this simulation.
SPEC_FILE=/tmp/test_listing.csv

# playground
assisi_playground &
sleep 1

# spawn things in it
./spawn_bees_hetero.py -r 11 -n 7 -ol ${SPEC_FILE}

# we want to run this, but because the ctrl-c doesn't propogate? we should do sep.
run_multiagent -ol ${SPEC_FILE} --logpath /tmp
#python ../../mgmt/run_multiagent.py -ol ${SPEC_FILE} --logpath /tmp



