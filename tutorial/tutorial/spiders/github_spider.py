import copy
import gc
import json
import time
import os

import scrapy
import openpyxl

from ..settings import settings, BASE_DIR


def auth_failed(response):
    return not (response.status == 200 and
                response.request.method == 'GET' and
                response.request.url == 'https://github.com')


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
        self.repos_data_mask = {
            'page': None,
            'link': None,
            'repo': None,
            'commit': None
        }
        start, limit = int(start), int(limit)
        self.use_query_settings = bool(json.loads(str(config).lower()))
        if self.use_query_settings:
            self.start = int(settings.start) if settings.start.isdigit() else start
            self.limit = int(settings.limit) if settings.start.isdigit() else limit
            self.limit = self.limit + self.start - 1
            self.login = settings.login if settings.login else None
            self.password = settings.password if settings.password else None
            self.print_list = bool(json.loads(str(settings.print_list).lower()))
            self.print_item = bool(json.loads(str(settings.print_item).lower()))
            self.domain = settings.domain or self.domain
            self.start_urls = [''.join([self.domain, settings.query])]
            self.wb_path = os.path.join(BASE_DIR, settings.output_excel_file) if settings.output_excel_file else None
            if self.wb_path:
                wb = openpyxl.Workbook()
                wb.save(self.wb_path)
                wb.close()
                headers = ['link', 'commit']
                self._fill_excel_with_data(url=headers[0], commit=headers[-1])
        else:
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
        yield scrapy.Request(
            url='https://github.com/login',
            method='GET',
            encoding='utf-8',
            callback=self.log_in,
        )

    def log_in(self, response):
        if bool(self.login) and bool(self.password):
            yield scrapy.FormRequest.from_response(
                response,
                formdata={'login': self.login, 'password': self.password},
                callback=self.after_login,
            )
        else:
            for url in self.start_urls:
                yield scrapy.Request(url, dont_filter=True)

    def after_login(self, response):
        if auth_failed(response):
            self.logger.error('Not logged in!')
        else:
            self.logger.info('Successfully logged in!')
        for url in self.start_urls:
            yield scrapy.Request(url, dont_filter=True)

    def parse(self, response):
        next_page_url = response.css('a.next_page').xpath('@href').get()
        if next_page_url is not None:
            [self.next_page_number] = [int(item.split('=')[1])
                                       for item in next_page_url.split('?')[1].split('&')
                                       if item.startswith('p=')]
        else:
            self.next_page_number = self.limit + 1

        repos_urls = response. \
            css('ul.repo-list li.public.source div.mt-n1 div.f4.text-normal a').\
            xpath('@href').getall()

        if self.print_list:
            with open(f'./output/links-page{self.next_page_number-1}.json', 'w') as links_json:
                links_json.write(json.dumps(dict(data=repos_urls)))

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
            repos_data = copy.copy(self.repos_data_mask)

            repos_last_commit = response.css('a.link-gray.text-small::text').get()

            repos_data['page'] = page_number
            repos_data['link'] = link_number
            repos_data['repo'] = repo
            repos_data['commit'] = repos_last_commit.strip() if isinstance(repos_last_commit, str) else None

            if self.print_item:
                with open(f'./output/page{page_number}link{link_number}.json', 'w') as json_doc:
                    json_doc.write(json.dumps(repos_data))

            if self.wb_path:
                self._fill_excel_with_data(response.url, repos_data['commit'])

            yield repos_data

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
        repos_data = copy.copy(self.repos_data_mask)
        repos_data['page'] = page_number
        repos_data['link'] = link_number
        repos_data['repo'] = repo
        repos_data['commit'] = repos_last_commit.strip() if isinstance(repos_last_commit, str) else None

        if self.print_item:
            with open(f'./output/page{page_number}link{link_number}.json', 'w') as json_doc:
                json_doc.write(json.dumps(repos_data))

        if self.wb_path:
            self._fill_excel_with_data(self.domain+repo, repos_data['commit'])

        yield repos_data

    def _controller_sleep(self, seconds=30):
        self.crawler.engine.pause()
        time.sleep(seconds)
        self.crawler.engine.unpause()

    def _fill_excel_with_data(self, url, commit):
        wb = openpyxl.load_workbook(filename=self.wb_path)
        ws = wb.active
        ws.append([url, commit])
        wb.save(self.wb_path)
        wb.close()


class GithubLoginSpider(scrapy.Spider):
    name = 'githublogin'

    start_urls = [
        'https://google.com/',
    ]

    def __init__(self, login=None, password=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.login = login
        self.password = password

    def start_requests(self):
        yield scrapy.Request(
            url='https://github.com/login',
            method='GET',
            encoding='utf-8',
            callback=self.log_in,
        )

    def log_in(self, response):
        if (self.login and self.password) is not None:
            return scrapy.FormRequest.from_response(
                response,
                formdata={'login': self.login, 'password': self.password},
                callback=self.after_login,
            )

    def after_login(self, response):
        if auth_failed(response):
            self.logger.error('Not logged in!')
        else:
            self.logger.info('Successfully logged in!')
        for url in self.start_urls:
            yield scrapy.Request(url, dont_filter=True)

    def parse(self, response):
        for _ in range(20):
            self.logger.info('In PARSE method!')
