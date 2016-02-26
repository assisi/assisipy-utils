#!/bin/sh

# What does this example do?
# - the primary aim is to demonstrate how to execute multiple different
#   agent behaviours simultaneously.  It also provides an example for how
#   to structure an (extremely) simple agent behaviour
#
# 1. runs the playground
# 2. spawns several agents, also a wall. Logged in a spec listing
# 3. runs behavioural program for all agents in the listing, with
#    differing config files -- heterogeneity.

### set up the few parts to run this simulation.
SPEC_FILE=/tmp/test_listing.csv

# playground
assisi_playground &
sleep 1

# spawn things in it
./spawn_bees.py -r 11 -n 6 -ol ${SPEC_FILE} -e ./basic_bee.py

# we want to run this, but because the ctrl-c doesn't propogate? we should do sep.
run_multiagent -ol ${SPEC_FILE} --logpath /tmp
#python ../../mgmt/run_multiagent.py -ol ${SPEC_FILE} --logpath /tmp



