import logging
import time

import scrapy
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

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
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/91.0.4472.124 "
            "Safari/537.36"
        )

        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        products = response.css("div.product__wrapper")
        for product in products:
            pid = product.css("div.product.one-product-in-row::attr(id)").get()
            rpc = pid[2:]
            link = product.css("a.title::attr(href)").get()
            title = product.css("a.title::text").get()
            vcount = product.css("div.variants-count::text").get()

            yield scrapy.Request(
                url=response.urljoin(link),
                callback=self.parse_details,
                meta={
                    "RPC": rpc,
                    "link": link,
                    "title": title,
                    "variants": vcount if vcount else None,
                }
            )

    def parse_details(self, response):
        self.driver.get(response.url)
        time.sleep(10)

        try:
            brand = self.driver.find_element(By.XPATH, "//a[contains(@href, 'products?brand=')]")
            brand = brand.text or "Unknown brand"
        except NoSuchElementException as e:
            brand = None
            logging.error(f"Error finding brand: {e}")

        try:
            description = self.driver.find_element(
                By.CSS_SELECTOR,
                "div.product-details div.description"
            ).text
        except NoSuchElementException as e:
            description = None
            logging.error(f"Error finding description: {e}")

        try:
            special_price = self.driver.find_element(By.CSS_SELECTOR, "div.prices div.special-price").text
        except NoSuchElementException as e:
            special_price = None
            logging.error(f"Error finding special_price: {e}")

        try:
            regular_price = self.driver.find_element(By.CSS_SELECTOR, "div.prices div.regular-price").text
        except NoSuchElementException as e:
            regular_price = None
            logging.error(f"Error finding regular_price: {e}")

        yield {
            "timestamp": int(time.time()),
            "RPC": response.meta["RPC"],
            "url": response.meta["link"],
            "title": response.meta["title"],
            "marketing_tags": "str",
            "brand": brand,
            "section": "str",
            "price_data": {
                "current": special_price if special_price else regular_price,
                "original": regular_price,
                "sale_tag": "Скидка {}%"
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
                "__description": description,
                "KEY": "str",
            },
            "variants": response.meta["variants"],
        }

    def closed(self, reason):
        self.driver.quit()
