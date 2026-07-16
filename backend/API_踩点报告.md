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

## 五、实际 API 调测结果（2026-07-16 实测）

### 5.1 关键发现：Base URL 与认证

用户提供的 API Key (`sk-ws-H...`) 是**阿里云百炼国内**的 Key，不是 CSDN Model Router 的。

| 端点 | 认证结果 | 说明 |
|------|---------|------|
| `model-router.edu-aliyun.com/v1` | ❌ 401 `InvalidApiKeyException` | CSDN 赛方端点，需赛方专属 Key |
| `dashscope.aliyuncs.com/compatible-mode/v1` | ✅ 200 OK | **阿里云百炼国内兼容模式** |
| `dashscope-intl.aliyuncs.com/compatible-mode/v1` | ❌ 401 | 国际端点不可用 |

**解决方案**：`.env` 中 `MODEL_ROUTER_BASE_URL` 改为 `https://dashscope.aliyuncs.com/compatible-mode/v1`

### 5.2 模型 ID 格式差异

阿里云百炼原生 API 的模型 ID **不需要** `qwen/` 前缀：

| 用途 | CSDN Model Router 格式 | 阿里云百炼原生格式 |
|------|----------------------|-------------------|
| 高质量文本 | `qwen/qwen3.7-max` ❌ 404 | `qwen-max` ✅ |
| 快速文本 | `qwen/qwen3.5-flash` ❌ 404 | `qwen-turbo` ✅ |
| 推理 | `qwen/deepseek-r1` ❌ 404 | `deepseek-r1` ✅ |
| TTS | `qwen/qwen3-tts-instruct-flash` ❌ | `cosyvoice-v1` ❓(compatible mode下不支持) |
| 图片 | `qwen/wan2.7-image-pro` ❌ | `wan2.1-t2i-turbo` ❓(compatible mode下不支持) |

### 5.3 各接口实测结果

| 接口 | 模型 | 状态 | 延迟 | 质量 |
|------|------|------|------|------|
| `/chat/completions` | `qwen-max` | ✅ 200 | ~5s | 高质量，英文+日文文案均通顺 |
| `/chat/completions` | `qwen-turbo` | ✅ 200 | ~1s | 快速，适合原型验证 |
| `/chat/completions` | `deepseek-r1` | ✅ 200 | ~55s | 慢但推理质量好，JSON有控制字符(已修复) |
| `/audio/speech` | 多种尝试 | ❌ 404 | — | compatible mode 不支持TTS，需达摩院原生API |
| `/images/generations` | 多种尝试 | ❌ 404 | — | compatible mode 不支持图片，需达摩院原生API |

### 5.4 Pipeline 端到端测试

通过 `POST /api/generate` → 轮询 → `GET /api/task/{id}/result` 完整链路：

```
产品：Portable Bluetooth Speaker (IPX7防水/24h续航/TWS立体声)
市场：美国 + 日本
平台：TikTok + Instagram
内容：copy (文案) + strategy (策略)
总耗时：82.8s
```

**Pipeline B — 文案矩阵 (✅ REAL AI)：**
- TikTok/美国：*"Hey TikTok fam! 🎶 Got a new fave for your adventures! This portable Bluetooth speaker is 💯 IPX7 waterproof..."*
- TikTok/日本：*"音楽をどこでも楽しもう！このBluetoothスピーカー、IPX7防水だからプールサイドでも大丈夫！..."*
- Instagram/美国：带换行符、多 hashtag、storytelling 风格

**Pipeline C — 投流策略 (✅ REAL AI)：**
- 推荐平台：TikTok
- 预估 ROAS：2.5-3.8x（非固定模板）
- 预算建议 + 内容角度 + 受众定向

### 5.5 踩坑与修复

| 问题 | 根因 | 修复 |
|------|------|------|
| HTTP请求返回fallback | FastAPI `BackgroundTasks` 对async函数不稳定 | 改用 `asyncio.create_task()` |
| deepseek-r1 JSON解析失败 | 返回含控制字符 `\x00-\x1f` | `chat_json()` 添加正则清洗 + 回退提取 |
| 多进程残留占用8000端口 | `pkill` 在Windows上不生效 | 用 `taskkill /F /PID` 清理 |

### 5.6 当前状态总结

| 能力 | 状态 | 备注 |
|------|------|------|
| 文本对话 (`qwen-max`) | ✅ 已打通 | 文案/脚本/策略均可生产 |
| 文本对话 (`deepseek-r1`) | ✅ 已打通 | 慢但推理强，JSON清理已修复 |
| TTS 语音合成 | ⚠️ 待确认 | compatible mode不支持，需达摩院原生端点 |
| 图片生成 | ⚠️ 待确认 | 同上 |
| 视频生成 | ⚠️ 待确认 | 同上 |
| FFmpeg 本地合成 | ❌ 未装 | 需安装 FFmpeg (Phase 2 需求) |

### 5.7 Pipeline A (视频) 的降级方案

由于 TTS 和图片生成在 compatible mode 下不可用，Pipeline A 当前策略：
1. **脚本生成**：✅ 用 `qwen-max` 产出（已验证）
2. **配音**：先跳过，用静音或公开音效替代
3. **素材**：用本地素材库 + 占位图
4. **合成**：安装 FFmpeg 后本地合成

正式 Key（赛方发放）发放后，切换到 CSDN Model Router 端点可恢复完整能力。

---

## 六、当前配置快照

```bash
# .env 关键配置（阿里云百炼国内兼容模式）
MODEL_ROUTER_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MODEL_ROUTER_API_KEY=sk-ws-H... （已填入）
TEXT_MODEL=qwen-max
FAST_TEXT_MODEL=qwen-turbo
REASONING_MODEL=deepseek-r1
TTS_MODEL=cosyvoice-v1           # 待验证（达摩院原生API）
IMAGE_MODEL=wan2.1-t2i-turbo     # 待验证
VIDEO_MODEL=wan2.1-t2v-turbo     # 待验证
```
