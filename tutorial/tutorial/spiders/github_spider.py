import copy
import time

import scrapy


class GithubSpider(scrapy.Spider):
    name = 'github'

    start_urls = [
        'https://github.com/search?p=1&q=python&type=Repositories'
    ]

    def __init__(self, start=1, limit=10, *args, **kwargs):
        super().__init__(*args, **kwargs)
        start, limit = int(start), int(limit)
        self.start = start
        self.limit = limit + start - 1
        self.next_page_number = None
        self.repos_data_mask = {
            'page': None,
            'link': None,
            'repo': None,
            'commit': None
        }
        if start != 1:
            url = self.start_urls[0]
            current_page_in_url_index = url.find('p=')
            url = url[:current_page_in_url_index+2] + str(start) + url[url.find('&', current_page_in_url_index):]
            self.start_urls[0] = url

    def parse(self, response):
        self._controller(10)
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
        for link_number, repo_url in enumerate(repos_urls, start=1):
            yield response.follow(repo_url,
                                  callback=self.parse_repos,
                                  cb_kwargs=dict(
                                      page_number=self.next_page_number-1,
                                      link_number=link_number,
                                  ))

        if self.next_page_number <= self.limit:
            yield response.follow(next_page_url, callback=self.parse)

    def parse_repos(self, response, page_number, link_number):
        if 'Cannot retrieve the latest commit at this time' not in response.text:
            repos_data = copy.copy(self.repos_data_mask)

            repos_last_commit = response.css('a.commit-tease-sha.mr-1::text').get()

            repos_data['page'] = page_number
            repos_data['link'] = link_number
            repos_data['repo'] = response.url.split('github.com/')[1]
            repos_data['commit'] = repos_last_commit.strip() if isinstance(repos_last_commit, str) else None
            return repos_data
        else:
            page_with_commits_url = response.css('ul.numbers-summary li.commits a').xpath('@href').get()
            self._controller(10)
            return response.follow(page_with_commits_url,
                                   callback=self.parse_commits,
                                   cb_kwargs=dict(
                                       page_number=page_number,
                                       link_number=link_number,
                                   ))

    def parse_commits(self, response, page_number, link_number):
        repos_last_commit = response.css('ol.commit-group.Box li.commit div.commit-links-group a.sha::text').get()
        repos_data = copy.copy(self.repos_data_mask)
        repos_data['page'] = page_number
        repos_data['link'] = link_number
        repos_data['repo'] = response.url.split('github.com/')[1]
        repos_data['commit'] = repos_last_commit.strip() if isinstance(repos_last_commit, str) else None
        return repos_data

    def _controller(self, seconds=30):
        self.crawler.engine.pause()
        time.sleep(seconds)
        self.crawler.engine.unpause()
