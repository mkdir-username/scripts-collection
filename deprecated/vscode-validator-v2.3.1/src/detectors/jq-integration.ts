/**
 * JQ Integration v1.0.0
 *
 * Интеграция с jq для сложных JSON запросов
 *
 * ВОЗМОЖНОСТИ:
 * ============
 * - Выполнение jq запросов к JSON данным
 * - Кэширование результатов запросов
 * - Graceful fallback на нативный JavaScript
 * - Валидация jq синтаксиса
 * - Поддержка сложных фильтров и трансформаций
 * - Метрики производительности
 * - Singleton паттерн
 *
 * ТРЕБОВАНИЯ:
 * ===========
 * - jq должен быть установлен в системе (brew install jq / apt install jq)
 * - Для fallback режима зависимости не требуются
 *
 * ИСПОЛЬЗОВАНИЕ:
 * ==============
 * ```typescript
 * const jq = JQIntegration.getInstance();
 *
 * // Простой запрос
 * const types = await jq.query(contract, '.components[].type');
 *
 * // Сложный фильтр
 * const result = await jq.query(contract, '.components | map(select(.type == "ButtonView"))');
 *
 * // С fallback
 * const data = await jq.queryWithFallback(contract, '.data.field', (obj) => obj.data?.field);
 *
 * // Проверка доступности jq
 * if (jq.isAvailable()) {
 *   console.log('jq доступен');
 * }
 * ```
 *
 * МЕТРИКИ:
 * ========
 * - jq.getMetrics().totalQueries - общее количество запросов
 * - jq.getMetrics().jqUsage - запросов выполнено через jq
 * - jq.getMetrics().fallbackUsage - запросов выполнено через fallback
 * - jq.getMetrics().averageQueryTime - среднее время выполнения
 */

import { exec } from 'child_process';
import { promisify } from 'util';
import { writeFileSync, unlinkSync } from 'fs';
import { tmpdir } from 'os';
import { join } from 'path';

const execAsync = promisify(exec);

// ============================================================================
// ТИПЫ И ИНТЕРФЕЙСЫ
// ============================================================================

/**
 * Результат выполнения jq запроса
 */
export interface JQResult<T = any> {
  /** Результат запроса */
  data: T;

  /** Был ли использован jq или fallback */
  method: 'jq' | 'fallback' | 'cache';

  /** Время выполнения в мс */
  executionTime: number;

  /** Ошибка (если была) */
  error?: string;
}

/**
 * Опции выполнения jq запроса
 */
export interface JQOptions {
  /** Таймаут выполнения в мс (по умолчанию 5000) */
  timeout?: number;

  /** Компактный вывод JSON */
  compact?: boolean;

  /** Raw output (без кавычек для строк) */
  raw?: boolean;

  /** Null input (не передавать JSON на вход) */
  nullInput?: boolean;

  /** Принудительно использовать fallback */
  forceFallback?: boolean;
}

/**
 * Fallback функция для обработки данных
 */
export type FallbackFunction<T = any> = (data: any) => T;

/**
 * Метрики работы jq интеграции
 */
export interface JQMetrics {
  /** Общее количество запросов */
  totalQueries: number;

  /** Использовано jq */
  jqUsage: number;

  /** Использован fallback */
  fallbackUsage: number;

  /** Попаданий в кэш */
  cacheHits: number;

  /** Ошибок выполнения */
  errors: number;

  /** Среднее время выполнения (мс) */
  averageQueryTime: number;

  /** Общее время выполнения (мс) */
  totalExecutionTime: number;

  /** jq доступен в системе */
  jqAvailable: boolean;
}

// ============================================================================
// JQ INTEGRATION (SINGLETON)
// ============================================================================

/**
 * Интеграция с jq для выполнения сложных JSON запросов
 */
export class JQIntegration {
  private static instance: JQIntegration;

  /** Кэш результатов запросов: key = query + JSON hash */
  private cache: Map<string, any>;

  /** Метрики работы */
  private metrics: JQMetrics;

