import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Video,
  FileText,
  Lightbulb,
  Plus,
  ArrowRight,
  Clock,
  CheckCircle2,
  XCircle,
} from 'lucide-react'
import { getWeeklyStats, getTasks } from '../services/api'
import type { WeeklyStats, TaskRecord } from '../types'

export default function Dashboard() {
  const navigate = useNavigate()
  const [stats, setStats] = useState<WeeklyStats | null>(null)
  const [tasks, setTasks] = useState<TaskRecord[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchData() {
      const [s, t] = await Promise.all([getWeeklyStats(), getTasks(1, 5)])
      setStats(s)
      setTasks(t.tasks)
      setLoading(false)
    }
    fetchData()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="w-8 h-8 border-3 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in-up">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-[var(--color-text)]">
          工作台
        </h1>
        <p className="text-[var(--color-text-muted)] mt-1">
          欢迎回来，查看你的内容营销概览
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          icon={Video}
          label="本周生成视频"
          value={stats?.videoCount ?? 0}
          unit="个"
          color="bg-gradient-to-br from-blue-500 to-cyan-500"
        />
        <StatCard
          icon={FileText}
          label="本周生成文案"
          value={stats?.copyCount ?? 0}
          unit="条"
          color="bg-gradient-to-br from-emerald-500 to-teal-500"
        />
        <StatCard
          icon={Lightbulb}
          label="本周投放建议"
          value={stats?.strategyCount ?? 0}
          unit="份"
          color="bg-gradient-to-br from-amber-500 to-orange-500"
        />
      </div>

      {/* Quick Start Card */}
      <div
        onClick={() => navigate('/create')}
        className="group relative overflow-hidden rounded-xl bg-gradient-to-r from-[var(--color-primary)] via-purple-500 to-pink-500 p-6 text-white cursor-pointer transition-all duration-300 hover:shadow-xl hover:scale-[1.01]"
      >
        <div className="absolute inset-0 bg-black/10 group-hover:bg-black/0 transition-colors" />
        <div className="relative z-10 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold">创建新的营销任务</h2>
            <p className="mt-1 text-white/80">
              输入产品信息，AI自动生成短视频和社媒文案
            </p>
          </div>
          <div className="flex items-center gap-2 bg-white/20 rounded-full px-4 py-2 group-hover:bg-white/30 transition-colors">
            <Plus className="w-5 h-5" />
            <span className="font-medium">开始创建</span>
            <ArrowRight className="w-4 h-4" />
          </div>
        </div>
      </div>

      {/* Recent Tasks */}
      <div className="rounded-xl bg-[var(--color-bg-card)] border border-[var(--color-border)] overflow-hidden">
        <div className="px-6 py-4 border-b border-[var(--color-border)] flex items-center justify-between">
          <h2 className="font-semibold text-[var(--color-text)]">最近任务</h2>
          <button
            onClick={() => navigate('/create')}
            className="text-sm text-[var(--color-primary)] hover:underline flex items-center gap-1"
          >
            查看全部 <ArrowRight className="w-3 h-3" />
          </button>
        </div>
        <div className="divide-y divide-[var(--color-border)]">
          {tasks.length === 0 ? (
            <div className="px-6 py-12 text-center text-[var(--color-text-muted)]">
              暂无任务，点击上方卡片开始创建
            </div>
          ) : (
            tasks.map((task) => (
              <TaskRow key={task.taskId} task={task} />
            ))
          )}
        </div>
      </div>
    </div>
  )
}

// ============ Sub-components ============

function StatCard({
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
  return (
    <div className="rounded-xl bg-[var(--color-bg-card)] border border-[var(--color-border)] p-5 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-[var(--color-text-muted)]">{label}</p>
          <p className="text-3xl font-bold mt-1 text-[var(--color-text)]">
            {value}
            <span className="text-lg font-normal text-[var(--color-text-muted)] ml-1">
              {unit}
            </span>
          </p>
        </div>
        <div className={`w-10 h-10 rounded-lg ${color} flex items-center justify-center`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
      </div>
    </div>
  )
}

function TaskRow({ task }: { task: TaskRecord }) {
  const statusIcons = {
    completed: <CheckCircle2 className="w-4 h-4 text-[var(--color-success)]" />,
    generating: <Clock className="w-4 h-4 text-[var(--color-accent)]" />,
    failed: <XCircle className="w-4 h-4 text-[var(--color-danger)]" />,
  }

  const statusText = {
    completed: '已完成',
    generating: '生成中',
    failed: '失败',
  }

  const timeAgo = (dateStr: string) => {
    const diff = Date.now() - new Date(dateStr).getTime()
    const hours = Math.floor(diff / 3600000)
    if (hours < 1) return '刚刚'
    if (hours < 24) return `${hours}小时前`
    return `${Math.floor(hours / 24)}天前`
  }

  return (
    <div className="px-6 py-3.5 flex items-center justify-between hover:bg-[var(--color-bg)] transition-colors">
      <div className="flex items-center gap-3 min-w-0">
        {statusIcons[task.status]}
        <div>
          <p className="font-medium text-[var(--color-text)] truncate">
            {task.productName}
          </p>
          <p className="text-xs text-[var(--color-text-muted)]">
            {task.platforms.join(' · ')} · {timeAgo(task.createdAt)}
          </p>
        </div>
      </div>
      <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-[var(--color-bg)] text-[var(--color-text-muted)]">
        {statusText[task.status]}
      </span>
    </div>
  )
}
