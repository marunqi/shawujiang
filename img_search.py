import json

import aiohttp

from nonebot.typing import T_State
from nonebot.adapters import Bot, Event
from nonebot import on_keyword
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot import logger


img_search = on_keyword("搜图", priority=6, block=True)


@img_search.handle()
async def img_search_handle(bot: Bot, event: Event, state: T_State):
    Text = ''.join([seg.data.get('text') for seg in event.message if seg.type == "text"]).strip()
    img_url = [seg.data.get('url') for seg in event.message if seg.type == "image"]
    if not img_url and event.dict().get('reply') and event.dict().get('reply').get('message'):
        reply_message = event.dict()['reply']['message']
        img_url = [seg.data.get('url') for seg in reply_message if seg.type == "image"]
    if len(img_url) != 1 or Text.replace('\n', '') != "搜图":
        return

    img_url = img_url[0]
    params = {
        'api_key': '',
        'numres': 3,
        'url': img_url,
        'db': 999,
        'output_type': 2,
    }
    async with aiohttp.ClientSession(trust_env=True) as aio_session:
        async with aio_session.get('https://saucenao.com/search.php', params=params) as res:
            if not res.status == 200:
                await img_search.send(MessageSegment.text("图片搜索失败！"))
            sauces = json.loads(await res.text())
            rst = []
            for sauce in sauces['results']:
                if 'ext_urls' in sauce['data'].keys():
                    url = sauce['data']['ext_urls'][0].replace("\\", "").strip()
                    similarity = sauce['header']['similarity']
                    pixiv_id = sauce['data'].get('pixiv_id')
                    member_name = sauce['data'].get('member_name')
                    if float(similarity) > 50:
                        dec = f"{url}     相似度:{similarity}%"
                        if pixiv_id and member_name:
                            dec += f"    画师名:{member_name}"
                        rst.append(dec)
            if len(rst) > 0:
                await img_search.send(MessageSegment.text("\n".join(rst)))
            else:
                await img_search.send(MessageSegment.text("图片搜索失败！"))
