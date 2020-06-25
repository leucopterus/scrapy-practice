# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class GitHubRepoInfoItem(scrapy.Item):
    page = scrapy.item.Field(serializer=int)
    link = scrapy.item.Field(serializer=int)
    repo = scrapy.item.Field(serializer=str)
    commit = scrapy.item.Field(serializer=str)
