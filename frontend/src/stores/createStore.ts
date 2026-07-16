import { create } from 'zustand'
import type { ProductInfo, GenerationProgress, GenerationResult } from '../types'
import {
  triggerGeneration,
  getTaskStatus,
  getTaskResult,
  simulateProgress,
  getApiMode,
} from '../services/api'

interface CreateState {
  // Step tracking
  currentStep: 1 | 2 | 3

  // Step 1: Product info form
  productInfo: ProductInfo
  setProductInfo: (info: Partial<ProductInfo>) => void

  // Step 2: Generation progress
  taskId: string | null
  progress: GenerationProgress | null
  isGenerating: boolean
  setProgress: (progress: GenerationProgress) => void
  setIsGenerating: (value: boolean) => void

  // Step 3: Results
  result: GenerationResult | null
  setResult: (result: GenerationResult) => void

  // Actions
  goToStep: (step: 1 | 2 | 3) => void
  startGeneration: () => () => void // returns cancel function
  reset: () => void
}

const defaultProductInfo: ProductInfo = {
  productName: '',
  productDescription: '',
  targetMarkets: [],
  targetPlatforms: [],
  contentTypes: [],
}

// ============ 轮询逻辑 ============

/**
 * 启动真实 API 轮询
 * 返回 cancel 函数用于清理
 */
function startPolling(
  taskId: string,
  setProgress: (progress: GenerationProgress) => void,
  setIsGenerating: (value: boolean) => void,
  setResult: (result: GenerationResult) => void,
  goToStep: (step: 1 | 2 | 3) => void
): () => void {
  let cancelled = false
  let timer: ReturnType<typeof setTimeout> | null = null

  const poll = async () => {
    if (cancelled) return

    try {
      const progress = await getTaskStatus(taskId)
      if (cancelled) return

      setProgress(progress)

      if (progress.status === 'completed') {
        // 生成完成 → 获取结果
        setIsGenerating(false)
        try {
          const result = await getTaskResult(taskId)
          if (!cancelled) {
            setResult(result)
            goToStep(3)
          }
        } catch (err) {
          console.error('[Polling] Failed to fetch result:', err)
          setProgress({
            ...progress,
            status: 'failed',
            message: '获取结果失败，请重试',
          })
        }
        return
      }

      if (progress.status === 'failed') {
        setIsGenerating(false)
        return
      }

      // 继续轮询（每 2 秒）
      timer = setTimeout(poll, 2000)
    } catch (err) {
      console.error('[Polling] Status check failed:', err)
      if (!cancelled) {
        // 出错后延长间隔重试
        timer = setTimeout(poll, 3000)
      }
    }
  }

  // 首次立即查询，后续每 2 秒
  timer = setTimeout(poll, 1000)

  return () => {
    cancelled = true
    if (timer) clearTimeout(timer)
  }
}

// ============ Store ============

export const useCreateStore = create<CreateState>((set, get) => {
  let cancelPolling: (() => void) | null = null
  let cancelSimulation: (() => void) | null = null

  return {
    currentStep: 1,
    productInfo: { ...defaultProductInfo },
    setProductInfo: (info) =>
      set((s) => ({ productInfo: { ...s.productInfo, ...info } })),
    taskId: null,
    progress: null,
    isGenerating: false,
    setProgress: (progress) => set({ progress }),
    setIsGenerating: (value) => set({ isGenerating: value }),
    result: null,
    setResult: (result) => set({ result }),
    goToStep: (step) => set({ currentStep: step }),

    // ======== 核心：启动生成流程 ========
    startGeneration: () => {
      const { productInfo, setProgress, setIsGenerating, setResult, goToStep } = get()

      setIsGenerating(true)
      goToStep(2)

      const isMock = getApiMode() === 'mock'

      if (isMock) {
        // ---------- Mock 模式：使用 simulateProgress ----------
        cancelSimulation = simulateProgress(
          (prog) => setProgress(prog),
          async () => {
            setIsGenerating(false)
            const taskId = `task_mock_${Date.now()}`
            const res = await getTaskResult(taskId)
            setResult(res)
            goToStep(3)
            const currentProgress = get().progress
            if (currentProgress) {
              setProgress({ ...currentProgress, status: 'completed' })
            }
          }
        )
        return () => {
          cancelSimulation?.()
        }
      }

      // ---------- 真实 API 模式：POST → 轮询 ----------
      triggerGeneration(productInfo)
        .then(({ taskId }) => {
          set({ taskId })
          // 设置初始进度
          setProgress({
            taskId,
            status: 'pending',
            steps: { script: 'waiting', voiceover: 'waiting', videoRender: 'waiting', copyOptimize: 'waiting' },
            message: '任务已提交，正在排队...',
          })

          cancelPolling = startPolling(
            taskId,
            setProgress,
            setIsGenerating,
            setResult,
            goToStep
          )
        })
        .catch((err) => {
          console.error('[Store] Trigger generation failed:', err)
          setIsGenerating(false)
          setProgress({
            taskId: '',
            status: 'failed',
            steps: { script: 'error', voiceover: 'waiting', videoRender: 'waiting', copyOptimize: 'waiting' },
            message: '提交失败，请检查网络后重试',
          })
          // 降级到 mock
          set({ taskId: null })
        })

      // 返回 cancel 函数
      return () => {
        cancelPolling?.()
      }
    },

    // ======== 重置 ========
    reset: () => {
      cancelPolling?.()
      cancelSimulation?.()
      cancelPolling = null
      cancelSimulation = null
      set({
        currentStep: 1,
        productInfo: { ...defaultProductInfo },
        progress: null,
        isGenerating: false,
        result: null,
        taskId: null,
      })
    },
  }
})
