/**
 * Path Converter v1.0.0
 *
 * Конвертация между различными форматами путей к JSON элементам
 *
 * ВОЗМОЖНОСТИ:
 * ============
 * - Конвертация между JSON Pointer (RFC 6901) и Property Path
 * - Конвертация в JSONPath формат
 * - Конвертация в jq формат
 * - Нормализация путей
 * - Валидация форматов
 * - Кэширование результатов конвертации
 * - Метрики производительности
 * - Singleton паттерн
 *
 * ПОДДЕРЖИВАЕМЫЕ ФОРМАТЫ:
 * =======================
 * 1. JSON Pointer (RFC 6901): /components/0/type
 * 2. Property Path:          components[0].type
 * 3. JSONPath:               $.components[0].type
 * 4. jq:                     .components[0].type
 * 5. Dot notation:           components.0.type
 *
 * ИСПОЛЬЗОВАНИЕ:
 * ==============
 * ```typescript
 * const converter = PathConverter.getInstance();
 *
 * // JSON Pointer -> Property Path
 * const propPath = converter.toPropertyPath('/components/0/type');
 * // => "components[0].type"
 *
 * // Property Path -> JSON Pointer
 * const pointer = converter.toJSONPointer('components[0].type');
 * // => "/components/0/type"
 *
 * // Property Path -> JSONPath
 * const jsonPath = converter.toJSONPath('components[0].type');
 * // => "$.components[0].type"
 *
 * // Property Path -> jq
 * const jqPath = converter.toJQ('components[0].type');
 * // => ".components[0].type"
 *
 * // Нормализация
 * const normalized = converter.normalize('components.0.type');
 * // => "components[0].type"
 * ```
 *
 * МЕТРИКИ:
 * ========
 * - converter.getMetrics().totalConversions - общее количество конвертаций
 * - converter.getMetrics().cacheHitRate - процент попаданий в кэш
 */

// ============================================================================
// ТИПЫ И ИНТЕРФЕЙСЫ
// ============================================================================

/**
 * Тип формата пути
 */
export type PathFormat =
  | 'json-pointer'    // RFC 6901: /components/0/type
  | 'property-path'   // components[0].type
  | 'jsonpath'        // $.components[0].type
  | 'jq'              // .components[0].type
  | 'dot-notation';   // components.0.type

/**
 * Результат конвертации пути
 */
export interface ConversionResult {
  /** Исходный путь */
  source: string;

  /** Результат конвертации */
  result: string;

  /** Исходный формат */
  sourceFormat: PathFormat;

  /** Целевой формат */
  targetFormat: PathFormat;

  /** Использован кэш */
  cached: boolean;

  /** Время конвертации в мс */
  executionTime: number;

  /** Ошибка (если была) */
  error?: string;
}

/**
 * Опции конвертации
 */
export interface ConversionOptions {
  /** Валидировать результат */
  validate?: boolean;

  /** Нормализовать перед конвертацией */
  normalize?: boolean;

  /** Экранировать специальные символы */
  escape?: boolean;
}

/**
 * Сегмент пути
 */
export interface PathSegment {
  /** Тип сегмента */
  type: 'key' | 'index';

  /** Значение (имя ключа или индекс) */
  value: string | number;

  /** Исходное представление */
  raw: string;
}

/**
 * Метрики конвертера
 */
export interface ConverterMetrics {
  /** Общее количество конвертаций */
  totalConversions: number;

  /** Попаданий в кэш */
  cacheHits: number;

  /** Промахов кэша */
  cacheMisses: number;

  /** Процент попаданий в кэш */
  cacheHitRate: number;

  /** Ошибок конвертации */
  errors: number;

  /** Среднее время конвертации (мс) */
  averageConversionTime: number;

  /** Общее время конвертации (мс) */
  totalExecutionTime: number;

  /** Распределение по типам конвертаций */
  byConversionType: {
    [key: string]: number;
  };
}

// ============================================================================
// PATH CONVERTER (SINGLETON)
// ============================================================================

/**
 * Конвертер форматов путей
 */
export class PathConverter {
  private static instance: PathConverter;

