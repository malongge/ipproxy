#!/usr/bin/env bash

source /root/venvs/ipproxy/bin/activate

cd /root/ipproxy

python3 adsl.py $1 2>&1 | tee /root/adsl.log