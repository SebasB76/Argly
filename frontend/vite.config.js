import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// El front llama a /api/* y Vite lo proxya al backend FastAPI.
// En local apunta a localhost:8000; en Docker se sobreescribe con
// VITE_PROXY_TARGET=http://backend:8000 (nombre del servicio del compose).
const proxyTarget = process.env.VITE_PROXY_TARGET || 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': proxyTarget,
    },
  },
})
