import copy

import scrapy


class GithubSpider(scrapy.Spider):
    name = 'github'

    start_urls = [
        'https://github.com/search?p=1&q=python&type=Repositories'
    ]

    def __init__(self, limit=2, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.limit = limit + 1
        self.next_page_number = None
        self.repos_urls = []
        self.repos_data_mask = {'link number': None, 'repo': None, 'last commit': None}

    def parse(self, response):
        next_page_url = response.css('a.next_page').xpath('@href').get()
        [self.next_page_number] = [int(item.split('=')[1])
                                   for item in next_page_url.split('?')[1].split('&')
                                   if item.startswith('p=')]

        if self.next_page_number <= self.limit:
            repos_urls = response. \
                css('ul.repo-list li.public.source div.mt-n1 div.f4.text-normal a').xpath('@href').getall()
            for repo_url in repos_urls:
                self.repos_urls.append(''.join(['https://github.com/', repo_url]))

            yield response.follow(next_page_url, callback=self.parse)
        else:
            for link_number, repo_url in enumerate(self.repos_urls, start=1):
                yield response.follow(repo_url, callback=self.parse_repos, cb_kwargs=dict(link_number=link_number))

    def parse_repos(self, response, link_number):
        if 'Cannot retrieve the latest commit at this time' not in str(response.body):
            repos_data = copy.copy(self.repos_data_mask)

            repos_last_commit = response.css('a.commit-tease-sha.mr-1::text').get()

            repos_data['link number'] = link_number
            repos_data['repo'] = response.url.split('github.com/')[1]
            repos_data['last commit'] = repos_last_commit.strip() if isinstance(repos_last_commit, str) else None
            yield repos_data
        else:
            yield response.follow(response.url, self.parse_repos, cb_kwargs=dict(link_number=link_number))
