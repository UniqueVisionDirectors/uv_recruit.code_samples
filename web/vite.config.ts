import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    host: true,
    proxy: {
      "/api/app": {
        target: "http://app:8000",
        rewrite: (p: string) => p.replace(/^\/api\/app/, ""),
      },
      "/api/runner": {
        target: "http://runner:9000",
        rewrite: (p: string) => p.replace(/^\/api\/runner/, ""),
      },
    },
  },
})
