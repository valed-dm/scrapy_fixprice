import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
import time
import logging


logging.basicConfig(
    filename='scrapy_spider.log',
    filemode='w',  # Overwrite the log file each run
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


class GoodsSpiderSelenium(scrapy.Spider):
    name = "goods_selenium"
    start_urls = [
        "https://fix-price.com/catalog/kosmetika-i-gigiena/ukhod-za-polostyu-rta",
    ]

    def __init__(self, *args, **kwargs):
        super(GoodsSpiderSelenium, self).__init__(*args, **kwargs)
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=chrome_options
        )

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        self.driver.get(response.url)
        time.sleep(5)  # Wait for JavaScript to load content

        products = self.driver.find_elements(By.CSS_SELECTOR, "div.product__wrapper")
        for product in products:
            try:
                title = product.find_element(By.CSS_SELECTOR, "a.title").text
            except NoSuchElementException as e:
                title = None
                logging.error(f"Error finding title: {e}")

            try:
                link = product.find_element(By.CSS_SELECTOR, "a.title").get_attribute("href")
            except NoSuchElementException as e:
                link = None
                logging.error(f"Error finding link: {e}")

            try:
                variants_count = product.find_element(By.CSS_SELECTOR, "div.variants-count").text
            except NoSuchElementException as e:
                variants_count = None
                logging.error(f"Error finding variants count: {e}")

            try:
                regular_price = product.find_element(By.CSS_SELECTOR, "div.regular-price").text
            except NoSuchElementException as e:
                regular_price = None
                logging.error(f"Error finding regular price: {e}")

            try:
                pid = product.find_element(
                    By.CSS_SELECTOR,
                    "div.product.one-product-in-row"
                ).get_attribute("id")
                rpc = pid[2:]
            except NoSuchElementException as e:
                rpc = None
                logging.error(f"Error finding retail product code: {e}")

            yield {
                "timestamp": int(time.time()),
                "RPC": rpc,
                "url": link,
                "title": title,
                "marketing_tags": "str",
                "brand": "str",
                "section": "str",
                "price_data": {
                    "current": "float",  # Цена со скидкой, если скидки нет то = original.
                    "original": regular_price,   # Оригинальная цена.
                    "sale_tag": "Скидка {discount_percentage}%"
                },
                "stock": {
                    "in_stock": "bool",
                    "count": "int",
                },
                "assets": {
                    "main_image": "str",
                    "set_images": "str",
                    "view360": "str",
                    "video": "str",
                },
                "metadata": {
                    "__description": "str",
                    "KEY": "str",
                },
                "variants": variants_count,
            }

    def closed(self, reason):
        self.driver.quit()
