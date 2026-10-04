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
CACHEDIR: Path = WORKDIR / 'cache'

_exclude = config.get('exclude', {})
EXCLUDE_TITLE: list[str] = _exclude.get('title', [])
EXCLUDE_LINK: list[str] = _exclude.get('link', [])
EXCLUDE_DESCRIPTION: list[str] = _exclude.get('description', [])


def is_excluded(title: str, link: str, description: str | None) -> bool:
    """部分一致したなら True"""
    def _submatch(s: str | None, filter: list[str]) -> bool:  # noqa: A002
        if not s:
            return False
        else:
            return any(s in f for f in filter)

    return _submatch(title, EXCLUDE_TITLE) or _submatch(link, EXCLUDE_LINK) or _submatch(description, EXCLUDE_DESCRIPTION)


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
    site_dir: Path = CACHEDIR / cfg['name']
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

        m: Metadata = meta_parse(page)  # , cfg['meta_parser'])

        if is_excluded(m.title, url, m.description):
            page.close()
            continue

        html: Path = site_dir / f'{linux_safe(m.title)}.html'
        html.write_text(page.content(), encoding='utf-8')

        dgst: ArticleDigest | None = digest(html)
        if dgst is None:
            logger.warning(f'  Failed to digest article: {url}')
            continue

        send_discord(m.title, url, dgst)
        send_slack(m.title, url, dgst)

        articles.append(
            Article(
                title=m.title,
                link=url,
                description=m.description,
                image=m.image,
                summary=dgst.summary,
                target=dgst.target,
                stacks=dgst.stacks,
            )
        )
        articles_json.write_text(
            json.dumps([a.__dict__ for a in articles], ensure_ascii=False, skipkeys=False, indent=4)
        )

        page.close()
        sleep(5)  # polite crawling


def main():
    SITES_JSON: Path = Path(__file__).parent / 'sites.json'
    sites: list[dict] = json.loads(SITES_JSON.read_text())
    logger.info(f"Loaded '{len(sites)}' sites")

    with sync_playwright() as p:
        browser: Browser = p.chromium.launch(headless=True)

        for i, site_cfg in enumerate(sites):
            for n in range(100):
                try:
                    logger.info(f'[{i + 1}/{len(sites)}]: {site_cfg["name"]}')
                    download(browser, SiteCfg(**site_cfg))
                    break
                except Exception as e:
                    if n == 99:
                        raise e


if __name__ == '__main__':
    main()
