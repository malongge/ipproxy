#!usr/bin/env python
# -*- coding:utf-8 -*-

"""
@author:max
@file: adsl.py
@time: 2019/05/13
"""

import re
import time
from collections import defaultdict
import asyncio
import aiohttp
from redis import init_redis, close_redis, RedisClient
from config import conf
from subprocess import Popen, PIPE

# 拨号网卡
# ADSL_IFNAME = 'ppp0'
ADSL_IFNAME = 'en0'
# 测试 URL
TEST_URL = 'http://www.baidu.com'
# 测试超时时间
TEST_TIMEOUT = 20
# 拨号间隔
ADSL_CYCLE = 60 * 10
# 拨号出错重试间隔
ADSL_ERROR_CYCLE = 5
# ADSL命令
# ADSL_BASH = ['adsl-stop;adsl-start']
ADSL_BASH = ['ping', '-c3', 'www.baidu.com']
# 代理运行端口
PROXY_PORT = 9999
# 客户端唯一标识
CLIENT_NAME = 'adsl1'
# 获取 IP 地址命令
IFCONFIG_BASH = ['ifconfig']


async def connect_write_pipe(loop, file):
    """Return a write-only transport wrapping a writable pipe"""
    # loop = asyncio.get_event_loop()
    transport, _ = await loop.connect_write_pipe(asyncio.Protocol, file)
    return transport


async def connect_read_pipe(loop, file):
    """Wrap a readable pipe in a stream"""
    # loop = asyncio.get_event_loop()
    stream_reader = asyncio.StreamReader(loop=loop)

    def factory():
        return asyncio.StreamReaderProtocol(stream_reader)

    transport, _ = await loop.connect_read_pipe(factory, file)
    return stream_reader, transport


async def run_command(loop, command, enters=None):
    # start subprocess and wrap stdin, stdout, stderr
    p = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE)

    stdin = await connect_write_pipe(loop, p.stdin)
    stdout, stdout_transport = await connect_read_pipe(loop, p.stdout)
    stderr, stderr_transport = await connect_read_pipe(loop, p.stderr)

    # interact with subprocess
    name = {stdout: 'OUT', stderr: 'ERR'}
    registered = {
        asyncio.Task(stderr.read()): stderr,
        asyncio.Task(stdout.read()): stdout
    }
    if enters is not None:  # 命令后面需要追加输入的命令
        temp = b'\n'.join([each.encode('utf-8') for each in enters]) + b'\n'
        stdin.write(temp)
        stdin.close()  # 不再进行输入操作
    results = defaultdict(list)
    timeout = None
    while registered:
        done, pending = await asyncio.wait(
            registered, timeout=timeout,
            return_when=asyncio.FIRST_COMPLETED)
        if not done:
            break
        for f in done:
            stream = registered.pop(f)
            res = f.result()
            if res != b'':
                results[name[stream]].append(res.decode('utf-8').rstrip())
                registered[asyncio.Task(stream.read())] = stream
        timeout = 0.0

    stdout_transport.close()
    stderr_transport.close()
    if 'ERR' in results:
        return -1, '\n'.join(results['ERR'])
    return 0, '\n'.join(results['OUT'])


class Dialer:
    ip_pattern = re.compile(ADSL_IFNAME + '.*?inet.*?(\d+\.\d+\.\d+\.\d+).*?netmask', re.S)

    def __init__(self, loop):
        self.loop = loop
        self.db = None

    async def get_ip(self):
        """
        获取本机IP
        :return:
        """
        status, output = await run_command(self.loop, IFCONFIG_BASH)
        if status == 0:
            result = re.search(self.ip_pattern, output)
            if result:
                ip = result.group(1)
                return ip

    async def test_proxy(self, proxy):
        """
        测试代理
        :param proxy: 代理
        :return: 测试结果
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(TEST_URL, timeout=TEST_TIMEOUT, proxy='http://' + proxy) as resp:
                    if resp.status == 200:
                        return True
        except Exception as e:
            print(e)
            return False

    async def remove_proxy(self):
        """
        移除代理
        :return: None
        """
        await self.db.remove(CLIENT_NAME)
        print('Successfully Removed Proxy')

    async def set_proxy(self, proxy):
        """
        设置代理
        :param proxy: 代理
        :return: None
        """
        result = await self.db.set(CLIENT_NAME, proxy)
        if result:
            print('Successfully Set Proxy', proxy)

    async def adsl(self):
        """
        拨号主进程
        :return: None
        """
        if not self.db:
            self.db = RedisClient(await init_redis(conf['redis'], loop))
        while True:
            print('ADSL Start, Remove Proxy, Please wait')
            await self.remove_proxy()
            status, output = await run_command(self.loop, ADSL_BASH)
            if status == 0:
                print('ADSL Successfully')
                ip = await self.get_ip()
                if ip:
                    print('Now IP', ip)
                    print('Testing Proxy, Please Wait')
                    proxy = '{ip}:{port}'.format(ip=ip, port=PROXY_PORT)
                    if await self.test_proxy(proxy):
                        print('Valid Proxy')
                        await self.set_proxy(proxy)
                        print('Sleeping')
                        time.sleep(ADSL_CYCLE)
                    else:
                        print('Invalid Proxy')
                else:
                    print('Get IP Failed, Re Dialing')
                    time.sleep(ADSL_ERROR_CYCLE)
            else:
                print('ADSL Failed, Please Check')
                time.sleep(ADSL_ERROR_CYCLE)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    dial = Dialer(loop)
    try:
        result = loop.run_until_complete(dial.adsl())
    finally:
        if dial.db:
            loop.run_until_complete(close_redis(dial.db))
        loop.close()
