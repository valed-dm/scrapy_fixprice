import os
import json
import random
import asyncio

import scrapy
from scrapy import signals
from scrapy.exceptions import DropItem
from playwright.async_api import async_playwright
from scrapy_fixprice.spiders.fpspider import MySpider


class MultiFilePipeline:

    def __init__(self):
        self.files = {}
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/58.0.3029.110 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:54.0) Gecko/20100101 Firefox/54.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:54.0) Gecko/20100101 Firefox/54.0',
        ]

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.open_spider, signal=signals.spider_opened)
        crawler.signals.connect(pipeline.close_spider, signal=signals.spider_closed)
        return pipeline

    def open_spider(self, spider):
        pass

    def close_spider(self, spider):
        for file in self.files.values():
            file.close()

    async def scrape_with_playwright(self, item, spider):
        category_url = item['url']
        file_name = category_url.split('/')[-2] + ".json"
        if file_name not in self.files:
            file_path = os.path.join(spider.settings.get('FEED_URI', '.'), file_name)
            self.files[file_name] = open(file_path, 'w')

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(user_agent=random.choice(self.user_agents))
            page = await context.new_page()
            await page.goto(category_url)

            # Use spider's parse logic within Playwright context
            response = await self.fake_response_from_playwright(page, category_url)
            await spider.parse(response)

            await context.close()
            await browser.close()

        line = json.dumps(dict(item)) + "\n"
        self.files[file_name].write(line)

    async def fake_response_from_playwright(self, page, url):
        """Generate a Scrapy-like response from Playwright page."""
        body = await page.content()
        headers = await page.evaluate('() => JSON.parse(JSON.stringify(document.headers))')
        response = scrapy.http.HtmlResponse(
            url=url,
            body=body.encode('utf-8'),
            encoding='utf-8',
            request=scrapy.Request(url),
            headers=headers,
        )
        response.meta['playwright_page'] = page
        return response

    def process_item(self, item, spider):
        asyncio.run(self.scrape_with_playwright(item, spider))
        return item
