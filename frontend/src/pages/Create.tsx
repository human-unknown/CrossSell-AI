import { useState, useEffect, useRef } from 'react'
import {
  ArrowLeft,
  Sparkles,
  CheckCircle2,
  Loader2,
  Clock,
  Play,
  Pause,
  Download,
  Copy,
  Check,
  Maximize2,
  ChevronRight,
  Globe,
  FileText,
  Target,
  Video,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react'
import { useCreateStore } from '../stores/createStore'
import type {
  TargetMarket,
  TargetPlatform,
  ContentType,
  GenerationResult,
  VideoResult,
} from '../types'
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'

// ============ 选项数据 ============

const MARKET_OPTIONS: { value: TargetMarket; label: string; flag: string }[] = [
  { value: '美国', label: '美国', flag: '🇺🇸' },
  { value: '英国', label: '英国', flag: '🇬🇧' },
  { value: '德国', label: '德国', flag: '🇩🇪' },
  { value: '日本', label: '日本', flag: '🇯🇵' },
  { value: '东南亚', label: '东南亚', flag: '🌏' },
  { value: '法国', label: '法国', flag: '🇫🇷' },
  { value: '巴西', label: '巴西', flag: '🇧🇷' },
  { value: '印度', label: '印度', flag: '🇮🇳' },
]

const PLATFORM_OPTIONS: { value: TargetPlatform; label: string; icon: string }[] = [
  { value: 'TikTok', label: 'TikTok', icon: '🎵' },
  { value: 'Instagram', label: 'Instagram', icon: '📸' },
  { value: 'YouTube Shorts', label: 'YouTube Shorts', icon: '▶️' },
  { value: 'Facebook', label: 'Facebook', icon: '📘' },
  { value: 'Pinterest', label: 'Pinterest', icon: '📌' },
]

const CONTENT_TYPE_OPTIONS: { value: ContentType; label: string; icon: string }[] = [
  { value: '短视频', label: '短视频', icon: '🎬' },
  { value: '社媒文案', label: '社媒文案', icon: '📝' },
]

// ============ Main Page ============

export default function Create() {
  const {
    currentStep,
    productInfo,
    setProductInfo,
    progress,
    isGenerating,
    errorMessage,
    result,
    goToStep,
    startGeneration,
    retryGeneration,
    reset,
  } = useCreateStore()

  const cancelRef = useRef<(() => void) | null>(null)

  // Clean up on unmount
  useEffect(() => {
    return () => {
      cancelRef.current?.()
    }
  }, [])

  const handleStartGenerate = () => {
    if (!productInfo.productName.trim()) return
    if (productInfo.targetMarkets.length === 0) return
    if (productInfo.targetPlatforms.length === 0) return
    if (productInfo.contentTypes.length === 0) return

    // Store handles both real API polling & mock simulation internally
    const cancel = startGeneration()
    cancelRef.current = cancel
  }

  const handleReset = () => {
    cancelRef.current?.()
    reset()
  }

  return (
    <div className="animate-fade-in-up">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        {currentStep > 1 && (
          <button
            onClick={handleReset}
            className="p-3 rounded-lg hover:bg-[var(--color-bg)] transition-colors text-[var(--color-text-muted)]"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
        )}
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text)]">
            内容生成
          </h1>
          <p className="text-[var(--color-text-muted)] text-sm mt-0.5">
            AI驱动，一键生成多平台本土化营销内容
          </p>
        </div>
      </div>

      {/* Step Indicator */}
      <StepIndicator currentStep={currentStep} />

      {/* Step Content */}
      <div className="mt-6">
        {currentStep === 1 && (
          <Step1ProductForm
            productInfo={productInfo}
            onChange={setProductInfo}
            onSubmit={handleStartGenerate}
          />
        )}
        {currentStep === 2 && (
          <Step2Progress
            progress={progress}
            isGenerating={isGenerating}
            errorMessage={errorMessage}
            onRetry={retryGeneration}
            onReset={handleReset}
          />
        )}
        {currentStep === 3 && result && (
          <Step3Results result={result} />
        )}
        {currentStep === 3 && !result && (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <Loader2 className="w-8 h-8 text-[var(--color-primary)] animate-spin mx-auto mb-3" />
              <p className="text-sm text-[var(--color-text-muted)]">正在加载结果...</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// ============ Step Indicator ============

function StepIndicator({ currentStep }: { currentStep: number }) {
  const steps = [
    { num: 1, label: '产品信息' },
    { num: 2, label: '生成进度' },
    { num: 3, label: '查看结果' },
  ]

  return (
    <div className="flex items-center gap-0">
      {steps.map((step, i) => (
        <div key={step.num} className="flex items-center">
          <div
            className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all duration-300 ${
              currentStep === step.num
                ? 'bg-[var(--color-primary)] text-white shadow-md shadow-purple-500/20'
                : currentStep > step.num
                ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
                : 'bg-[var(--color-bg)] text-[var(--color-text-muted)]'
            }`}
          >
            {currentStep > step.num ? (
              <CheckCircle2 className="w-4 h-4" />
            ) : (
              <span
                className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold ${
                  currentStep === step.num
                    ? 'bg-white/20'
                    : 'bg-[var(--color-border)]'
                }`}
              >
                {step.num}
              </span>
            )}
            {step.label}
          </div>
          {i < steps.length - 1 && (
            <ChevronRight className="w-4 h-4 text-[var(--color-border)] mx-1 shrink-0" />
          )}
        </div>
      ))}
    </div>
  )
}

