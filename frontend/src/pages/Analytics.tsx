import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  BarChart3,
  Video,
  FileText,
  Lightbulb,
  Layers,
  Clock,
  CheckCircle2,
  Loader2,
  Globe,
} from 'lucide-react'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts'
import { getAnalyticsData } from '../services/api'
import type { AnalyticsData, TimeRange } from '../types'

const PLATFORM_COLORS: Record<string, string> = {
  TikTok: '#ff0050',
  Instagram: '#e4405f',
  'YouTube Shorts': '#ff0000',
  Facebook: '#1877f2',
  Pinterest: '#e60023',
}

const TIME_RANGE_OPTIONS: { value: TimeRange; label: string }[] = [
  { value: '本周', label: '本周' },
  { value: '本月', label: '本月' },
  { value: '本季度', label: '本季度' },
]

export default function Analytics() {
  const navigate = useNavigate()
  const [timeRange, setTimeRange] = useState<TimeRange>('本周')
  const [data, setData] = useState<AnalyticsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    // 取消上一次未完成的请求
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    async function fetchData() {
      setLoading(true)
      setError(null)
      try {
        const result = await getAnalyticsData(timeRange)
        if (!controller.signal.aborted) {
          setData(result)
        }
      } catch (err) {
        if (controller.signal.aborted) return
        console.error('[Analytics] Failed to load data:', err)
        setError('加载数据失败，请检查网络连接')
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false)
        }
      }
    }
    fetchData()
  }, [timeRange])

  if (loading) {
    return <AnalyticsSkeleton timeRange={timeRange} onTimeRangeChange={setTimeRange} />
  }

  if (error) {
    return (
      <div className="space-y-6 animate-fade-in-up">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-2xl font-bold text-[var(--color-text)]">数据中心</h1>
            <p className="text-[var(--color-text-muted)] mt-1">追踪内容生产与投放效果</p>
          </div>
        </div>
        <div className="rounded-xl bg-[var(--color-bg-card)] border border-[var(--color-border)] p-12 text-center">
          <div className="w-12 h-12 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mx-auto mb-3">
            <span className="text-2xl">⚠️</span>
          </div>
          <p className="text-lg font-medium text-[var(--color-text)]">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 text-sm bg-[var(--color-primary)] text-white rounded-lg hover:shadow-md hover:scale-[1.01] transition-all duration-200"
          >
            重新加载
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in-up">
      {/* Header + Time Range Selector */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text)]">数据中心</h1>
          <p className="text-[var(--color-text-muted)] mt-1">
            追踪内容生产与投放效果，数据驱动决策
          </p>
        </div>
        <div className="flex items-center gap-1 bg-[var(--color-bg)] rounded-lg p-1">
          {TIME_RANGE_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setTimeRange(opt.value)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                timeRange === opt.value
                  ? 'bg-[var(--color-bg-card)] text-[var(--color-text)] shadow-sm'
                  : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <SummaryCard
          icon={Layers}
          label="总生成内容"
          value={data?.summary.totalContent ?? 0}
          unit="个"
          color="bg-gradient-to-br from-purple-500 to-violet-600"
        />
        <SummaryCard
          icon={Video}
          label="生成视频"
          value={data?.summary.videoCount ?? 0}
          unit="个"
          color="bg-gradient-to-br from-blue-500 to-cyan-500"
        />
        <SummaryCard
          icon={FileText}
          label="生成文案"
          value={data?.summary.copyCount ?? 0}
          unit="条"
          color="bg-gradient-to-br from-emerald-500 to-teal-500"
        />
        <SummaryCard
          icon={Lightbulb}
          label="策略建议"
          value={data?.summary.strategyCount ?? 0}
          unit="份"
          color="bg-gradient-to-br from-amber-500 to-orange-500"
        />
      </div>

      {/* Main Content: Platform Distribution + Recent Tasks */}
      {data && (data.platformDistribution.length > 0 || data.recentTasks.length > 0) ? (
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Left: Platform Distribution Pie */}
          <div className="lg:col-span-2 rounded-xl bg-[var(--color-bg-card)] border border-[var(--color-border)] p-5">
            <h3 className="text-sm font-semibold text-[var(--color-text-muted)] uppercase tracking-wide mb-1">
              平台内容分布
            </h3>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data.platformDistribution.map((p) => ({
                      name: p.platform,
                      value: p.count,
                    }))}
                    cx="50%"
                    cy="45%"
                    innerRadius={55}
                    outerRadius={90}
                    paddingAngle={3}
                    dataKey="value"
                    label={({ name, value }) => `${name} (${value})`}
                    labelLine={{ stroke: 'var(--color-border)', strokeWidth: 1 }}
                  >
                    {data.platformDistribution.map((entry) => (
                      <Cell
                        key={entry.platform}
                        fill={PLATFORM_COLORS[entry.platform] || '#6366f1'}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      borderRadius: '12px',
                      border: '1px solid var(--color-border)',
                      background: 'var(--color-bg-card)',
                      color: 'var(--color-text)',
                    }}
                    formatter={(_v: unknown) => [`${_v} 条内容`, '']}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Right: Recent Tasks Table */}
          <div className="lg:col-span-3 rounded-xl bg-[var(--color-bg-card)] border border-[var(--color-border)] overflow-hidden">
            <div className="px-5 py-4 border-b border-[var(--color-border)]">
              <h3 className="text-sm font-semibold text-[var(--color-text-muted)] uppercase tracking-wide">
                最近生成任务
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[var(--color-border)] bg-[var(--color-bg)]/50">
                    <th className="text-left px-5 py-3 font-medium text-[var(--color-text-muted)]">
                      产品名称
                    </th>
                    <th className="text-center px-3 py-3 font-medium text-[var(--color-text-muted)]">
                      平台
                    </th>
                    <th className="text-center px-3 py-3 font-medium text-[var(--color-text-muted)]">
                      市场
                    </th>
                    <th className="text-left px-3 py-3 font-medium text-[var(--color-text-muted)]">
                      生成时间
                    </th>
                    <th className="text-center px-5 py-3 font-medium text-[var(--color-text-muted)]">
                      状态
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--color-border)]">
                  {data.recentTasks.map((task) => (
                    <TaskRow key={task.id} task={task} />
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : (
        /* 空数据 */
        <div className="rounded-xl bg-[var(--color-bg-card)] border border-[var(--color-border)] p-12 text-center">
          <BarChart3 className="w-12 h-12 text-[var(--color-text-muted)] mx-auto mb-3 opacity-30" />
          <p className="text-lg font-medium text-[var(--color-text-muted)]">
            暂无数据
          </p>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">
            {timeRange}内没有内容生产记录
          </p>
          <button
            onClick={() => navigate('/create')}
            className="mt-6 inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-gradient-to-r from-[var(--color-primary)] to-purple-500 text-white text-sm font-medium hover:shadow-lg hover:scale-[1.02] transition-all duration-200"
          >
            <Video className="w-4 h-4" />
            去生成内容
          </button>
        </div>
      )}
    </div>
  )
}

