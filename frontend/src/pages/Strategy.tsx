import { useState, useEffect } from 'react'
import {
  Star,
  TrendingUp,
  DollarSign,
  Target,
  Lightbulb,
  ChevronDown,
  PieChartIcon,
  Radio,
} from 'lucide-react'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts'
import { getTasks, getStrategyData } from '../services/api'
import type { TaskRecord, StrategyData } from '../types'

// ============ 渠道配色 ============
const CHANNEL_COLORS: Record<string, string> = {
  TikTok: '#ff0050',
  Meta: '#1877f2',
  Google: '#4285f4',
}

const CHANNEL_ICONS: Record<string, string> = {
  TikTok: '🎵',
  Meta: '📘',
  Google: '🔍',
}

const CHANNEL_BG: Record<string, string> = {
  TikTok: 'bg-gradient-to-br from-pink-50 to-rose-100 dark:from-pink-950/30 dark:to-rose-950/20',
  Meta: 'bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-blue-950/30 dark:to-indigo-950/20',
  Google: 'bg-gradient-to-br from-green-50 to-emerald-100 dark:from-green-950/30 dark:to-emerald-950/20',
}

// ============ Page ============

export default function Strategy() {
  const [tasks, setTasks] = useState<TaskRecord[]>([])
  const [selectedTaskId, setSelectedTaskId] = useState<string>('')
  const [strategyData, setStrategyData] = useState<StrategyData | null>(null)
  const [loading, setLoading] = useState(true)
  const [dataLoading, setDataLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // 加载产品列表
  useEffect(() => {
    async function fetchTasks() {
      try {
        const res = await getTasks(1, 50)
        const completed = res.tasks.filter(
          (t) => t.status === 'completed'
        )
        setTasks(completed)
        if (completed.length > 0) {
          setSelectedTaskId(completed[0].taskId)
        }
      } catch (err) {
        console.error('[Strategy] Failed to load tasks:', err)
        setError('加载任务列表失败，请检查网络连接')
      } finally {
        setLoading(false)
      }
    }
    fetchTasks()
  }, [])

  // 选中产品变化 → 加载策略数据
  useEffect(() => {
    if (!selectedTaskId) {
      setStrategyData(null)
      return
    }
    async function fetchStrategy() {
      setDataLoading(true)
      setError(null)
      try {
        const data = await getStrategyData(selectedTaskId)
        setStrategyData(data)
      } catch (err) {
        console.error('[Strategy] Failed to load strategy:', err)
        setError('加载策略数据失败，请稍后重试')
        setStrategyData(null)
      } finally {
        setDataLoading(false)
      }
    }
    fetchStrategy()
  }, [selectedTaskId])

  // ---- 加载中 ----
  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="w-8 h-8 border-3 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  // ---- 加载出错 ----
  if (error && tasks.length === 0) {
    return (
      <div className="space-y-6">
        <PageHeader />
        <div className="rounded-xl bg-[var(--color-bg-card)] border border-[var(--color-border)] p-12 text-center">
          <div className="w-12 h-12 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mx-auto mb-3">
            <span className="text-2xl">⚠️</span>
          </div>
          <p className="text-lg font-medium text-[var(--color-text)]">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 text-sm bg-[var(--color-primary)] text-white rounded-lg hover:opacity-90 transition-opacity"
          >
            重新加载
          </button>
        </div>
      </div>
    )
  }

  // ---- 空数据：没有已完成的任务 ----
  if (tasks.length === 0) {
    return (
      <div className="space-y-6">
        <PageHeader />
        <div className="rounded-xl bg-[var(--color-bg-card)] border border-[var(--color-border)] p-12 text-center">
          <Target className="w-12 h-12 text-[var(--color-text-muted)] mx-auto mb-3 opacity-30" />
          <p className="text-lg font-medium text-[var(--color-text-muted)]">
            暂无投放策略数据
          </p>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">
            请先在「内容生成」页面完成至少一个任务
          </p>
        </div>
      </div>
    )
  }

  const selectedTask = tasks.find((t) => t.taskId === selectedTaskId)

  return (
    <div className="space-y-6 animate-fade-in-up">
      <PageHeader />

      {/* 产品选择器 */}
      <div className="rounded-xl bg-[var(--color-bg-card)] border border-[var(--color-border)] p-4">
        <div className="flex items-center gap-3">
          <label className="text-sm font-semibold text-[var(--color-text)] shrink-0">
            选择产品
          </label>
          <div className="relative flex-1 max-w-xs">
            <select
              value={selectedTaskId}
              onChange={(e) => setSelectedTaskId(e.target.value)}
              className="w-full appearance-none pl-4 pr-10 py-2.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] text-[var(--color-text)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent transition-all cursor-pointer"
            >
              {tasks.map((t) => (
                <option key={t.taskId} value={t.taskId}>
                  {t.productName}
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)] pointer-events-none" />
          </div>
          {selectedTask && (
            <span className="text-xs text-[var(--color-text-muted)]">
              {selectedTask.platforms.join(' · ')}
            </span>
          )}
        </div>
      </div>

      {/* 主内容 */}
      {dataLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="w-8 h-8 border-3 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin" />
        </div>
      ) : strategyData ? (
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* 左栏：渠道卡片 (3/5) */}
          <div className="lg:col-span-3 space-y-4">
            <SectionTitle icon={Radio} text="渠道推荐" />
            {strategyData.recommendedChannels.map((ch, i) => (
              <ChannelCard key={ch.channel} channel={ch} index={i} />
            ))}
          </div>

          {/* 右栏：饼图 + 策略建议 (2/5) */}
          <div className="lg:col-span-2 space-y-6">
            {/* 预算分配饼图 */}
            <div className="rounded-xl bg-[var(--color-bg-card)] border border-[var(--color-border)] p-5">
              <SectionTitle icon={PieChartIcon} text="预算分配" />
              <div className="h-56 mt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={strategyData.budgetAllocation.map((b) => ({
                        name: b.channel,
                        value: b.value,
                      }))}
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={80}
                      paddingAngle={4}
                      dataKey="value"
                    >
                      {strategyData.budgetAllocation.map((entry) => (
                        <Cell
                          key={entry.channel}
                          fill={CHANNEL_COLORS[entry.channel] || '#6366f1'}
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
                      formatter={(_v: unknown) => [`${_v}%`, '预算占比']}
                    />
                    <Legend
                      formatter={(value: string) => (
                        <span style={{ color: 'var(--color-text)', fontSize: '12px' }}>
                          {value}
                        </span>
                      )}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* 策略要点 */}
            <div className="rounded-xl bg-[var(--color-bg-card)] border border-[var(--color-border)] p-5">
              <SectionTitle icon={Lightbulb} text="投放建议" />
              <ul className="space-y-2.5 mt-2">
                {strategyData.keySuggestions.map((s, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2.5 text-sm text-[var(--color-text)]"
                  >
                    <span className="w-5 h-5 rounded-full bg-[var(--color-primary)]/10 text-[var(--color-primary)] flex items-center justify-center shrink-0 mt-0.5 text-xs font-bold">
                      {i + 1}
                    </span>
                    <span className="leading-relaxed">{s}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      ) : (
        /* 选中产品但无策略数据 */
        <div className="rounded-xl bg-[var(--color-bg-card)] border border-[var(--color-border)] p-12 text-center">
          <Target className="w-12 h-12 text-[var(--color-text-muted)] mx-auto mb-3 opacity-30" />
          <p className="text-lg font-medium text-[var(--color-text-muted)]">
            该产品暂无策略建议
          </p>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">
            确保生成任务中包含了投放策略分析
          </p>
        </div>
      )}
    </div>
  )
}

// ============ Sub-components ============

function PageHeader() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-[var(--color-text)]">投放策略</h1>
      <p className="text-[var(--color-text-muted)] mt-1">
        基于 AI 分析，为每个产品推荐最优投放方案
      </p>
    </div>
  )
}

