# -*- coding: utf-8 -*-
import os
import configparser

# Scrapy settings for tutorial project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'tutorial'

SPIDER_MODULES = ['tutorial.spiders']
NEWSPIDER_MODULE = 'tutorial.spiders'


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'tutorial (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 16

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 1
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
COOKIES_ENABLED = True

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    'tutorial.middlewares.TutorialSpiderMiddleware': 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    'tutorial.middlewares.TutorialDownloaderMiddleware': 543,
#}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
#ITEM_PIPELINES = {
#    'tutorial.pipelines.TutorialPipeline': 300,
#}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

RETRY_HTTP_CODES = [429]

DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
    'tutorial.middlewares.TooManyRequestsRetryMiddleware': 543,
}


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Settings:
    @staticmethod
    def _normalize_path(path):
        if not os.path.isfile(path):
            raise FileNotFoundError(f'No such file - {path}')
        return path

    def __init__(self, file_path):
        self.file_path = self._normalize_path(file_path)
        self.config = configparser.ConfigParser()
        self.config.read(self.file_path)
        credentials = self.config['Credentials'] if 'Credentials' in self.config.sections() else {}
        query_keys = self.config['QueryKeys'] if 'QueryKeys' in self.config.sections() else {}
        parameters = self.config['Parameters'] if 'Parameters' in self.config.sections() else {}
        cookies = self.config['Cookies'] if 'Cookies' in self.config.sections() else {}
        output = self.config['Output'] if 'Output' in self.config.sections() else {}

        self.login = credentials.get('LOGIN', 'test')
        self.password = credentials.get('PASSWORD', 'qwerty123')

        self.query_keys_query = query_keys.get('QUERY', 'q')
        self.query_keys_page = query_keys.get('PAGE', 'p')

        self.domain = parameters.get('DOMAIN', 'https://github.com')
        self.start = parameters.get('START_PAGE_NUMBER', '1')
        self.limit = parameters.get('NUMBER_OF_PAGES', '0')
        self.print_list = parameters.get('SHOW_LINKS_PER_SEARCH_PAGE', 'false')
        self.print_item = parameters.get('SHOW_REPOSITORY_INFO_SEPARATELY', 'false')
        _query_line = '+'.join(parameters.get('QUERY').split(' ')) if parameters.get('QUERY') else None
        self.query = f'/search?{self.query_keys_page}=' + self.start + \
                     f'&{self.query_keys_query}=' + _query_line

        self.get_cookies_file = cookies.get('COOKIES_INPUT')
        self.set_cookies_file = cookies.get('COOKIES_OUTPUT')

        self.output_excel_file = output.get('EXCEL')


settings = Settings(file_path=os.path.join(BASE_DIR, 'config.ini'))
