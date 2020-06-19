import scrapy


class GithubSpider(scrapy.Spider):
    name = 'github'

    start_urls = [
        'https://github.com/search?p=1&q=python&type=Repositories'
    ]

    limit = 11

    def parse(self, response):
        repos_urls = response.\
                css('ul.repo-list').css('li.public').css('div.f4.text-normal')\
                .css('a').xpath('@href').getall()
        next_page_url = response.css('a.next_page').xpath('@href').get()
        [next_page_number] = [int(item.split('=')[1])
                              for item in next_page_url.split('?')[1].split('&')
                              if item.startswith('p=')]

        if next_page_number <= self.limit:
            yield from response.follow_all(repos_urls, self.parse_repos, cb_kwargs=dict(page=next_page_number-1))
            yield response.follow(next_page_url, callback=self.parse)

    def parse_repos(self, response, page):
        repos_name = response.url.split('github.com/')[1]
        repos_last_commit = response.css('a.commit-tease-sha.mr-1::text').get().strip()
        yield {
            'page': page,
            'repo': repos_name,
            'last_commit': repos_last_commit,
        }
