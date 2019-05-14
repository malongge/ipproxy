#!/usr/bin/env bash

source /root/venvs/ipproxy/bin/activate

cd /root/ipproxy

python3 adls.py 2>&1 | tee script.log &