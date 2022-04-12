import random

from nonebot import on_notice, on_startswith, on_keyword
from nonebot.adapters.cqhttp import Event, FriendRequestEvent, GroupRequestEvent
from nonebot.adapters.cqhttp import GroupIncreaseNoticeEvent
from nonebot.log import logger
from nonebot.typing import T_State
from nonebot.adapters import Bot
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import MessageSegment

get_roll = on_startswith("roll", priority=3, block=True)


@get_roll.handle()
async def get_roll_handle(bot: Bot, event: Event, state: T_State):
    if str(event.get_message()).strip() == 'roll':
        await get_roll.send(MessageSegment.text(str(random.randint(1, 100))))


food = on_keyword(("吃什么", "吃啥"), priority=5, block=True)


@food.handle()
async def food_handle(bot: Bot, event: Event, state: T_State):
    await food.send(MessageSegment.image(f"file:///mnt/share/food/1.gif"))


MENU_STR = """色图功能:
    二次元涩图：来点二次元/来点涩图/来点【关键字】
    三次元涩图：来点三次元/来点真人
    动图: 来点动图/来点gif
    声音: 来点娇喘
只有二次元有搜索功能，静态图默认非r18，在后面带+号为r18版本的，动图只有r18版本的，多关键字以&分隔
roll点（1-100）：roll
点歌: 点歌【歌曲名】
转发功能: 先将要转发的图片私发给机器人，然后在要转发的群发【转发】两个字
以图搜图: 搜图【图片】(搜图这两个字需和图片在同一条消息内)，直接回复要搜的图片也可以
在群内艾特或私聊可与AI（zhizhang）聊天
"""

get_menu = on_startswith("菜单", priority=4, block=True)


@get_menu.handle()
async def get_menu_handle(bot: Bot, event: Event, state: T_State):
    if str(event.get_message()).strip() == '菜单':
        await get_menu.send(MessageSegment.text(MENU_STR))


notice_event = on_notice()


@notice_event.handle()
async def notice_event_handle(bot: Bot, event: GroupIncreaseNoticeEvent, state: T_State):
    user = event.user_id
    self_qq = event.self_id
    if user == self_qq:
        await notice_event.send(MessageSegment.text(MENU_STR))
