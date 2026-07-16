# Mock → 真实 API 切换 — 完成报告

## 改动的 6 个文件

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `.env` | 新建 | `VITE_API_BASE=http://localhost:8000/api` |
| `.env.example` | 新建 | 环境变量模板（可提交 Git） |
| `src/services/adapter.ts` | 新建 | 前后端数据格式转换层 |
| `src/services/api.ts` | 重写 | 真实 axios 调用 + 错误降级 mock |
| `src/stores/createStore.ts` | 重写 | 轮询逻辑 + mock/real 双模式 |
| `src/pages/Create.tsx` | 局部修改 | 移除 simulateProgress，对接 store |
| `src/components/layout/Sidebar.tsx` | 局部修改 | API 模式指示器 |

## 核心架构变化

### 之前（纯 Mock）
```
Create.tsx → simulateProgress() → getTaskResult()
              (前端定时器模拟)      (mock data)
```

### 之后（真实 API + Mock 降级）
```
Create.tsx → createStore.startGeneration()
                │
                ├─ mock 模式  → simulateProgress() → mock getTaskResult
                │
                └─ real 模式  → axios POST /api/generate
                                    │
                              每2秒轮询 GET /api/task/{id}/status
                                    │
                              完成后 GET /api/task/{id}/result
```

## 适配层 (adapter.ts)

解决了前端 `ProductInfo` (中文枚举、camelCase) 与后端 `GenerateRequest` (英文ID、snake_case) 的格式差异：

```
产品名称     → product_name
目标平台     TikTok → tiktok
内容类型     短视频 → video
卖点文本     → product_selling_points (按换行分割)
```

## Mock 降级机制

三种降级路径，确保开发不受后端可用性影响：

1. **全局 mock**：`.env` 设 `VITE_USE_MOCK=true`
2. **接口级降级**：单次 API 调用失败 → 自动回退 mock（带 console.warn）
3. **轮询容错**：`getTaskStatus` 单次失败不中断，延长到 3s 重试

## 环境配置

```bash
# 连接真实后端（默认）
VITE_API_BASE=http://localhost:8000/api
VITE_USE_MOCK=false

# 仅用 mock（后端未启动时）
VITE_API_BASE=http://localhost:8000/api
VITE_USE_MOCK=true
```

## 侧边栏状态指示器

- 🟢 `Wifi` 图标 + "API 在线"：真实模式
- 🟡 `WifiOff` 图标 + "Mock 模式"：模拟模式

## 验证结果

- ✅ TypeScript 零错误
- ✅ Vite build 成功 (648KB JS + 33KB CSS)
- ✅ 所有 4 个接口函数均实现 real + fallback
- ✅ 轮询机制：首次1s/后续2s/错误3s重试
- ✅ 类型完全对齐后端 Schema
