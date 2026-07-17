# CrossSell AI — 跨境社媒内容引擎

> **AI+跨境黑客松巅峰赛 · 场景二：AI社媒营销**
>
> 面向跨境品牌卖家，用AI将"产品卖点→多平台本土化内容→智能投流"全链路自动化

---

## 产品定义

把跨境社媒营销从"人海战术"变为"一人控全场"——输入产品信息，AI自动生成适配TikTok/Instagram/YouTube Shorts等多平台的本土化短视频和社媒文案，并给出投流策略建议。

---

## 项目架构

```
CrossSell AI
├── frontend/          React 19 + Vite 8 + TailwindCSS 4 + TypeScript
│   ├── Dashboard      工作台首页（统计 + 快速启动 + 任务列表）
│   ├── Create         内容生成页（三步骤向导：输入→进度→结果）
│   ├── Strategy       投放策略页（建设中，复赛上线）
│   └── Analytics      数据中心页（建设中，复赛上线）
│
├── backend/           FastAPI + async SQLAlchemy + aiosqlite
│   ├── Pipeline A     短视频生产（脚本→配音→图片→FFmpeg合成）
│   ├── Pipeline B     多平台文案矩阵（并发LLM调用）
│   ├── Pipeline C     投流策略（DeepSeek-R1推理分析）
│   └── Model Router   阿里云百炼API客户端（6个模型，含重试/fallback）
│
└── .env.example       后端/前端环境变量模板
```

---

## 快速开始

### 前端

```bash
cd frontend
npm install
npm run dev        # 开发模式 → http://localhost:5173
npm run build      # 生产构建 → dist/
```

### 后端

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env    # 编辑填入 MODEL_ROUTER_API_KEY
uvicorn app.main:app --reload   # → http://localhost:8000
```

### Docker

```bash
cd backend
docker compose up -d   # API (8000) + Redis (6379)
```

---

## API端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/health` | 健康检查 |
| `POST` | `/api/generate` | 触发内容生成 (202 Accepted) |
| `GET` | `/api/task/{id}/status` | 查询任务进度 |
| `GET` | `/api/task/{id}/result` | 获取生成结果 |
| `GET` | `/api/tasks` | 历史任务列表 (分页) |
