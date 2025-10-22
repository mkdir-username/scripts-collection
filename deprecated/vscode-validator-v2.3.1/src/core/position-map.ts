/**
 * Enhanced Position Map Module
 *
 * Оптимизированная карта позиций для быстрого поиска строк/колонок по JSON paths.
 * Построение за O(n), поиск за O(1) с использованием Map и кэширования.
 *
 * @module core/position-map
 * @version 2.3.1
 */

import type { ConfigManager } from './config';

/**
 * Информация о позиции в файле
 */
export interface PositionInfo {
  /** Номер строки (начиная с 1) */
  readonly line: number;
  /** Номер колонки (начиная с 1) */
  readonly column: number;
  /** Смещение от начала файла в символах */
  readonly offset: number;
  /** Длина токена в символах */
  readonly length?: number;
  /** Родительский путь */
  readonly parent?: string;
}

/**
 * Статистика построения Position Map
 */
export interface PositionMapStats {
  /** Количество индексированных JSON Pointers */
  readonly pointerCount: number;
  /** Количество индексированных property paths */
  readonly pathCount: number;
  /** Количество записей в nested cache */
  readonly nestedCacheSize: number;
  /** Общее количество строк */
  readonly totalLines: number;
  /** Время построения в миллисекундах */
  readonly buildTimeMs: number;
  /** Размер исходного текста в символах */
  readonly sourceLength: number;
}

/**
 * Результат поиска позиции
 */
export interface PositionSearchResult {
  /** Найденная позиция */
  readonly position: PositionInfo | null;
  /** Уровень уверенности в результате */
  readonly confidence: 'exact' | 'parent' | 'fallback' | 'none';
  /** Причина результата */
  readonly reason: string;
}

/**
 * Enhanced Position Map
 *
 * Карта позиций с оптимизированным построением и поиском.
 * Поддерживает JSON Pointers (RFC 6901) и property paths (lodash-style).
 *
 * ОСОБЕННОСТИ v2.3.1:
 * - O(n) построение за один проход
 * - O(1) поиск через Map
 * - Кэширование вложенных путей
 * - Отслеживание родительских связей
 * - Сохранение длины токенов
 * - Поддержка массивов любой вложенности
 *
 * @example
 * ```typescript
 * const builder = new PositionMapBuilder(config);
 * const positionMap = builder.build(jsonText);
 *
 * // Поиск по JSON Pointer
 * const result = positionMap.findByPointer('/components/0/type');
 * console.log(result.position?.line); // 42
 *
 * // Поиск по property path
 * const result2 = positionMap.findByPath('components[0].type');
 * console.log(result2.position?.line); // 42
 * ```
 */
export class PositionMap {
  private readonly byPointer: ReadonlyMap<string, PositionInfo>;
  private readonly byPath: ReadonlyMap<string, PositionInfo>;
  private readonly nestedCache: ReadonlyMap<string, readonly PositionInfo[]>;
  private readonly stats: PositionMapStats;

  constructor(
    byPointer: Map<string, PositionInfo>,
    byPath: Map<string, PositionInfo>,
    nestedCache: Map<string, PositionInfo[]>,
    stats: PositionMapStats
  ) {
    this.byPointer = byPointer;
    this.byPath = byPath;
    this.nestedCache = nestedCache;
    this.stats = stats;
  }

  /**
   * Найти позицию по JSON Pointer (RFC 6901)
   *
   * @param pointer - JSON Pointer (например, '/components/0/type')
   * @returns Результат поиска
   */
  public findByPointer(pointer: string): PositionSearchResult {
    // Прямой поиск
    if (this.byPointer.has(pointer)) {
      return {
        position: this.byPointer.get(pointer)!,
        confidence: 'exact',
        reason: 'Direct match by JSON Pointer',
      };
    }

    // Поиск родительского пути
    const segments = this.parsePointer(pointer);
    for (let i = segments.length - 1; i >= 0; i--) {
      const parentPointer = this.buildPointer(segments.slice(0, i));
      if (this.byPointer.has(parentPointer)) {
        return {
          position: this.byPointer.get(parentPointer)!,
          confidence: 'parent',
          reason: `Found parent pointer: ${parentPointer}`,
        };
      }
    }

    return {
      position: null,
      confidence: 'none',
      reason: 'No matching pointer found',
    };
  }

