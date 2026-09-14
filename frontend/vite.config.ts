import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const apiProxyTarget = process.env.VITE_API_PROXY_TARGET ?? 'https://meercatb.onrender.com'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // 로컬 개발: /api 요청을 Render 백엔드로 프록시 (CORS 우회)
      '/api': {
        target: apiProxyTarget,
        changeOrigin: true,
        secure: true,
      },
    },
  },
})
