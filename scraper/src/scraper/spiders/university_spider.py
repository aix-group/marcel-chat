import json
from typing import Any
from urllib.parse import urljoin, urlparse, urlunparse

import scrapy
from bs4 import BeautifulSoup, Tag
from html2text import HTML2Text
from scrapy import Request
from scrapy.linkextractors import LinkExtractor  # type: ignore


def og_properties(soup):
    props = {}
    for meta_tag in soup.find_all(
        "meta", property=lambda prop: prop and prop.startswith("og:")
    ):
        property_name = meta_tag.get("property")
        content = meta_tag.get("content")
        props[property_name] = content
    return props


def find_title(soup):
    if isinstance(soup, str):
        soup = BeautifulSoup(soup, features="lxml")

    if soup.title:
        return soup.title.text
    return None


def find_favicon(soup):
    if isinstance(soup, str):
        soup = BeautifulSoup(soup, features="lxml")
    for rel in ("icon", "shortcut icon"):
        link_tag = soup.find("link", attrs={"rel": rel})
        if isinstance(link_tag, Tag) and link_tag.get(key="href"):
            return link_tag["href"]
    return None


def find_content(soup, domain):
    if isinstance(soup, str):
        soup = BeautifulSoup(soup, features="lxml")

    generic_filters = [
        {"id": "content"},
        {"name": "main"},
        {"name": "body"},
    ]
    for tag_filter in generic_filters:
        name = tag_filter.pop("name", None)
        tag = soup.find(name=name, attrs=tag_filter)
        if tag:
            return tag

    return None


def get_domain(url):
    """
    Extracts domain (netloc) from a full URL without www (if present)
    Example: 'http://www.foo.com/bar/example' --> 'foo.com'
    """
    domain = urlparse(url).netloc
    domain = domain.removeprefix("www.")
    return domain


def get_domain_with_schema(url):
    """
    Extracts the base domain (scheme + netloc) from a full URL.
    Example: 'http://foo.com/bar/example' --> 'http://foo.com'
    """
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def replace_domain(url, domain_map):
    parsed_url = urlparse(url)
    canonical_domain = domain_map.get(parsed_url.netloc, parsed_url.netloc)
    new_url = urlunparse(parsed_url._replace(netloc=canonical_domain))
    return str(new_url)


def ensure_scheme(url, default_scheme="http"):
    """Add default scheme if missing."""
    parsed = urlparse(url)
    if not parsed.scheme:
        return f"{default_scheme}://{url}"
    return url


def resolve_link(base_url, link):
    """Resolve link to an absolute url. If the link is already absolute return unchanged."""
    base_url = ensure_scheme(base_url)
    parsed = urlparse(link)
    if not parsed.scheme and not parsed.netloc:
        return urljoin(base_url, link)
    return link


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

    def __parse_kwargs(self, **kwargs):
        for key in ["start_urls", "domain_map", "deny"]:
            if key not in kwargs:
                continue
            val = kwargs.get(key)
            if isinstance(val, str):
                try:
                    setattr(self, key, json.loads(val))
                except json.JSONDecodeError:
                    raise ValueError(f"Invalid JSON format in argument '{key}': {val}")

    def __init__(self, name: str | None = None, **kwargs: Any):
        super().__init__(name, **kwargs)
        self.__parse_kwargs(**kwargs)

        self.link_extractor = LinkExtractor(
            allow=[
                # only allow urls which are sub-pages of the start urls
                f"^{url.replace('https://', 'https?://')}"
                for url in self.start_urls
            ],
            deny=self.deny,
        )
        html_handler = HTML2Text()
        html_handler.inline_links = False
        html_handler.wrap_links = False
        html_handler.body_width = 0
        self.html_handler = html_handler

    async def start(self):
        # override this to make sure that start_urls are part of the duplicate filter:
        # https://hexfox.com/p/how-to-filter-out-duplicate-urls-from-scrapys-start-urls/
        for url in self.start_urls:
            url = replace_domain(url, self.domain_map)
            yield Request(url)

    def parse(self, response, **kwargs):
        self.logger.info(f"Scraped {response.url}")
        cache_control = response.headers.get("Cache-Control", b"").decode("utf-8")
        if "private" in cache_control.lower():
            self.logger.warning(f"Skipping internal page: {response.url}")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        og_props = og_properties(soup)
        content = find_content(soup, get_domain(response.url))
        content = self.html_handler.handle(str(content))
        icon = find_favicon(soup)
        if icon:
            base_url = get_domain_with_schema(response.url)
            icon = resolve_link(base_url, icon)
        title = find_title(soup)

        yield {
            "url": response.url,
            "status": response.status,
            "html": response.text,
            "content": content,
            "og": og_props,
            "title": title,
            "favicon": icon,
        }

        for link in self.link_extractor.extract_links(response):
            url = replace_domain(link.url, self.domain_map)
            yield Request(url, callback=self.parse)