  /** Кэш конвертаций */
  private cache: Map<string, string>;

  /** Метрики */
  private metrics: ConverterMetrics;

  /**
   * Приватный конструктор (Singleton)
   */
  private constructor() {
    this.cache = new Map();
    this.metrics = {
      totalConversions: 0,
      cacheHits: 0,
      cacheMisses: 0,
      cacheHitRate: 0,
      errors: 0,
      averageConversionTime: 0,
      totalExecutionTime: 0,
      byConversionType: {},
    };
  }

  /**
   * Получение единственного экземпляра
   */
  public static getInstance(): PathConverter {
    if (!PathConverter.instance) {
      PathConverter.instance = new PathConverter();
    }
    return PathConverter.instance;
  }

  /**
   * Конвертация в JSON Pointer (RFC 6901)
   *
   * @param path - Путь в любом формате
   * @param options - Опции конвертации
   * @returns JSON Pointer
   */
  public toJSONPointer(path: string, options: ConversionOptions = {}): string {
    return this.convert(path, 'json-pointer', options);
  }

  /**
   * Конвертация в Property Path
   */
  public toPropertyPath(path: string, options: ConversionOptions = {}): string {
    return this.convert(path, 'property-path', options);
  }

  /**
   * Конвертация в JSONPath
   */
  public toJSONPath(path: string, options: ConversionOptions = {}): string {
    return this.convert(path, 'jsonpath', options);
  }

  /**
   * Конвертация в jq формат
   */
  public toJQ(path: string, options: ConversionOptions = {}): string {
    return this.convert(path, 'jq', options);
  }

  /**
   * Конвертация в dot notation
   */
  public toDotNotation(path: string, options: ConversionOptions = {}): string {
    return this.convert(path, 'dot-notation', options);
  }

  /**
   * Универсальная функция конвертации
   */
  private convert(
    path: string,
    targetFormat: PathFormat,
    options: ConversionOptions = {}
  ): string {
    const startTime = Date.now();
    this.metrics.totalConversions++;

    // Нормализуем путь если требуется
    let normalizedPath = options.normalize ? this.normalize(path) : path;

    // Проверяем кэш
    const cacheKey = `${normalizedPath}||${targetFormat}||${JSON.stringify(options)}`;
    if (this.cache.has(cacheKey)) {
      this.metrics.cacheHits++;
      this.updateCacheHitRate();
      return this.cache.get(cacheKey)!;
    }

    this.metrics.cacheMisses++;

    try {
      // Определяем исходный формат
      const sourceFormat = this.detectFormat(normalizedPath);

      // Обновляем статистику по типу конвертации
      const conversionType = `${sourceFormat}->${targetFormat}`;
      this.metrics.byConversionType[conversionType] =
        (this.metrics.byConversionType[conversionType] || 0) + 1;

      // Парсим путь в сегменты
      const segments = this.parseToSegments(normalizedPath, sourceFormat);

      // Конвертируем в целевой формат
      const result = this.segmentsToFormat(segments, targetFormat, options);

      // Кэшируем результат
      this.cache.set(cacheKey, result);

      // Обновляем метрики
      const executionTime = Date.now() - startTime;
      this.metrics.totalExecutionTime += executionTime;
      this.updateAverageConversionTime();

      return result;
    } catch (error) {
      this.metrics.errors++;
      throw error;
    } finally {
      this.updateCacheHitRate();
    }
  }

  /**
   * Определение формата пути
   */
  public detectFormat(path: string): PathFormat {
    // JSON Pointer: начинается с /
    if (path.startsWith('/')) {
      return 'json-pointer';
    }

    // JSONPath: начинается с $
    if (path.startsWith('$')) {
      return 'jsonpath';
    }

    // jq: начинается с .
    if (path.startsWith('.')) {
      return 'jq';
    }

    // Dot notation: содержит только точки без скобок
    if (!path.includes('[') && path.includes('.')) {
      return 'dot-notation';
    }

    // Property Path: по умолчанию
    return 'property-path';
  }