function SectionTitle({
  icon: Icon,
  text,
}: {
  icon: React.ComponentType<{ className?: string }>
  text: string
}) {
  return (
    <div className="flex items-center gap-2 mb-1">
      <Icon className="w-4 h-4 text-[var(--color-primary)]" />
      <h3 className="text-sm font-semibold text-[var(--color-text-muted)] uppercase tracking-wide">
        {text}
      </h3>
    </div>
  )
}

function ChannelCard({
  channel,
  index,
}: {
  channel: StrategyData['recommendedChannels'][number]
  index: number
}) {
  const color = CHANNEL_COLORS[channel.channel.replace(' Ads', '')] || '#6366f1'
  const icon = CHANNEL_ICONS[channel.channel.replace(' Ads', '')] || '📊'
  const bg = CHANNEL_BG[channel.channel.replace(' Ads', '')] || ''

  return (
    <div
      className={`rounded-xl border border-[var(--color-border)] overflow-hidden hover:shadow-md transition-shadow ${bg}`}
    >
      <div className="p-5">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{icon}</span>
            <div>
              <h3 className="font-semibold text-[var(--color-text)]">
                {channel.channel}
              </h3>
              {/* Star Rating */}
              <div className="flex items-center gap-0.5 mt-0.5">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Star
                    key={i}
                    className={`w-3.5 h-3.5 ${
                      i < channel.rating
                        ? 'fill-amber-400 text-amber-400'
                        : 'text-[var(--color-border)]'
                    }`}
                  />
                ))}
              </div>
            </div>
          </div>
          {/* Priority Badge */}
          <span
            className={`text-xs font-bold px-2.5 py-1 rounded-full ${
              index === 0
                ? 'bg-red-100 text-red-700 dark:bg-red-950/30 dark:text-red-400'
                : index === 1
                ? 'bg-amber-100 text-amber-700 dark:bg-amber-950/30 dark:text-amber-400'
                : 'bg-blue-100 text-blue-700 dark:bg-blue-950/30 dark:text-blue-400'
            }`}
          >
            {index === 0 ? '首选' : index === 1 ? '次选' : '备选'}
          </span>
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-2 gap-3 mb-3">
          <div className="rounded-lg bg-white/60 dark:bg-black/10 p-3">
            <div className="flex items-center gap-1 text-xs text-[var(--color-text-muted)] mb-0.5">
              <DollarSign className="w-3 h-3" />
              建议日预算
            </div>
            <p className="text-lg font-bold text-[var(--color-text)]">
              ${channel.dailyBudget}
            </p>
          </div>
          <div className="rounded-lg bg-white/60 dark:bg-black/10 p-3">
            <div className="flex items-center gap-1 text-xs text-[var(--color-text-muted)] mb-0.5">
              <TrendingUp className="w-3 h-3" />
              预计 ROAS
            </div>
            <p className="text-lg font-bold" style={{ color }}>
              {channel.estimatedROAS}
            </p>
          </div>
        </div>

        {/* Reason */}
        <p className="text-sm text-[var(--color-text-muted)] leading-relaxed">
          💡 {channel.reason}
        </p>
      </div>
    </div>
  )
}
