from __future__ import annotations

from logging import Logger, getLogger
from pathlib import Path
from time import sleep
from typing import cast

from .common import ArticleDigest

import html2text
import outlines
from openai import OpenAI
from readability import Document

logger: Logger = getLogger('techdigest')

PROMPT = """\
あなたは技術ブログの記事を読み、指示に従って内容を要約するエージェントです。

以下の記事を解析し、JSON で出力してください。

# ルール
1. 全ての応答を日本語で回答すること。技術の固有用語は英語で構わない。
2. 要約は 200 文字以内で、記事の内容全体を過不足なく含むこと。HTML タグや Markdown の記法は除去すること。
3. 技術スタックは単語で表すこと (例: SIMD, GPU, LLM)。
4. 対象読者は技術スタックと関連性のある読者層を示すこと (例: 「GPU 最適化に興味のあるエンジニア」)。
5. 技術スタックは記事で着目している技術の top 3 を示すこと。

# 出力フォーマット
{
  "summary": "記事の要約",
  "target": "対象読者",
  "stacks": ["技術1", "技術2", "技術3"]
}

# 記事本文
"""

client: OpenAI | None = None
model: str | None = None


def init_digest(config: dict) -> None:
    global client, model

    client = OpenAI(
        base_url=config['openai']['base_url'],
        api_key=config['openai']['api_key'],
    )
    model = config['openai']['model']

    return


def _extract_article(html: str) -> str:
    doc = Document(html)
    summary = doc.summary()
    h = html2text.HTML2Text()
    h.ignore_links = True
    h.ignore_images = True
    h.ignore_emphasis = True
    h.body_width = 0
    return h.handle(summary)


def digest(
    html_path: Path,
) -> ArticleDigest:
    if not (client and model):
        raise RuntimeError(f'LLM is not initialized: client="{client}", model="{model}"')

    # HTML をそのまま渡すと消費トークンが激しいので圧縮
    # e.g) 550,000 トークン => 1,500
    html: str = html_path.read_text(encoding='utf-8')
    markdown: str = _extract_article(html)

    outlines_model = outlines.from_openai(client, model_name=model)
    generator = outlines.Generator(outlines_model, output_type=ArticleDigest)

    for attempt in range(10):
        try:
            result = cast(str, generator(PROMPT + markdown))
            return ArticleDigest.model_validate_json(result)
        except Exception as e:
            logger.warning(f'  Attempt {attempt + 1} failed: {e}')
            if attempt < 9:
                sleep(5)

    raise RuntimeError(f'Failed to digest after 10 attempts: {html_path}')
