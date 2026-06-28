#!/usr/bin/env python3

import json
import re
import tomllib
from logging import INFO, Formatter, Logger, StreamHandler, getLogger
from pathlib import Path
from time import sleep
from typing import List

from techdigest.common import Article, ArticleDigest, SiteCfg
from techdigest.digester import digest, init_digest
from techdigest.discord import init_discord, send_discord
from techdigest.meta_parser import Metadata, meta_parse
from techdigest.slack import init_slack, send_slack
from techdigest.url_parser import url_parse

from playwright.sync_api import Browser, Page, sync_playwright

# stderr
LOGFMT: Formatter = Formatter('%(asctime)s | %(message)s')
logger: Logger = getLogger('techdigest')
logger.setLevel(INFO)

sh: StreamHandler = StreamHandler()
sh.setLevel(INFO)
sh.setFormatter(LOGFMT)
logger.addHandler(sh)

# config
CONFIG_PATH: Path = Path(__file__).parent / 'techdigest.toml'
config: dict = tomllib.loads(CONFIG_PATH.read_text())

init_digest(config)
init_discord(config)
init_slack(config)


WORKDIR: Path = Path(__file__).parent
HTMLDIR: Path = WORKDIR / 'html'


def linux_safe(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|\x00-\x1f]', '_', name).strip('. ')[:100]


def download(browser: Browser, cfg: SiteCfg) -> None:
    # Get article URLs
    urls: List[str] = url_parse(
        browser,
        cfg['url'],
        cfg['url_parser'],
    )
    logger.info(f'  Found {len(urls)} urls')

    # Download HTML
    site_dir: Path = HTMLDIR / cfg['name']
    site_dir.mkdir(exist_ok=True, parents=True)

    # already downloaded
    articles_json: Path = site_dir / '_articles.json'
    if not articles_json.exists():
        articles_json.write_text('[]')
    articles: List[Article] = [Article(**a) for a in json.loads(articles_json.read_text())]
    article_urls: set[str | None] = set(a.link for a in articles)

    for url in urls:
        logger.info(f'  Downloading article: {url}')
        if url in article_urls:
            continue

        page: Page = browser.new_page()
        page.goto(url)

        m: Metadata = meta_parse(page, cfg['meta_parser'])
        a: Article = Article(link=url, **m.__dict__)

        html: Path = site_dir / f'{linux_safe(a.title)}.html'
        html.write_text(page.content(), encoding='utf-8')

        dgst: ArticleDigest = digest(html)
        send_discord(a.title, a.link, dgst)
        send_slack(a.title, a.link, dgst)

        articles.append(a)
        articles_json.write_text(json.dumps([a.__dict__ for a in articles], ensure_ascii=False, skipkeys=False))

        sleep(5)  # polite crawling


def main():
    SITES_JSON: Path = Path(__file__).parent / 'sites.json'
    sites: list[dict] = json.loads(SITES_JSON.read_text())
    logger.info(f"Loaded '{len(sites)}' sites")

    with sync_playwright() as p:
        browser: Browser = p.chromium.launch(headless=True)

        for i, site_cfg in enumerate(sites):
            logger.info(f'[{i + 1}/{len(sites)}]: {site_cfg["name"]}')
            download(browser, SiteCfg(**site_cfg))


if __name__ == '__main__':
    main()
