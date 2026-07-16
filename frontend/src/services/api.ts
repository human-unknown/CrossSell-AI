import type { ProductInfo, GenerationResult, TaskRecord, WeeklyStats } from '../types'

// Base URL — 后续改为真实后端地址
const API_BASE = import.meta.env.VITE_API_BASE || '/api'

// ============ API 函数 ============
// 当前阶段使用 mock 数据，由 mock handler 拦截

import {
  mockGenerationResult,
  mockTasks,
  mockWeeklyStats,
  simulateProgress,
} from '../mock/data'
import type { GenerationProgress } from '../types'

// ---------- 触发内容生成 ----------
export async function triggerGeneration(productInfo: ProductInfo): Promise<{ taskId: string }> {
  // 真实接口：
  // const res = await axios.post(`${API_BASE}/generate`, productInfo)
  // return res.data

  // Mock:
  await delay(600)
  return { taskId: `task_${Date.now()}` }
}

// ---------- 查询生成进度（轮询用） ----------
export async function getTaskStatus(taskId: string): Promise<GenerationProgress> {
  // const res = await axios.get(`${API_BASE}/task/${taskId}/status`)
  // return res.data

  await delay(200)
  throw new Error('Mock: 进度请使用 simlateProgress 函数')
}

// ---------- 获取生成结果 ----------
export async function getTaskResult(taskId: string): Promise<GenerationResult> {
  // const res = await axios.get(`${API_BASE}/task/${taskId}/result`)
  // return res.data

  await delay(800)
  return { ...mockGenerationResult, taskId }
}

// ---------- 历史任务列表 ----------
export async function getTasks(page = 1, size = 10): Promise<{ tasks: TaskRecord[]; total: number }> {
  // const res = await axios.get(`${API_BASE}/tasks`, { params: { page, size } })
  // return res.data

  await delay(400)
  return {
    tasks: mockTasks.slice((page - 1) * size, page * size),
    total: mockTasks.length,
  }
}

// ---------- 周统计 ----------
export async function getWeeklyStats(): Promise<WeeklyStats> {
  await delay(300)
  return mockWeeklyStats
}

// ---------- 模拟进度（前端模拟用） ----------
export { simulateProgress }

// ---------- 工具 ----------
function delay(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms))
}
