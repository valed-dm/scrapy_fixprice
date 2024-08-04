# Scrapy settings for scrapy project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "scrapy_fixprice"

SPIDER_MODULES = ["scrapy_fixprice.spiders"]
NEWSPIDER_MODULE = "scrapy_fixprice.spiders"

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = "scrapy (+http://www.yourdomain.com)"

# User Agent rotation
FAKEUSERAGENT_PROVIDERS = [
    'scrapy_fake_useragent.providers.FakeUserAgentProvider',
    'scrapy_fake_useragent.providers.FakerProvider',
    'scrapy_fake_useragent.providers.FixedUserAgentProvider',
]

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 1.0
RANDOMIZE_DOWNLOAD_DELAY = True

# The download delay setting will honor only one of:
CONCURRENT_REQUESTS_PER_DOMAIN = 16
CONCURRENT_REQUESTS_PER_IP = 16

# Disable Telnet Console (enabled by default)
TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
# }

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    "scrapy.middlewares.ScrapyFixpriceSpiderMiddleware": 543,
# }

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html

# Enable the proxy middleware
# DOWNLOADER_MIDDLEWARES = {
#     'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 1,
#     'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
#     'scrapy_user_agents.middlewares.RandomUserAgentMiddleware': 400,
#     'scrapy_proxy_pool.middlewares.ProxyPoolMiddleware': 410,
#     'scrapy_proxy_pool.middlewares.BanDetectionMiddleware': 420,
# }
DOWNLOADER_MIDDLEWARES = {
    # "scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware": None,
    "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": 90,
    # "scrapy_fixprice.middlewares.ProxyMiddleware": 100,
    "scrapy_user_agents.middlewares.RandomUserAgentMiddleware": 400,
}
# DOWNLOADER_MIDDLEWARES.update({
#     "scrapy_fixprice.middlewares.ProxyMiddleware": 543,
# })

# DOWNLOAD_HANDLERS = {
#     "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
#     "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
# }

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
# }
EXTENSIONS = {
    "scrapy.extensions.memusage.MemoryUsage": None,
    "scrapy_playwright.memusage.ScrapyPlaywrightMemoryUsageExtension": 0,
}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    "scrapy_fixprice.pipelines.ItemFilterPipeline": 1,
    "scrapy_fixprice.pipelines.MultiFilePipeline": 2,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
AUTOTHROTTLE_ENABLED = True
# The initial download delay
AUTOTHROTTLE_START_DELAY = 1.0
# The maximum download delay to be set in case of high latencies
AUTOTHROTTLE_MAX_DELAY = 60.0
# The average number of requests Scrapy should be sending in parallel to
# each remote server
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
AUTOTHROTTLE_DEBUG = False

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# Proxy pool settings
# PROXY_POOL_ENABLED = True
# PROXY_POOL_PAGE_RETRY_TIMES = 3
# PROXY_POOL_CLOSE_SPIDER = False

# Retry settings
RETRY_ENABLED = True
RETRY_TIMES = 10

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = "httpcache"
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

FEEDS = {
    'output.jsonl': {
        'format': 'jsonlines',
        'encoding': 'utf8',
        'store_empty': False,
        'fields': None,
        'indent': 4,
    },
}

# ScraperAPI settings
# SCRAPERAPI_KEY = 'd719fa90954daf1487b4148425e1490f'  # Replace with your ScraperAPI key

# Bright Data settings
# BRIGHTDATA_PROXY = 'http://brd-customer-hl_6f43352b-zone-datacenter_proxy1:nbfja0tg2dnj@brd.superproxy.io:22225'

# Webshare credentials
# WEBSHARE_API_KEY = "0g2afd8373721xvegcz88h4q7zqtexmfz3jtlvv3"
# WEBSHARE_API_URL = "https://proxy.webshare.io/api/proxy/list/"

# Proxy settings
# PROXY_USERNAME = "hjgjyxnh-rotate"
# PROXY_PASSWORD = "o4kgivvegm5n"
# DOMAIN_NAME = "p.webshare.io"
# PROXY_PORT = 80

# PLAYWRIGHT_BROWSER_TYPE = "webkit"
# PLAYWRIGHT_LAUNCH_OPTIONS = {
#     "headless": False,
#     "proxy": {
#         "server": f"http://{DOMAIN_NAME}:{PROXY_PORT}",
#         "username": PROXY_USERNAME,
#         "password": PROXY_PASSWORD,
#     },
# }
