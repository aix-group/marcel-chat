# scraper

## Install

```sh
pdm install
```

## Running scraper

There are two ways to specify parameters. 
\
The first is to define them directly in the [UniversitySpider](./src/scraper/spiders/university_spider.py):
```python
class UniversitySpider(scrapy.Spider):
    name = "university"
    start_urls = [
        "https://www.uni-marburg.de/en/fb12/studying/degree-programs/m-sc-data-science"  # Example start URL
    ]
    # Define equivalent domains. Both variants need to be in start_urls (to allow prefixes in link_extractor).
    # Before scraping they are normalized so that potential duplicates are filtered.
    domain_map = {"studierendenwerk-marburg.de": "studentenwerk-marburg.de"}

    # Pages that should not be scraped, e.g. because they are internal or not relevant.
    deny = [
        r"uni-marburg.de/en/studying/after-your-first-degree/masters-programs/application-for-a-masters-programme/eap/(?!eap-data-science$)"
    ]

```
Then run the crawler:
```sh
# HTTP requests are cached (.scrapy/httpcache/university)
# Crawler state is persisted to JOBDIR -- can resume based on this
# Crawled pages are appended to data.jsonl
pdm run scrapy crawl university \
    -o ../data/crawls/knowledgebase.jsonl \
    -s JOBDIR=../data/crawls/queue/
```
Second method: pass parameters through Scrapy’s -a option.
```sh
pdm run scrapy crawl university \
    -a start_urls='["https://www.uni-marburg.de/en/fb12/studying/degree-programs/m-sc-data-science"]' \
    -a domain_map='{"studierendenwerk-marburg.de":"studentenwerk-marburg.de"}' \
    -a deny='["uni-marburg\\.de/en/studying/after-your-first-degree/masters-programs/application-for-a-masters-programme/eap/(?!eap-data-science$)"]' \
    -o ../data/crawls/knowledgebase.jsonl \
    -s JOBDIR=../data/crawls/queue/
```
## Terminating running scraping job

```sh
kill -s sigint $(pgrep -f "pdm run scrapy")
```


## Useful debugging commands

```sh
# Fetch a single page
pdm run scrapy fetch https://www.uni-marburg.de/en/studying/degree-programs/sciences/datasciencems > examples/datascience.html

# Run parser for one page (observe scraped items and followup requests)
pdm run scrapy parse --spider=university https://www.uni-marburg.de/en/studying/life-at-umr/
```

## Development

```sh
pdm run lint
pdm run format
```

## Tests
```sh
pdm run test 
```
