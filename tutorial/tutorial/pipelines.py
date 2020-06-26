# -*- coding: utf-8 -*-
import json
import os

import openpyxl
from scrapy.exceptions import DropItem

from .items import GitHubLinksItem, GitHubRepoInfoItem
from .settings import settings, BASE_DIR

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


class ExcelPipeline:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.print_list = bool(json.loads(str(settings.print_list).lower()))
        self.print_item = bool(json.loads(str(settings.print_item).lower()))
        self.wb_path = os.path.join(BASE_DIR, settings.output_excel_file) if settings.output_excel_file else None
        if self.wb_path:
            wb = openpyxl.Workbook()
            wb.save(self.wb_path)
            wb.close()
            self._fill_excel_with_data()

    def process_item(self, item, spider):
        domain = 'https://github.com'
        if isinstance(item, GitHubLinksItem):
            if self.print_list:
                with open(f'./output/links-page{item.get("page")}.json', 'w') as links_json:
                    output_data = [domain + obj for obj in item.get('data')]
                    links_json.write(json.dumps(dict(data=output_data)))
            raise DropItem

        elif isinstance(item, GitHubRepoInfoItem):
            item['repo'] = domain + '/' + item.get('repo')

            if self.print_item:
                with open(f'./output/page{item.get("page")}link{item.get("link")}.json', 'w') as json_doc:
                    json_doc.write(json.dumps(dict(item)))

            if self.wb_path:
                self._fill_excel_with_data(item)

            return item

        raise DropItem

    def _fill_excel_with_data(self, data=None):
        if data is None:
            data = {'repo': 'link', 'commit': 'commit'}
        wb = openpyxl.load_workbook(filename=self.wb_path)
        ws = wb.active
        ws.append([data.get('repo'), data.get('commit')])
        wb.save(self.wb_path)
        wb.close()
