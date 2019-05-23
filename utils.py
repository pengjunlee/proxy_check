# -*- coding: utf-8 -*-
import logging
from settings import PROXY_URL_FORMATTER

# 设置日志的输出样式
logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)-15s] [%(levelname)8s] [%(name)10s ] - %(message)s (%(filename)s:%(lineno)s)',
                    datefmt='%Y-%m-%d %T'
                    )
logger = logging.getLogger(__name__)


# 剔除字符串的首位空格
def strip(data):
    if data is not None:
        return data.strip()
    return data

# 获取代理IP的url地址
def _get_url(proxy):
    return PROXY_URL_FORMATTER % {'schema': proxy['schema'], 'ip': proxy['ip'], 'port': proxy['port']}

# 根据请求结果更新代理IP的字段信息
def _update(proxy, successed=False):
    proxy['used_total'] = proxy['used_total'] + 1
    if successed:
        proxy['continuous_failed'] = 0
        proxy['success_times'] = proxy['success_times'] + 1
    else:
        proxy['continuous_failed'] = proxy['continuous_failed'] + 1
