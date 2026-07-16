# CrossSell AI — Sprint 1 任务分配（7月17日 — 8月5日）

> **Sprint 目标**：完成初赛Idea文档交付 + 前后端真实验证联调 + 可演示的在线原型
>
> **截止硬线**：8月20日初赛作品提交

---

## 📋 三栏任务看板

---

### 🖥️ 后端开发

| # | 任务 | 优先级 | 预估工时 | 依赖 | 
|----|------|:------:|:--------:|------|
| BE-1 | **API Key配置 + 三条Pipeline真实验证** | 🔴 P0 | 4h | 需去阿里云百炼生成Key |
| BE-2 | **补充 /api/weekly-stats 接口** | 🟡 P1 | 2h | 无 |
| BE-3 | **前后端联调适配** | 🔴 P0 | 3h | BE-1完成后 |
| BE-4 | **错误码标准化 + API文档完善** | 🟢 P2 | 2h | 无 |

---

#### BE-1：API Key配置 + 三条Pipeline真实验证

**说明**：当前后端所有服务都有fallback降级（Mock数据），但从未跑过真实API。这是整个项目最大的不确定性——AI生成的内容质量直接决定Demo说服力。

在 `backend/.env` 配置 `MODEL_ROUTER_API_KEY`，依次验证：
- Pipeline A：用真实产品信息跑完整视频Pipeline（脚本→TTS→图片→合成），验证输出MP4可用
- Pipeline B：用真实LLM生成 (3平台 × 2市场) 文案矩阵，验证本土化质量
- Pipeline C：用推理模型输出投流策略，验证建议合理性

**交付物**：
- `backend/.env`（已配置真实Key，.gitignore已排除）
- Pipeline A/B/C 各至少一份真实产出（保存在 `backend/output/sprint1-verify/`）
- 真实API调用问题记录（如有模型不可用/质量不佳/限速问题）

**提示词**：
```
你是CrossSell AI项目的后端开发。当前项目已有完整的FastAPI后端，5个API端点和3条AI Pipeline，但从未配置真实的阿里云百炼Model Router API Key，所有AI调用返回的是fallback mock数据。

任务：配置真实API Key并验证三条Pipeline。

步骤：
1. 读取 backend/.env.example 了解需要的环境变量，创建 backend/.env 并填入 MODEL_ROUTER_API_KEY=你的真实Key（Base URL已有默认值 https://model-router.edu-aliyun.com/v1）
2. 启动后端：cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000
3. 用 curl 或 Swagger UI (http://localhost:8000/docs) 调用 POST /api/generate，传入一个真实的跨境产品（如"蓝牙音箱，防水24h续航，面向美国日本市场，生成TikTok视频和Instagram文案"）
4. 轮询 GET /api/task/{task_id}/status 直到完成
5. 获取 GET /api/task/{task_id}/result 检查输出质量
6. 记录每个API调用的延迟、输出质量、任何报错
7. 如果某个模型不可用，记录错误并标注降级方案

关键文件：backend/app/config.py（模型配置）、backend/app/worker.py（任务调度）、backend/app/services/model_router.py（API客户端）
```

---

#### BE-2：补充 /api/weekly-stats 接口

**说明**：前端 `api.ts` 调用了 `getWeeklyStats()` 获取Dashboard的统计数字，但后端根本没有这个端点。当前前端全靠mock数据硬撑着。

**交付物**：
- `backend/app/routes/stats.py`（新增路由文件）
- `GET /api/stats/weekly` 接口（返回本周已生成的视频数/文案数/任务数）
- 在 `backend/app/main.py` 中注册路由
- 测试用例 `backend/tests/test_stats.py`

**提示词**：
```
你是CrossSell AI项目的后端开发。我们需要补充一个缺失的API端点。

前端 Dashboard 页面调用了 getWeeklyStats() 来显示"本周生成视频数/文案数/投放建议数"三个统计卡片。但后端还没有这个接口，前端目前靠mock数据。

任务：实现 GET /api/stats/weekly 接口

要求：
1. 创建 backend/app/routes/stats.py
2. 查询数据库中的tasks表，统计本周（星期一到今天）的数据：
   - total_videos: 所有completed状态任务的结果中videos数组的总长度
   - total_copies: 所有completed状态任务的结果中copies数组的总长度  
   - total_strategies: 所有completed状态且strategy非空的任务数
   - total_tasks: 本周创建的任务总数
3. 使用SQLAlchemy异步查询（参考 backend/app/models.py 中的数据模型和 backend/app/database.py 的Session创建方式）
4. 在 backend/app/main.py 中注册路由：app.include_router(stats.router, prefix="/api/stats", tags=["Stats"])
5. 写测试用例 backend/tests/test_stats.py（至少2个：正常查询和空数据）

注意：Task 模型在 app/models.py 中，已经定义了 id/status/created_at 等字段，TaskResult 在同一个文件中。Task和TaskResult是关联的，通过 task.result 访问。
```

