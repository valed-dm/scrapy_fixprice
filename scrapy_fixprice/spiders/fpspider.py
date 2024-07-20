import logging
import time

import scrapy
from playwright.async_api import Page
from scrapy_playwright.page import PageMethod

logging.basicConfig(
    filename='scrapy_spider.log',
    filemode='w',  # Overwrite the log file each run
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


class MySpider(scrapy.Spider):
    name = "fpspider"
    start_urls = [
        "https://fix-price.com/catalog/produkty-i-napitki/konditerskie-izdeliya",
        "https://fix-price.com/catalog/kosmetika-i-gigiena/ukhod-za-polostyu-rta",
        "https://fix-price.com/catalog/sad-i-ogorod/tovary-dlya-rassady-i-semena",
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        # PageMethod('route', "**/*.{png,jpg,jpeg,gif}", lambda route: route.abort()),
                        # PageMethod('route', self.block_trackers),
                        # PageMethod('goto', url),
                    ],
                },
                # meta=dict(
                #     playwright=True,
                #     playwright_include_page=True,
                #     playwright_page_methods=[
                #         # PageMethod('route', "**/*.{png,jpg,jpeg,gif}", lambda route: route.abort()),
                #         # PageMethod('route', self.block_trackers),
                #         # PageMethod('goto', url),
                #     ]
                # ),
                errback=self.errback_close_page,
            )

    async def parse(self, response):
        page: Page = response.meta["playwright_page"]
        products = response.css("div.product__wrapper")
        for product in products:
            pid = product.css("div.product.one-product-in-row::attr(id)").get()
            link = product.css("a.title::attr(href)").get()
            title = product.css("a.title::text").get()
            vcount = product.css("div.variants-count::text").get()

            yield scrapy.Request(
                url=response.urljoin(link),
                callback=self.parse_details,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page": page,
                    "RPC": pid[2:],
                    "link": link,
                    "title": title,
                    "variants": vcount if vcount else None,
                },
                errback=self.errback_close_page,
            )

    async def parse_details(self, response):
        element_timeout = 10000

        page: Page = response.meta["playwright_page"]
        # await page.wait_for_selector("div.product__wrapper", timeout=element_timeout * 2)
        # self.logger.info("Page loaded, starting to extract details.")

        try:
            await page.wait_for_selector("a[href*='products?brand=']", timeout=element_timeout)
            brand = await page.query_selector("a[href*='products?brand=']")
            brand_text = await brand.inner_text() if brand else "Unknown brand"
        except Exception as e:
            brand_text = None
            self.logger.error(f"Error finding brand: {e}")

        try:
            await page.wait_for_selector("div.product-details div.description", timeout=element_timeout)
            description = await page.query_selector("div.product-details div.description")
            description_text = await description.inner_text() if description else None
        except Exception as e:
            description_text = None
            self.logger.error(f"Error finding description: {e}")

        try:
            await page.wait_for_selector("div.product-images div.sticker", timeout=element_timeout)
            marketing_tag = await page.query_selector("div.product-images div.sticker")
            marketing_tag_text = await marketing_tag.inner_text() if marketing_tag else None
        except Exception as e:
            marketing_tag_text = None
            self.logger.error(f"Error finding marketing tag: {e}")

        try:
            await page.wait_for_selector("div.prices div.special-price", timeout=element_timeout)
            special_price = await page.query_selector("div.prices div.special-price")
            special_price_text = await special_price.inner_text() if special_price else None
        except Exception as e:
            special_price_text = None
            self.logger.error(f"Error finding special price: {e}")

        try:
            await page.wait_for_selector("div.prices div.regular-price", timeout=element_timeout)
            regular_price = await page.query_selector("div.prices div.regular-price")
            regular_price_text = await regular_price.inner_text() if regular_price else None
        except Exception as e:
            regular_price_text = None
            self.logger.error(f"Error finding regular price: {e}")

        special_price_value = None
        regular_price_value = None
        discount_value = 0

        if special_price_text:
            special_price_value = round(float(
                special_price_text.replace('₽', '').replace(',', '.').strip()
            ), 2)

        if regular_price_text:
            regular_price_value = round(float(
                regular_price_text.replace('₽', '').replace(',', '.').strip()
            ), 2)

        if special_price_value and regular_price_value:
            if special_price_value >= regular_price_value:
                special_price_value = regular_price_value
                self.logger.warning(
                    f"Special price {special_price_text} is not less than regular price {regular_price_text},"
                    f" is replaced with {regular_price_text}")
            else:
                cash_discount = regular_price_value - special_price_value
                discount_value = round(cash_discount / regular_price_value * 100)

        self.logger.info(f"Scraped Prices - "
                         f"Regular Price: {regular_price_text}, "
                         f"Special Price: {special_price_text}, "
                         f"Discount Value: {discount_value}")

        yield {
            "timestamp": int(time.time()),
            "RPC": response.meta.get("RPC"),
            "url": response.meta.get("link"),
            "title": response.meta.get("title"),
            "marketing_tags": marketing_tag_text,
            "brand": brand_text,
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
                "__description": description_text,
                "KEY": "str",
            },
            "variants": response.meta.get("variants"),
        }

    async def errback_close_page(self, failure):
        page: Page = failure.request.meta.get("playwright_page")
        if page:
            await page.close()

    async def block_trackers(self, route):
        url = route.request.url
        if any(tracker in str(url) for tracker in [
            # "google-analytics.com",
            # "googletagmanager.com",
            # "facebook.net",
            # "facebook.com",
            # "doubleclick.net",
            # "adsbygoogle.js",
            # "adservice.google.com",
            # "tracking_domain_1.com",
            # "tracking_domain_2.com",
            "top-fwz1.mail.ru",
            "mc.yandex.ru",
        ]):
            await route.abort()
        else:
            await route.continue_()
