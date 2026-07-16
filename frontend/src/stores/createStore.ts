import { create } from 'zustand'
import axios from 'axios'
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
  errorMessage: string | null
  setProgress: (progress: GenerationProgress) => void
  setIsGenerating: (value: boolean) => void

  // Step 3: Results
  result: GenerationResult | null
  setResult: (result: GenerationResult) => void

  // Actions
  goToStep: (step: 1 | 2 | 3) => void
  startGeneration: () => () => void // returns cancel function
  retryGeneration: () => void
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
            message: '获取生成结果失败，请点击重试',
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

  // 首次延迟 1 秒后查询，后续每 2 秒
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
  let savedProductInfo: ProductInfo | null = null

  return {
    currentStep: 1,
    productInfo: { ...defaultProductInfo },
    setProductInfo: (info) =>
      set((s) => ({ productInfo: { ...s.productInfo, ...info } })),
    taskId: null,
    progress: null,
    isGenerating: false,
    errorMessage: null,
    setProgress: (progress) => set({ progress }),
    setIsGenerating: (value) => set({ isGenerating: value }),
    result: null,
    setResult: (result) => set({ result }),
    goToStep: (step) => set({ currentStep: step }),

    // ======== 核心：启动生成流程 ========
    startGeneration: () => {
      const { productInfo } = get()

      // 保存产品信息（失败后重试用）
      savedProductInfo = { ...productInfo }

      set({
        isGenerating: true,
        errorMessage: null,
        currentStep: 2,
      })

      const isMock = getApiMode() === 'mock'

      if (isMock) {
        // ---------- Mock 模式 ----------
        cancelSimulation = simulateProgress(
          (prog) => set({ progress: prog }),
          async () => {
            set({ isGenerating: false })
            try {
              const taskId = `task_mock_${Date.now()}`
              const res = await getTaskResult(taskId)
              set({ result: res })
              const currentProgress = get().progress
              if (currentProgress) {
                set({ progress: { ...currentProgress, status: 'completed' } })
              }
              set({ currentStep: 3 })
            } catch (err) {
              console.error('[Store] Mock getTaskResult failed:', err)
              set({
                errorMessage: '获取结果失败，请重试',
                progress: get().progress
                  ? { ...get().progress!, status: 'failed', message: '获取结果失败，请重试' }
                  : null,
              })
            }
          }
        )
        return () => cancelSimulation?.()
      }

      // ---------- 真实 API 模式 ----------
      triggerGeneration(productInfo)
        .then(({ taskId }) => {
          set({ taskId })

          // 设置初始进度
          const initialProgress: GenerationProgress = {
            taskId,
            status: 'pending',
            steps: {
              script: 'waiting',
              voiceover: 'waiting',
              videoRender: 'waiting',
              copyOptimize: 'waiting',
            },
            message: '任务已提交，AI 正在分析产品信息...',
          }
          set({ progress: initialProgress })

          cancelPolling = startPolling(
            taskId,
            (prog) => set({ progress: prog }),
            (val) => set({ isGenerating: val }),
            (res) => set({ result: res }),
            (step) => set({ currentStep: step })
          )
        })
        .catch((err) => {
          console.error('[Store] Trigger generation failed:', err)
          const message =
            err instanceof Error
              ? err.message
              : axios.isAxiosError(err)
              ? err.response?.data?.detail || '服务器错误，请稍后重试'
              : '网络连接失败，请检查后端是否已启动'

          set({
            isGenerating: false,
            errorMessage: message,
            progress: {
              taskId: '',
              status: 'failed',
              steps: {
                script: 'error',
                voiceover: 'waiting',
                videoRender: 'waiting',
                copyOptimize: 'waiting',
              },
              message,
            },
          })
        })

      return () => cancelPolling?.()
    },

    // ======== 重试 ========
    retryGeneration: () => {
      // 先清理旧的轮询
      cancelPolling?.()
      cancelSimulation?.()
      cancelPolling = null
      cancelSimulation = null

      // 恢复保存的产品信息
      const info = savedProductInfo || get().productInfo
      if (info) {
        set({ productInfo: info })
      }

      // 重新启动（startGeneration 内部会赋值 cancelPolling）
      get().startGeneration()
    },

    // ======== 重置 ========
    reset: () => {
      cancelPolling?.()
      cancelSimulation?.()
      cancelPolling = null
      cancelSimulation = null
      savedProductInfo = null
      set({
        currentStep: 1,
        productInfo: { ...defaultProductInfo },
        progress: null,
        isGenerating: false,
        result: null,
        taskId: null,
        errorMessage: null,
      })
    },
  }
})
