import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
    watch: {
      // dist/ contains build artifacts (large PNGs); watching it can crash Vite
      // with EBUSY on Windows.
      ignored: ['**/dist/**'],
    },
  },
})