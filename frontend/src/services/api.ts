import axios from 'axios'
import type { ProductInfo, GenerationProgress, GenerationResult, TaskRecord, WeeklyStats, StrategyData, AnalyticsData, TimeRange } from '../types'
import { toBackendRequest } from './adapter'
import {
  mockGenerationResult,
  mockTasks,
  mockWeeklyStats,
  mockStrategyData,
  mockAnalyticsData,
  simulateProgress,
} from '../mock/data'

// ============ 配置 ============

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api'
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

// 带超时的 axios 实例
const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// ============ 请求日志（开发调试用） ============

function logApi(method: string, url: string, data?: unknown) {
  if (import.meta.env.DEV) {
    console.log(`[API] ${method} ${url}`, data ? data : '')
  }
}

// ============ API 函数（真实 + mock fallback） ============

/**
 * 触发内容生成
 * POST /api/generate
 */
export async function triggerGeneration(
  productInfo: ProductInfo
): Promise<{ taskId: string }> {
  const url = '/generate'
  const backendData = toBackendRequest(productInfo)

  if (USE_MOCK) {
    return mockTriggerGeneration()
  }

  try {
    logApi('POST', url, backendData)
    const res = await api.post(url, backendData)
    // 后端返回 { taskId: string }
    return { taskId: res.data.taskId || res.data.task_id }
  } catch (err) {
    console.error('[API] triggerGeneration failed:', err)
    throw err  // 真实模式不降级，让调用方处理
  }
}

async function mockTriggerGeneration(): Promise<{ taskId: string }> {
  await delay(400)
  return { taskId: `task_mock_${Date.now()}` }
}

// ---------- 轮询生成进度 ----------

/**
 * 查询生成进度（用于轮询）
 * GET /api/task/{taskId}/status
 */
export async function getTaskStatus(
  taskId: string
): Promise<GenerationProgress> {
  const url = `/task/${taskId}/status`

  if (USE_MOCK) {
    throw new Error('MOCK_MODE: 请使用 simulateProgress')
  }

  try {
    const res = await api.get(url)
    return res.data as GenerationProgress
  } catch (err) {
    console.warn('[API] getTaskStatus failed:', err)
    throw err
  }
}

// ---------- 获取生成结果 ----------

/**
 * 获取任务生成结果
 * GET /api/task/{taskId}/result
 */
export async function getTaskResult(
  taskId: string
): Promise<GenerationResult> {
  const url = `/task/${taskId}/result`

  if (USE_MOCK) {
    return mockGetTaskResult(taskId)
  }

  try {
    logApi('GET', url)
    const res = await api.get(url)
    return res.data as GenerationResult
  } catch (err) {
    console.error('[API] getTaskResult failed:', err)
    throw err  // 真实模式不降级
  }
}

async function mockGetTaskResult(taskId: string): Promise<GenerationResult> {
  await delay(600)
  return { ...mockGenerationResult, taskId }
}

// ---------- 历史任务列表 ----------

/**
 * 获取历史任务列表
 * GET /api/tasks?page=1&size=10
 */
export async function getTasks(
  page = 1,
  size = 10
): Promise<{ tasks: TaskRecord[]; total: number }> {
  const url = '/tasks'

  if (USE_MOCK) {
    return mockGetTasks(page, size)
  }

  try {
    logApi('GET', `${url}?page=${page}&size=${size}`)
    const res = await api.get(url, { params: { page, size } })
    return res.data as { tasks: TaskRecord[]; total: number }
  } catch (err) {
    console.warn('[API] getTasks failed, using mock fallback:', err)
    return mockGetTasks(page, size)
  }
}

function mockGetTasks(page: number, size: number) {
  return {
    tasks: mockTasks.slice((page - 1) * size, page * size),
    total: mockTasks.length,
  }
}

// ---------- 周统计 ----------

/**
 * 获取本周统计
 * GET /api/stats/weekly
 */
export async function getWeeklyStats(): Promise<WeeklyStats> {
  const url = '/stats/weekly'

  if (USE_MOCK) {
    return mockGetWeeklyStats()
  }

  try {
    logApi('GET', url)
    const res = await api.get(url)
    return res.data as WeeklyStats
  } catch (err) {
    console.warn('[API] getWeeklyStats failed, falling back to mock:', err)
    return mockGetWeeklyStats()
  }
}

async function mockGetWeeklyStats(): Promise<WeeklyStats> {
  await delay(200)
  return mockWeeklyStats
}

// ---------- 投放策略 ----------

/**
 * 获取投放策略数据
 * GET /api/strategy?taskId=xxx（当前基于task查询，后端暂用mock）
 */
export async function getStrategyData(
  _taskId?: string
): Promise<StrategyData> {
  const url = '/strategy'

  if (USE_MOCK) {
    return mockGetStrategyData()
  }

  try {
    logApi('GET', url)
    const res = await api.get(url, { params: _taskId ? { taskId: _taskId } : {} })
    return res.data as StrategyData
  } catch (err) {
    console.warn('[API] getStrategyData failed, using mock fallback:', err)
    return mockGetStrategyData()
  }
}

async function mockGetStrategyData(): Promise<StrategyData> {
  await delay(350)
  return mockStrategyData
}

// ---------- 数据分析 ----------

/**
 * 获取数据分析数据
 * GET /api/analytics?timeRange=本周
 */
export async function getAnalyticsData(
  _timeRange: TimeRange = '本周'
): Promise<AnalyticsData> {
  const url = '/analytics'

  if (USE_MOCK) {
    return mockGetAnalyticsData()
  }

  try {
    logApi('GET', `${url}?timeRange=${encodeURIComponent(_timeRange)}`)
    const res = await api.get(url, { params: { timeRange: _timeRange } })
    return res.data as AnalyticsData
  } catch (err) {
    console.warn('[API] getAnalyticsData failed, falling back to mock:', err)
    return mockGetAnalyticsData()
  }
}

async function mockGetAnalyticsData(): Promise<AnalyticsData> {
  await delay(350)
  return mockAnalyticsData
}

// ---------- 模拟进度（纯前端 mock 用） ----------

/**
 * 模拟生成进度（仅 mock 模式使用）
 * 真实模式下使用 getTaskStatus 轮询
 */
export { simulateProgress }

// ---------- 工具导出 ----------

/**
 * 获取当前 API 模式
 */
export function getApiMode(): 'real' | 'mock' {
  return USE_MOCK ? 'mock' : 'real'
}

/**
 * 获取 API Base URL（调试用）
 */
export function getApiBase(): string {
  return API_BASE
}

function delay(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms))
}
