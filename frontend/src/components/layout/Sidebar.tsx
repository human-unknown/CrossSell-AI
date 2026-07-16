import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  Video,
  Target,
  BarChart3,
  Sun,
  Moon,
  Sparkles,
} from 'lucide-react'
import { useThemeStore } from '../../stores/themeStore'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: '工作台' },
  { to: '/create', icon: Video, label: '内容生成' },
  { to: '/strategy', icon: Target, label: '投放策略' },
  { to: '/analytics', icon: BarChart3, label: '数据中心' },
]

export default function Sidebar() {
  const location = useLocation()
  const { isDark, toggle } = useThemeStore()

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/'
    return location.pathname.startsWith(path)
  }

  return (
    <aside className="fixed left-0 top-0 h-full w-60 bg-[var(--color-bg-card)] border-r border-[var(--color-border)] flex flex-col z-40">
      {/* Logo */}
      <div className="h-16 flex items-center gap-3 px-5 border-b border-[var(--color-border)] shrink-0">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[var(--color-primary)] to-purple-500 flex items-center justify-center">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <span className="font-bold text-lg text-[var(--color-text)] tracking-tight">
          CrossSell AI
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive: active }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                active || isActive(to)
                  ? 'bg-[var(--color-primary)] text-white shadow-md shadow-purple-500/20'
                  : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-bg)]'
              }`
            }
          >
            <Icon className="w-5 h-5 shrink-0" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Theme toggle */}
      <div className="p-3 border-t border-[var(--color-border)]">
        <button
          onClick={toggle}
          className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm font-medium text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-bg)] transition-all duration-200"
        >
          {isDark ? (
            <>
              <Sun className="w-5 h-5 shrink-0" />
              <span>切换亮色模式</span>
            </>
          ) : (
            <>
              <Moon className="w-5 h-5 shrink-0" />
              <span>切换暗色模式</span>
            </>
          )}
        </button>
      </div>
    </aside>
  )
}
