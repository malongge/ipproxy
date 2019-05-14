#!usr/bin/env python
# -*- coding:utf-8 -*-

"""
@author:max
@file: adsl.py
@time: 2019/05/13
"""

import asyncio
import re
import time
from collections import defaultdict
from subprocess import Popen, PIPE

import aiohttp

from config import (ADSL_IFNAME, TEST_URL, TEST_TIMEOUT,
                    ADSL_CYCLE, ADSL_ERROR_CYCLE, ADSL_BASH, PROXY_PORT, IFCONFIG_BASH)
from redis import init_redis, RedisClient


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

    def __init__(self, loop, client_name):
        self.loop = loop
        self.db = None
        self.client_name = client_name

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

    async def remove_proxy(self):
        """
        移除代理
        :return: None
        """
        await self.db.remove(self.client_name)
        print('Successfully Removed Proxy')

    async def set_proxy(self, proxy):
        """
        设置代理
        :param proxy: 代理
        :return: None
        """
        result = await self.db.set(self.client_name, proxy)
        if result:
            print('Successfully Set Proxy', proxy)

    async def adsl(self):
        """
        拨号主进程
        :return: None
        """
        if not self.db:
            self.db = RedisClient(await init_redis(loop))
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
                    if await test_proxy(proxy):
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


async def test_proxy(proxy):
    """
    测试代理
    :param proxy: 代理
    :return: 测试结果
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(TEST_URL, timeout=TEST_TIMEOUT, proxy='http://' + proxy) as resp:
                if resp.status == 200:
                    print('test proxy success')
                    return True

    except Exception as e:
        print(e)
        return False


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print('Need client name!!!')
        sys.exit(0)
    client_name = sys.argv[1]
    loop = asyncio.get_event_loop()
    dial = Dialer(loop, client_name)
    try:
        result = loop.run_until_complete(dial.adsl())
    finally:
        if dial.db:
            loop.run_until_complete(dial.db.close())
        loop.close()
        print('Clean data finished')