  /**
   * Найти позицию по property path
   *
   * @param path - Property path (например, 'components[0].type')
   * @returns Результат поиска
   */
  public findByPath(path: string): PositionSearchResult {
    // Прямой поиск
    if (this.byPath.has(path)) {
      return {
        position: this.byPath.get(path)!,
        confidence: 'exact',
        reason: 'Direct match by property path',
      };
    }

    // Поиск через nested cache
    const segments = this.parsePropertyPath(path);
    for (let i = segments.length; i > 0; i--) {
      const partialPath = segments.slice(0, i).join('.');
      if (this.nestedCache.has(partialPath)) {
        const positions = this.nestedCache.get(partialPath)!;
        if (positions.length > 0) {
          return {
            position: positions[0] ?? null,
            confidence: 'parent',
            reason: `Found in nested cache: ${partialPath}`,
          };
        }
      }
    }

    // Поиск родительского пути
    for (let i = segments.length - 1; i >= 0; i--) {
      const parentPath = this.buildPropertyPath(segments.slice(0, i));
      if (this.byPath.has(parentPath)) {
        return {
          position: this.byPath.get(parentPath)!,
          confidence: 'parent',
          reason: `Found parent path: ${parentPath}`,
        };
      }
    }

    return {
      position: null,
      confidence: 'none',
      reason: 'No matching path found',
    };
  }

  /**
   * Найти позицию с автоопределением типа пути
   *
   * @param pathOrPointer - JSON Pointer или property path
   * @returns Результат поиска
   */
  public find(pathOrPointer: string): PositionSearchResult {
    // Определяем тип пути
    if (pathOrPointer.startsWith('/')) {
      return this.findByPointer(pathOrPointer);
    }
    return this.findByPath(pathOrPointer);
  }

  /**
   * Получить номер строки по пути (упрощенный API)
   *
   * @param pathOrPointer - JSON Pointer или property path
   * @returns Номер строки или 1 (fallback)
   */
  public getLineNumber(pathOrPointer: string): number {
    const result = this.find(pathOrPointer);
    return result.position?.line || 1;
  }

  /**
   * Получить детальную информацию о позиции
   *
   * @param pathOrPointer - JSON Pointer или property path
   * @returns Информация о позиции или null
   */
  public getPositionInfo(pathOrPointer: string): PositionInfo | null {
    const result = this.find(pathOrPointer);
    return result.position;
  }

  /**
   * Получить статистику карты позиций
   */
  public getStats(): PositionMapStats {
    return this.stats;
  }

  /**
   * Преобразовать property path в JSON Pointer
   *
   * @param path - Property path (например, 'a.b[0].c')
   * @returns JSON Pointer (например, '/a/b/0/c')
   */
  public pathToPointer(path: string): string {
    const segments = this.parsePropertyPath(path);
    return this.buildPointer(segments);
  }

  /**
   * Преобразовать JSON Pointer в property path
   *
   * @param pointer - JSON Pointer (например, '/a/b/0/c')
   * @returns Property path (например, 'a.b[0].c')
   */
  public pointerToPath(pointer: string): string {
    const segments = this.parsePointer(pointer);
    return this.buildPropertyPath(segments);
  }

  /**
   * Парсинг JSON Pointer
   */
  private parsePointer(pointer: string): string[] {
    if (!pointer || pointer === '/') {
      return [];
    }

    return pointer
      .split('/')
      .slice(1) // Пропускаем первый пустой элемент
      .map((seg) => seg.replace(/~1/g, '/').replace(/~0/g, '~')); // RFC 6901 unescape
  }

