import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const devApiTarget =
    env.VITE_DEV_API_TARGET || 'https://neuro-cue.vercel.app'

  return {
    plugins: [react()],
    server: {
      // Vite does not run frontend/api/*.js — those are Vercel serverless routes.
      // Forward /api/* to deployed Vercel (or `vercel dev`) so `npm run dev` works.
      proxy: {
        '/api': {
          target: devApiTarget,
          changeOrigin: true,
          secure: true,
        },
      },
    },
  }
})
