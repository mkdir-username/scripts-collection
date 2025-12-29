/**
 * Playwright Runtime Validator
 * Loads contract in browser and collects console errors + screenshot
 */

import { chromium, type Browser, type Page, type ConsoleMessage } from 'playwright';
import { writeFileSync, copyFileSync, mkdirSync } from 'fs';
import { join, basename } from 'path';
import type { ValidatorConfig, ValidationError, RuntimeValidation } from '../types/report.js';

interface RuntimeResult extends Omit<RuntimeValidation, 'consoleErrors'> {
  consoleErrors: Array<{ level: 'error' | 'warn'; message: string; source: string }>;
  errors?: ValidationError[];
}

const TEMP_CONTRACT_PATH = '/tmp/fms-validate-contract.json';

export async function runRuntimeValidation(
  contractPath: string,
  config: ValidatorConfig
): Promise<RuntimeResult> {
  const errors: ValidationError[] = [];
  const consoleErrors: Array<{ level: 'error' | 'warn'; message: string; source: string }> = [];
  const networkErrors: string[] = [];

  let browser: Browser | null = null;
  let rendered = false;
  let renderStatus: 'FULL' | 'PARTIAL' | 'FAILED' = 'FAILED';

  try {
    // Copy contract to temp location for newclick to load
    copyFileSync(contractPath, TEMP_CONTRACT_PATH);
    console.error(`📦 Contract copied to ${TEMP_CONTRACT_PATH}`);

    // Launch browser
    browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
      viewport: { width: 1280, height: 720 },
    });
    const page = await context.newPage();

    // Collect console messages
    page.on('console', (msg: ConsoleMessage) => {
      const type = msg.type();
      if (type === 'error' || type === 'warning') {
        consoleErrors.push({
          level: type === 'error' ? 'error' : 'warn',
          message: msg.text(),
          source: msg.location()?.url || 'unknown',
        });
      }
    });

    // Collect page errors (uncaught exceptions)
    page.on('pageerror', (error: Error) => {
      consoleErrors.push({
        level: 'error',
        message: error.message,
        source: 'pageerror',
      });
    });

    // Collect network failures
    page.on('requestfailed', (request) => {
      networkErrors.push(`${request.method()} ${request.url()}: ${request.failure()?.errorText}`);
    });

    // Navigate to validation endpoint
    const port = process.env.NEWCLICK_PORT || '8043';
    const url = `http://localhost:${port}/?endpoint=${config.endpoint}`;
    console.error(`🌐 Navigating to ${url}`);

    try {
      await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
      rendered = true;

      // Wait a bit for any async rendering
      await page.waitForTimeout(2000);

      // Check if there are visible errors in the page
      const errorElements = await page.locator('[data-testid*="error"], .error, .sdui-error').count();
      if (errorElements > 0) {
        renderStatus = 'PARTIAL';
      } else if (consoleErrors.filter(e => e.level === 'error').length > 0) {
        renderStatus = 'PARTIAL';
      } else {
        renderStatus = 'FULL';
      }

    } catch (navError) {
      console.error(`❌ Navigation failed: ${navError}`);
      renderStatus = 'FAILED';
      consoleErrors.push({
        level: 'error',
        message: `Navigation failed: ${navError}`,
        source: 'playwright',
      });
    }

    // Take screenshot
    let screenshot;
    if (config.screenshot && rendered) {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const contractName = basename(contractPath, '.json');
      const screenshotDir = join(process.cwd(), 'screenshots');

      try {
        mkdirSync(screenshotDir, { recursive: true });
      } catch { /* ignore */ }

      const screenshotPath = join(screenshotDir, `${timestamp}_${contractName}.png`);

      await page.screenshot({ path: screenshotPath, fullPage: true });
      console.error(`📸 Screenshot saved: ${screenshotPath}`);

      screenshot = {
        path: screenshotPath,
        viewport: { width: 1280, height: 720 },
        timestamp: new Date().toISOString(),
      };
    }

    // Convert console errors to ValidationErrors
    let errorCounter = 200;
    for (const consoleErr of consoleErrors) {
      if (consoleErr.level === 'error') {
        // Skip React dev warnings (non-blocking)
        const isReactWarning = consoleErr.message.includes('Warning:') ||
                               consoleErr.message.includes('unique "key" prop') ||
                               consoleErr.message.includes('CORS') ||
                               consoleErr.message.includes('Failed to load resource');

        // Parse SDUI-specific errors (blocking)
        const isSduiError = (consoleErr.message.includes('Unknown') && consoleErr.message.includes('type')) ||
                            consoleErr.message.includes('SDUI error');

        if (isSduiError && !isReactWarning) {
          errors.push({
            id: `E${++errorCounter}`,
            severity: 'error',
            category: 'RENDER_ERROR',
            blocking: true,
            location: {
              jsonPath: '$.rootElement',
              jsonPointer: '/rootElement',
              snippet: consoleErr.message,
            },
            message: consoleErr.message,
            rawMessage: consoleErr.message,
            fix: {
              action: 'Fix the component causing the render error',
              refs: ['Check console error message for details'],
            },
            aiHint: `Browser error: ${consoleErr.message}. Check the component tree for invalid types.`,
          });
        }
      }
    }

    await context.close();

    return {
      rendered,
      renderStatus,
      consoleErrors,
      networkErrors,
      screenshot,
      errors,
    };

  } catch (error) {
    console.error(`💥 Runtime validation error: ${error}`);
    return {
      rendered: false,
      renderStatus: 'FAILED',
      consoleErrors: [{
        level: 'error',
        message: String(error),
        source: 'validator',
      }],
      networkErrors,
      errors: [{
        id: 'E999',
        severity: 'critical',
        category: 'RENDER_ERROR',
        blocking: true,
        location: {
          jsonPath: '$',
          jsonPointer: '',
          snippet: String(error),
        },
        message: `Runtime validation failed: ${error}`,
        fix: {
          action: 'Ensure newclick is running: cd ~/Documents/newclick-server-driven-ui && yarn start',
          refs: ['Check that localhost:8043 is accessible'],
        },
        aiHint: 'Runtime validation failed. Make sure newclick dev server is running.',
      }],
    };

  } finally {
    if (browser) {
      await browser.close();
    }
  }
}