  /** Проверено ли наличие jq в системе */
  private jqChecked: boolean = false;

  /** Доступен ли jq */
  private jqAvailableFlag: boolean = false;

  /**
   * Приватный конструктор (Singleton)
   */
  private constructor() {
    this.cache = new Map();
    this.metrics = {
      totalQueries: 0,
      jqUsage: 0,
      fallbackUsage: 0,
      cacheHits: 0,
      errors: 0,
      averageQueryTime: 0,
      totalExecutionTime: 0,
      jqAvailable: false,
    };
  }

  /**
   * Получение единственного экземпляра
   */
  public static getInstance(): JQIntegration {
    if (!JQIntegration.instance) {
      JQIntegration.instance = new JQIntegration();
    }
    return JQIntegration.instance;
  }

  /**
   * Проверка доступности jq в системе
   */
  public async isAvailable(): Promise<boolean> {
    if (this.jqChecked) {
      return this.jqAvailableFlag;
    }

    try {
      const { stdout } = await execAsync('which jq', { timeout: 1000 });
      this.jqAvailableFlag = stdout.trim().length > 0;
    } catch {
      this.jqAvailableFlag = false;
    }

    this.jqChecked = true;
    this.metrics.jqAvailable = this.jqAvailableFlag;
    return this.jqAvailableFlag;
  }

  /**
   * Синхронная проверка доступности jq
   */
  public isAvailableSync(): boolean {
    return this.jqAvailableFlag;
  }

  /**
   * Выполнение jq запроса
   *
   * @param data - JSON данные для обработки
   * @param query - jq запрос
   * @param options - Опции выполнения
   * @returns Результат выполнения запроса
   */
  public async query<T = any>(
    data: any,
    query: string,
    options: JQOptions = {}
  ): Promise<JQResult<T>> {
    const startTime = Date.now();
    this.metrics.totalQueries++;

    // Проверяем кэш
    const cacheKey = this.generateCacheKey(data, query, options);
    if (this.cache.has(cacheKey)) {
      this.metrics.cacheHits++;
      const executionTime = Date.now() - startTime;
      return {
        data: this.cache.get(cacheKey),
        method: 'cache',
        executionTime,
      };
    }

    // Проверяем доступность jq
    if (!options.forceFallback) {
      await this.isAvailable();
    }

    // Выполняем запрос
    let result: JQResult<T>;

    if (this.jqAvailableFlag && !options.forceFallback) {
      result = await this.executeJQ<T>(data, query, options, startTime);
    } else {
      result = this.executeFallback<T>(data, query, startTime);
    }

    // Кэшируем результат (только если нет ошибки)
    if (!result.error) {
      this.cache.set(cacheKey, result.data);
    }

    // Обновляем метрики
    this.updateMetrics(result);

    return result;
  }

