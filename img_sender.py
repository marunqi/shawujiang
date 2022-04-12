import os
import random
import string
import shutil
import multiprocessing
from datetime import datetime
import time
import traceback
import copy

import json
from PIL import Image as pil_img
from aiohttp import TCPConnector, ClientSession

from nonebot import on_startswith, on_startswith
from nonebot.typing import T_State
from nonebot.adapters import Bot, Event
# from nonebot.adapters.cqhttp.event import MessageEvent, GroupMessageEvent
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.log import logger
from nonebot.rule import to_me


img_3 = []
img_3R = []
img_gif = []
voices = []

def list_all_file(root, save_type='static'):
    rst = []
    f_ls = []
    for dirpath, dirnames, filenames in os.walk(root):
        for file_name in filenames:
            file_type = file_name.split('.')[-1].lower()
            if file_type not in f_ls:
                f_ls.append(file_type)
            if save_type == 'gif':
                if not file_name.lower().endswith('gif'):
                    continue
            elif save_type == 'static':
                if not file_name.lower().endswith(('jpg', 'png', 'jpeg', 'bmp')):
                    continue
            elif save_type == 'voices':
                if not file_name.lower().endswith(('wav', 'mp3', 'ogg')):
                    continue
            else:
                if not file_name.lower().endswith(('gif', 'jpg', 'png', 'jpeg', 'bmp')):
                    continue
            filepath = os.path.join(dirpath, file_name)
            rst.append(filepath)
    logger.info(f"{root}路径下所有文件类型{f_ls}")
    return rst


def refresh_all_img():
    global img_3
    global img_3R
    global img_gif
    global voices
    img_3 = list_all_file("/mnt/share/3")
    img_3R = list_all_file("/mnt/share/3R")
    img_gif = list_all_file("/mnt/share/GIF", 'gif')
    voices = list_all_file("/mnt/share/voices", 'voices')


refresh_all_img()


def deal_img(img_path, delele_flag=False):
    img = pil_img.open(img_path)
    width, height = img.size
    file_type = os.path.splitext(img_path)[-1]
    rep_ls = ['\\', '/', ':', '[', ']', '{', '}', '%']
    new_path = img_path
    for q in rep_ls:
        new_path = new_path.replace(q, '_')
    new_path = os.path.join("/mnt/share/tmp", new_path)
    # if new_path.endswith('.jpg'):
    #    new_path = new_path.replace('.jpg', '.png')
    box = (random.randint(1, 10), random.randint(1, 10), width - random.randint(1, 10), height - random.randint(1, 10))
    # logger.info(f"pillow版本{pil_img.__version__}")
    if file_type == '.gif':
        frames = [img.crop(box) for frame in range(0, img.n_frames) if not img.seek(frame)]
        frames[0].save(new_path, save_all=True, append_images=frames, loop=0, duration=img.info['duration'])
    else:
        img = img.crop(box)
        width, height = img.size
        for _ in range(10):
            img.putpixel((random.randint(10, width - 10), random.randint(10, height - 10)), 0)
        img.save(new_path)
    if delele_flag:
        os.remove(img_path)
    return new_path


async def send_img(sender, send_ls, delele_flag=False):
    pool = multiprocessing.Pool(min(multiprocessing.cpu_count(), len(send_ls)))
    res_list = []
    for img in send_ls:
        if not img or not os.path.exists(img):
            continue
        res = pool.apply_async(deal_img, args=(img, delele_flag))
        res_list.append(res)
    pool.close()
    pool.join()
    for res in res_list:
        new_img = res.get()
        if new_img and os.path.exists(new_img):
            logger.info(f"发送图片{new_img}")
            await sender.send(MessageSegment.image(f"file:///{new_img}"))
            os.remove(new_img)


def list_in_str(ls, string):
    return any(q in string for q in ls)