---

#### BE-3：前后端联调适配

**说明**：当前前端使用 `import.meta.env.VITE_API_BASE || '/api'` 且所有调用走mock。联调时需要确保：前端能正确指向后端地址、请求体格式完全一致、跨域CORS正常、进度轮询机制工作。

**交付物**：
- 联调成功的验证记录（至少跑通一次完整的"前端点击生成→后端真实处理→前端展示结果"流程）
- 前端 `services/api.ts` 切换为真实Axios调用（去掉mock代码或通过环境变量切换）
- 联调中发现的问题清单 + 修复记录

**提示词**：
```
你是CrossSell AI项目的后端开发。前端和后端的基本实现都已完成，但两边的数据从未真正流通。

任务：完成前后端联调。

步骤：
1. 确认后端CORS配置：backend/app/config.py 中的 CORS_ORIGINS 列表包含前端地址（Vite dev server默认 localhost:5173）
2. 启动后端：uvicorn app.main:app --reload --port 8000
3. 用 curl 测试所有端点，确认返回格式与前端期望一致：
   - POST /api/generate 返回 {"task_id": "uuid"}
   - GET /api/task/{id}/status 返回 {status, progress, steps: [{name, status}], current_step}
   - GET /api/task/{id}/result 返回 {videos: [{platform, url}], copies: [{platform, text, hashtags}], strategy: {...}}
   - GET /api/stats/weekly 返回 {total_videos, total_copies, total_strategies, total_tasks}
4. 对照前端类型定义 frontend/src/types/index.ts 确认字段名完全匹配
5. 如果发现字段名不一致，优先修改后端（因为后端还在我们控制中，前端类型已经定义好了）

关键检查点：前端期望 GenerationResult 类型包含 taskId/videos/copies/strategy/totalGenerated，确保后端返回这些字段。前端期望 GenerationProgress 包含 taskId/status/progress/steps。
```

---

#### BE-4：错误码标准化 + API文档完善

**说明**：比赛评委可能查看API文档。当前异常处理过于简单（统一500），正式提交作品前需要更好的错误码体系。

**交付物**：
- `backend/app/errors.py`（统一错误码定义：400参数错误、401未授权、404任务不存在、425结果未就绪、429限流、500内部错误）
- 更新 `backend/app/main.py` 的全局异常处理器
- Swagger文档中所有端点都有清晰的错误响应示例

**提示词**：
```
你是CrossSell AI项目的后端开发。当前所有异常都返回500，缺乏细粒度错误处理。

任务：实现标准化的错误码体系。

要求：
1. 创建 backend/app/errors.py，定义：
   - AppError 基类（code, message, status_code）
   - TaskNotFoundError (404)
   - TaskNotReadyError (425)
   - ValidationError (400)
   - RateLimitError (429)
   - AIServiceError (502, 区别于500)
2. 更新 backend/app/main.py 的 global_exception_handler，根据异常类型返回不同的status_code
3. 更新 backend/app/routes/tasks.py，在task不存在时主动抛出 TaskNotFoundError
4. 更新 backend/app/routes/tasks.py，在result未就绪时主动抛出 TaskNotReadyError（目前返回的硬编码425可以改用错误类）
5. 不需要修改现有的24个测试用例，但新增2个测试验证错误处理逻辑

所有错误响应格式：{"detail": "人类可读的描述", "error_code": "TASK_NOT_FOUND", "status_code": 404}
```

---

### 🎨 前端开发

| # | 任务 | 优先级 | 预估工时 | 依赖 | 
|----|------|:------:|:--------:|------|
| FE-1 | **接入真实后端API + 实现进度轮询** | 🔴 P0 | 4h | BE-1 + BE-3完成 |
| FE-2 | **Strategy投放策略页基础实现** | 🟡 P1 | 3h | 无（可先mock） |
| FE-3 | **Analytics数据中心页基础实现** | 🟢 P2 | 2h | BE-2完成（有真实接口更好） |
| FE-4 | **部署到线上可访问URL** | 🔴 P0 | 1h | FE-1完成后 |

