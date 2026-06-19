import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // 로컬 개발: /api 요청을 Render 백엔드로 프록시 (CORS 우회)
      '/api': {
        target: 'https://meercatb.onrender.com',
        changeOrigin: true,
        secure: true,
      },
    },
  },
})
