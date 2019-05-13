#!usr/bin/env python
# -*- coding:utf-8 -*-

"""
@author:max
@file: config.py
@time: 2019/05/13
"""
import pathlib

import yaml

PROJ_ROOT = pathlib.Path(__file__).parent


def load_config(fname):
    with open(fname, 'rt') as f:
        data = yaml.safe_load(f)
    # TODO: add config validation
    return data


conf = load_config(PROJ_ROOT / 'config.yml')