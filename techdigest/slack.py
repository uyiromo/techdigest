from logging import Logger, getLogger

from .common import ArticleDigest

import httpx

logger: Logger = getLogger('techdigest')

client: httpx.Client | None = None
channel_id: str | None = None


def init_slack(config: dict) -> None:
    global client, channel_id

    if 'slack' in config:
        headers = {'Authorization': f'Bearer {config["slack"]["bot_token"]}'}
        client = httpx.Client(headers=headers, timeout=10)
        channel_id = config['slack']['channel_id']
    else:
        pass

    logger.info('Slack initialized')
    return


def send_slack(title: str, url: str, dgst: ArticleDigest) -> None:
    if not (client and channel_id):
        return

    msg: str = '\n'.join(
        [
            f'*{title}*',
            f'> {dgst.summary}',
            f'🎯 {dgst.target}',
            *[f'🛠️ `{_s}`' for _s in dgst.stacks],
            f'<{url}>',
        ]
    )
    response = client.post(
        'https://slack.com/api/chat.postMessage',
        json={'channel': channel_id, 'text': msg},
    )
    response.raise_for_status()
