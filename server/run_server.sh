#!/bin/bash
dname=$(dirname ${BASH_SOURCE[0]})
python3 $dname/server.py $1 $2