from scrapy.dupefilters import RFPDupeFilter


class CustomDupeFilter(RFPDupeFilter):

    def __init__(self, path=None, debug=False, include_headers=None):
        self.include_headers = include_headers
        self.crawler = None  # Ensure crawler is initialized as None
        super().__init__(path, debug)

    @classmethod
    def from_settings(cls, settings):
        path = settings.get('HTTPCACHE_DIR')
        debug = settings.getbool('DUPEFILTER_DEBUG')
        include_headers = settings.getlist('DUPEFILTER_INCLUDE_HEADERS', None)
        return cls(path, debug, include_headers)

    @classmethod
    def from_crawler(cls, crawler):
        obj = cls.from_settings(crawler.settings)
        obj.crawler = crawler  # Set the crawler attribute
        return obj

    def request_fingerprint(self, request):
        if self.include_headers:
            return self.crawler.request_fingerprinter.fingerprint(request, include_headers=self.include_headers)
        else:
            return self.crawler.request_fingerprinter.fingerprint(request)

    def request_seen(self, request):
        try:
            fp = self.request_fingerprint(request).decode('utf-8')  # Decode bytes to string
        except UnicodeDecodeError:
            fp = self.request_fingerprint(request).hex()  # Fallback to hex representation if decoding fails

        if fp in self.fingerprints:
            return True
        self.fingerprints.add(fp)
        if self.file:
            self.file.write(fp + "\n")
        return False
