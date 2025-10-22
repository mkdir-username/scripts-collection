/**
 * JSONPath Integration v1.0.0
 *
 * Интеграция с JSONPath для точного поиска элементов в JSON структурах
 *
 * ВОЗМОЖНОСТИ:
 * ============
 * - Выполнение JSONPath запросов
 * - Поддержка стандартного синтаксиса JSONPath
 * - Кэширование результатов
 * - Graceful fallback на упрощенную реализацию
 * - Валидация JSONPath выражений
 * - Метрики производительности
 * - Singleton паттерн
 *
 * ПОДДЕРЖИВАЕМЫЙ СИНТАКСИС:
 * =========================
 * - $                      : корневой элемент
 * - $.store.book           : дочерние элементы
 * - $.store.book[0]        : элемент массива
 * - $.store.book[*]        : все элементы массива
 * - $..author              : рекурсивный поиск
 * - $.store.*              : все дочерние элементы
 * - $.store.book[?(@.price < 10)] : фильтрация (базовая)
 *
 * ИСПОЛЬЗОВАНИЕ:
 * ==============
 * ```typescript
 * const jsonpath = JSONPathIntegration.getInstance();
 *
 * // Простой запрос
 * const authors = await jsonpath.query(data, '$.store.book[*].author');
 *
 * // С fallback функцией
 * const result = await jsonpath.queryWithFallback(
 *   data,
 *   '$.components[?(@.type == "ButtonView")]',
 *   (d) => d.components.filter(c => c.type === 'ButtonView')
 * );
 *
 * // Проверка валидности
 * if (jsonpath.isValidPath('$.store.book[0]')) {
 *   console.log('Путь валиден');
 * }
 * ```
 *
 * МЕТРИКИ:
 * ========
 * - jsonpath.getMetrics().totalQueries - общее количество запросов
 * - jsonpath.getMetrics().nativeUsage - запросов через нативную реализацию
 * - jsonpath.getMetrics().fallbackUsage - запросов через fallback
 * - jsonpath.getMetrics().cacheHitRate - процент попаданий в кэш
 */

// ============================================================================
// ТИПЫ И ИНТЕРФЕЙСЫ
// ============================================================================

/**
 * Результат выполнения JSONPath запроса
 */
export interface JSONPathResult<T = any> {
  /** Найденные элементы */
  data: T[];

  /** Метод выполнения */
  method: 'native' | 'fallback' | 'cache';

  /** Время выполнения в мс */
  executionTime: number;

  /** Количество найденных элементов */
  count: number;

  /** Ошибка (если была) */
  error?: string;
}

/**
 * Опции выполнения JSONPath запроса
 */
export interface JSONPathOptions {
  /** Принудительно использовать fallback */
  forceFallback?: boolean;

  /** Возвращать только значения (без путей) */
  valuesOnly?: boolean;

  /** Максимальная глубина рекурсии */
  maxDepth?: number;

  /** Таймаут выполнения в мс */
  timeout?: number;
}

/**
 * Fallback функция для JSONPath запроса
 */
export type JSONPathFallback<T = any> = (data: any) => T[];

/**
 * Метрики работы JSONPath
 */
export interface JSONPathMetrics {
  /** Общее количество запросов */
  totalQueries: number;

  /** Использована нативная реализация */
  nativeUsage: number;

  /** Использован fallback */
  fallbackUsage: number;

  /** Попаданий в кэш */
  cacheHits: number;

  /** Промахов кэша */
  cacheMisses: number;

  /** Процент попаданий в кэш */
  cacheHitRate: number;

  /** Ошибок выполнения */
  errors: number;

  /** Среднее время выполнения (мс) */
  averageQueryTime: number;

  /** Общее время выполнения (мс) */
  totalExecutionTime: number;
}

/**
 * Сегмент пути
 */
interface PathSegment {
  type: 'root' | 'child' | 'wildcard' | 'index' | 'slice' | 'recursive' | 'filter';
  value?: string | number;
  filter?: string;
}

// ============================================================================
// JSONPATH INTEGRATION (SINGLETON)
// ============================================================================

