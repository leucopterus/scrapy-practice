import scrapy


class GithubSpider(scrapy.Spider):
    name = 'github'

    start_urls = [
        'https://github.com/search?p=1&q=python&type=Repositories'
    ]

    limit = 11

    def parse(self, response):
        next_page_url = response.css('a.next_page').xpath('@href').get()
        [next_page_number] = [int(item.split('=')[1])
                              for item in next_page_url.split('?')[1].split('&')
                              if item.startswith('p=')]

        if next_page_number <= self.limit:
            repos_urls = response. \
                css('ul.repo-list li.public.source div.mt-n1 div.f4.text-normal a').xpath('@href').getall()
            for repo_url in repos_urls:
                # yield {
                #     f'{next_page_number-1}': f'{repo_url}'
                # }
                yield response.follow(repo_url, self.parse_repos, cb_kwargs=dict(page=next_page_number - 1))

            yield response.follow(next_page_url, callback=self.parse)
            # for repo_url in repos_urls:
            #     yield response.follow(repo_url, self.parse_repos, cb_kwargs=dict(page=next_page_number-1))
            #
            # yield response.follow(next_page_url, callback=self.parse)

    def parse_repos(self, response, page):
        if 'Cannot retrieve the latest commit at this time' not in str(response.body):
            repos_name = response.url.split('github.com/')[1]
            repos_last_commit = response.css('a.commit-tease-sha.mr-1::text').get()
            repos_last_commit = repos_last_commit.strip() if isinstance(repos_last_commit, str) else None
            yield {
                'page': page,
                'repo': repos_name,
                'last_commit': repos_last_commit,
            }
        else:
            yield response.follow(response.url, self.parse_repos, cb_kwargs=dict(page=page))
