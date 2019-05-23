# encoding=utf-8
import redis
from optparse import OptionParser
import random
import requests
from utils import logger, _get_url, _update
from proxy_queue import CheckedQueue, UncheckedQueue
from settings import USER_AGENT_LIST, BASE_HEADERS, REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, PROXY_CHECK_URLS

USAGE = "usage: python check_proxy.py [ -c -s <schema>] or [-u]"

parser = OptionParser(USAGE)
parser.add_option("-c", "--checked", action="store_true", dest="checked", help="check the proxies already checked")
parser.add_option("-u", "--unchecked", action="store_false", dest="checked", help="check the proxies to be checked")
parser.add_option("-s", "--schema", action="store", dest="schema", type="choice", choices=['http', 'https'],
                  help="the schema of the proxies to be checked")
options, args = parser.parse_args()

r = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
if options.checked:
    schema = options.schema
    if schema is None:
        logger.error("使用 -c 参数时，需要指定 -s 参数！！！")
    proxy_queue = CheckedQueue(r)
else:
    schema = None
    proxy_queue = UncheckedQueue(r)

# 获取当前待检测队列中代理的数量
count = proxy_queue.__len__(schema=schema)
while count > 0:

    logger.info("待检测代理数量： " + str(count))
    count = count - 1

    # 获取代理
    proxy = proxy_queue.pop(schema=options.schema)
    proxies = {proxy['schema']: _get_url(proxy)}

    # 初始化计数字段值
    if "used_total" not in proxy:
        proxy['used_total'] = 0
    if "success_times" not in proxy:
        proxy['success_times'] = 0
    if "continuous_failed" not in proxy:
        proxy['continuous_failed'] = 0

    # 构造请求头
    headers = dict(BASE_HEADERS)
    if 'User-Agent' not in headers.keys():
        headers['User-Agent'] = random.choice(USER_AGENT_LIST)

    for url in PROXY_CHECK_URLS[proxy['schema']]:
        try:
            # 使用代理发送请求，获取响应
            response = requests.get(url, headers=headers, proxies=proxies, timeout=5)
        except BaseException:
            logger.info("使用代理< " + _get_url(proxy) + " > 请求 < " + url + " > 结果： 失败 ")
            # 根据请求的响应结果更新代理
            _update(proxy, successed=False)
        else:
            if (response.status_code == 200):
                logger.info("使用代理< " + _get_url(proxy) + " > 请求 < " + url + " > 结果： 成功 ")
                # 根据请求的响应结果更新代理
                _update(proxy, successed=True)
                # 将代理返还给队列，返还时不校验可用性
                proxy_queue.push(proxy)
                break
            else:
                logger.info("使用代理< " + _get_url(proxy) + " > 请求 < " + url + " > 结果： 失败 ")
                # 根据请求的响应结果更新代理
                _update(proxy, successed=False)
