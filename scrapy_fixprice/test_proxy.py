from playwright.sync_api import sync_playwright

PROXY_USERNAME = "hjgjyxnh-rotate"
PROXY_PASSWORD = "o4kgivvegm5n"
DOMAIN_NAME = "p.webshare.io"
PROXY_PORT = 80

proxy = {
    "server": f"http://{DOMAIN_NAME}:{PROXY_PORT}",
    "username": PROXY_USERNAME,
    "password": PROXY_PASSWORD,
}

with sync_playwright() as p:
    browser = p.chromium.launch(proxy=proxy)
    page = browser.new_page()
    page.goto("https://httpbin.org/ip")
    print(page.content())
    browser.close()