// ============ Step 1: Product Form ============

function Step1ProductForm({
  productInfo,
  onChange,
  onSubmit,
}: {
  productInfo: ReturnType<typeof useCreateStore.getState>['productInfo']
  onChange: (info: Partial<ReturnType<typeof useCreateStore.getState>['productInfo']>) => void
  onSubmit: () => void
}) {
  const toggleItem = <T,>(arr: T[], item: T): T[] =>
    arr.includes(item) ? arr.filter((i) => i !== item) : [...arr, item]

  const canSubmit =
    productInfo.productName.trim() &&
    productInfo.targetMarkets.length > 0 &&
    productInfo.targetPlatforms.length > 0 &&
    productInfo.contentTypes.length > 0

  return (
    <div className="max-w-3xl space-y-6">
      {/* Product Name */}
      <div className="rounded-xl bg-[var(--color-bg-card)] border border-[var(--color-border)] p-6">
        <label className="block text-sm font-semibold text-[var(--color-text)] mb-2">
          产品名称 <span className="text-[var(--color-danger)]">*</span>
        </label>
        <input
          type="text"
          value={productInfo.productName}
          onChange={(e) => onChange({ productName: e.target.value })}
          placeholder="例如：便携式蓝牙音箱、瑜伽运动水壶..."
          className="w-full px-4 py-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent transition-all"
        />
      </div>

      {/* Product Description */}
      <div className="rounded-xl bg-[var(--color-bg-card)] border border-[var(--color-border)] p-6">
        <label className="block text-sm font-semibold text-[var(--color-text)] mb-2">
          产品简介 / 核心卖点
        </label>
        <textarea
          value={productInfo.productDescription}
          onChange={(e) => onChange({ productDescription: e.target.value })}
          rows={4}
          placeholder="描述产品的核心卖点、特色功能、使用场景...&#10;例如：IPX7级防水、12小时超长续航、重低音增强技术、轻便随身..."
          className="w-full px-4 py-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent transition-all resize-none"
        />
      </div>

      {/* Target Markets */}
      <div className="rounded-xl bg-[var(--color-bg-card)] border border-[var(--color-border)] p-6">
        <label className="block text-sm font-semibold text-[var(--color-text)] mb-3">
          目标市场 <span className="text-[var(--color-danger)]">*</span>
        </label>
        <div className="flex flex-wrap gap-2">
          {MARKET_OPTIONS.map((m) => {
            const selected = productInfo.targetMarkets.includes(m.value)
            return (
              <button
                key={m.value}
                onClick={() =>
                  onChange({
                    targetMarkets: toggleItem(productInfo.targetMarkets, m.value),
                  })
                }
                className={`px-4 py-2 rounded-lg text-sm font-medium border transition-all duration-200 ${
                  selected
                    ? 'bg-[var(--color-primary)] text-white border-[var(--color-primary)] shadow-md'
                    : 'border-[var(--color-border)] text-[var(--color-text)] hover:border-[var(--color-primary)] hover:text-[var(--color-primary)]'
                }`}
              >
                {m.flag} {m.label}
              </button>
            )
          })}
        </div>
      </div>

      {/* Target Platforms */}
      <div className="rounded-xl bg-[var(--color-bg-card)] border border-[var(--color-border)] p-6">
        <label className="block text-sm font-semibold text-[var(--color-text)] mb-3">
          目标平台 <span className="text-[var(--color-danger)]">*</span>
        </label>
        <div className="flex flex-wrap gap-2">
          {PLATFORM_OPTIONS.map((p) => {
            const selected = productInfo.targetPlatforms.includes(p.value)
            return (
              <button
                key={p.value}
                onClick={() =>
                  onChange({
                    targetPlatforms: toggleItem(
                      productInfo.targetPlatforms,
                      p.value
                    ),
                  })
                }
                className={`px-4 py-2 rounded-lg text-sm font-medium border transition-all duration-200 ${
                  selected
                    ? 'bg-[var(--color-primary)] text-white border-[var(--color-primary)] shadow-md'
                    : 'border-[var(--color-border)] text-[var(--color-text)] hover:border-[var(--color-primary)] hover:text-[var(--color-primary)]'
                }`}
              >
                {p.icon} {p.label}
              </button>
            )
          })}
        </div>
      </div>

      {/* Content Types */}
      <div className="rounded-xl bg-[var(--color-bg-card)] border border-[var(--color-border)] p-6">
        <label className="block text-sm font-semibold text-[var(--color-text)] mb-3">
          内容类型 <span className="text-[var(--color-danger)]">*</span>
        </label>
        <div className="flex flex-wrap gap-2">
          {CONTENT_TYPE_OPTIONS.map((ct) => {
            const selected = productInfo.contentTypes.includes(ct.value)
            return (
              <button
                key={ct.value}
                onClick={() =>
                  onChange({
                    contentTypes: toggleItem(
                      productInfo.contentTypes,
                      ct.value
                    ),
                  })
                }
                className={`px-4 py-2 rounded-lg text-sm font-medium border transition-all duration-200 ${
                  selected
                    ? 'bg-[var(--color-primary)] text-white border-[var(--color-primary)] shadow-md'
                    : 'border-[var(--color-border)] text-[var(--color-text)] hover:border-[var(--color-primary)] hover:text-[var(--color-primary)]'
                }`}
              >
                {ct.icon} {ct.label}
              </button>
            )
          })}
        </div>
      </div>

      {/* Submit */}
      <button
        onClick={onSubmit}
        disabled={!canSubmit}
        className="w-full py-4 rounded-xl text-lg font-bold transition-all duration-300 flex items-center justify-center gap-2
          enabled:bg-gradient-to-r enabled:from-[var(--color-primary)] enabled:to-purple-500
          enabled:text-white enabled:hover:shadow-xl enabled:hover:scale-[1.01]
          enabled:active:scale-[0.99]
          disabled:bg-[var(--color-border)] disabled:text-[var(--color-text-muted)] disabled:cursor-not-allowed"
      >
        <Sparkles className="w-5 h-5" />
        开始生成
      </button>
    </div>
  )
}

