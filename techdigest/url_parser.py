#!/usr/bin/env python3


from logging import Logger, getLogger

from .common import URLParser, URLParserType

import feedparser
from playwright.sync_api import Browser, Locator, Page

logger: Logger = getLogger('techdigest')


def url_parse(browser: Browser, url: str, parser: URLParser) -> list[str]:  # noqa: A002
    """Return page URLs"""
    urls: list[str]
    match parser['type']:
        case URLParserType.Feed:
            urls = _url_parse_feed(browser, url)
        case URLParserType.Selector:
            urls = _url_parse_selector(browser, url, parser['args'])
        case _:
            raise ValueError(f'{parser["type"]} is UNKNOWN')

    if len(urls) == 0:
        raise RuntimeError(f'{url} has NO pages!')
    else:
        pass

    return urls


def _url_parse_feed(browser: Browser, url: str) -> list[str]:
    feed: feedparser.FeedParserDict = feedparser.parse(url)
    page_urls: list[str] = [entry.get('link') for entry in feed.entries if entry.get('link')]  # pyright: ignore[reportAssignmentType]

    return page_urls


def _url_parse_selector(browser: Browser, url: str, args: dict) -> list[str]:
    selector: str = args['selector']
    attribute: str = args['attribute']
    exclude: set[str] = set(args['exclude'])
    base: str | None = args.get('base', None)

    page: Page = browser.new_page()
    page.goto(url)
    page.goto(url)

    loc: Locator = page.locator(selector)
    page_urls: list[str] = []

    for ll in loc.all():
        href: str | None = ll.get_attribute(attribute)
        if href and href not in exclude:
            page_urls.append(href)
        else:
            pass

    if base:
        page_urls = [base + href for href in page_urls]
    else:
        pass

    return page_urls
