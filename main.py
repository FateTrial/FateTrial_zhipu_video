from astrbot.api.message_components import *
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api.all import *
import importlib
import subprocess
import sys
from zhipuai import ZhipuAI
import time
import aiohttp
import asyncio
from typing import Dict, Optional
from astrbot.core.utils.io import download_image_by_url
import base64

# 用于跟踪每个用户的状态，防止超时或重复请求
USER_STATES: Dict[str, Optional[float]] = {}

@register("FateTrial_zhipu_video", "FateTrial", "使用智谱AI生成视频。使用 /aivd <提示词> 生成视频。", "1.0")
class ZhipuVideoPlugin(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config
        self.api_key = config.get("api_key", "")
        self.model = config.get("model", "CogVideoX-Flash")
        
        # 检查并安装 zhipuai
        if not self._check_zhipuai():
            self._install_zhipuai()
        
        # 导入 zhipuai
        global ZhipuAI
        from zhipuai import ZhipuAI

    def _check_zhipuai(self) -> bool:
        """检查是否安装了 zhipuai"""
        try:
            importlib.import_module('zhipuai')
            return True
        except ImportError:
            return False

    def _install_zhipuai(self):
        """安装 zhipuai 包"""
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "zhipuai"])
            print("成功安装 zhipuai 包")
        except subprocess.CalledProcessError as e:
            print(f"安装 zhipuai 包失败: {str(e)}")
            raise

    @filter.command("aivd")
    async def generate_video(self, event: AstrMessageEvent, prompt: str = ""):
        # 检查是否配置了API密钥
        if not self.api_key:
            yield event.plain_result("\n请先在配置文件中设置智谱AI的API密钥")
            return

        # 检查提示词是否为空
        if not prompt:
            yield event.plain_result("\n请提供提示词！使用方法：/aivd <提示词>")
            return

        try:
            # 创建智谱AI客户端
            client = ZhipuAI(api_key=self.api_key)
            
            # 发送生成请求
            response = client.videos.generations(
                model=self.model,
                prompt=prompt,
                with_audio=True,
            )          
            chain = [
                Plain(f"提示词：{prompt}\n"),
                Plain(f"ID：{response.id}")
            ]
            yield event.chain_result(chain)
            
        except Exception as e:
            yield event.plain_result(f"\n生成视频失败: {str(e)}")
    @filter.command("aivd查询")
    async def chaxun_video(self, event: AstrMessageEvent, ide: str = ""):
        # 检查是否配置了API密钥
        if not self.api_key:
            yield event.plain_result("\n请先在配置文件中设置智谱AI的API密钥")
            return

        # 检查提示词是否为空
        if not ide:
            yield event.plain_result("\n请提供id！使用方法：/aivd查询 <id>")
            return

        try:
            # 创建智谱AI客户端
            client = ZhipuAI(api_key=self.api_key)
            
            # 发送请求
            response = client.videos.retrieve_videos_result(
                        id=ide
                        )
            chain = [
                Plain(f"模型：{response.model}\n"),
                Plain(f"视频结果：{response.video_result}")
            ]
            yield event.chain_result(chain)
            
        except Exception as e:
            yield event.plain_result(f"\n查询失败: {str(e)}")
    @filter.command("aiivd")
    async def tuzhuan_video(self, event: AstrMessageEvent):
        # 检查是否配置了API密钥
        if not self.api_key:
            yield event.plain_result("\n请先在配置文件中设置智谱AI的API密钥")
            return
        user_id = event.get_sender_id()  # 获取用户ID
        USER_STATES[user_id] = time.time()  # 记录用户请求的时间
        yield event.plain_result("杂鱼~还得靠我呢!限你30秒内发送你要生成的图片yo~")  # 提示用户发送图片
        await asyncio.sleep(30)  # 等待30秒
        # 如果超时，删除用户状态并通知用户
        if user_id in USER_STATES:
            del USER_STATES[user_id]
            yield event.plain_result("超时了哦，杂鱼~")      
    @event_message_type(EventMessageType.ALL)
    async def handle_image(self, event: AstrMessageEvent):
        user_id = event.get_sender_id()  # 获取发送者的ID
        if user_id not in USER_STATES:  # 如果用户没有发起请求，跳过
            return
        
        # 检查消息中是否包含图片
        images = [c for c in event.message_obj.message if isinstance(c, Image)]
        if not images:
            return
        
        # 删除用户状态，表示用户已提交图片
        del USER_STATES[user_id]
        image_url = images[0].url
        path = await download_image_by_url(image_url)
        with open(path, "rb") as f:
            img = f.read()
            img_base64 = base64.b64encode(img).decode()
        try:
            # 创建智谱AI客户端
            client = ZhipuAI(api_key=self.api_key)
            
            # 发送请求
            response = client.videos.generations(
                model=self.model,
                image_url=img_base64,  # 提供的图片URL地址或者 Base64 编码
                prompt="让画面动起来",
                with_audio=True,
            )          
            chain = [
                Plain(f"ID：{response.id}")
            ]
            yield event.chain_result(chain)
            
        except Exception as e:
            yield event.plain_result(f"\n生成失败: {str(e)}")

