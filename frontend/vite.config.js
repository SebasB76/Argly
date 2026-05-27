import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// El front llama a /api/* y Vite lo proxya al backend FastAPI (puerto 8000).
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
