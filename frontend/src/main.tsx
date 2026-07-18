import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App'

// ============ CloudStudio Beacon 防御层 ============
// CloudStudio 注入的腾讯灯塔 SDK 在 document 上监听 click 事件，
// 每次点击侧栏导航后额外触发一次 window.location.href 赋值，
// 导致 React Router 单次导航后页面被重复刷新。
//
// 修复：记录 React Router pushState 调用时间，
// 在 800ms 内通过 location.href 发起的导航视为 Beacon 干扰并拦截。

let _lastPushStateTime = 0
const _origPushState = window.history.pushState
window.history.pushState = function (...args: Parameters<typeof _origPushState>) {
  _lastPushStateTime = performance.now()
  return _origPushState.apply(this, args)
}

// 拦截 location.href 的 setter
const _origLocationDescriptor = Object.getOwnPropertyDescriptor(
  window,
  'location'
)!
Object.defineProperty(window, 'location', {
  get: () => _origLocationDescriptor.get!.call(window),
  set(value: string) {
    if (typeof value === 'string') {
      const elapsed = performance.now() - _lastPushStateTime
      if (elapsed < 800) {
        // 800ms 内的 location 赋值 → 大概率是 Beacon 干扰，忽略
        return
      }
    }
    _origLocationDescriptor.set!.call(window, value)
  },
  configurable: true,
  enumerable: true,
})
// ============ End Beacon Guard ============

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
)
