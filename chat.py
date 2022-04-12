import os
import json
from urllib import request
import random
import string
import time

import aiohttp

from nonebot import on_message
from nonebot.rule import to_me
from nonebot.typing import T_State
from nonebot.adapters import Bot, Event
from nonebot.log import logger
from nonebot.adapters.onebot.v11 import MessageSegment

chat = on_message(rule=to_me(), priority=99, block=True)


async def ownthink(msg):
    async with aiohttp.ClientSession(trust_env=True) as aio_session:
        url = 'https://api.ownthink.com/bot'
        params = {
            'appid':'',
            'userid': '',
            'spoken': msg,
        }
        async with aio_session.get(url, params=params) as res:
            resp = json.loads(await res.text())
            return resp['data']['info']['text']


@chat.handle()
async def chat_handle(bot: Bot, event: Event, state: T_State):
    if time.time() - event.time >= 180:
        return

    images = [seg.data.get('url') for seg in event.message if seg.type == "image"]
    if not images:
        msg = str(event.get_message()).strip()
        if msg:
            if len(msg) == 1:
                await chat.send(MessageSegment.text(msg))
            else:
                resp = await ownthink(msg)
                await chat.send(MessageSegment.text(resp))
    else:
        save_path = '/mnt/share/receive_img/' + event.get_user_id()
        if not os.path.exists(save_path):
            os.mkdir(save_path)
        async with aiohttp.ClientSession(trust_env=True) as aio_session:
            for url in images:
                async with aio_session.get(url) as res:
                    img = await res.content.read()
                    if str(img[:3]).lower() == "b'gif'":
                        file_type = '.gif'
                    else:
                        file_type = '.png'
                    file_name = ''.join(random.sample(string.ascii_lowercase +
                                                      string.ascii_uppercase, 5)) + file_type
                    with open(os.path.join(save_path, file_name), 'wb')as f:
                        f.write(img)
            img_num = len(os.listdir(save_path))
            await chat.send(MessageSegment.text(f"图片接收成功，当前共{img_num}张图片，发送清空可删除全部"))