  /**
   * Парсинг пути в сегменты
   */
  private parseToSegments(path: string, format: PathFormat): PathSegment[] {
    const segments: PathSegment[] = [];

    switch (format) {
      case 'json-pointer':
        return this.parseJSONPointer(path);

      case 'property-path':
        return this.parsePropertyPath(path);

      case 'jsonpath':
        return this.parseJSONPath(path);

      case 'jq':
        return this.parseJQ(path);

      case 'dot-notation':
        return this.parseDotNotation(path);

      default:
        throw new Error(`Unknown format: ${format}`);
    }
  }

  /**
   * Парсинг JSON Pointer
   */
  private parseJSONPointer(path: string): PathSegment[] {
    if (path === '' || path === '/') {
      return [];
    }

    const parts = path.split('/').slice(1); // Убираем первый пустой элемент
    return parts.map((part) => {
      // Декодируем экранирование: ~0 -> ~, ~1 -> /
      const decoded = part.replace(/~1/g, '/').replace(/~0/g, '~');

      // Проверяем, является ли индексом
      const index = parseInt(decoded, 10);
      if (!isNaN(index) && String(index) === decoded) {
        return { type: 'index', value: index, raw: part };
      }

      return { type: 'key', value: decoded, raw: part };
    });
  }

  /**
   * Парсинг Property Path
   */
  private parsePropertyPath(path: string): PathSegment[] {
    const segments: PathSegment[] = [];
    let current = '';
    let inBracket = false;

    for (let i = 0; i < path.length; i++) {
      const char = path[i];

      if (char === '[') {
        if (current) {
          segments.push({ type: 'key', value: current, raw: current });
          current = '';
        }
        inBracket = true;
        continue;
      }

      if (char === ']' && inBracket) {
        const index = parseInt(current, 10);
        if (!isNaN(index)) {
          segments.push({ type: 'index', value: index, raw: `[${current}]` });
        } else {
          segments.push({ type: 'key', value: current, raw: `[${current}]` });
        }
        current = '';
        inBracket = false;
        continue;
      }

      if (char === '.' && !inBracket) {
        if (current) {
          segments.push({ type: 'key', value: current, raw: current });
          current = '';
        }
        continue;
      }

      current += char;
    }

    if (current) {
      segments.push({ type: 'key', value: current, raw: current });
    }

    return segments;
  }

  /**
   * Парсинг JSONPath
   */
  private parseJSONPath(path: string): PathSegment[] {
    // Убираем $ в начале
    const withoutRoot = path.startsWith('$') ? path.slice(1) : path;
    return this.parsePropertyPath(withoutRoot);
  }

  /**
   * Парсинг jq формата
   */
  private parseJQ(path: string): PathSegment[] {
    // Убираем . в начале
    const withoutDot = path.startsWith('.') ? path.slice(1) : path;
    return this.parsePropertyPath(withoutDot);
  }

  /**
   * Парсинг dot notation
   */
  private parseDotNotation(path: string): PathSegment[] {
    const parts = path.split('.');
    return parts.map((part) => {
      const index = parseInt(part, 10);
      if (!isNaN(index) && String(index) === part) {
        return { type: 'index', value: index, raw: part };
      }
      return { type: 'key', value: part, raw: part };
    });
  }

  /**
   * Конвертация сегментов в целевой формат
   */
  private segmentsToFormat(
    segments: PathSegment[],
    format: PathFormat,
    options: ConversionOptions
  ): string {
    switch (format) {
      case 'json-pointer':
        return this.segmentsToJSONPointer(segments, options);

      case 'property-path':
        return this.segmentsToPropertyPath(segments);

      case 'jsonpath':
        return this.segmentsToJSONPath(segments);

      case 'jq':
        return this.segmentsToJQ(segments);

      case 'dot-notation':
        return this.segmentsToDotNotation(segments);

      default:
        throw new Error(`Unknown target format: ${format}`);
    }
  }