// ============ Step 2: Progress ============

const STEP_LIST = [
  { key: 'script', label: '脚本生成', detail: 'AI分析产品卖点，生成多平台适配脚本' },
  { key: 'voiceover', label: '配音合成', detail: '多语种AI配音，本土化语音合成' },
  { key: 'videoRender', label: '视频渲染', detail: '智能匹配素材，自动剪辑合成视频' },
  { key: 'copyOptimize', label: '文案优化', detail: '平台风格适配，关键词优化' },
] as const

function Step2Progress({
  progress,
  isGenerating,
  errorMessage,
  onRetry,
  onReset,
}: {
  progress: ReturnType<typeof useCreateStore.getState>['progress']
  isGenerating: boolean
  errorMessage: string | null
  onRetry: () => void
  onReset: () => void
}) {
  const isFailed = progress?.status === 'failed'

  return (
    <div className="max-w-2xl mx-auto py-8">
      {/* Status Icon */}
      <div className="flex justify-center mb-10">
        <div className="relative">
          <div
            className={`w-24 h-24 rounded-2xl flex items-center justify-center transition-all duration-500 ${
              isFailed
                ? 'bg-gradient-to-br from-red-500 to-rose-500 shadow-lg shadow-red-500/20'
                : isGenerating
                ? 'bg-gradient-to-br from-[var(--color-primary)] to-purple-500 animate-pulse-glow'
                : 'bg-gradient-to-br from-emerald-500 to-teal-500'
            }`}
          >
            {isFailed ? (
              <AlertTriangle className="w-12 h-12 text-white" />
            ) : isGenerating ? (
              <Loader2 className="w-12 h-12 text-white animate-spin" />
            ) : (
              <CheckCircle2 className="w-12 h-12 text-white" />
            )}
          </div>
        </div>
      </div>

      {/* Status Message */}
      <p
        className={`text-center text-lg font-medium mb-4 ${
          isFailed ? 'text-[var(--color-danger)]' : 'text-[var(--color-text)]'
        }`}
      >
        {progress?.message || (isGenerating ? '准备中...' : '生成完成')}
      </p>

      {/* Error Actions */}
      {isFailed && (
        <div className="flex items-center justify-center gap-3 mb-8">
          <button
            onClick={onRetry}
            className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-gradient-to-r from-[var(--color-primary)] to-purple-500 text-white text-sm font-medium hover:shadow-lg hover:scale-[1.02] transition-all duration-200"
          >
            <RefreshCw className="w-4 h-4" />
            重试
          </button>
          <button
            onClick={onReset}
            className="flex items-center gap-2 px-5 py-2.5 rounded-lg border border-[var(--color-border)] text-[var(--color-text-muted)] text-sm font-medium hover:text-[var(--color-text)] hover:border-[var(--color-text-muted)] transition-all duration-200"
          >
            <ArrowLeft className="w-4 h-4" />
            返回修改
          </button>
        </div>
      )}

      {/* Error Detail (axios error only) */}
      {isFailed && errorMessage && (
        <div className="mb-6 p-4 rounded-lg bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800/30">
          <p className="text-sm text-red-700 dark:text-red-400 break-all">
            {errorMessage}
          </p>
        </div>
      )}

      {/* Progress Steps */}
      <div className="space-y-0">
        {STEP_LIST.map((step, i) => {
          const hasStep = progress?.steps && step.key in progress.steps
          if (import.meta.env.DEV && progress?.steps && !hasStep) {
            console.warn(
              `[Step2Progress] 步骤键 "${step.key}" 不在后端返回的 steps 中。` +
              `后端返回的键: [${Object.keys(progress.steps).join(', ')}]`
            )
          }
          const status = hasStep ? progress!.steps[step.key] : 'waiting'
          return (
            <div key={step.key} className="relative flex items-start gap-4">
              {/* Connector line */}
              {i < STEP_LIST.length - 1 && (
                <div className="absolute left-[15px] top-10 bottom-0 w-0.5 bg-[var(--color-border)]" />
              )}

              {/* Status Icon */}
              <div
                className={`relative z-10 w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-1 transition-all duration-500 ${
                  status === 'completed'
                    ? 'bg-emerald-500 text-white'
                    : status === 'active'
                    ? 'bg-[var(--color-primary)] text-white animate-pulse-glow'
                    : status === 'error'
                    ? 'bg-red-500 text-white'
                    : 'bg-[var(--color-border)] text-[var(--color-text-muted)]'
                }`}
              >
                {status === 'completed' ? (
                  <CheckCircle2 className="w-5 h-5" />
                ) : status === 'active' ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : status === 'error' ? (
                  <AlertTriangle className="w-4 h-4" />
                ) : (
                  <Clock className="w-4 h-4" />
                )}
              </div>

              {/* Content */}
              <div className={`pb-8 flex-1 ${i === STEP_LIST.length - 1 ? 'pb-0' : ''}`}>
                <p
                  className={`font-medium transition-colors duration-300 ${
                    status === 'completed'
                      ? 'text-emerald-600 dark:text-emerald-400'
                      : status === 'active'
                      ? 'text-[var(--color-primary)]'
                      : status === 'error'
                      ? 'text-red-600 dark:text-red-400'
                      : 'text-[var(--color-text-muted)]'
                  }`}
                >
                  {step.label}
                </p>
                <p className="text-sm text-[var(--color-text-muted)] mt-0.5">
                  {step.detail}
                </p>
                {status === 'active' && (
                  <div className="mt-2 h-1.5 w-full bg-[var(--color-border)] rounded-full overflow-hidden">
                    <div className="h-full bg-[var(--color-primary)] rounded-full animate-shimmer" />
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ============ Step 3: Results ============

function Step3Results({ result }: { result: GenerationResult }) {
  const [activeTab, setActiveTab] = useState<'videos' | 'copies' | 'strategy'>(
    result.videos.length > 0 ? 'videos' : result.copies.length > 0 ? 'copies' : 'strategy'
  )

  return (
    <div className="space-y-6">
      {/* Success Banner */}
      <div className="rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 p-4 text-white flex items-center gap-3">
        <CheckCircle2 className="w-6 h-6 shrink-0" />
        <div>
          <p className="font-semibold">内容生成完成！</p>
          <p className="text-sm text-white/80">
            已生成 {result.videos.length} 个视频 + {result.copies.length} 条文案 + 投放策略建议
          </p>
        </div>
      </div>

      {/* Tab Switcher */}
      <div className="flex gap-1 bg-[var(--color-bg)] rounded-lg p-1 w-fit">
        {result.videos.length > 0 && (
          <TabButton
            active={activeTab === 'videos'}
            onClick={() => setActiveTab('videos')}
            icon={Video}
            label="短视频"
            count={result.videos.length}
          />
        )}
        {result.copies.length > 0 && (
          <TabButton
            active={activeTab === 'copies'}
            onClick={() => setActiveTab('copies')}
            icon={FileText}
            label="文案矩阵"
            count={result.copies.length}
          />
        )}
        <TabButton
          active={activeTab === 'strategy'}
          onClick={() => setActiveTab('strategy')}
          icon={Target}
          label="投放建议"
        />
      </div>

      {/* Tab Content */}
      {activeTab === 'videos' && <VideoTab videos={result.videos} />}
      {activeTab === 'copies' && <CopyTab copies={result.copies} />}
      {activeTab === 'strategy' && <StrategyTab strategy={result.strategy} />}
    </div>
  )
}

function TabButton({
  active,
  onClick,
  icon: Icon,
  label,
  count,
}: {
  active: boolean
  onClick: () => void
  icon: React.ComponentType<{ className?: string }>
  label: string
  count?: number
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
        active
          ? 'bg-[var(--color-bg-card)] text-[var(--color-text)] shadow-sm'
          : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'
      }`}
    >
      <Icon className="w-4 h-4" />
      {label}
      {count !== undefined && (
        <span className="ml-0.5 text-xs bg-[var(--color-primary)] text-white px-1.5 py-0.5 rounded-full">
          {count}
        </span>
      )}
    </button>
  )
}

// ============ Video Tab ============

function VideoTab({ videos }: { videos: VideoResult[] }) {
  const [activePlatform, setActivePlatform] = useState(videos[0]?.platform || 'TikTok')
  const [isPlaying, setIsPlaying] = useState(false)
  const [videoError, setVideoError] = useState(false)
  const videoRef = useRef<HTMLVideoElement>(null)

  // 切换平台时重置错误状态
  useEffect(() => setVideoError(false), [activePlatform])

  const currentVideo = videos.find((v) => v.platform === activePlatform) || videos[0]

  const togglePlay = () => {
    if (!videoRef.current) return
    if (isPlaying) {
      videoRef.current.pause()
    } else {
      videoRef.current.play()
    }
    setIsPlaying(!isPlaying)
  }

  const handleFullscreen = () => {
    videoRef.current?.requestFullscreen()
  }

  if (!currentVideo) return null

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Video Player */}
      <div className="lg:col-span-2 rounded-xl bg-[var(--color-bg-card)] border border-[var(--color-border)] overflow-hidden">
        <div className="relative bg-black aspect-video flex items-center justify-center group">
          {videoError ? (
            <div className="text-center text-white/70 p-4">
              <AlertTriangle className="w-10 h-10 mx-auto mb-2 opacity-50" />
              <p className="text-sm">视频加载失败</p>
              <p className="text-xs text-white/40 mt-1">Mock 模式下示例视频不可用时出现此提示</p>
            </div>
          ) : (
            <>
          <video
            ref={videoRef}
            src={currentVideo.url}
            className="w-full h-full object-contain"
            onEnded={() => setIsPlaying(false)}
            onPlay={() => setIsPlaying(true)}
            onPause={() => setIsPlaying(false)}
            onError={() => { setIsPlaying(false); setVideoError(true) }}
          />
          {/* Play overlay */}
          {!isPlaying && (
            <button
              onClick={togglePlay}
              className="absolute inset-0 flex items-center justify-center bg-black/30 group-hover:bg-black/40 transition-colors"
            >
              <div className="w-16 h-16 rounded-full bg-white/90 flex items-center justify-center shadow-xl hover:scale-105 transition-transform">
                <Play className="w-7 h-7 text-[var(--color-primary)] ml-1" />
              </div>
            </button>
          )}
          {/* Controls bar */}
          <div className="absolute bottom-0 left-0 right-0 p-3 bg-gradient-to-t from-black/70 to-transparent flex items-center justify-between opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={togglePlay}
              className="text-white p-2 rounded-full hover:bg-white/20 transition-colors"
            >
              {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
            </button>
            <div className="flex items-center gap-2">
              <button
                onClick={handleFullscreen}
                className="text-white p-2 rounded-full hover:bg-white/20 transition-colors"
              >
                <Maximize2 className="w-4 h-4" />
              </button>
              <a
                href={currentVideo.url}
                download
                className="text-white p-2 rounded-full hover:bg-white/20 transition-colors"
              >
                <Download className="w-4 h-4" />
              </a>
            </div>
          </div>
            </>
          )}
        </div>
        <div className="p-4">
          <h3 className="font-medium text-[var(--color-text)]">
            {currentVideo.title}
          </h3>
          <p className="text-sm text-[var(--color-text-muted)] mt-0.5">
            {currentVideo.platform} · {currentVideo.duration}秒
          </p>
        </div>
      </div>

      {/* Platform Switcher */}
      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-[var(--color-text-muted)] uppercase tracking-wide mb-3">
          平台适配版本
        </h3>
        {videos.map((v) => (
          <button
            key={v.id}
            onClick={() => setActivePlatform(v.platform)}
            className={`w-full text-left p-3 rounded-lg border transition-all duration-200 ${
              activePlatform === v.platform
                ? 'border-[var(--color-primary)] bg-[var(--color-primary)]/5'
                : 'border-[var(--color-border)] hover:border-[var(--color-text-muted)] bg-[var(--color-bg-card)]'
            }`}
          >
            <div className="flex items-center gap-2">
              <Globe className="w-4 h-4 text-[var(--color-text-muted)]" />
              <span className="font-medium text-sm text-[var(--color-text)]">{v.platform}版</span>
              {activePlatform === v.platform && (
                <span className="ml-auto text-xs text-[var(--color-primary)] font-medium">
                  当前
                </span>
              )}
            </div>
            <p className="text-xs text-[var(--color-text-muted)] mt-1 truncate">
              {v.duration}秒 · {v.title}
            </p>
          </button>
        ))}
      </div>
    </div>
  )
}

// ============ Copy Tab ============

function CopyTab({ copies }: { copies: GenerationResult['copies'] }) {
  const platformIcons: Record<string, string> = {
    TikTok: '🎵',
    Instagram: '📸',
    'YouTube Shorts': '▶️',
    Facebook: '📘',
    Pinterest: '📌',
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {copies.map((copy) => (
        <CopyCard
          key={copy.id}
          copy={copy}
          icon={platformIcons[copy.platform] || '🌐'}
        />
      ))}
    </div>
  )
}

function CopyCard({
  copy,
  icon,
}: {
  copy: GenerationResult['copies'][number]
  icon: string
}) {
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (!copied) return
    const timer = setTimeout(() => setCopied(false), 2000)
    return () => clearTimeout(timer)
  }, [copied])

  const handleCopy = async () => {
    const text = `${copy.content}\n\n${copy.hashtags.map((t) => '#' + t).join(' ')}`
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
    } catch {
      // Clipboard API 不可用（HTTP 环境/权限被拒），静默降级
      console.warn('[CopyCard] clipboard.writeText failed')
    }
  }

  return (
    <div className="rounded-xl bg-[var(--color-bg-card)] border border-[var(--color-border)] p-5 hover:shadow-md transition-shadow flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-xl">{icon}</span>
          <span className="font-semibold text-[var(--color-text)]">{copy.platform}</span>
          <span className="text-xs text-[var(--color-text-muted)]">
            {copy.characterCount}字
          </span>
        </div>
        <button
          onClick={handleCopy}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 ${
            copied
              ? 'bg-emerald-500 text-white'
              : 'bg-[var(--color-bg)] text-[var(--color-text-muted)] hover:text-[var(--color-primary)] hover:bg-[var(--color-primary)]/10'
          }`}
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5" />
              已复制
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              一键复制
            </>
          )}
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 rounded-lg bg-[var(--color-bg)] p-4 text-sm text-[var(--color-text)] whitespace-pre-wrap leading-relaxed">
        {copy.content}
      </div>

      {/* Hashtags */}
      <div className="flex flex-wrap gap-1.5 mt-3">
        {copy.hashtags.map((tag) => (
          <span
            key={tag}
            className="text-xs px-2 py-0.5 rounded-full bg-[var(--color-primary)]/10 text-[var(--color-primary)] font-medium"
          >
            #{tag}
          </span>
        ))}
      </div>
    </div>
  )
}

// ============ Strategy Tab ============

function StrategyTab({ strategy }: { strategy: GenerationResult['strategy'] }) {
  const COLORS = ['#6366f1', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6']

  const pieData = strategy.budgetAllocation.map((item, i) => ({
    name: item.platform,
    value: item.percentage,
    color: COLORS[i % COLORS.length],
  }))

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Pie Chart */}
      <div className="rounded-xl bg-[var(--color-bg-card)] border border-[var(--color-border)] p-6">
        <h3 className="font-semibold text-[var(--color-text)] mb-4">
          建议预算分配
        </h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={90}
                paddingAngle={4}
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  borderRadius: '12px',
                  border: '1px solid var(--color-border)',
                  background: 'var(--color-bg-card)',
                  color: 'var(--color-text)',
                }}
                formatter={(_value: unknown) => [`${_value}%`, '预算占比']}
              />
              <Legend
                formatter={(value: string) => (
                  <span style={{ color: 'var(--color-text)', fontSize: '13px' }}>{value}</span>
                )}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Strategy Cards */}
      <div className="space-y-3">
        <h3 className="font-semibold text-[var(--color-text)] mb-4">
          策略建议
        </h3>
        {strategy.recommendedPlatforms.map((rec, i) => (
          <div
            key={i}
            className="rounded-xl bg-[var(--color-bg-card)] border border-[var(--color-border)] p-4 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: COLORS[i % COLORS.length] }}
                />
                <span className="font-semibold text-[var(--color-text)]">
                  {rec.platform}
                </span>
              </div>
              <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400">
                ROAS {rec.expectedROAS}
              </span>
            </div>
            <p className="text-sm text-[var(--color-text-muted)] mb-2">
              {rec.reasoning}
            </p>
            <div className="flex items-center gap-3 text-sm">
              <span className="font-medium text-[var(--color-text)]">
                建议日预算：<span className="text-[var(--color-primary)]">{rec.dailyBudget}</span>
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
