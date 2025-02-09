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
