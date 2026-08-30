from logging import Logger, getLogger

from .common import ArticleDigest

import httpx

logger: Logger = getLogger('techdigest')

client: httpx.Client | None = None
channel_id: str | None = None


def init_discord(config: dict) -> None:
    global client, channel_id

    if 'discord' in config:
        headers = {'Authorization': f'Bot {config["discord"]["token"]}'}
        client = httpx.Client(headers=headers, timeout=10)
        channel_id = config['discord']['channel_id']
    else:
        pass

    logger.info('Discord initialized')
    return


def send_discord(title: str, url: str, dgst: ArticleDigest) -> None:
    if not (client and channel_id):
        return

    msg: str = '\n'.join(
        [
            f'**{title}**',
            f'> {dgst.summary}',
            f'🎯 {dgst.target}',
            *[f'🛠️ `{_s}`' for _s in dgst.stacks],
            f'<{url}>',
        ]
    )
    response = client.post(
        f'https://discord.com/api/v10/channels/{channel_id}/messages',
        json={'content': msg},
    )
    response.raise_for_status()
