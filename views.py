#!usr/bin/env python
# -*- coding:utf-8 -*-

"""
@author:max
@file: views.py
@time: 2019/05/13
"""

from aiohttp import web


class Handler:

    def __init__(self, redis):
        self._redis = redis

    async def index(self):
        raise web.HTTPNotFound()

    async def _choice(self, name):
        func = getattr(self._redis, name, None)
        if func is None:
            return
        await func()

    async def choice(self, request):
        choice = request.match_info['choice']
        ip = await self._choice(choice)
        if ip is None:
            return {'errcode': -1, "msg": 'not found ip proxy'}
        return {'errcode': 0, "proxy": ip}
