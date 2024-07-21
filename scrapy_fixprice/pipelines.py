# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import json
import os

# useful for handling different item types with a single interface


class MultiFilePipeline:
    def __init__(self):
        self.files = {}

    def open_spider(self, spider):
        pass

    def close_spider(self, spider):
        for file in self.files.values():
            file.close()

    def process_item(self, item, spider):
        category_url = item['url']
        file_name = category_url.split('/')[-2] + ".json"
        if file_name not in self.files:
            file_path = os.path.join(spider.settings.get('FEED_URI', '.'), file_name)
            self.files[file_name] = open(file_path, 'w')

        line = json.dumps(dict(item)) + "\n"
        self.files[file_name].write(line)
        return item
