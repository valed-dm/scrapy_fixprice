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
        # "https://fix-price.com/catalog/produkty-i-napitki/konditerskie-izdeliya"
        "https://fix-price.com/catalog/kosmetika-i-gigiena/ukhod-za-polostyu-rta",
        # "https://fix-price.com/catalog/sad-i-ogorod/tovary-dlya-rassady-i-semena",
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
        discount_value = 0
        special_price_value = None
        regular_price_value = None

        rpc = response.meta.get("RPC")
        link = response.meta.get("link")
        title = response.meta.get("title")
        variants = response.meta.get("variants")

        # Scrapy extraction
        brand = response.xpath("//a[contains(@href, 'products?brand=')]/text()").get()
        description = response.css("div.product-details div.description::text").get()
        marketing_tag = response.css("div.product-images div.sticker::text").get()

        # Selenium for dynamic content
        self.driver.get(response.url)

        # Clear cache to ensure fresh data
        self.driver.execute_script("window.localStorage.clear();")
        self.driver.execute_script("window.sessionStorage.clear();")
        self.driver.delete_all_cookies()

        time.sleep(20)

        try:
            special_price_element = self.driver.find_element(
                By.CSS_SELECTOR,
                "div.price-in-cart div.special-price"
            )
            if special_price_element.is_displayed():
                special_price = special_price_element.text
            else:
                special_price = None
        except NoSuchElementException as e:
            special_price = None
            logging.error(f"Error finding special_price: {e}")

        try:
            regular_price = self.driver.find_element(
                By.CSS_SELECTOR,
                "div.price-in-cart div.regular-price"
            ).text
        except NoSuchElementException as e:
            regular_price = None
            logging.error(f"Error finding regular_price: {e}")

        if special_price:
            special_price_value = round(float(
                special_price.replace('₽', '').replace(',', '.').strip()
            ), 2)
        if regular_price:
            regular_price_value = round(float(
                regular_price.replace('₽', '').replace(',', '.').strip()
            ), 2)

        # Validate that prices make sense
        if special_price_value and regular_price_value:
            if special_price_value >= regular_price_value:
                logging.warning(
                    f"Special price {special_price} is not less than regular price {regular_price},"
                    f"is replaced with {regular_price_value}")
                special_price_value = regular_price_value
            else:
                cash_discount = regular_price_value - special_price_value
                discount_value = round(cash_discount / regular_price_value * 100)

        # Log the prices for debugging purposes
        logging.info(f"Scraped Prices - "
                     f"Regular Price: {regular_price}, "
                     f"Special Price: {special_price}, "
                     f"Discount Value: {discount_value}"
                     )

        yield {
            "timestamp": int(time.time()),
            "RPC": rpc,
            "url": link,
            "title": title,
            "marketing_tags": marketing_tag,
            "brand": brand,
            "section": "str",
            "price_data": {
                "current": special_price_value,
                "original": regular_price_value,
                "sale_tag": f"Скидка {discount_value}%"
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
            "variants": variants,
        }

    def closed(self, reason):
        self.driver.quit()
