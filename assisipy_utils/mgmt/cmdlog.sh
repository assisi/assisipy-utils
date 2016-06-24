#!/bin/sh
# assume the first parameter is the file to emit.
# if not given, look for the latest command log
f=${1:-LATEST}

if [ "$f" = "LATEST" ] ; then
    echo "looking for latest file"
    f=`ls -t1 commands*log | head -n1`

fi
echo $f

if [ -f $f ] ; then
    # simple program to show commands from an assisi exec log in 
    # without all the leading info
    # (e.g. to re-execute)
    #cat $1 | | tr -s " " | cut -d " " -f3,5-
    cat $f | tr -s " " | cut -d " " -f5-
else
    echo "[W] $f does not exist"
fi