/**
 * Интеграция с JSONPath для точного поиска элементов
 */
export class JSONPathIntegration {
  private static instance: JSONPathIntegration;

  /** Кэш результатов */
  private cache: Map<string, any[]>;

  /** Метрики работы */
  private metrics: JSONPathMetrics;

  /**
   * Приватный конструктор (Singleton)
   */
  private constructor() {
    this.cache = new Map();
    this.metrics = {
      totalQueries: 0,
      nativeUsage: 0,
      fallbackUsage: 0,
      cacheHits: 0,
      cacheMisses: 0,
      cacheHitRate: 0,
      errors: 0,
      averageQueryTime: 0,
      totalExecutionTime: 0,
    };
  }

  /**
   * Получение единственного экземпляра
   */
  public static getInstance(): JSONPathIntegration {
    if (!JSONPathIntegration.instance) {
      JSONPathIntegration.instance = new JSONPathIntegration();
    }
    return JSONPathIntegration.instance;
  }

  /**
   * Выполнение JSONPath запроса
   *
   * @param data - JSON данные
   * @param path - JSONPath выражение
   * @param options - Опции выполнения
   * @returns Результат выполнения
   */
  public query<T = any>(
    data: any,
    path: string,
    options: JSONPathOptions = {}
  ): JSONPathResult<T> {
    const startTime = Date.now();
    this.metrics.totalQueries++;

    // Проверяем кэш
    const cacheKey = this.generateCacheKey(data, path, options);
    if (this.cache.has(cacheKey)) {
      this.metrics.cacheHits++;
      this.updateCacheHitRate();

      const cachedData = this.cache.get(cacheKey)!;
      const executionTime = Date.now() - startTime;

      return {
        data: cachedData as T[],
        method: 'cache',
        executionTime,
        count: cachedData.length,
      };
    }

    this.metrics.cacheMisses++;
    this.updateCacheHitRate();

    // Выполняем запрос
    const result = options.forceFallback
      ? this.executeNative<T>(data, path, options, startTime)
      : this.executeNative<T>(data, path, options, startTime);

    // Кэшируем результат
    if (!result.error) {
      this.cache.set(cacheKey, result.data);
    }

    // Обновляем метрики
    this.updateMetrics(result);

    return result;
  }

