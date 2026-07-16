# Phase 0: Model Router API 踩点报告 — 基于赛方官方文档

> 日期：2026-07-16  
> 文档来源：`ModelRouter_API.docx` + 官方参赛指南页面  
> 范围：126 个模型的完整 API 接口

---

## 一、文档核心信息提取

### 1.1 基础信息

- **Base URL**: `https://model-router.edu-aliyun.com/v1`
- **认证方式**: Bearer Token (`Authorization: Bearer <api-key>`)
- **Content-Type**: `application/json`

### 1.2 模型分类全景（8大类 × 126个）

| 类别 | 数量 | 代表模型 |
|------|------|---------|
| **文本对话** | 59 | qwen/qwen3.7-max, qwen/qwen3.6-plus, qwen/qwq-plus |
| **第三方文本** | 19 | qwen/deepseek-r1, qwen/deepseek-v4-pro, qwen/kimi-k2.6, qwen/glm-5.1 |
| **视觉/多模态** | 8 | qwen/qwen3-vl-plus, qwen/qwen3-vl-flash, qwen/qwen-vl-ocr |
| **图片生成/编辑** | 10 | qwen/wan2.7-image-pro, qwen/wan2.7-image, qwen/qwen-image-plus |
| **视频生成** | 18 | qwen/wan2.7-t2v, qwen/wan2.7-i2v, qwen/wan2.7-videoedit |
| **语音** | 5 | qwen/qwen3-tts-instruct-flash (TTS), qwen/qwen3-asr-flash (ASR) |
| **向量** | 4 | qwen/text-embedding-v4, qwen/qwen3-vl-embedding |
| **排序** | 3 | qwen/qwen3-rerank, qwen/gte-rerank-v2 |

### 1.3 接口调用方式汇总

| 模态 | 接口 | 方式 | 特殊说明 |
|------|------|------|---------|
| 文本对话 | `POST /v1/chat/completions` | 同步/流式 | qwq 系列仅支持 stream: true |
| 图片生成(新) | `POST /v1/images/generations` | 同步 | wan2.7/2.6 系列 |
| 图片生成(旧) | `POST /v1/images/generations` | 异步 | wan2.5/2.2 系列，需 `X-DashScope-Async: enable` |
| 图片编辑 | `POST /v1/images/generations` | 异步 | 需 `X-DashScope-Async: enable` |
| 视频生成 | `POST /v1/videos/generations` | 异步 | 返回 task_id → 轮询 `GET /v1/tasks/{task_id}` |
| TTS | `POST /v1/audio/speech` | 同步 | OpenAI 兼容，voice: Chelsie/Ethan/Serena |
| ASR | `POST /v1/audio/transcriptions` | 同步 | multipart/form-data |
| 向量 | `POST /v1/embeddings` | 同步 | 多模态需特殊格式 |
| 排序 | `POST /v1/rerank` | 同步 | 多模态需嵌套 input |
| 任务查询 | `GET /v1/tasks/{task_id}` | GET | 查询异步任务状态 |

---

## 二、代码修正清单

### ✅ 已修正

| # | 项目 | 修正前 | 修正后 | 文件 |
|---|------|--------|--------|------|
| 1 | **DeepSeek 模型ID** | `deepseek-r1` | `qwen/deepseek-r1` | `config.py` |
| 2 | **TTS 音色** | `voice="default"` | `voice="Chelsie"`（Chelsie/Ethan/Serena 三选一） | `model_router.py`, `tts_service.py` |
| 3 | **视频生成** | 假装同步返回 URL | 提交→task_id→轮询 `GET /v1/tasks/{task_id}`→解析 video_url | `model_router.py` |
| 4 | **图生视频** | 未实现 | 新增 `image_to_video()` 方法 | `model_router.py` |
| 5 | **通用任务查询** | 未实现 | 新增 `get_task_status()` 方法 | `model_router.py` |

### ⚠️ 已知差异（暂不影响 MVP）

| 项目 | 说明 |
|------|------|
| **旧版图片模型异步** | wan2.5/2.2 系列需要 `X-DashScope-Async: enable` + DashScope 格式，但我们 MVP 用新版 wan2.7，暂不处理 |
| **qwq 系列 stream 限制** | qwq-plus 等推理模型仅支持 stream，schema 中已标记 |
| **多模态向量/排序** | 我们暂时不调用这些接口 |

---

## 三、CrossSell AI 实际使用的模型映射

| Pipeline 步骤 | 模型 ID | 接口 | 调用方式 |
|--------------|---------|------|---------|
| 脚本生成 / 文案 | `qwen/qwen3.7-max` | `/v1/chat/completions` | 同步 (stream: false) |
| 快速原型验证 | `qwen/qwen3.5-flash` | `/v1/chat/completions` | 同步 |
| 投流策略分析 | `qwen/deepseek-r1` | `/v1/chat/completions` | 同步 |
| TTS 配音 | `qwen/qwen3-tts-instruct-flash` | `/v1/audio/speech` | 同步 (返回 audio bytes) |
| 图片素材生成 | `qwen/wan2.7-image-pro` | `/v1/images/generations` | 同步 |
| 视频生成(备选) | `qwen/wan2.7-t2v` | `/v1/videos/generations` | **异步** (提交→轮询) |

---

## 四、Phase 0 踩点下一步

按启动文档优先级，需要实际调通以下接口：

1. **🔴 文本对话** — `POST /chat/completions`（qwen/qwen3.7-max） — 最高优先级，文案/脚本的基础
2. **🟡 TTS** — `POST /audio/speech`（Chelsie 音色，测中/英/日三种语言） — 配音质量决定 Demo 效果
3. **🟡 图片生成** — `POST /images/generations`（wan2.7-image-pro） — 素材来源
4. **🟢 视频生成** — `POST /videos/generations`（wan2.7-t2v，异步轮询） — 可选，MVP 优先用 FFmpeg 合成

**阻塞项**: 需要 API Key。初赛前可用阿里云百炼免费额度测试，初赛通过后赛方发放专属 Key。
