import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/query': 'http://127.0.0.1:8001',
      '/stream': 'http://127.0.0.1:8001',
      '/history': 'http://127.0.0.1:8001',
      '/health': 'http://127.0.0.1:8001',
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
})