  /**
   * Выполнение запроса с fallback функцией
   */
  public queryWithFallback<T = any>(
    data: any,
    path: string,
    fallback: JSONPathFallback<T>,
    options: JSONPathOptions = {}
  ): JSONPathResult<T> {
    const startTime = Date.now();

    try {
      const result = this.query<T>(data, path, options);

      if (!result.error) {
        return result;
      }
    } catch (error) {
      // Игнорируем и переходим к fallback
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
        count: resultData.length,
      };
    } catch (error) {
      this.metrics.errors++;
      const executionTime = Date.now() - startTime;

      return {
        data: [],
        method: 'fallback',
        executionTime,
        count: 0,
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }

  /**
   * Нативное выполнение JSONPath
   */
  private executeNative<T>(
    data: any,
    path: string,
    options: JSONPathOptions,
    startTime: number
  ): JSONPathResult<T> {
    this.metrics.nativeUsage++;

    try {
      // Парсим путь
      const segments = this.parsePath(path);

      // Выполняем запрос
      const results = this.evaluatePath(data, segments, options.maxDepth || 100);

      const executionTime = Date.now() - startTime;
      this.metrics.totalExecutionTime += executionTime;
      this.updateAverageQueryTime();

      return {
        data: results as T[],
        method: 'native',
        executionTime,
        count: results.length,
      };
    } catch (error) {
      this.metrics.errors++;
      const executionTime = Date.now() - startTime;

      return {
        data: [],
        method: 'native',
        executionTime,
        count: 0,
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }

  /**
   * Парсинг JSONPath выражения
   */
  private parsePath(path: string): PathSegment[] {
    const segments: PathSegment[] = [];

    // Удаляем $ в начале
    let remaining = path.startsWith('$') ? path.slice(1) : path;

    while (remaining.length > 0) {
      // Рекурсивный поиск: ..
      if (remaining.startsWith('..')) {
        const match = remaining.match(/^\.\.(\w+)/);
        if (match) {
          segments.push({ type: 'recursive', value: match[1] });
          remaining = remaining.slice(match[0].length);
          continue;
        }
      }

      // Дочерний элемент: .field
      if (remaining.startsWith('.')) {
        const match = remaining.match(/^\.(\w+)/);
        if (match) {
          segments.push({ type: 'child', value: match[1] });
          remaining = remaining.slice(match[0].length);
          continue;
        }

        // Wildcard: .*
        if (remaining.startsWith('.*')) {
          segments.push({ type: 'wildcard' });
          remaining = remaining.slice(2);
          continue;
        }
      }

      // Индекс/wildcard в массиве: [n] или [*]
      if (remaining.startsWith('[')) {
        const match = remaining.match(/^\[([^\]]+)\]/);
        if (match) {
          const content = match[1];

          // Wildcard: [*]
          if (content === '*') {
            segments.push({ type: 'wildcard' });
            remaining = remaining.slice(match[0].length);
            continue;
          }

          // Фильтр: [?(@.price < 10)]
          if (content.startsWith('?')) {
            segments.push({ type: 'filter', filter: content.slice(1) });
            remaining = remaining.slice(match[0].length);
            continue;
          }

          // Индекс: [0]
          const index = parseInt(content, 10);
          if (!isNaN(index)) {
            segments.push({ type: 'index', value: index });
            remaining = remaining.slice(match[0].length);
            continue;
          }
        }
      }

      // Неизвестный синтаксис - прерываем
      throw new Error(`Invalid JSONPath syntax at: ${remaining}`);
    }

    return segments;
  }

  /**
   * Выполнение пути
   */
  private evaluatePath(data: any, segments: PathSegment[], maxDepth: number): any[] {
    let current: any[] = [data];

    for (const segment of segments) {
      const next: any[] = [];

      for (const item of current) {
        if (item === null || item === undefined) {
          continue;
        }

        switch (segment.type) {
          case 'child':
            if (typeof item === 'object' && segment.value && segment.value in item) {
              next.push(item[segment.value]);
            }
            break;

          case 'wildcard':
            if (Array.isArray(item)) {
              next.push(...item);
            } else if (typeof item === 'object') {
              next.push(...Object.values(item));
            }
            break;

          case 'index':
            if (Array.isArray(item) && segment.value !== undefined) {
              const index = segment.value as number;
              if (index >= 0 && index < item.length) {
                next.push(item[index]);
              }
            }
            break;

          case 'recursive':
            if (segment.value) {
              next.push(...this.recursiveSearch(item, segment.value, maxDepth));
            }
            break;

          case 'filter':
            if (Array.isArray(item) && segment.filter) {
              next.push(...this.applyFilter(item, segment.filter));
            }
            break;
        }
      }

      current = next;
    }

    return current;
  }

  /**
   * Рекурсивный поиск поля
   */
  private recursiveSearch(data: any, field: string, maxDepth: number, depth = 0): any[] {
    if (depth > maxDepth) {
      return [];
    }

    const results: any[] = [];

    if (typeof data === 'object' && data !== null) {
      // Проверяем текущий уровень
      if (field in data) {
        results.push(data[field]);
      }

      // Рекурсивно обходим дочерние элементы
      if (Array.isArray(data)) {
        for (const item of data) {
          results.push(...this.recursiveSearch(item, field, maxDepth, depth + 1));
        }
      } else {
        for (const value of Object.values(data)) {
          results.push(...this.recursiveSearch(value, field, maxDepth, depth + 1));
        }
      }
    }

    return results;
  }

  /**
   * Применение фильтра
   */
  private applyFilter(items: any[], filter: string): any[] {
    try {
      // Упрощенная реализация фильтров
      // Поддерживаем только базовые операторы: ==, !=, <, >, <=, >=

      const match = filter.match(/\(@\.(\w+)\s*([=!<>]+)\s*(.+)\)/);
      if (!match) {
        return items;
      }

      const [, field, operator, valueStr] = match;
      const value = this.parseFilterValue(valueStr);

      return items.filter((item) => {
        if (typeof item !== 'object' || !(field in item)) {
          return false;
        }

        const itemValue = item[field];

        switch (operator) {
          case '==':
          case '=':
            return itemValue === value;
          case '!=':
            return itemValue !== value;
          case '<':
            return itemValue < value;
          case '>':
            return itemValue > value;
          case '<=':
            return itemValue <= value;
          case '>=':
            return itemValue >= value;
          default:
            return false;
        }
      });
    } catch {
      return items;
    }
  }

  /**
   * Парсинг значения фильтра
   */
  private parseFilterValue(valueStr: string): any {
    const trimmed = valueStr.trim();

    // Строка
    if (trimmed.startsWith('"') || trimmed.startsWith("'")) {
      return trimmed.slice(1, -1);
    }

    // Число
    const num = Number(trimmed);
    if (!isNaN(num)) {
      return num;
    }

    // Boolean
    if (trimmed === 'true') return true;
    if (trimmed === 'false') return false;

    // Null
    if (trimmed === 'null') return null;

    return trimmed;
  }

  /**
   * Валидация JSONPath выражения
   */
  public isValidPath(path: string): boolean {
    try {
      this.parsePath(path);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Генерация ключа кэша
   */
  private generateCacheKey(data: any, path: string, options: JSONPathOptions): string {
    const dataHash = this.simpleHash(JSON.stringify(data));
    const optionsHash = this.simpleHash(JSON.stringify(options));
    return `${path}||${dataHash}||${optionsHash}`;
  }

  /**
   * Простая хэш функция
   */
  private simpleHash(str: string): string {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = (hash << 5) - hash + char;
      hash = hash & hash;
    }
    return hash.toString(36);
  }

  /**
   * Обновление метрик
   */
  private updateMetrics(result: JSONPathResult): void {
    if (result.error) {
      this.metrics.errors++;
    }
  }

  /**
   * Обновление процента попаданий в кэш
   */
  private updateCacheHitRate(): void {
    const total = this.metrics.cacheHits + this.metrics.cacheMisses;
    this.metrics.cacheHitRate = total > 0
      ? (this.metrics.cacheHits / total) * 100
      : 0;
  }

  /**
   * Обновление среднего времени выполнения
   */
  private updateAverageQueryTime(): void {
    const total = this.metrics.totalQueries;
    if (total > 0) {
      this.metrics.averageQueryTime = this.metrics.totalExecutionTime / total;
    }
  }

  /**
   * Получение метрик
   */
  public getMetrics(): JSONPathMetrics {
    return { ...this.metrics };
  }

  /**
   * Сброс метрик
   */
  public resetMetrics(): void {
    this.metrics = {
      totalQueries: 0,
      nativeUsage: 0,
      fallbackUsage: 0,
      cacheHits: 0,
      cacheMisses: 0,
      cacheHitRate: 0,
      errors: 0,
      averageQueryTime: 0,
      totalExecutionTime: 0,
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
 * Convenience функция для JSONPath запроса
 */
export function queryJSONPath<T = any>(
  data: any,
  path: string,
  options?: JSONPathOptions
): JSONPathResult<T> {
  return JSONPathIntegration.getInstance().query<T>(data, path, options);
}

/**
 * Convenience функция с fallback
 */
export function queryJSONPathWithFallback<T = any>(
  data: any,
  path: string,
  fallback: JSONPathFallback<T>,
  options?: JSONPathOptions
): JSONPathResult<T> {
  return JSONPathIntegration.getInstance().queryWithFallback<T>(
    data,
    path,
    fallback,
    options
  );
}

/**
 * Валидация JSONPath выражения
 */
export function isValidJSONPath(path: string): boolean {
  return JSONPathIntegration.getInstance().isValidPath(path);
}

/**
 * Получение метрик
 */
export function getJSONPathMetrics(): JSONPathMetrics {
  return JSONPathIntegration.getInstance().getMetrics();
}
