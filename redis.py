#!usr/bin/env python
# -*- coding:utf-8 -*-

"""
@author:max
@file: redis.py
@time: 2019/05/13
"""

import random

# 代理池键名
import aioredis
from config import CONFIG

PROXY_KEY = 'adsl'


class RedisClient(object):
    def __init__(self, db, proxy_key=PROXY_KEY):
        """
        :param db Redis 连接
        :param proxy_key: Redis 散列表名
        """
        self.db = db
        self.proxy_key = proxy_key

    async def set(self, name, proxy):
        """
        设置代理
        :param name: 主机名称
        :param proxy: 代理
        :return: 设置结果
        """
        return await self.db.hset(self.proxy_key, name, proxy)

    async def get(self, name):
        """
        获取代理
        :param name: 主机名称
        :return: 代理
        """
        return await self.db.hget(self.proxy_key, name)

    async def count(self):
        """
        获取代理总数
        :return: 代理总数
        """
        return await self.db.hlen(self.proxy_key)

    async def remove(self, name):
        """
        删除代理
        :param name: 主机名称
        :return: 删除结果
        """
        return await self.db.hdel(self.proxy_key, name)

    async def names(self):
        """
        获取主机名称列表
        :return: 获取主机名称列表
        """
        return await self.db.hkeys(self.proxy_key)

    async def proxies(self):
        """
        获取代理列表
        :return: 代理列表
        """
        return await self.db.hvals(self.proxy_key)

    async def random(self):
        """
        随机获取代理
        :return:
        """
        proxies = await self.proxies()
        return random.choice(proxies)

    async def all(self):
        """
        获取字典
        :return:
        """
        return await self.db.hgetall(self.proxy_key)

    async def close(self):
        self.db.close()
        await self.db.wait_closed()


async def init_redis(loop):
    _conf = CONFIG['redis']
    pool = await aioredis.create_redis_pool(
        (_conf['host'], _conf['port']), db=_conf['db'], password=_conf['password'],
        minsize=_conf['minsize'],
        maxsize=_conf['maxsize'],
        loop=loop,
        encoding='utf-8'
    )
    return pool


async def setup_redis(app, loop):
    pool = await init_redis(loop)

    async def close_redis(app):
        pool.close()
        await pool.wait_closed()

    app.on_cleanup.append(close_redis)
    app['redis_pool'] = pool
    return pool
