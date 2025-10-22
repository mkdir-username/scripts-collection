/**
 * Error Field Detector v1.0.0
 *
 * Умный детектор полей с ошибками в SDUI контрактах
 *
 * ВОЗМОЖНОСТИ:
 * ============
 * - Определение точного поля ошибки из сообщения
 * - Множественные паттерны распознавания
 * - Оценка уверенности в результате (high/medium/low)
 * - Поддержка вложенных полей
 * - Распознавание SDUI-специфичных ошибок
 * - Кэширование результатов для производительности
 * - Singleton паттерн для глобального доступа
 *
 * ПАТТЕРНЫ РАСПОЗНАВАНИЯ:
 * ======================
 * 1. Component type errors: "Component XXX not found" → field: type
 * 2. Required fields: "Missing required field 'xxx'" → field: xxx
 * 3. Invalid values: "Invalid value for 'xxx'" → field: xxx
 * 4. Unexpected fields: "Unexpected field 'xxx'" → field: xxx
 * 5. Property requirements: "Property 'xxx' is required" → field: xxx
 * 6. Enum validation: "must be one of [...]" → infer from path
 * 7. Type mismatches: "should be string" → infer from path
 * 8. SDUI specific: releaseVersion, stateAware, etc.
 *
 * ИСПОЛЬЗОВАНИЕ:
 * ==============
 * ```typescript
 * const detector = ErrorFieldDetector.getInstance();
 * const result = detector.detect("Component ButtonView not found", "components[0]");
 *
 * console.log(result.field);       // "type"
 * console.log(result.path);        // "components[0].type"
 * console.log(result.confidence);  // "high"
 * console.log(result.reason);      // "Component type error"
 * ```
 *
 * МЕТРИКИ:
 * ========
 * - Успешных детекций: detector.getMetrics().successfulDetections
 * - Промахов: detector.getMetrics().cacheHits
 * - Процент кэш-попаданий: detector.getMetrics().cacheHitRate
 */

// ============================================================================
// ТИПЫ И ИНТЕРФЕЙСЫ
// ============================================================================

/**
 * Уровень уверенности в определении поля
 */
export type ConfidenceLevel = 'high' | 'medium' | 'low';

/**
 * Информация о найденном поле с ошибкой
 */
export interface ErrorFieldInfo {
  /** Название поля с ошибкой (null если не удалось определить) */
  field: string | null;

  /** Полный путь к полю */
  path: string;

  /** Уровень уверенности в результате */
  confidence: ConfidenceLevel;

  /** Причина/метод определения */
  reason: string;
}

/**
 * Паттерн распознавания ошибки
 */
interface DetectionPattern {
  /** Регулярное выражение для поиска */
  regex: RegExp;

  /** Функция извлечения имени поля из match */
  extract: (match: RegExpMatchArray, path: string) => ErrorFieldInfo;

  /** Описание паттерна для отладки */
  description: string;

  /** Приоритет паттерна (больше = выше) */
  priority: number;
}

/**
 * Метрики работы детектора
 */
export interface DetectorMetrics {
  /** Общее количество запросов */
  totalRequests: number;

  /** Успешных детекций (confidence: high/medium) */
  successfulDetections: number;

  /** Попаданий в кэш */
  cacheHits: number;

  /** Промахов кэша */
  cacheMisses: number;

  /** Процент попаданий в кэш */
  cacheHitRate: number;

  /** Распределение по confidence */
  byConfidence: {
    high: number;
    medium: number;
    low: number;
  };
}

// ============================================================================
// ERROR FIELD DETECTOR (SINGLETON)
// ============================================================================

/**
 * Детектор полей с ошибками
 *
 * Использует Singleton паттерн для глобального доступа и переиспользования кэша
 */
export class ErrorFieldDetector {
  private static instance: ErrorFieldDetector;

  /** Кэш результатов: key = message + path */
  private cache: Map<string, ErrorFieldInfo>;

  /** Паттерны распознавания (упорядочены по приоритету) */
  private patterns: DetectionPattern[];

  /** Метрики работы */
  private metrics: DetectorMetrics;

  /**
   * Приватный конструктор (Singleton)
   */
  private constructor() {
    this.cache = new Map();
    this.metrics = {
      totalRequests: 0,
      successfulDetections: 0,
      cacheHits: 0,
      cacheMisses: 0,
      cacheHitRate: 0,
      byConfidence: { high: 0, medium: 0, low: 0 },
    };

    // Инициализация паттернов (упорядочены по приоритету)
    this.patterns = this.initializePatterns();
  }

  /**
   * Получение единственного экземпляра детектора
   */
  public static getInstance(): ErrorFieldDetector {
    if (!ErrorFieldDetector.instance) {
      ErrorFieldDetector.instance = new ErrorFieldDetector();
    }
    return ErrorFieldDetector.instance;
  }

