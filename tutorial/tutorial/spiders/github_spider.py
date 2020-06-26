import copy
import gc
import json
import time
import os

import scrapy
import openpyxl

from ..settings import settings, BASE_DIR
from ..items import GitHubRepoInfoItem, GitHubLinksItem


class GithubSpider(scrapy.Spider):
    name = 'github'

    domain = 'https://github.com'
    start_urls = [
        'https://github.com/search?p=1&q=python&type=Repositories',
    ]

    def __init__(self, start=1, limit=10,
                 lists=False, items=False,
                 login=None, password=None,
                 config=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wb_path = None
        self.visited_repos_urls = set()
        self.next_page_number = None
        start, limit = int(start), int(limit)
        self.use_query_settings = bool(json.loads(str(config).lower()))
        if self.use_query_settings:
            self._init_with_settings(start, limit)
        else:
            self._init_with_console(login, password, start, limit, lists, items)

    def _init_with_settings(self, start, limit):
        self.start = int(settings.start) if settings.start.isdigit() else start
        self.limit = int(settings.limit) if settings.start.isdigit() else limit
        self.limit = self.limit + self.start - 1
        self.login = settings.login if settings.login else None
        self.password = settings.password if settings.password else None
        self.domain = settings.domain or self.domain
        self.start_urls = [''.join([self.domain, settings.query])]
        self.get_cookies_path = os.path.join(BASE_DIR, settings.get_cookies_file) if settings.get_cookies_file else None
        self.set_cookies_path = os.path.join(BASE_DIR, settings.set_cookies_file) if settings.set_cookies_file else None

    def _init_with_console(self, login, password, start, limit, lists, items):
        self.start = start
        self.limit = limit + start - 1
        self.login = login
        self.password = password
        self.print_list = bool(json.loads(str(lists).lower()))
        self.print_item = bool(json.loads(str(items).lower()))

        if start != 1 and not self.use_query_settings:
            url = self.start_urls[-1]
            current_page_in_url_index = url.find('p=')
            url = url[:current_page_in_url_index + 2] + str(start) + url[url.find('&', current_page_in_url_index):]
            self.start_urls[-1] = url

    def start_requests(self):
        cookies = self._read_cookies() or {}
        yield scrapy.Request(
            url='https://github.com/login',
            method='GET',
            cookies=cookies,
            encoding='utf-8',
            callback=self._log_in,
        )

    def _log_in(self, response):
        if self._auth_failed(response):
            if bool(self.login) and bool(self.password):
                yield scrapy.FormRequest.from_response(
                    response,
                    formdata={'login': self.login, 'password': self.password},
                    callback=self._after_login,
                )
            else:
                self.logger.error('NOT LOGGED IN BECAUSE NO LOGIN AND PASSWORD WERE PRESENTED')
                for url in self.start_urls:
                    yield scrapy.Request(url, dont_filter=True)
        else:
            self.logger.info('SUCCESSFULLY LOGGED IN WITH COOKIES')
            self._write_cookies(response)
            for url in self.start_urls:
                yield scrapy.Request(url, dont_filter=True)

    def _after_login(self, response):
        if self._auth_failed(response):
            self.logger.error('NOT LOGGED IN')
        else:
            self.logger.info('SUCCESSFULLY LOGGED IN WITH CREDENTIALS')
            self._write_cookies(response)

        for url in self.start_urls:
            yield scrapy.Request(url, dont_filter=True)

    def _auth_failed(self, response):
        return not (
                response.status == 200 and
                response.request.method == 'GET' and
                (response.request.url in [self.domain, self.domain+'/'])
        )

    def _write_cookies(self, response):
        if hasattr(self, 'set_cookies_path') and self.set_cookies_path:
            site_cookies = response.request.headers.get('Cookie').decode('utf-8').split(';')
            with open(self.set_cookies_path, 'w') as set_cookie:
                for cookie in site_cookies:
                    set_cookie.write(cookie + '\n')
            self.logger.info('COOKIES ARE STORED')

    def _read_cookies(self):
        if hasattr(self, 'get_cookies_path') and self.get_cookies_path:
            cookies_from_file = []
            if os.path.isfile(self.get_cookies_path):
                with open(self.get_cookies_path, 'r') as get_cookies:
                    for line in get_cookies:
                        cookies_from_file.append(line)
            if cookies_from_file:
                return {item.strip().split('=')[0]: item.strip().split('=')[1] for item in cookies_from_file}

    def parse(self, response):
        next_page_url = response.css('a.next_page').xpath('@href').get()

        [current_page] = [int(item.split('=')[1])
                          for item in response.url.split('?')[1].split('&')
                          if item.startswith('p=')]

        if next_page_url is not None:
            [self.next_page_number] = [int(item.split('=')[1])
                                       for item in next_page_url.split('?')[1].split('&')
                                       if item.startswith('p=')]
        else:
            self.next_page_number = self.limit + 1

        repos_urls = response. \
            css('ul.repo-list li.public.source div.mt-n1 div.f4.text-normal a').\
            xpath('@href').getall()

        yield GitHubLinksItem(page=current_page, data=repos_urls)

        for link_number, repo_url in enumerate(repos_urls, start=1):
            if repo_url not in self.visited_repos_urls:
                self.visited_repos_urls.add(repo_url)
                yield response.follow(repo_url,
                                      callback=self.parse_repos,
                                      dont_filter=True,
                                      cb_kwargs=dict(
                                          page_number=self.next_page_number-1,
                                          link_number=link_number,
                                      ))

        self._controller_sleep(60)
        gc.collect()

        if self.next_page_number <= self.limit:
            yield response.follow(next_page_url, callback=self.parse)

    def parse_repos(self, response, page_number, link_number):
        repo = response.url.split('github.com/')[1]
        if 'Cannot retrieve the latest commit at this time' not in response.text:
            repos_last_commit = response.css('a.link-gray.text-small::text').get()
            commit = repos_last_commit.strip() if isinstance(repos_last_commit, str) else ''
            yield GitHubRepoInfoItem(
                page=page_number,
                link=link_number,
                repo=repo,
                commit=commit,
            )

        else:
            page_with_commits_url = response.css('ul.list-style-none.d-flex li.ml-3 a.link-gray-dark').xpath('@href').get()
            yield response.follow(page_with_commits_url,
                                  callback=self.parse_commits,
                                  cb_kwargs=dict(
                                      page_number=page_number,
                                      link_number=link_number,
                                      repo=repo,
                                  ))

    def parse_commits(self, response, page_number, link_number, repo):
        repos_last_commit = response.css('ol.commit-group.Box li.commit div.commit-links-group a.sha::text').get()  # !
        commit = repos_last_commit.strip() if isinstance(repos_last_commit, str) else ''
        yield GitHubRepoInfoItem(
            page=page_number,
            link=link_number,
            repo=repo,
            commit=commit,
        )

    def _controller_sleep(self, seconds=30):
        self.crawler.engine.pause()
        time.sleep(seconds)
        self.crawler.engine.unpause()
