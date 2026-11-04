import { defineConfig } from '@playwright/test'
import { fileURLToPath } from 'node:url'

const repository = fileURLToPath(new URL('..', import.meta.url))

export default defineConfig({
  testDir: './e2e',
  workers: 1,
  retries: 0,
  timeout: 30000,
  reporter: 'list',
  use: {
    baseURL: 'http://127.0.0.1:5173',
    viewport: { width: 1440, height: 1000 },
    screenshot: 'only-on-failure',
    launchOptions: {
      executablePath: process.env.BROWSER_EXECUTABLE_PATH || undefined,
      args: process.env.BROWSER_ARGS ? JSON.parse(process.env.BROWSER_ARGS) : [],
    },
  },
  webServer: [
    {
      command: `"${process.env.E2E_PYTHON || 'python'}" -m uvicorn api.app.main:app --host 127.0.0.1 --port 8000`,
      cwd: repository,
      url: 'http://127.0.0.1:8000/health',
      reuseExistingServer: !process.env.CI,
    },
    {
      command: 'npm run dev -- --host 127.0.0.1 --port 5173 --strictPort',
      url: 'http://127.0.0.1:5173',
      env: { VITE_API_URL: '/' },
      reuseExistingServer: !process.env.CI,
    },
  ],
})