  /**
   * Инициализация паттернов распознавания
   */
  private initializePatterns(): DetectionPattern[] {
    return [
      // ПАТТЕРН 1: Component type errors (highest priority)
      {
        regex: /Component\s+(\w+)\s+not found/i,
        priority: 100,
        description: 'Component type error',
        extract: (_match, path) => ({
          field: 'type',
          path: path ? `${path}.type` : 'type',
          confidence: 'high',
          reason: 'Component type error',
        }),
      },

      // ПАТТЕРН 2: Missing required field
      {
        regex: /Missing required field ['"](\w+)['"]/i,
        priority: 95,
        description: 'Missing required field',
        extract: (match, path) => ({
          field: match[1] ?? null,
          path: path ? `${path}.${match[1] ?? ''}` : (match[1] ?? ''),
          confidence: 'high',
          reason: 'Explicit field name in error message',
        }),
      },

      // ПАТТЕРН 3: Invalid value for field
      {
        regex: /Invalid value for ['"](\w+)['"]/i,
        priority: 95,
        description: 'Invalid value error',
        extract: (match, path) => ({
          field: match[1] ?? null,
          path: path ? `${path}.${match[1] ?? ''}` : (match[1] ?? ''),
          confidence: 'high',
          reason: 'Explicit field name in error message',
        }),
      },

      // ПАТТЕРН 4: Unexpected field(s)
      {
        regex: /Unexpected field(?:s)?\s+(?:found\s+)?['"]?(\w+)['"]?/i,
        priority: 90,
        description: 'Unexpected field error',
        extract: (match, path) => ({
          field: match[1] ?? null,
          path: path ? `${path}.${match[1] ?? ''}` : (match[1] ?? ''),
          confidence: 'high',
          reason: 'Explicit field name in error message',
        }),
      },

      // ПАТТЕРН 5: Property requirement
      {
        regex: /Property ['"](\w+)['"] is required/i,
        priority: 90,
        description: 'Property requirement',
        extract: (match, path) => ({
          field: match[1] ?? null,
          path: path ? `${path}.${match[1] ?? ''}` : (match[1] ?? ''),
          confidence: 'high',
          reason: 'Property requirement error',
        }),
      },

      // ПАТТЕРН 6: Field must be ...
      {
        regex: /Field ['"](\w+)['"] must be/i,
        priority: 85,
        description: 'Field constraint violation',
        extract: (match, path) => ({
          field: match[1] ?? null,
          path: path ? `${path}.${match[1] ?? ''}` : (match[1] ?? ''),
          confidence: 'high',
          reason: 'Field constraint in error message',
        }),
      },

      // ПАТТЕРН 7: Enum validation (без явного имени поля)
      {
        regex: /must be (?:one of|equal to)\s+(.+)/i,
        priority: 60,
        description: 'Enum validation error',
        extract: (_match, path) => {
          const segments = path.split(/[.\[\]]/).filter(Boolean);
          const lastSegment = segments[segments.length - 1] || '';
          return {
            field: lastSegment,
            path,
            confidence: 'medium',
            reason: 'Enum validation error on last path segment',
          };
        },
      },

      // ПАТТЕРН 8: Type mismatch
      {
        regex: /should be (\w+)/i,
        priority: 55,
        description: 'Type mismatch',
        extract: (_match, path) => {
          const segments = path.split(/[.\[\]]/).filter(Boolean);
          const lastSegment = segments[segments.length - 1] || '';
          return {
            field: lastSegment,
            path,
            confidence: 'medium',
            reason: 'Type mismatch on last path segment',
          };
        },
      },

      // ПАТТЕРН 9: SDUI - releaseVersion
      {
        regex: /releaseVersion|notReleased|willNotBeReleased/i,
        priority: 70,
        description: 'Release version error',
        extract: (_match, path) => ({
          field: 'releaseVersion',
          path: path ? `${path}.releaseVersion` : 'releaseVersion',
          confidence: 'medium',
          reason: 'Release version related error',
        }),
      },

      // ПАТТЕРН 10: SDUI - stateAware
      {
        regex: /StateAware|stateAware/,
        priority: 70,
        description: 'StateAware pattern error',
        extract: (_match, path) => ({
          field: 'stateAware',
          path: path ? `${path}.stateAware` : 'stateAware',
          confidence: 'medium',
          reason: 'StateAware pattern error',
        }),
      },

      // ПАТТЕРН 11: SDUI - deprecated
      {
        regex: /deprecated|deprecatedVersion/i,
        priority: 65,
        description: 'Deprecation error',
        extract: (_match, path) => ({
          field: 'deprecatedVersion',
          path: path ? `${path}.deprecatedVersion` : 'deprecatedVersion',
          confidence: 'medium',
          reason: 'Deprecation related error',
        }),
      },

      // ПАТТЕРН 12: Data binding errors
      {
        regex: /binding|dataBinding|\$\{/,
        priority: 60,
        description: 'Data binding error',
        extract: (_match, path) => {
          const segments = path.split(/[.\[\]]/).filter(Boolean);
          const lastSegment = segments[segments.length - 1] || '';
          return {
            field: lastSegment,
            path,
            confidence: 'medium',
            reason: 'Data binding related error',
          };
        },
      },
    ];
  }

  /**
   * Определение поля ошибки из сообщения
   *
   * @param message - Сообщение об ошибке
   * @param path - Путь к объекту с ошибкой
   * @returns Информация о найденном поле
   */
  public detect(message: string, path: string = ''): ErrorFieldInfo {
    this.metrics.totalRequests++;

    // Проверяем кэш
    const cacheKey = `${message}||${path}`;
    if (this.cache.has(cacheKey)) {
      this.metrics.cacheHits++;
      this.updateCacheHitRate();
      return this.cache.get(cacheKey)!;
    }

    this.metrics.cacheMisses++;

    // Сортируем паттерны по приоритету (если еще не отсортированы)
    const sortedPatterns = this.patterns.sort((a, b) => b.priority - a.priority);

    // Пытаемся найти совпадение
    for (const pattern of sortedPatterns) {
      const match = message.match(pattern.regex);
      if (match) {
        const result = pattern.extract(match, path);

        // Кэшируем результат
        this.cache.set(cacheKey, result);

        // Обновляем метрики
        this.updateMetrics(result);

        return result;
      }
    }

    // Fallback: используем последний сегмент пути
    const fallbackResult = this.fallbackDetection(path);
    this.cache.set(cacheKey, fallbackResult);
    this.updateMetrics(fallbackResult);

    return fallbackResult;
  }

  /**
   * Fallback детекция (когда ни один паттерн не сработал)
   */
  private fallbackDetection(path: string): ErrorFieldInfo {
    if (!path) {
      return {
        field: null,
        path: '',
        confidence: 'low',
        reason: 'Could not detect specific field',
      };
    }

    const segments = path.split(/[.\[\]]/).filter(Boolean);
    if (segments.length > 0) {
      const lastSegment = segments[segments.length - 1] ?? null;
      return {
        field: lastSegment,
        path,
        confidence: 'low',
        reason: 'Inferred from last path segment',
      };
    }

    return {
      field: null,
      path,
      confidence: 'low',
      reason: 'Could not detect specific field',
    };
  }

  /**
   * Обновление метрик
   */
  private updateMetrics(result: ErrorFieldInfo): void {
    // Обновляем счетчики по confidence
    this.metrics.byConfidence[result.confidence]++;

    // Считаем успешными детекции с high/medium confidence
    if (result.confidence === 'high' || result.confidence === 'medium') {
      this.metrics.successfulDetections++;
    }

    this.updateCacheHitRate();
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
   * Получение текущих метрик
   */
  public getMetrics(): DetectorMetrics {
    return { ...this.metrics };
  }

  /**
   * Сброс метрик
   */
  public resetMetrics(): void {
    this.metrics = {
      totalRequests: 0,
      successfulDetections: 0,
      cacheHits: 0,
      cacheMisses: 0,
      cacheHitRate: 0,
      byConfidence: { high: 0, medium: 0, low: 0 },
    };
  }

  /**
   * Очистка кэша
   */
  public clearCache(): void {
    this.cache.clear();
  }

  /**
   * Получение размера кэша
   */
  public getCacheSize(): number {
    return this.cache.size;
  }

  /**
   * Добавление кастомного паттерна
   */
  public addPattern(pattern: DetectionPattern): void {
    this.patterns.push(pattern);
    // Сортируем по приоритету
    this.patterns.sort((a, b) => b.priority - a.priority);
  }
}

// ============================================================================
// ЭКСПОРТ CONVENIENCE ФУНКЦИИ
// ============================================================================

/**
 * Convenience функция для быстрого доступа
 */
export function detectErrorField(message: string, path: string = ''): ErrorFieldInfo {
  return ErrorFieldDetector.getInstance().detect(message, path);
}

/**
 * Получение метрик детектора
 */
export function getDetectorMetrics(): DetectorMetrics {
  return ErrorFieldDetector.getInstance().getMetrics();
}

/**
 * Сброс состояния детектора
 */
export function resetDetector(): void {
  const detector = ErrorFieldDetector.getInstance();
  detector.resetMetrics();
  detector.clearCache();
}
