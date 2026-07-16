"""
Model Router API 客户端
=======================
封装阿里云百炼 Model Router API 的 HTTP 调用，
支持：文本对话（流式/非流式）、图片生成（同步/异步）、TTS、视频生成（异步轮询）。

API 文档来源: ModelRouter_API.docx (赛方官方文档, 126 模型)
Base URL: https://model-router.edu-aliyun.com/v1
"""

from __future__ import annotations

import json
import time
import logging
from typing import AsyncIterator

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ModelRouterError(Exception):
    """Model Router API 调用异常"""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class ModelRouterClient:
    """阿里云百炼 Model Router API 异步客户端"""

    def __init__(self) -> None:
        self._base_url: str = settings.MODEL_ROUTER_BASE_URL
        self._api_key: str = settings.MODEL_ROUTER_API_KEY
        self._timeout: int = settings.REQUEST_TIMEOUT
        self._max_retries: int = settings.MAX_RETRIES
        self._retry_delay: float = settings.RETRY_DELAY

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._base_url,
            headers=self._headers(),
            timeout=httpx.Timeout(self._timeout),
        )

    async def _request_with_retry(
        self,
        method: str,
        endpoint: str,
        json_data: dict | None = None,
    ) -> httpx.Response:
        """带重试的 HTTP 请求"""
        last_error: Exception | None = None

        for attempt in range(self._max_retries):
            try:
                async with self._client() as client:
                    response = await client.request(
                        method, endpoint, json=json_data
                    )
                    if response.status_code < 500:
                        return response
                    logger.warning(
                        f"Model Router 响应 {response.status_code}, "
                        f"第 {attempt + 1}/{self._max_retries} 次重试"
                    )
            except httpx.RequestError as e:
                last_error = e
                logger.warning(
                    f"Model Router 请求失败: {e}, "
                    f"第 {attempt + 1}/{self._max_retries} 次重试"
                )

            if attempt < self._max_retries - 1:
                await _async_sleep(self._retry_delay * (2 ** attempt))

        raise ModelRouterError(
            f"请求失败（已重试 {self._max_retries} 次）: {last_error}"
        )

    # ------------------------------------------------------------------
    # 文本对话
    # ------------------------------------------------------------------

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.8,
        max_tokens: int = 4096,
    ) -> str:
        """
        非流式文本对话

        Args:
            messages: [{"role": "system", "content": "..."}, ...]
            model: 模型 ID，默认 qwen/qwen3.7-max
            temperature: 0.0 ~ 2.0
            max_tokens: 最大输出 token

        Returns:
            模型回复文本
        """
        model = model or settings.TEXT_MODEL
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        response = await self._request_with_retry("POST", "/chat/completions", payload)
        if response.status_code != 200:
            raise ModelRouterError(
                f"对话请求失败: {response.text}", response.status_code
            )

        data = response.json()
        return data["choices"][0]["message"]["content"]

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.8,
    ) -> AsyncIterator[str]:
        """
        流式文本对话

        Yields:
            每次 yield 一个 token/chunk 的文本
        """
        model = model or settings.TEXT_MODEL
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }

        async with self._client() as client:
            async with client.stream(
                "POST", "/chat/completions", json=payload
            ) as response:
                if response.status_code != 200:
                    text = await response.aread()
                    raise ModelRouterError(
                        f"流式对话请求失败: {text}", response.status_code
                    )
                async for line in response.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        try:
                            chunk = json.loads(line[6:])
                            content = (
                                chunk.get("choices", [{}])[0]
                                .get("delta", {})
                                .get("content", "")
                            )
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    async def chat_json(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.3,
    ) -> dict:
        """
        文本对话并解析为 JSON（用于结构化输出如脚本、策略）

        prompt 中需要明确要求模型输出 JSON 格式。
        """
        import re

        text = await self.chat(messages, model=model, temperature=temperature)
        text = text.strip()

        # 去除 markdown 代码块标记
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        # 去除 JSON 中非法的控制字符（deepseek-r1 等模型可能混入）
        # 保留 \n, \t, \r 这些 JSON 合法的转义
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)

        # 尝试解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # 尝试提取第一个 { } 或 [ ] 块
            match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
            raise

    # ------------------------------------------------------------------
    # 图片生成
    # ------------------------------------------------------------------

    async def generate_image(
        self,
        prompt: str,
        model: str | None = None,
        size: str = "1024x1024",
        n: int = 1,
    ) -> list[str]:
        """
        生成图片

        Returns:
            图片 URL 列表
        """
        model = model or settings.IMAGE_MODEL
        payload = {
            "model": model,
            "prompt": prompt,
            "n": n,
            "size": size,
        }

        response = await self._request_with_retry(
            "POST", "/images/generations", payload
        )
        if response.status_code != 200:
            raise ModelRouterError(
                f"图片生成失败: {response.text}", response.status_code
            )

        data = response.json()
        return [img["url"] for img in data.get("data", [])]

    # ------------------------------------------------------------------
    # TTS 语音合成
    # ------------------------------------------------------------------

    async def text_to_speech(
        self,
        text: str,
        model: str | None = None,
        language: str = "en",
        voice: str = "Chelsie",
    ) -> bytes:
        """
        文本转语音 (POST /v1/audio/speech, OpenAI 兼容)

        Args:
            voice: 音色名称，支持 Chelsie / Ethan / Serena

        Returns:
            音频数据 (MP3 bytes)
        """
        model = model or settings.TTS_MODEL
        payload = {
            "model": model,
            "input": text,
            "language": language,
            "voice": voice,
        }

        response = await self._request_with_retry(
            "POST", "/audio/speech", payload
        )
        if response.status_code != 200:
            raise ModelRouterError(
                f"TTS 生成失败: {response.text}", response.status_code
            )

        return response.content

    # ------------------------------------------------------------------
    # 视频生成（文生视频 / 图生视频 — 异步 + 轮询）
    # ------------------------------------------------------------------

    # 视频生成异步轮询配置
    POLL_INITIAL_DELAY: float = 5.0
    POLL_INTERVAL: float = 3.0
    POLL_MAX_WAIT: float = 300.0  # 最多等 5 分钟

    async def text_to_video(
        self,
        prompt: str,
        model: str | None = None,
        duration: str = "5",
        size: str | None = None,
    ) -> str:
        """
        文生视频 (POST /v1/videos/generations, 异步)

        提交任务 → 轮询 GET /v1/tasks/{task_id} → 返回视频 URL

        Returns:
            视频 URL
        """
        task_id = await self._submit_video_task(
            prompt=prompt, model=model, duration=duration, size=size
        )
        return await self._poll_video_result(task_id)

    async def image_to_video(
        self,
        image_url: str,
        prompt: str = "",
        model: str | None = None,
        duration: str = "5",
        size: str | None = None,
    ) -> str:
        """
        图生视频 (POST /v1/videos/generations, 异步)

        Returns:
            视频 URL
        """
        task_id = await self._submit_video_task(
            prompt=prompt, image_url=image_url, model=model, duration=duration, size=size
        )
        return await self._poll_video_result(task_id)

    async def _submit_video_task(
        self,
        prompt: str,
        image_url: str | None = None,
        model: str | None = None,
        duration: str = "5",
        size: str | None = None,
    ) -> str:
        """提交视频生成任务，返回 task_id"""
        model = model or settings.VIDEO_MODEL
        payload: dict = {
            "model": model,
            "prompt": prompt,
            "duration": duration,
        }
        if image_url:
            payload["image_url"] = image_url
        if size:
            payload["size"] = size

        response = await self._request_with_retry(
            "POST", "/videos/generations", payload
        )
        if response.status_code != 200:
            raise ModelRouterError(
                f"视频生成任务提交失败: {response.text}", response.status_code
            )

        data = response.json()
        task_id = data.get("task_id", "")
        if not task_id:
            raise ModelRouterError(f"视频生成响应缺少 task_id: {data}")
        logger.info(f"视频任务已提交: {task_id}")
        return task_id

    async def _poll_video_result(self, task_id: str) -> str:
        """轮询视频生成任务直到完成，返回视频 URL"""
        import asyncio

        await asyncio.sleep(self.POLL_INITIAL_DELAY)

        elapsed = self.POLL_INITIAL_DELAY
        while elapsed < self.POLL_MAX_WAIT:
            try:
                response = await self._request_with_retry("GET", f"/tasks/{task_id}")
                if response.status_code != 200:
                    logger.warning(f"轮询返回 {response.status_code}")
                else:
                    data = response.json()
                    status = data.get("status", "")
                    logger.info(f"视频任务 {task_id}: {status} ({elapsed:.0f}s)")

                    if status in ("SUCCEEDED", "succeeded", "completed"):
                        output = data.get("output", {})
                        url = output.get("video_url", output.get("url", ""))
                        if not url:
                            # 尝试从 results 提取
                            results = output.get("results", [])
                            if results:
                                url = results[0].get("video_url", results[0].get("url", ""))
                        if url:
                            return url
                        raise ModelRouterError(f"任务完成但无视频 URL: {data}")

                    if status in ("FAILED", "failed", "error"):
                        error_msg = data.get("error", data.get("message", "未知错误"))
                        raise ModelRouterError(f"视频生成失败: {error_msg}")

                    # 仍在处理中
                    await asyncio.sleep(self.POLL_INTERVAL)
                    elapsed += self.POLL_INTERVAL
                    continue

            except ModelRouterError:
                raise
            except Exception as e:
                logger.warning(f"轮询异常: {e}")
                await asyncio.sleep(self.POLL_INTERVAL)
                elapsed += self.POLL_INTERVAL

        raise ModelRouterError(f"视频生成超时 (>{self.POLL_MAX_WAIT}s): {task_id}")

    # ------------------------------------------------------------------
    # 任务状态查询（通用异步任务）
    # ------------------------------------------------------------------

    async def get_task_status(self, task_id: str) -> dict:
        """查询异步任务状态 (GET /v1/tasks/{task_id})"""
        response = await self._request_with_retry("GET", f"/tasks/{task_id}")
        if response.status_code != 200:
            raise ModelRouterError(
                f"查询任务失败: {response.text}", response.status_code
            )
        return response.json()


async def _async_sleep(seconds: float) -> None:
    """异步 sleep 包装"""
    import asyncio
    await asyncio.sleep(seconds)


# ------------------------------------------------------------------
# 单例
# ------------------------------------------------------------------

_client: ModelRouterClient | None = None


def get_model_router() -> ModelRouterClient:
    global _client
    if _client is None:
        _client = ModelRouterClient()
    return _client