// ============ Sub-components ============

function SummaryCard({
  icon: Icon,
  label,
  value,
  unit,
  color,
}: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: number
  unit: string
  color: string
}) {
  const displayed = useCountUp(value)

  return (
    <div className="rounded-xl bg-[var(--color-bg-card)] border border-[var(--color-border)] p-5 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-[var(--color-text-muted)]">{label}</p>
          <p className="text-3xl font-bold mt-1 text-[var(--color-text)]">
            {displayed}
            <span className="text-lg font-normal text-[var(--color-text-muted)] ml-1">
              {unit}
            </span>
          </p>
        </div>
        <div className={`w-10 h-10 rounded-lg ${color} flex items-center justify-center shrink-0`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
      </div>
    </div>
  )
}

function TaskRow({ task }: { task: AnalyticsData['recentTasks'][number] }) {
  const statusConfig: Record<string, { icon: React.ReactNode; label: string; className: string }> = {
    completed: {
      icon: <CheckCircle2 className="w-3.5 h-3.5" />,
      label: '已完成',
      className: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
    },
    generating: {
      icon: <Loader2 className="w-3.5 h-3.5 animate-spin" />,
      label: '生成中',
      className: 'bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
    },
    failed: {
      icon: <Clock className="w-3.5 h-3.5" />,
      label: '失败',
      className: 'bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    },
  }

  const config = statusConfig[task.status] || statusConfig.completed

  const timeStr = new Date(task.createdAt).toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })

  return (
    <tr className="hover:bg-[var(--color-bg)]/50 transition-colors">
      <td className="px-5 py-3.5">
        <span className="font-medium text-[var(--color-text)]">{task.productName}</span>
      </td>
      <td className="px-3 py-3.5 text-center">
        <div className="flex items-center justify-center gap-1 text-[var(--color-text-muted)]">
          <Globe className="w-3.5 h-3.5" />
          <span>{task.platformCount}</span>
        </div>
      </td>
      <td className="px-3 py-3.5 text-center text-[var(--color-text-muted)]">
        {task.marketCount}
      </td>
      <td className="px-3 py-3.5 text-[var(--color-text-muted)] whitespace-nowrap">
        {timeStr}
      </td>
      <td className="px-5 py-3.5 text-center">
        <span
          className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${config.className}`}
        >
          {config.icon}
          {config.label}
        </span>
      </td>
    </tr>
  )
}

// ============ Count-Up Hook ============

function useCountUp(target: number, duration = 600): number {
  const [current, setCurrent] = useState(0)
  const prevTarget = useRef(target)

  useEffect(() => {
    if (target === 0) {
      setCurrent(0)
      prevTarget.current = 0
      return
    }

    let cancelled = false
    let raf: number
    const startValue = prevTarget.current
    const delta = target - startValue
    const startTime = performance.now()

    const step = (now: number) => {
      if (cancelled) return
      const elapsed = now - startTime
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - (1 - progress) * (1 - progress)
      setCurrent(Math.round(startValue + eased * delta))

      if (progress < 1) {
        raf = requestAnimationFrame(step)
      }
    }

    raf = requestAnimationFrame(step)

    return () => {
      cancelled = true
      cancelAnimationFrame(raf)
      prevTarget.current = target
    }
  }, [target, duration])

  return current
}

// ============ Skeleton Screen ============

function AnalyticsSkeleton({
  timeRange,
  onTimeRangeChange,
}: {
  timeRange: TimeRange
  onTimeRangeChange: (v: TimeRange) => void
}) {
  return (
    <div className="space-y-6 animate-fade-in-up">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text)]">数据中心</h1>
          <p className="text-[var(--color-text-muted)] mt-1">
            追踪内容生产与投放效果，数据驱动决策
          </p>
        </div>
        <div className="flex items-center gap-1 bg-[var(--color-bg)] rounded-lg p-1">
          {TIME_RANGE_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => onTimeRangeChange(opt.value)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                timeRange === opt.value
                  ? 'bg-[var(--color-bg-card)] text-[var(--color-text)] shadow-sm'
                  : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Stat Cards Skeleton */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="rounded-xl bg-[var(--color-bg-card)] border border-[var(--color-border)] p-5 animate-pulse"
          >
            <div className="flex items-start justify-between">
              <div className="space-y-2">
                <div className="h-4 w-16 bg-[var(--color-border)] rounded" />
                <div className="h-8 w-20 bg-[var(--color-border)] rounded" />
              </div>
              <div className="w-10 h-10 bg-[var(--color-border)] rounded-lg" />
            </div>
          </div>
        ))}
      </div>

      {/* Main Content Skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        <div className="lg:col-span-2 rounded-xl bg-[var(--color-bg-card)] border border-[var(--color-border)] p-5 animate-pulse">
          <div className="h-4 w-20 bg-[var(--color-border)] rounded mb-4" />
          <div className="h-56 bg-[var(--color-border)] rounded-lg" />
        </div>
        <div className="lg:col-span-3 rounded-xl bg-[var(--color-bg-card)] border border-[var(--color-border)] animate-pulse">
          <div className="px-5 py-4 border-b border-[var(--color-border)]">
            <div className="h-4 w-24 bg-[var(--color-border)] rounded" />
          </div>
          <div className="space-y-0">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="flex items-center gap-4 px-5 py-3.5 border-b border-[var(--color-border)]">
                <div className="h-4 flex-1 bg-[var(--color-border)] rounded" />
                <div className="h-4 w-8 bg-[var(--color-border)] rounded" />
                <div className="h-4 w-8 bg-[var(--color-border)] rounded" />
                <div className="h-4 w-20 bg-[var(--color-border)] rounded" />
                <div className="h-6 w-16 bg-[var(--color-border)] rounded-full" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
