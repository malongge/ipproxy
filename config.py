#!usr/bin/env python
# -*- coding:utf-8 -*-

"""
@author:max
@file: config.py
@time: 2019/05/13
"""
import hashlib
import os
import pathlib

import yaml

PROJ_ROOT = pathlib.Path(__file__).parent


def load_config(fname):
    with open(fname, 'rt') as f:
        data = yaml.safe_load(f)
    # TODO: add config validation
    return data


DEV = int(os.environ.get('DEV_MODE', 1))

# 获取 IP 地址命令
CONFIG = load_config(PROJ_ROOT / 'config.yml')

# 拨号网卡
if DEV is 0:
    ADSL_IFNAME = 'en0'
    ADSL_BASH = ['ping', '-c3', 'www.baidu.com']
else:
    ADSL_IFNAME = 'ppp0'
    # ADSL命令
    ADSL_BASH = ['adsl-stop;adsl-start']

TEST_URL = 'http://www.baidu.com'
TEST_TIMEOUT = 20

# 拨号间隔
ADSL_CYCLE = 60 * 10

# 拨号出错重试间隔
ADSL_ERROR_CYCLE = 5

PROXY_PORT = 9999

IFCONFIG_BASH = ['ifconfig']

HASH_KEY = os.environ.get('HASH_KEY', 'test')
md5 = hashlib.md5()
md5.update(HASH_KEY.encode('utf-8'))
HASH_TOKEN = md5.hexdigest()