async def download_img(tag, sender, echo_flag=True):
    async with ClientSession(trust_env=True,
                             connector=TCPConnector(verify_ssl=False)) as aio_session:
        img_path = '/mnt/share/tmp'
        if "+" in tag or '＋' in tag:
            tag = tag.replace('+', '').replace('＋', '')
            r18 = 1
        elif "-" in tag:
            tag = tag.replace('-', '')
            r18 = 2
        else:
            r18 = 0
        data = {
            'r18': r18,
            'num': 3,
            'size': 'original',
            'proxy': 'https://i.pixiv.re'
        }

        if '&amp;' in tag:
            data['tag'] = [q for q in tag.split('&amp;') if q]
        else:
            data['keyword'] = tag
        url = 'https://api.lolicon.app/setu/v2'
        async with aio_session.post(url, json=data) as res:
            if res.status != 200:
                await sender.send(MessageSegment.text("查询图片失败!"))
                return
            resp = json.loads(await res.text())
            if len(resp['data']) == 0:
                await sender.send(MessageSegment.text("无符合条件的图片!"))
                return
            [logger.info(q) for q in resp['data']]
            url_ls = [q['urls']['original'] for q in resp['data']]
        send_ls = []
        if echo_flag:
            await sender.send(MessageSegment.text("图片下载中，请稍等!"))
        logger.info(f"图片开始下载")
        date1 = datetime.now()
        for url in url_ls:
            file_type = url.split('.')[-1]
            file_name = ''.join(random.sample(string.ascii_lowercase, 10)) + '.' + file_type
            file_path = os.path.join(img_path, file_name)
            headers = {'referer': "www.pixiv.net"}
            async with aio_session.get(url, headers=headers, timeout=60) as res:
                if res.status == 200:
                    send_ls.append(file_path)
                    img = await res.content.read()
                    with open(file_path, 'wb')as f:
                        f.write(img)
        logger.info(f"{len(send_ls)}张图片下载完成,耗时{datetime.now() - date1}")
        await send_img(get_img, send_ls, True)


get_img = on_startswith("来点", priority=1, block=True)


@get_img.handle()
async def get_img_handle(bot: Bot, event: Event, state: T_State):
    tag = str(event.get_message()).replace('来点', '').strip()
    if event.sub_type != "normal":
        logger.info(event.sub_type)
        await get_img.send(MessageSegment.text("涩图功能不再支持私聊"))
        return

    ban_ls = [852033704, 924026546, 218578923]
    if list_in_str(['gif', 'GIF', '动图', '+', '＋'], tag) and event.group_id in ban_ls:
        await get_img.send(MessageSegment.text("此群已禁用R18功能"))
        return
    if 1 <= len(tag):
        if "伤城" in tag or "绝奏" in tag:
            await get_img.send(MessageSegment.text("无符合条件的图片!"))
        elif list_in_str(['gif', 'GIF', '动图'], tag):
            if tag.replace('+', '').replace('＋', '') not in ['gif', 'GIF', '动图']:
                await get_img.send(MessageSegment.text("动图暂无搜索功能！"))
                return
            send_ls = random.sample(img_gif, 3)
            await send_img(get_img, send_ls)
        elif list_in_str(['真人', '三次元'], tag):
            if tag.replace('+', '').replace('＋', '') not in ['真人', '三次元']:
                await get_img.send(MessageSegment.text("真人暂无搜索功能！"))
                return
            if list_in_str(['+', '＋'], tag):
                send_ls = random.sample(img_3R, 3)
            else:
                send_ls = random.sample(img_3, 3)
            await send_img(get_img, send_ls)
        elif tag == '娇喘':
            record = random.choice(voices)
            await get_img.send(MessageSegment.record(f"file:///{record}"))
        else:
            ls = ['二次元', '假人', '纸片人', '涩图', '色图']
            tag = tag
            for q in ls:
                tag = tag.replace(q, '')
            try:
                await download_img(tag, get_img)
            except:
                try:
                    await download_img(tag, get_img, False)
                except:
                    logger.info(traceback.format_exc())
                    await get_img.send(MessageSegment.text("图片下载出错!"))


del_img = on_startswith("清空", rule=to_me(), priority=7, block=True)


@del_img.handle()
async def del_img_handle(bot: Bot, event: Event, state: T_State):
    if str(event.get_message()).strip() != '清空':
        return
    save_path = '/mnt/share/receive_img/' + event.get_user_id()
    if os.path.exists(save_path):
        shutil.rmtree(save_path)
    await del_img.send(MessageSegment.text("清空结束"))


img_forward = on_startswith("转发", priority=8, block=True)


@img_forward.handle()
async def img_forward_handle(bot: Bot, event: Event, state: T_State):
    if str(event.get_message()).strip() != '转发':
        return
    save_path = '/mnt/share/receive_img/' + event.get_user_id()
    if not os.path.exists(save_path):
        await del_img.send(MessageSegment.text("无可转发图片,请先私发要转发的图片给机器人！"))
        return

    forwards = list_all_file(save_path, 'all')
    await send_img(img_forward, forwards)


get_img_num = on_startswith("库存", priority=9, block=True)


@get_img_num.handle()
async def get_img_num_handle(bot: Bot, event: Event, state: T_State):
    if str(event.get_message()).strip() != '库存':
        return

    refresh_all_img()
    msg = f"""本地图片数量：
    三次元(不含r18): {len(img_3)};
    三次元R18: {len(img_3R)};
    动图: {len(img_gif)};
    音频:{len(voices)}"""
    await get_img_num.send(MessageSegment.text(msg))
