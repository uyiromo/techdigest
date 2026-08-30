# techdigest

技術ブログの新着記事を収集し、LLM で要約したうえで Slack / Discord に投稿するツール

## セットアップ

### 前提

```sh
./init.sh
cp techdigest.toml.example techdigest.toml
```

### techdigest.toml

```toml
[openai]
base_url = ""
api_key = ""
model = ""

# [slack]
# app_token = "xapp-*****"
# bot_token = "xoxb-*****"
# channel_id = "C0*****"

# [discord]
# token = "MTU*****"
# channel_id = ""
```

## Slack 連携

`[slack]` セクションを記述すると Slack 投稿が有効になります（セクション削除で無効）。

| 項目         | 説明                                              |
| ------------ | ------------------------------------------------- |
| `app_token`  | Socket Mode 用アプリレベルトークン (`xapp-...`)   |
| `bot_token`  | ボットトークン (`xoxb-...`)                       |
| `channel_id` | 投稿先チャネル ID (`C...`)                        |

`chat.postMessage` API を `Authorization: Bearer <bot_token>` で呼び出します。
投稿フォーマットは `techdigest/slack.py` で定義しています（タイトル / 要約 / 対象読者 / 技術スタック / 記事URL）。

## Discord 連携

`[discord]` セクションを記述すると Discord 投稿が有効になります（セクション削除で無効）。

| 項目         | 説明                                  |
| ------------ | ------------------------------------- |
| `token`      | ボットトークン                        |
| `channel_id` | 投稿先チャネル ID                     |

`/channels/<channel_id>/messages` を `Authorization: Bot <token>` で呼び出します。
投稿フォーマットは Slack と同様です（`techdigest/discord.py` 参照）。
