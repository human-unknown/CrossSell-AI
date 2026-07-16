import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  // 注意：axios 使用绝对 baseURL 时不经过此 proxy。
  // proxy 仅在 VITE_API_BASE 设为相对路径（如 /api）时生效，用于同源请求转发。
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
