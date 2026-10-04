from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated, List, TypedDict

from pydantic import BaseModel, ConfigDict, Field


class SiteCfg(TypedDict):
    name: str
    url: str
    url_parser: URLParser
    meta_parser: MetaParser


#
# URL
#
class URLParserType(StrEnum):
    Feed = 'feed'
    Selector = 'selector'


class URLParser(TypedDict):
    type: URLParserType
    args: dict


#
# Metadata
#
class MetaParserType(StrEnum):
    General = 'general'
    General2 = 'general2'
    LdJson = 'ld+json'
    Github = 'github'


class MetaParser(TypedDict):
    type: MetaParserType
    args: dict


@dataclass
class Metadata:
    title: str
    description: str
    image: str


#
# Digest
#
class ArticleDigest(BaseModel):
    model_config = ConfigDict(extra='forbid')

    summary: str = Field(description='記事内容の要約', max_length=200)
    target: str = Field(description='記事の想定読者')

    stacks: Annotated[
        List[str],
        Field(
            description='記事が対象としている技術スタックの top 3。全て技術名の単語。例: SIMD, LLM, GPU, cuDNN',
            min_length=1,
            max_length=3,
        ),
    ]


#
# I/F
#
@dataclass
class Article:
    title: str
    link: str
    description: str | None
    image: str | None
    summary: str
    target: str
    stacks: list[str]
