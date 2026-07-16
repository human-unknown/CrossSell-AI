# CrossSell AI — Backend

> 跨境社媒内容引擎后端服务。FastAPI + SQLite + Model Router API + FFmpeg。

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 MODEL_ROUTER_API_KEY

# 3. 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 4. 访问 API 文档
#    Swagger UI: http://localhost:8000/docs
#    ReDoc:      http://localhost:8000/redoc
```

## 项目结构

```
backend/
├── app/
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # 配置管理
│   ├── database.py          # 数据库引擎 + 会话
│   ├── models.py            # SQLAlchemy 数据模型
│   ├── schemas.py           # Pydantic 请求/响应 Schema
│   ├── worker.py            # 后台任务调度器
│   ├── routes/
│   │   ├── health.py        # GET  /api/health
│   │   ├── generate.py      # POST /api/generate
│   │   └── tasks.py         # GET  /api/task/{id}/status, /result, /api/tasks
│   ├── services/
│   │   ├── model_router.py      # Model Router API 客户端
│   │   ├── script_generator.py  # 短视频脚本生成
│   │   ├── tts_service.py       # TTS 语音合成
│   │   ├── image_service.py     # AI 图片生成
│   │   ├── video_composer.py    # FFmpeg 视频合成
│   │   ├── copy_generator.py    # 多平台文案生成
│   │   └── strategy_engine.py   # 投流策略分析
│   └── pipeline/
│       ├── video_pipeline.py    # Pipeline A: 短视频生产
│       ├── copy_pipeline.py     # Pipeline B: 文案矩阵
│       └── strategy_pipeline.py # Pipeline C: 投流策略
├── tests/
│   ├── test_routes.py       # API 路由测试
│   ├── test_services.py     # 服务层测试
│   └── test_config.py       # 配置测试
├── output/                  # 生成的视频/音频/图片
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/generate` | 触发内容生成 |
| `GET` | `/api/task/{task_id}/status` | 查询任务进度 |
| `GET` | `/api/task/{task_id}/result` | 获取生成结果 |
| `GET` | `/api/tasks` | 历史任务列表 |
| `GET` | `/api/health` | 健康检查 |

完整文档见 Swagger UI: `/docs`

## 数据模型

```
Task (任务)
├── id, status, progress, current_step
├── steps: [{name, status}, ...]
├── TaskInput (1:1)  — 输入参数
│   ├── product_name, selling_points, description
│   ├── target_markets, target_platforms, content_types
└── TaskResult (1:1) — 生成结果
    ├── videos: [...]
    ├── copies: [...]
    └── strategy: {...}
```

## 核心 Pipeline

```
Pipeline A (视频):  脚本生成 → TTS配音 → AI图片素材 → FFmpeg合成 → 输出MP4
Pipeline B (文案):  并行调用 LLM → 多平台×多市场文案矩阵
Pipeline C (投流):  推理模型 → 投放策略 + 预算建议 + ROAS预估
```

## Docker 部署

```bash
docker-compose up -d
```

## 测试

```bash
pytest tests/ -v
```

## 环境要求

- Python 3.12+
- FFmpeg (视频合成)
- 阿里云百炼 API Key (踩点) / 赛方 Model Router API Key (正式)