---

#### FE-1：接入真实后端API + 实现进度轮询

**说明**：当前 `frontend/src/services/api.ts` 全部走mock数据，Create页面的进度条是通过 `simulateProgress` 前端模拟的。接入真实后端后，需要实现轮询 `GET /api/task/{id}/status` 获取真实的步骤进度。

**交付物**：
- `frontend/src/services/api.ts` 改为真实Axios调用（保留环境变量切换能力）
- `frontend/.env`（`VITE_API_BASE=http://localhost:8000/api`）
- Create页面 Step 2 的进度条改为读取后端返回的 steps 数组（备选：两阶段——优先后端API，失败时降级mock）

**提示词**：
```
你是CrossSell AI项目的前端开发。当前前端Create页面的三步骤向导中：
- Step 1 表单正常工作
- Step 2 进度条使用 mock/simulateProgress 模拟
- Step 3 结果展示使用 mockGenerationResult

后端API已就绪（假设），需要将前端切换到真实API。

任务：将前端从mock切换到真实后端API。

步骤：
1. 在 frontend/ 创建 .env 文件，写入 VITE_API_BASE=http://localhost:8000/api
2. 修改 frontend/src/services/api.ts：
   - triggerGeneration: 改为 axios.post(`${API_BASE}/generate`, productInfo)
   - getTaskStatus: 改为 axios.get(`${API_BASE}/task/${taskId}/status`)
   - getTaskResult: 改为 axios.get(`${API_BASE}/task/${taskId}/result`)
   - getTasks: 改为 axios.get(`${API_BASE}/tasks`, { params: { page, size } })
   - getWeeklyStats: 改为 axios.get(`${API_BASE}/stats/weekly`)
   - 删除 simulateProgress 导入（不再需要）
3. 修改 frontend/src/stores/createStore.ts：
   - 删除 startProgressSimulation 函数中的 simulateProgress 调用
   - 改为每2秒轮询 getTaskStatus(taskId)
   - 用后端返回的 steps 数组驱动进度步骤条
   - 当 status === 'completed' 时自动调用 getTaskResult
4. 确保所有类型定义与后端返回一致（对照 frontend/src/types/index.ts）
5. 保留 fallback：当 API 调用失败时，仍可降级为mock模式

关键文件：frontend/src/services/api.ts、frontend/src/stores/createStore.ts、frontend/src/pages/Create.tsx
```

---

#### FE-2：Strategy投放策略页基础实现

**说明**：当前 `Strategy.tsx` 只是一个"建设中"的占位页。初赛评审时评委可能浏览所有页面，至少有基础内容才有说服力。此页面可先使用mock数据，不依赖后端。

**交付物**：
- `frontend/src/pages/Strategy.tsx` 完整重构（不再是占位页）
- 包含：产品选择器 + 各渠道推荐卡片（TikTok/Meta/Google）+ 预算分配饼图 + 策略建议列表

**提示词**：
```
你是CrossSell AI项目的前端开发。当前 Strategy.tsx 只是一个占位页面（"复赛阶段上线 — 建设中"）。

任务：实现Strategy投放策略页面的基础版本，使用mock数据。

功能要求：
1. 页面顶部：产品选择器（下拉框，从已有的mock任务中选取）
2. 主区域分两栏：
   左栏：渠道推荐卡片（TikTok Ads / Meta Ads / Google Ads 三个卡片）
     每个卡片展示：渠道图标、推荐级别（星标1-5）、建议日预算、预计ROAS范围、投放建议理由
   右栏：Recharts饼图（预算分配比例）+ 策略要点列表
3. 使用与Dashboard/Create一致的TailwindCSS卡片样式（bg-card、border-border等class）
4. 使用 useWeeklyStats() 模式获取mock数据（在 api.ts 中新增 getStrategyData 函数）
5. 处理三种状态：加载中（spinner）、正常展示、空数据提示

样式参考：与 Dashboard.tsx 使用相同的卡片样式（bg-card rounded-xl shadow-sm border border-border p-6），保持设计语言一致。

mock数据结构：
{
  recommended_channels: [
    { channel: "TikTok Ads", rating: 5, daily_budget: 50, estimated_roas: "2.8-4.2x", reason: "产品年轻化、视觉冲击力强" },
    { channel: "Meta Ads", rating: 4, daily_budget: 30, estimated_roas: "2.0-3.5x", reason: "覆盖面广、兴趣定向精准" },
    { channel: "Google Ads", rating: 3, daily_budget: 20, estimated_roas: "1.5-2.8x", reason: "搜索意图强、适合长尾词" }
  ],
  budget_allocation: [
    { channel: "TikTok", value: 50 }, { channel: "Meta", value: 30 }, { channel: "Google", value: 20 }
  ],
  key_suggestions: ["优先投放TikTok", "A/B测试不同素材角度", "15-30秒短视频效果最佳"]
}
```

