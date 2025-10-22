/**
 * Jest setup file for parser tests
 * @version 1.0.0
 */

import { mkdirSync, rmSync } from 'fs';
import { join } from 'path';

// Глобальная настройка перед всеми тестами
beforeAll(() => {
  // Создаем временную директорию для тестов
  const tmpDir = join(__dirname, '.tmp');
  mkdirSync(tmpDir, { recursive: true });
});

// Глобальная очистка после всех тестов
afterAll(() => {
  // Очищаем временные файлы
  const tmpDir = join(__dirname, '.tmp');
  try {
    rmSync(tmpDir, { recursive: true, force: true });
  } catch (error) {
    console.error('Failed to clean up temp directory:', error);
  }
});

// Увеличиваем таймаут для медленных тестов
jest.setTimeout(10000);

// Кастомные матчеры
expect.extend({
  toBeValidParseResult(received) {
    const pass =
      received &&
      typeof received === 'object' &&
      'success' in received &&
      'data' in received &&
      'errors' in received &&
      'warnings' in received &&
      'metadata' in received;

    if (pass) {
      return {
        message: () => `expected ${received} not to be a valid ParseResult`,
        pass: true,
      };
    } else {
      return {
        message: () => `expected ${received} to be a valid ParseResult`,
        pass: false,
      };
    }
  },

  toHaveParseError(received, errorType) {
    if (!received || !received.errors) {
      return {
        message: () => `expected result to have errors`,
        pass: false,
      };
    }

    const hasError = received.errors.some((e: any) => e.type === errorType);

    if (hasError) {
      return {
        message: () => `expected not to have error of type ${errorType}`,
        pass: true,
      };
    } else {
      return {
        message: () => `expected to have error of type ${errorType}`,
        pass: false,
      };
    }
  },
});

// Расширяем типы для TypeScript
declare global {
  namespace jest {
    interface Matchers<R> {
      toBeValidParseResult(): R;
      toHaveParseError(errorType: string): R;
    }
  }
}