  /**
   * Сегменты -> JSON Pointer
   */
  private segmentsToJSONPointer(
    segments: PathSegment[],
    options: ConversionOptions
  ): string {
    if (segments.length === 0) {
      return '';
    }

    const parts = segments.map((seg) => {
      const value = String(seg.value);
      // Экранирование по RFC 6901: ~ -> ~0, / -> ~1
      if (options.escape !== false) {
        return value.replace(/~/g, '~0').replace(/\//g, '~1');
      }
      return value;
    });

    return '/' + parts.join('/');
  }

  /**
   * Сегменты -> Property Path
   */
  private segmentsToPropertyPath(segments: PathSegment[]): string {
    if (segments.length === 0) {
      return '';
    }

    return segments.reduce<string>((acc, seg) => {
      if (seg.type === 'index') {
        return `${acc}[${seg.value}]`;
      }
      return acc ? `${acc}.${seg.value}` : String(seg.value);
    }, '');
  }

  /**
   * Сегменты -> JSONPath
   */
  private segmentsToJSONPath(segments: PathSegment[]): string {
    if (segments.length === 0) {
      return '$';
    }

    const propertyPath = this.segmentsToPropertyPath(segments);
    return `$.${propertyPath}`;
  }

  /**
   * Сегменты -> jq
   */
  private segmentsToJQ(segments: PathSegment[]): string {
    if (segments.length === 0) {
      return '.';
    }

    const propertyPath = this.segmentsToPropertyPath(segments);
    return `.${propertyPath}`;
  }

  /**
   * Сегменты -> Dot Notation
   */
  private segmentsToDotNotation(segments: PathSegment[]): string {
    return segments.map((seg) => String(seg.value)).join('.');
  }

  /**
   * Нормализация пути
   */
  public normalize(path: string): string {
    // Определяем формат
    const format = this.detectFormat(path);

    // Парсим в сегменты
    const segments = this.parseToSegments(path, format);

    // Конвертируем в property path (нормализованный формат)
    return this.segmentsToPropertyPath(segments);
  }

  /**
   * Валидация пути
   */
  public validate(path: string, format?: PathFormat): boolean {
    try {
      const detectedFormat = format || this.detectFormat(path);
      this.parseToSegments(path, detectedFormat);
      return true;
    } catch {
      return false;
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
   * Обновление среднего времени конвертации
   */
  private updateAverageConversionTime(): void {
    const total = this.metrics.totalConversions;
    if (total > 0) {
      this.metrics.averageConversionTime =
        this.metrics.totalExecutionTime / total;
    }
  }

  /**
   * Получение метрик
   */
  public getMetrics(): ConverterMetrics {
    return { ...this.metrics };
  }

  /**
   * Сброс метрик
   */
  public resetMetrics(): void {
    this.metrics = {
      totalConversions: 0,
      cacheHits: 0,
      cacheMisses: 0,
      cacheHitRate: 0,
      errors: 0,
      averageConversionTime: 0,
      totalExecutionTime: 0,
      byConversionType: {},
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
 * Конвертация в JSON Pointer
 */
export function toJSONPointer(path: string, options?: ConversionOptions): string {
  return PathConverter.getInstance().toJSONPointer(path, options);
}

/**
 * Конвертация в Property Path
 */
export function toPropertyPath(path: string, options?: ConversionOptions): string {
  return PathConverter.getInstance().toPropertyPath(path, options);
}

/**
 * Конвертация в JSONPath
 */
export function toJSONPath(path: string, options?: ConversionOptions): string {
  return PathConverter.getInstance().toJSONPath(path, options);
}

/**
 * Конвертация в jq формат
 */
export function toJQ(path: string, options?: ConversionOptions): string {
  return PathConverter.getInstance().toJQ(path, options);
}

/**
 * Нормализация пути
 */
export function normalizePath(path: string): string {
  return PathConverter.getInstance().normalize(path);
}

/**
 * Определение формата пути
 */
export function detectPathFormat(path: string): PathFormat {
  return PathConverter.getInstance().detectFormat(path);
}

/**
 * Валидация пути
 */
export function validatePath(path: string, format?: PathFormat): boolean {
  return PathConverter.getInstance().validate(path, format);
}

/**
 * Получение метрик конвертера
 */
export function getConverterMetrics(): ConverterMetrics {
  return PathConverter.getInstance().getMetrics();
}
