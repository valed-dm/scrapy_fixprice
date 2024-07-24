# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import logging
import os
import json

import scrapy

logging.basicConfig(
    filename='scrapy_spider.log',
    filemode='w',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)


class ItemFilterPipeline:
    def __init__(self, start_urls):
        self.categories = [url.split('/')[-2] for url in start_urls]
        logging.info(f"Categories to filter: {self.categories}")

    @classmethod
    def from_crawler(cls, crawler):
        start_urls = crawler.spider.start_urls
        return cls(start_urls)

    def process_item(self, item, spider):
        item_url = item['url']
        if any(category in item_url for category in self.categories):
            logging.info(f"Item accepted: {item_url}")
            return item
        else:
            logging.warning(f"Item dropped: {item_url}")
            raise scrapy.exceptions.DropItem(f"Item does not belong to any category: {item['url']}")


class MultiFilePipeline:
    def __init__(self, start_urls):
        self.feed_uri = None
        self.files = {}
        self.categories = [url.split('/')[-2] for url in start_urls]

    @classmethod
    def from_crawler(cls, crawler):
        start_urls = crawler.spider.start_urls
        return cls(start_urls)

    def open_spider(self, spider):
        self.feed_uri = './output/'  # Set your output directory
        if not os.path.exists(self.feed_uri):
            os.makedirs(self.feed_uri)
        for category in self.categories:
            file_path = os.path.join(self.feed_uri, f"{category}.jsonl")
            self.files[category] = open(file_path, 'w', encoding='utf8')

    def close_spider(self, spider):
        for file in self.files.values():
            file.close()

    def process_item(self, item, spider):
        item_url = item['url']
        for category in self.categories:
            if category in item_url:
                line = json.dumps(dict(item), ensure_ascii=False) + "\n"
                self.files[category].write(line)
                return item
        return item  # sorting done in ItemFilterPipeline, to avoid NoneType errors;
