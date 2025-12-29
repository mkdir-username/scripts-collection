import { defineConfig } from 'playwright/test';

export default defineConfig({
  timeout: 60000,
  retries: 0,
  workers: 1,
  reporter: 'list',
  use: {
    headless: true,
    viewport: { width: 1280, height: 720 },
    baseURL: 'http://localhost:8080',
    screenshot: 'on',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'validation',
      use: { browserName: 'chromium' },
    },
  ],
});