---

#### FE-3：Analytics数据中心页基础实现

**说明**：同Strategy页，当前是占位页。初赛阶段不需要完整数据分析功能，有一个展示"内容生产统计概览"的基础页即可。

**交付物**：
- `frontend/src/pages/Analytics.tsx` 重构
- 包含：本周内容生产数量（柱状图/卡片）、各平台内容分布（饼图）、最近生成任务列表

**提示词**：
```
你是CrossSell AI项目的前端开发。当前 Analytics.tsx 只是一个占位页面。

任务：实现Analytics数据中心页面的基础版本，使用mock数据。

功能要求：
1. 页面顶部：日期范围选择器（本周/本月/本季度，默认本周）
2. 统计概览行：4个数字卡片（总生成内容数、视频数、文案数、策略建议数）
3. 主内容区：
   - 左：各平台内容分布 Recharts饼图（TikTok/Instagram/YouTube Shorts/Facebook/Pinterest）
   - 右：最近生成任务列表（表格：产品名称 | 平台数 | 市场数 | 生成时间 | 状态）
4. 使用与Dashboard一致的卡片样式

mock数据在 frontend/src/mock/data.ts 中新增 getAnalyticsData 导出函数。

保持三个状态：加载中/正常/无数据。
```

---

#### FE-4：部署到线上可访问URL

**说明**：初赛提交时需要提供可访问的链接。当前只有本地开发环境，需要构建并部署。

**交付物**：
- 线上可访问URL（Vercel/Netlify/CloudStudio）
- 部署配置说明
- 确认前端指向正确的后端地址（如后端也部署，需要更新API地址）

**提示词**：
```
你是CrossSell AI项目的前端开发。项目需要在线上可访问，让评委能直接打开使用。

任务：将前端部署到线上。

步骤：
1. cd frontend && npm run build（确认构建无错误）
2. 在 frontend/ 根目录创建 vercel.json：
   {
     "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
   }
3. 部署到 Vercel（推荐，免费）：
   cd frontend && npx vercel --prod
   或 Netlify：直接拖拽 dist/ 文件夹到 netlify.com
   或 CloudStudio：按 cloudstudio-deploy skill 的指引
4. 如果当前阶段后端没有线上部署，前端的 VITE_API_BASE 可以暂时指向 localhost（或mock模式）
5. 记录部署URL，确保可以直接在浏览器访问

注意：如果是SPA，需要确保所有路由都重定向到 index.html（Vercel的vercel.json已处理）。
```

---

### 📐 产品经理

| # | 任务 | 优先级 | 预估工时 | 依赖 |
|----|------|:------:|:--------:|------|
| PM-1 | **Figma低保真原型设计** | 🔴 P0 | 6h | 无 |
| PM-2 | **初赛Idea文档初稿** | 🔴 P0 | 4h | PM-1原型设计开始后 |
| PM-3 | **产品方案文档定稿** | 🟡 P1 | 3h | PM-1完成后 |
| PM-4 | **真实卖家验证访谈** | 🟡 P1 | 3h | 无 |

---

#### PM-1：Figma低保真原型设计

**说明**：产品调研已完成（五重断裂模型、18竞品、MVP优先级），但还没有视觉原型。Figma原型是Idea文档的视觉支撑，也是前后端开发的对齐依据。

需要设计4个核心页面：工作台首页、内容生成页（三步骤）、投放策略页、数据中心页。

**交付物**：
- Figma文件链接（至少包含4个页面的低保真线框图）
- 关键交互标注（点击跳转、表单验证状态、进度动画说明）
- 设计规范：颜色（靛蓝 #6366f1 主色调）、字体（Inter）、卡片间距

