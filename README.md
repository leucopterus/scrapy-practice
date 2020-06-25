# scrapy-practice
Main purpose of this practice is to practise with python scrapy framework by scrapping results of a custom search in **github** and present repositories with their last commits 

## HOW-TO run code
* If you want to use `config.ini` file just add in into repos working dir and in your console write `crawl github -a config=true`
* Also it is possible to use other parameters of the scrapy framework

## config.ini configuration
* `config.ini` can look like:
```
[Credentials]
LOGIN = yourlogin
PASSWORD = yourpassword

[QueryKeys]
QUERY = q
PAGE = p

[Parameters]
DOMAIN = https://github.com
START_PAGE_NUMBER = 1
NUMBER_OF_PAGES = 10
SHOW_LINKS_PER_SEARCH_PAGE = true
SHOW_REPOSITORY_INFO_SEPARATELY = true
QUERY = python django

[Cookies]
COOKIES_INPUT = cookie.txt
COOKIES_OUTPUT = cookie.txt

[Output]
EXCEL = output.xlsx
```