  /**
   * Выполнение запроса с fallback функцией
   *
   * @param data - JSON данные
   * @param query - jq запрос
   * @param fallback - Функция fallback
   * @param options - Опции
   * @returns Результат выполнения
   */
  public async queryWithFallback<T = any>(
    data: any,
    query: string,
    fallback: FallbackFunction<T>,
    options: JQOptions = {}
  ): Promise<JQResult<T>> {
    const startTime = Date.now();

    try {
      // Пытаемся выполнить через jq
      const result = await this.query<T>(data, query, options);

      if (!result.error) {
        return result;
      }
    } catch (error) {
      // Игнорируем ошибки jq, переходим к fallback
    }

    // Выполняем fallback
    this.metrics.fallbackUsage++;

    try {
      const resultData = fallback(data);
      const executionTime = Date.now() - startTime;

      this.metrics.totalExecutionTime += executionTime;
      this.updateAverageQueryTime();

      return {
        data: resultData,
        method: 'fallback',
        executionTime,
      };
    } catch (error) {
      this.metrics.errors++;
      const executionTime = Date.now() - startTime;

      return {
        data: null as T,
        method: 'fallback',
        executionTime,
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }

  /**
   * Выполнение jq через shell
   */
  private async executeJQ<T>(
    data: any,
    query: string,
    options: JQOptions,
    startTime: number
  ): Promise<JQResult<T>> {
    this.metrics.jqUsage++;

    // Создаем временный файл с данными
    const tmpFile = join(tmpdir(), `jq-input-${Date.now()}.json`);

    try {
      writeFileSync(tmpFile, JSON.stringify(data), 'utf-8');

      // Формируем команду jq
      const jqFlags: string[] = [];

      if (options.compact) {
        jqFlags.push('-c');
      }

      if (options.raw) {
        jqFlags.push('-r');
      }

      if (options.nullInput) {
        jqFlags.push('-n');
      }

      const jqCommand = `jq ${jqFlags.join(' ')} '${query.replace(/'/g, "'\\''")}' ${tmpFile}`;

      // Выполняем jq
      const { stdout, stderr } = await execAsync(jqCommand, {
        timeout: options.timeout || 5000,
        maxBuffer: 10 * 1024 * 1024, // 10MB
      });

      if (stderr) {
        throw new Error(stderr);
      }

      const executionTime = Date.now() - startTime;
      this.metrics.totalExecutionTime += executionTime;
      this.updateAverageQueryTime();

      // Парсим результат
      let resultData: T;

      if (options.raw) {
        resultData = stdout.trim() as T;
      } else {
        try {
          resultData = JSON.parse(stdout);
        } catch {
          resultData = stdout.trim() as T;
        }
      }

      return {
        data: resultData,
        method: 'jq',
        executionTime,
      };
    } catch (error) {
      this.metrics.errors++;
      const executionTime = Date.now() - startTime;

      return {
        data: null as T,
        method: 'jq',
        executionTime,
        error: error instanceof Error ? error.message : String(error),
      };
    } finally {
      // Удаляем временный файл
      try {
        unlinkSync(tmpFile);
      } catch {
        // Игнорируем ошибки удаления
      }
    }
  }

  /**
   * Fallback обработка (встроенная)
   */
  private executeFallback<T>(data: any, query: string, startTime: number): JQResult<T> {
    this.metrics.fallbackUsage++;

    try {
      // Простая реализация базовых jq операций
      const result = this.executeSimpleQuery(data, query);
      const executionTime = Date.now() - startTime;

      this.metrics.totalExecutionTime += executionTime;
      this.updateAverageQueryTime();

      return {
        data: result as T,
        method: 'fallback',
        executionTime,
      };
    } catch (error) {
      this.metrics.errors++;
      const executionTime = Date.now() - startTime;

      return {
        data: null as T,
        method: 'fallback',
        executionTime,
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }

  /**
   * Упрощенная реализация jq запросов
   */
  private executeSimpleQuery(data: any, query: string): any {
    // Удаляем ведущую точку
    let path = query.startsWith('.') ? query.slice(1) : query;

    // Обработка пустого пути
    if (!path || path === '.') {
      return data;
    }

    // Разбиваем путь на сегменты
    const segments = this.parsePath(path);

    // Обходим путь
    let current = data;

    for (const segment of segments) {
      if (current === null || current === undefined) {
        return null;
      }

      if (segment.type === 'key') {
        current = current[segment.value];
      } else if (segment.type === 'index') {
        current = current[segment.value];
      } else if (segment.type === 'all') {
        // Обработка [] - возврат всех элементов
        if (Array.isArray(current)) {
          return current;
        } else {
          return Object.values(current);
        }
      } else if (segment.type === 'map') {
        // Обработка [].field - map по массиву
        if (!Array.isArray(current)) {
          throw new Error('Cannot map over non-array');
        }
        return current.map((item) => item[segment.value]);
      }
    }

    return current;
  }

  /**
   * Парсинг пути в сегменты
   */
  private parsePath(path: string): Array<{ type: string; value: any }> {
    const segments: Array<{ type: string; value: any }> = [];
    let current = '';
    let inBracket = false;

    for (let i = 0; i < path.length; i++) {
      const char = path[i];

      if (char === '[') {
        if (current) {
          segments.push({ type: 'key', value: current });
          current = '';
        }
        inBracket = true;
        continue;
      }

      if (char === ']' && inBracket) {
        if (current === '') {
          // [] означает все элементы
          const nextChar = path[i + 1];
          if (nextChar === '.' && path[i + 2]) {
            // [].field - map operation
            i += 2; // skip ].
            let fieldName = '';
            while (i < path.length && path[i] !== '.' && path[i] !== '[') {
              fieldName += path[i];
              i++;
            }
            segments.push({ type: 'map', value: fieldName });
            i--; // откат на 1 для корректного continue
          } else {
            segments.push({ type: 'all', value: null });
          }
        } else {
          // [index]
          const index = parseInt(current, 10);
          if (isNaN(index)) {
            segments.push({ type: 'key', value: current });
          } else {
            segments.push({ type: 'index', value: index });
          }
          current = '';
        }
        inBracket = false;
        continue;
      }

      if (char === '.' && !inBracket) {
        if (current) {
          segments.push({ type: 'key', value: current });
          current = '';
        }
        continue;
      }

      current += char;
    }

    if (current) {
      segments.push({ type: 'key', value: current });
    }

    return segments;
  }

  /**
   * Генерация ключа кэша
   */
  private generateCacheKey(data: any, query: string, options: JQOptions): string {
    // Простой хэш на основе JSON.stringify
    const dataHash = this.simpleHash(JSON.stringify(data));
    const optionsHash = this.simpleHash(JSON.stringify(options));
    return `${query}||${dataHash}||${optionsHash}`;
  }

  /**
   * Простая хэш функция
   */
  private simpleHash(str: string): string {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = (hash << 5) - hash + char;
      hash = hash & hash; // Convert to 32bit integer
    }
    return hash.toString(36);
  }

  /**
   * Обновление метрик
   */
  private updateMetrics(result: JQResult): void {
    if (result.error) {
      this.metrics.errors++;
    }
  }

  /**
   * Обновление среднего времени выполнения
   */
  private updateAverageQueryTime(): void {
    const totalQueries = this.metrics.totalQueries;
    if (totalQueries > 0) {
      this.metrics.averageQueryTime = this.metrics.totalExecutionTime / totalQueries;
    }
  }

  /**
   * Получение метрик
   */
  public getMetrics(): JQMetrics {
    return { ...this.metrics };
  }

  /**
   * Сброс метрик
   */
  public resetMetrics(): void {
    this.metrics = {
      totalQueries: 0,
      jqUsage: 0,
      fallbackUsage: 0,
      cacheHits: 0,
      errors: 0,
      averageQueryTime: 0,
      totalExecutionTime: 0,
      jqAvailable: this.jqAvailableFlag,
    };
  }

  /**
   * Очистка кэша
   */
  public clearCache(): void {
    this.cache.clear();
  }

  /**
   * Размер кэша
   */
  public getCacheSize(): number {
    return this.cache.size;
  }
}

// ============================================================================
// ЭКСПОРТ CONVENIENCE ФУНКЦИЙ
// ============================================================================

/**
 * Convenience функция для выполнения jq запроса
 */
export async function jq<T = any>(
  data: any,
  query: string,
  options?: JQOptions
): Promise<JQResult<T>> {
  return JQIntegration.getInstance().query<T>(data, query, options);
}

/**
 * Convenience функция с fallback
 */
export async function jqWithFallback<T = any>(
  data: any,
  query: string,
  fallback: FallbackFunction<T>,
  options?: JQOptions
): Promise<JQResult<T>> {
  return JQIntegration.getInstance().queryWithFallback<T>(data, query, fallback, options);
}

/**
 * Проверка доступности jq
 */
export async function isJQAvailable(): Promise<boolean> {
  return JQIntegration.getInstance().isAvailable();
}

/**
 * Получение метрик jq
 */
export function getJQMetrics(): JQMetrics {
  return JQIntegration.getInstance().getMetrics();
}
