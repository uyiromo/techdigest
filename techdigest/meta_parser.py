#!/usr/bin/env python3
from __future__ import annotations

import json
from logging import Logger, getLogger

from .common import Metadata

from playwright.sync_api import Locator, Page

logger: Logger = getLogger('techdigest')


def _dehtml(s: str) -> str:
    return s.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')


def _get_content(page: Page, prop: str) -> str:
    return _dehtml(
        page.locator(
            f'meta[property="{prop}"]',
        ).first.get_attribute('content')
        or ''
    )


def _get_content2(page: Page, name: str) -> str:
    return _dehtml(
        page.locator(
            f'meta[name="{name}"]',
        ).first.get_attribute('content')
        or ''
    )


def meta_parse(page: Page) -> Metadata:
    meta: Metadata | None = None

    for f in [_meta_parse_og, _meta_parse_og2, _meta_parse_meta, _meta_parse_ldjson]:
        try:
            meta = f(page)
            break
        except Exception:
            continue

    if (meta is None) or (not meta.title):
        raise RuntimeError(meta)
    else:
        pass

    return meta


def _meta_parse_og(page: Page) -> Metadata:
    return Metadata(
        title=page.title(),
        description=_get_content(page, 'og:description'),
        image=_get_content(page, 'og:image'),
    )


def _meta_parse_og2(page: Page) -> Metadata:
    return Metadata(
        title=page.title(),
        description='',
        image=_get_content(page, 'og:image'),
    )

def _meta_parse_meta(page: Page) -> Metadata:
    return Metadata(
        title=page.title(),
        description=_get_content2(page, 'description'),
        image='',
    )





def _meta_parse_twitter(page: Page) -> Metadata:
    """Parse the given _page_, and Return Metadata

    Args:
        page (Page): playwright.sync_api.Page instance

    Returns:
        Metadata: A Metadata object containing the parsed information
    """
    return Metadata(
        title=page.title(),
        description=_get_content(page, 'twitter:description'),
        image=_get_content2(page, 'twitter:image:src'),
    )


def _meta_parse_ldjson(page: Page) -> Metadata:
    loc: Locator = page.locator('script[type="application/ld+json"]')
    for i in range(loc.count()):
        ldjson: dict = json.loads(loc.nth(i).text_content())  # pyright: ignore[reportArgumentType]
        if ldjson['@type'] == 'Article':
            return Metadata(
                title=ldjson['headline'],
                description=ldjson['description'],
                image=ldjson['image'],
            )
        else:
            pass

    raise RuntimeError('No Article found in ld+json')