**提示词**：
```
你是CrossSell AI项目的产品经理。我们已经完成了用户调研（"五重断裂"模型）和竞品分析（18个竞品），MVP功能优先级也已明确。

任务：设计4个核心页面的Figma低保真原型。

原型要求：
1. 设计4个核心页面（低保真线框图即可，不需要高保真视觉）：
   a. **工作台首页**：顶部统计卡片（本周生成数）+ 快速启动CTA按钮 + 最近任务列表
   b. **内容生成页**（核心）：Step 1 产品信息表单（名称/卖点/目标市场/平台选型）→ Step 2 生成进度条（4个步骤）→ Step 3 结果展示（Tab切换：短视频/文案矩阵/投放建议）
   c. **投放策略页**：产品选择器 + 渠道推荐卡片 + 预算分配饼图
   d. **数据中心页**：日期选择 + 统计概览 + 内容分布饼图 + 任务列表表格

2. 设计规范：
   - 主色调：靛蓝 #6366f1
   - 字体：Inter（Google Fonts）
   - 卡片样式：白色背景、圆角12px、阴影、灰边框
   - 左侧导航栏：240px宽，4个导航项（工作台/内容生成/投放策略/数据中心）
   - 支持亮色/暗色模式

3. 用户流程标注：
   - 标注"工作台 → 点击创建任务 → 内容生成页"的跳转关系
   - 标注表单验证态（空字段时的错误提示）
   - 标注进度步骤条的状态变化

4. 导出为Figma分享链接，设置查看权限为"任何有链接的人可查看"

参考：前端已有完整实现的 Dashboard.tsx 和 Create.tsx，但设计上可以参考其功能来画原型，不必1:1复刻代码样式。
```

---

#### PM-2：初赛Idea文档初稿

**说明**：这是Sprint最重要的交付物。大赛要求填写10项内容，产品负责其中第3-7项和第9-10项（第8项技术方案由后端提供）。

**交付物**：
- `deliverables/初赛Idea文档_v1.md`（按照大赛提交表单的10项结构，填充产品负责部分）
- 第3项：要解决的具体业务问题（基于五重断裂模型）
- 第4项：方案名称 = CrossSell AI — 跨境社媒内容引擎
- 第5项：一句话定义
- 第6项：核心功能清单（3-5个，按P0/P1标注）
- 第7项：方案亮点（创新点/效率提升/成本节约，附数据支撑）
- 第9项：当前作品完成阶段标注（结合原型和前端Demo）
- 第10项：附加材料链接占位（等前后端准备好后填入）

**提示词**：
```
你是CrossSell AI项目的产品经理。初赛作品提交截止日期是8月20日，我们需要准备好Idea文档。

大赛初赛提交表单要求填写10项内容。产品经理负责撰写其中第3-7项和第9-10项。

任务：撰写初赛Idea文档（产品负责部分）。

请基于已有调研资料撰写：

第3项 — 要解决的具体业务问题（一句话）：
基于"五重断裂"模型（ deliverables/product-strategy/user-discovery-crosssell-2026-07-16.md ），提炼一句清晰的话描述我们切入的核心痛点。示例格式："跨境品牌卖家面临内容产能黑洞——3人团队80个SKU需要月产320条视频但传统产能仅30条/月，同时多平台多语言本土化造成15-20倍重复工作量，导致整体社媒ROI持续低于行业水平。"

第4项 — 方案名称：
CrossSell AI — 跨境社媒内容引擎

第5项 — 一句话定义：
面向跨境品牌卖家，用AI将"产品卖点→多平台本土化内容→智能投流"全链路自动化，把社媒营销从"人海战术"变为"一人控全场"。核心价值：内容产能提升10-20倍，本土化转化率差距从3.8倍缩至1.5倍以内，综合营销成本降至传统方式的1/10。

第6项 — 核心功能清单（3-5个）：
参考 product-strategy 文档中的MVP优先级（P0/P1/P2），选择3-5个核心功能，每个功能配一句话说明。

第7项 — 方案亮点：
基于竞品分析（18个竞品三维矩阵），阐述我们的差异化优势。必须包含数据支撑（如本土化3.8倍转化差距、素材质量权重的30-40%等市场数据）。

第9项 — 当前作品完成阶段：
标注为"已有Demo原型"，附上前后端的实现情况简述。

第10项 — 附加材料链接：
占位即可，等前后端准备好后填入（GitHub仓库、部署URL、Figma链接等）。

输出文件：deliverables/初赛Idea文档_v1.md
```

---

#### PM-3：产品方案文档定稿

**说明**：将用户调研、竞品分析、MVP优先级合并为一份完整的产品方案文档，用于对内对齐和对外展示。

**交付物**：
- `deliverables/CrossSell_AI_产品方案文档_v1.md`
- 包含：项目背景 → 用户画像 → 痛点分析 → 解决方案 → 核心功能 → 竞品对比 → 路线图 → 商业模式展望

