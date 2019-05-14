#!usr/bin/env python
# -*- coding:utf-8 -*-

"""
@author:max
@file: server.py
@time: 2019/05/13
"""

import asyncio
import logging

from aiohttp import web
from config import CONFIG
from redis import setup_redis
from views import Handler
from redis import RedisClient


def setup_routes(app, handler):
    router = app.router
    h = handler
    router.add_get('/', h.index, name='index')
    router.add_get('/{choice}', h.choice, name='choice')


async def init(loop):
    app = web.Application(loop=loop)
    redis_pool = await setup_redis(app, loop)

    handler = Handler(RedisClient(redis_pool))

    setup_routes(app, handler)
    host, port = CONFIG['host'], CONFIG['port']
    return app, host, port


def main():
    logging.basicConfig(level=logging.INFO)
    loop = asyncio.get_event_loop()
    app, host, port = loop.run_until_complete(init(loop))
    web.run_app(app, host=host, port=port)


if __name__ == '__main__':
    main()
