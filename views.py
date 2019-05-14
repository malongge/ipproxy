#!usr/bin/env python
# -*- coding:utf-8 -*-

"""
@author:max
@file: views.py
@time: 2019/05/13
"""

from aiohttp import web
import json
from config import HASH_TOKEN
import hashlib


class Handler:

    def __init__(self, redis):
        self._redis = redis

    def _check_token(self, for_check):
        # type: (str) -> bool
        return HASH_TOKEN == for_check.lower()

    async def index(self):
        raise web.HTTPNotFound()

    async def _choice(self, name):
        if not name:
            return
        func = getattr(self._redis, name, None)
        if func is None:
            return
        return await func()

    def get_web_response(self, response_obj):
        # type: (dict) -> web.Response
        return web.Response(text=json.dumps(response_obj))

    async def choice(self, request):
        token = request.rel_url.query.get('token', '')
        if not self._check_token(token):
            return self.get_web_response({'errcode': -1, "msg": 'auth failed'})
        choice = request.match_info.get('choice', '')
        ip = await self._choice(choice)
        if ip is None:
            return self.get_web_response({'errcode': -1, "msg": 'not found ip proxy'})
        return self.get_web_response({'errcode': 0, "proxy": ip})