**提示词**：
```
你是CrossSell AI项目的产品经理。基于已有的用户调研和竞品分析，需要输出一份完整的产品方案文档。

任务：撰写完整的产品方案文档。

结构如下：
1. **项目背景**：全球社交电商$1.16万亿，TikTok Shop GMV 37倍增长，AI工具采用率78%
2. **用户画像**：中小跨境卖家（月GMV $5K-$500K），3-8人团队，80-200个SKU
3. **痛点分析**：五重断裂模型（简版，每个痛点2-3句话+关键数据）
4. **解决方案**：CrossSell AI 三步走（产品输入→AI工厂→多平台分发+智能投流）
5. **核心功能**：P0/P1/P2功能优先级 + 各功能一句话说明
6. **竞品对比**：提取 product-strategy 文档中的关键竞品（Navos/易蛙智能/Topview AI/getsleek），用对比表格展示
7. **技术路线图**：初赛（Idea+原型）→ 复赛（完整产品）→ 决赛（商业落地）
8. **商业模式展望**：Free tier + Pro subscription + Enterprise 三级定价设想

输入参考：deliverables/product-strategy/user-discovery-crosssell-2026-07-16.md
输出：deliverables/CrossSell_AI_产品方案文档_v1.md
```

---

#### PM-4：真实卖家验证访谈

**说明**：产品调研中的"五重断裂"模型是基于二手数据（社区帖子/行业报告），需要至少1-2位真实跨境卖家验证痛点优先级。这直接影响Idea文档中"问题定义清晰度"（评审权重25%）的可信度。

**交付物**：
- 访谈提纲（5-8个问题）
- 1-2份访谈记录摘要
- 如有痛点优先级修正，更新到产品方案文档中

**提示词**：
```
你是CrossSell AI项目的产品经理。我们已经通过二手数据构建了"五重断裂"用户痛点模型，但还需要真实卖家验证。

任务：设计和执行跨境卖家访谈验证。

步骤：
1. 设计访谈提纲（5-8个问题），聚焦验证：
   - 内容产能是否确实是最大瓶颈？（让卖家排序：产能/本土化/投放/素材生命周期/跨文化）
   - 卖家当前用什么工具组合做社媒营销？（ChatGPT + CapCut + ElevenLabs + Canva + Later？）
   - 单条视频从制作到发布耗时多久？月产多少条？
   - 对"一站式AI内容工厂"的付费意愿？
   - 最大的社媒平台是什么？最头疼的平台是什么？

2. 访谈渠道建议：
   - 赛事官方群里的跨境卖家
   - 知无不言社区/卖家之家论坛私信
   - 微信跨境卖家社群
   - 如果没有真人，至少找1个有跨境经验的朋友做proxy验证

3. 输出访谈记录摘要（不需要逐字稿，核心发现即可），格式：
   - 卖家公司类型/规模/主做市场
   - 痛点排序结果
   - 当前工具栈
   - 对我们方案的反馈
   - 关键quote（至少1条）

4. 如果有痛点优先级变化，告知团队调整MVP功能排序

输出：deliverables/product-strategy/卖家访谈摘要_2026-07-XX.md
```

---

## 📐 依赖关系图

```
Sprint 1 依赖链：

PM-1 (Figma原型) ──┬── PM-2 (Idea文档) ── PM-3 (方案定稿)
                   │
                   ├── FE-2 (Strategy页) ─── FE-3 (Analytics页)
                   │
                   └── (前后端视觉对齐参考)

PM-4 (卖家访谈) ────── (独立，不阻塞其他任务)

BE-1 (API Key验证) ─── BE-3 (联调适配) ─── FE-1 (接入真实API) ─── FE-4 (部署)
                         │
BE-2 (weekly-stats) ─────┤
                         │
BE-4 (错误码) ─────────── (不阻塞，可并行)
```

---

## ⏱️ Sprint时间线建议

```
7/17 ───── 7/20 ───── 7/25 ───── 7/31 ───── 8/5
  │          │          │          │          │
  ▼          ▼          ▼          ▼          ▼
BE-1 ████│
PM-4 ██████│
BE-2   ██│
PM-1 ████████████│
BE-4     ████│
BE-3         ██████│
FE-1             ████████│
PM-2         ████████│
FE-2 ████████████│
PM-3                  ██████│
FE-3                    ████│
FE-4                       ██│
```

---

> **Sprint Review 检查点：8月5日** — 届时确认Idea文档是否就绪、前后端是否可演示、是否有线上URL。
