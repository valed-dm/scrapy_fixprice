import logging
import time

import playwright
import scrapy
from playwright.async_api import Page
from playwright_stealth import stealth_async
from scrapy_playwright.page import PageMethod
from fake_useragent import UserAgent

logging.basicConfig(
    filename='scrapy_spider.log',
    filemode='w',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)


class MySpider(scrapy.Spider):
    name = "fpspider"
    start_urls = [
        "https://fix-price.com/catalog/krasota-i-zdorove/dlya-litsa",
        "https://fix-price.com/catalog/igrushki/razvivayushchie-igry",
        "https://fix-price.com/catalog/kosmetika-i-gigiena/ukhod-za-polostyu-rta",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_agent = UserAgent()

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                headers={'User-Agent': self.user_agent.random},
                meta=dict(
                    playwright=True,
                    playwright_include_page=True,
                    playwright_page_methods=[
                        PageMethod('route', "**/*.{png,jpg,jpeg,gif}", self.abort_images_and_popups),
                        PageMethod('route', "**/*", self.block_trackers),
                        PageMethod('on', 'dialog', self.handle_dialog),
                        # PageMethod('wait_for_timeout', 5000),
                        # PageMethod('wait_for_load_state', 'networkidle', timeout=60000),
                        # PageMethod('goto', url, wait_until="networkidle", timeout=60000),
                    ]
                ),
                errback=self.errback_close_page,
            )

    async def parse(self, response):
        page: Page = response.meta["playwright_page"]
        await stealth_async(page)

        # Capture a screenshot
        # await page.screenshot(path="screenshot.png")

        # Extract item data on the catalog page
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
                    "RPC": pid[2:],
                    "link": link,
                    "title": title,
                    "variants": vcount if vcount else None,
                    "playwright_page_methods": [
                        PageMethod('route', "**/*.{png,jpg,jpeg,gif}", self.abort_images_and_popups),
                        PageMethod('route', "**/*", self.block_trackers),
                        PageMethod('on', 'dialog', self.handle_dialog),
                        # PageMethod('wait_for_load_state', 'networkidle', timeout=60000)
                    ],
                },
                errback=self.errback_close_page,
            )

        # Handle pagination
        current_page = response.css("a.button.active.number::attr(data-page)").get()
        if current_page:
            next_page = int(current_page) + 1
            next_page_link = response.css(f"a[data-page='{next_page}']::attr(href)").get()
            if next_page_link:
                yield scrapy.Request(
                    url=response.urljoin(next_page_link),
                    callback=self.parse,
                    meta={
                        "playwright": True,
                        "playwright_include_page": True,
                        "playwright_page_methods": [
                            PageMethod('route', "**/*.{png,jpg,jpeg,gif}", self.abort_images_and_popups),
                            PageMethod('route', "**/*", self.block_trackers),
                            PageMethod('on', 'dialog', self.handle_dialog),
                        ],
                    },
                    errback=self.errback_close_page,
                )

        await page.close()

    async def parse_details(self, response):
        element_timeout = 60000
        page = response.meta["playwright_page"]
        await stealth_async(page)

        try:
            try:
                await page.wait_for_selector("div.properties a[href*='products?brand=']", timeout=element_timeout)
                brand = await page.query_selector("div.properties a[href*='products?brand=']")
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

        finally:
            await page.close()

    async def errback_close_page(self, failure):
        self.logger.error(repr(failure))
        if failure.check(playwright._impl._errors.Error):
            self.logger.error('Playwright error: %s', failure.value)
        page: Page = failure.request.meta.get("playwright_page")
        if page:
            self.logger.info("Closing page due to error")
            self.crawler.engine.close_spider(self, "spider_error")

            await page.close()

    async def abort_images_and_popups(self, route, request):
        if request.resource_type in ["image", "media", "stylesheet", "font"]:
            await route.abort()
        elif any(keyword in request.url for keyword in ["popup", "modal", "advertisement", "ads"]):
            await route.abort()
        else:
            await route.continue_()

    async def block_trackers(self, route, request):
        blocked_resources = [
            "top-fwz1.mail.ru",
            "mc.yandex.ru",
            "vk.com",
            "img.fix-price.com",
            "secure.usedesk.ru",
            "cdn-cgi",
        ]
        keywords = ["tracker", "analytics", "ads", "doubleclick", "googletagmanager"]

        if any(resource in route.request.url for resource in blocked_resources) or \
                any(keyword in route.request.url for keyword in keywords):
            await route.abort()
        else:
            await route.continue_()

    async def handle_dialog(self, dialog):
        await dialog.dismiss()
