# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import logging

logging.basicConfig(
    filename='proxy_middleware.log',
    filemode='w',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)


class ProxyMiddleware:
    def __init__(self, settings):
        self.proxy_username = settings.get('PROXY_USERNAME')
        self.proxy_password = settings.get('PROXY_PASSWORD')
        self.domain_name = settings.get('DOMAIN_NAME')
        self.proxy_port = settings.get('PROXY_PORT')
        self.proxy_url = f"http://{self.proxy_username}:{self.proxy_password}@{self.domain_name}:{self.proxy_port}"

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def process_request(self, request, spider):
        logging.debug(f"Using proxy: {self.proxy_url}")
        request.meta['proxy'] = self.proxy_url

    def process_exception(self, request, exception, spider):
        logging.debug(f"Exception with proxy: {request.meta.get('proxy')} - {exception}")
        return request