  /**
   * Построение JSON Pointer из сегментов
   */
  private buildPointer(segments: string[]): string {
    if (segments.length === 0) {
      return '/';
    }

    return '/' + segments
      .map((seg) => seg.replace(/~/g, '~0').replace(/\//g, '~1')) // RFC 6901 escape
      .join('/');
  }

  /**
   * Парсинг property path
   */
  private parsePropertyPath(path: string): string[] {
    return path.split(/[.\[\]]/).filter(Boolean);
  }

  /**
   * Построение property path из сегментов
   */
  private buildPropertyPath(segments: string[]): string {
    return segments.reduce<string>((acc, seg, idx) => {
      if (idx === 0) {
        return seg;
      }
      // Проверяем является ли сегмент индексом массива
      if (/^\d+$/.test(seg)) {
        return `${acc}[${seg}]`;
      }
      return `${acc}.${seg}`;
    }, '');
  }
}

/**
 * Builder для Position Map
 *
 * Строит оптимизированную карту позиций за один проход по тексту.
 *
 * @example
 * ```typescript
 * const builder = new PositionMapBuilder(config);
 * const positionMap = builder.build(jsonText);
 * ```
 */
export class PositionMapBuilder {
  private readonly verbose: boolean;

  constructor(config: ConfigManager) {
    this.verbose = config.isVerbose();
  }

  /**
   * Построить Position Map
   *
   * @param jsonText - Исходный текст JSON
   * @returns Position Map
   */
  public build(jsonText: string): PositionMap {
    const startTime = Date.now();

    const byPointer = new Map<string, PositionInfo>();
    const byPath = new Map<string, PositionInfo>();
    const nestedCache = new Map<string, PositionInfo[]>();

    let line = 1;
    let column = 1;
    let offset = 0;

    // Стек для отслеживания текущего пути
    const pathStack: Array<string | number> = [];
    const parentStack: string[] = [];

    let inString = false;
    let escaped = false;
    let currentKey = '';
    let collectingKey = false;
    let keyStartOffset = 0;
    let arrayIndex = 0;
    let arrayStack: number[] = [];

    const savePosition = (
      path: Array<string | number>,
      tokenLength: number = 0
    ): void => {
      if (path.length === 0) return;

      const pointer = this.buildPointer(path);
      const propertyPath = this.buildPropertyPath(path);
      const parentPath = parentStack.length > 0
        ? parentStack[parentStack.length - 1]
        : undefined;

      const pos: PositionInfo = {
        line,
        column,
        offset,
        length: tokenLength,
        parent: parentPath,
      };

      byPointer.set(pointer, pos);
      byPath.set(propertyPath, pos);

      // Кэширование для вложенных путей
      const segments = propertyPath.split(/[.\[\]]/).filter(Boolean);
      for (let i = 1; i <= segments.length; i++) {
        const partialPath = segments.slice(0, i).join('.');
        if (!nestedCache.has(partialPath)) {
          nestedCache.set(partialPath, []);
        }
        nestedCache.get(partialPath)!.push(pos);
      }

      if (this.verbose) {
        console.log(`   [Position Map] ${propertyPath} -> line ${line}, col ${column}`);
      }
    };

    // Основной цикл парсинга
    for (let i = 0; i < jsonText.length; i++) {
      const char = jsonText[i];
      const prevChar = jsonText[i - 1] || '';
      const nextChar = jsonText[i + 1] || '';

      // Обработка escape-последовательностей
      if (escaped) {
        escaped = false;
        column++;
        offset++;
        continue;
      }

      if (char === '\\' && inString) {
        escaped = true;
        column++;
        offset++;
        continue;
      }

      // Обработка строк
      if (char === '"') {
        if (inString) {
          inString = false;
          if (collectingKey && nextChar === ':') {
            // Завершили сбор ключа
            const tokenLength = offset - keyStartOffset + 1;
            pathStack.push(currentKey);

            // Обновляем стек родительских путей
            const currentPath = this.buildPropertyPath(pathStack);
            parentStack.push(currentPath);

            savePosition(pathStack, tokenLength);
            collectingKey = false;
            currentKey = '';
          }
        } else {
          inString = true;
          keyStartOffset = offset;
          // Начинаем собирать ключ
          if (
            prevChar === '{' ||
            prevChar === ',' ||
            prevChar === '\n' ||
            prevChar === ' '
          ) {
            collectingKey = true;
            currentKey = '';
          }
        }
        column++;
        offset++;
        continue;
      }

      // Собираем имя ключа
      if (inString && collectingKey) {
        currentKey += char;
      }

      if (!inString) {
        // Начало массива
        if (char === '[') {
          arrayStack.push(arrayIndex);
          arrayIndex = 0;
        }

        // Конец объекта
        if (char === '}') {
          if (pathStack.length > 0) {
            pathStack.pop();
            if (parentStack.length > 0) {
              parentStack.pop();
            }
          }
        }

        // Конец массива
        if (char === ']') {
          if (pathStack.length > 0) {
            pathStack.pop();
          }
          if (arrayStack.length > 0) {
            arrayIndex = arrayStack.pop()!;
          }
        }

        // Запятая
        if (char === ',') {
          const parent = pathStack[pathStack.length - 1];
          // Проверяем, находимся ли в массиве
          if (
            typeof parent === 'number' ||
            (pathStack.length > 0 &&
              jsonText.lastIndexOf('[', i) > jsonText.lastIndexOf('{', i))
          ) {
            if (
              pathStack.length > 0 &&
              typeof pathStack[pathStack.length - 1] === 'number'
            ) {
              pathStack.pop();
            }
            arrayIndex++;
            pathStack.push(arrayIndex);
            savePosition(pathStack);
          } else {
            // Запятая в объекте
            if (pathStack.length > 0) {
              pathStack.pop();
              if (parentStack.length > 0) {
                parentStack.pop();
              }
            }
          }
        }

        // Двоеточие после ключа
        if (char === ':' && pathStack.length > 0) {
          let j = i + 1;
          while (
            j < jsonText.length &&
            (jsonText[j] === ' ' || jsonText[j] === '\n')
          ) {
            j++;
          }

          if (j < jsonText.length && jsonText[j] === '[') {
            // Массив - добавляем индекс 0
            pathStack.push(0);
            savePosition(pathStack);
          }
        }
      }

      // Обновление позиции
      if (char === '\n') {
        line++;
        column = 1;
      } else {
        column++;
      }
      offset++;
    }

    const buildTimeMs = Date.now() - startTime;

    const stats: PositionMapStats = {
      pointerCount: byPointer.size,
      pathCount: byPath.size,
      nestedCacheSize: nestedCache.size,
      totalLines: line,
      buildTimeMs,
      sourceLength: jsonText.length,
    };

    if (this.verbose) {
      console.log('');
      console.log(`   ✓ Position Map Statistics:`);
      console.log(`     - Pointers indexed: ${stats.pointerCount}`);
      console.log(`     - Paths indexed: ${stats.pathCount}`);
      console.log(`     - Nested cache entries: ${stats.nestedCacheSize}`);
      console.log(`     - Build time: ${stats.buildTimeMs}ms`);
      console.log('');
    }

    return new PositionMap(byPointer, byPath, nestedCache, stats);
  }

  /**
   * Построение JSON Pointer из массива сегментов
   */
  private buildPointer(path: Array<string | number>): string {
    if (path.length === 0) return '/';

    return '/' + path
      .map((p) => String(p).replace(/~/g, '~0').replace(/\//g, '~1'))
      .join('/');
  }

  /**
   * Построение property path из массива сегментов
   */
  private buildPropertyPath(path: Array<string | number>): string {
    return path.reduce<string>((acc, segment) => {
      if (typeof segment === 'number') {
        return `${acc}[${segment}]`;
      }
      return acc ? `${acc}.${segment}` : String(segment);
    }, '');
  }
}
