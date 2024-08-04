import scrapy
from fake_useragent import UserAgent
import logging
import time
from scrapy_splash import SplashRequest

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
            yield SplashRequest(
                url=url,
                callback=self.parse,
                headers={'User-Agent': self.user_agent.random},
                args={'wait': 5}
            )

    def parse(self, response):
        # Extract item data on the catalog page
        products = response.css("div.product__wrapper")
        for product in products:
            pid = product.css("div.product.one-product-in-row::attr(id)").get()
            link = product.css("a.title::attr(href)").get()
            title = product.css("a.title::text").get()
            vcount = product.css("div.variants-count::text").get()

            yield SplashRequest(
                url=response.urljoin(link),
                callback=self.parse_details,
                meta={
                    "RPC": pid[2:],
                    "link": link,
                    "title": title,
                    "variants": vcount if vcount else None,
                },
                args={'wait': 10}
            )

        # Handle pagination
        current_page = response.css("a.button.active.number::attr(data-page)").get()
        if current_page:
            next_page = int(current_page) + 1
            next_page_link = response.css(f"a[data-page='{next_page}']::attr(href)").get()
            if next_page_link:
                yield SplashRequest(
                    url=response.urljoin(next_page_link),
                    callback=self.parse,
                    args={'wait': 20}
                )

    def parse_details(self, response):

        try:
            brand_text = response.css("div.properties a[href*='products?brand=']::text").get(default="Unknown brand")
            description_text = response.css("div.product-details div.description::text").get()
            marketing_tag_text = response.css("div.product-images div.sticker::text").get()
            special_price_text = response.css("div.prices div.special-price::text").get()
            regular_price_text = response.css("div.prices div.regular-price::text").get()

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

        except Exception as e:
            self.logger.error(f"Error parsing details: {e}")
