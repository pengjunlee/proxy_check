# -*- coding: utf-8 -*-
import json
from utils import _get_url
from settings import PROXIES_REDIS_EXISTED, PROXIES_REDIS_FORMATTER, PROXIES_UNCHECKED_LIST, PROXIES_UNCHECKED_SET, \
    MAX_FAILURE_TIMES

"""
Proxy Queue Base Class
"""


class BaseQueue(object):

    def __init__(self, server):
        """Initialize the proxy queue instance

        Parameters
        ----------
        server : StrictRedis
            Redis client instance
        """
        self.server = server

    def _is_existed(self, proxy):
        """判断当前代理是否已经存在"""
        added = self.server.sadd(PROXIES_REDIS_EXISTED, _get_url(proxy))
        return added == 0

    def push(self, proxy):
        """根据检验结果，将代理放入相应队列"""
        if not self._is_existed(proxy) and proxy['continuous_failed'] < MAX_FAILURE_TIMES:
            key = PROXIES_REDIS_FORMATTER.format(proxy['schema'])
            self.server.rpush(key, json.dumps(proxy, ensure_ascii=False))

    def pop(self, schema, timeout=0):
        """Pop a proxy"""
        raise NotImplementedError

    def __len__(self, schema):
        """Return the length of the queue"""
        raise NotImplementedError


class CheckedQueue(BaseQueue):
    """待检测的代理队列"""

    def __len__(self, schema):
        """Return the length of the queue"""
        return self.server.llen(PROXIES_REDIS_FORMATTER.format(schema))

    def pop(self, schema, timeout=0):
        """从未检测列表弹出一个待检测的代理"""
        if timeout > 0:
            p = self.server.blpop(PROXIES_REDIS_FORMATTER.format(schema), timeout)
            if isinstance(p, tuple):
                p = p[1]
        else:
            p = self.server.lpop(PROXIES_REDIS_FORMATTER.format(schema))
        if p:
            p = eval(p)
            self.server.srem(PROXIES_REDIS_EXISTED, _get_url(p))
            return p


class UncheckedQueue(BaseQueue):
    """已检测的代理队列"""

    def __len__(self, schema=None):
        """Return the length of the queue"""
        return self.server.llen(PROXIES_UNCHECKED_LIST)

    def pop(self, schema=None, timeout=0):
        """从未检测列表弹出一个待检测的代理"""
        if timeout > 0:
            p = self.server.blpop(PROXIES_UNCHECKED_LIST, timeout)
            if isinstance(p, tuple):
                p = p[1]
        else:
            p = self.server.lpop(PROXIES_UNCHECKED_LIST)
        if p:
            p = eval(p)
            self.server.srem(PROXIES_UNCHECKED_SET, _get_url(p))
            return p
