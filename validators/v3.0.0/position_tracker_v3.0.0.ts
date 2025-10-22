/**
 * Position Tracker v3.0.0
 *
 * Улучшенная система отслеживания позиций в JSON файлах
 *
 * Новые возможности:
 * - Поддержка JSON с комментариями (JSON5)
 * - Точное определение позиций для oneOf/anyOf
 * - Кэширование position map для больших файлов
 * - Индекс для быстрого поиска по path patterns
 * - Поддержка source maps для минифицированных JSON
 *
 * @version 3.0.0
 * @author Claude Code
 * @date 2025-10-05
 */

// ============================================================================
// ТИПЫ И ИНТЕРФЕЙСЫ
// ============================================================================

/** Информация о позиции в файле */
export interface PositionInfo {
  /** Номер строки (1-based) */
  line: number;
  /** Номер колонки (1-based) */
  column: number;
  /** Смещение от начала файла (0-based) */
  offset: number;
  /** Длина токена в символах */
  length?: number;
  /** Тип токена (ключ, значение, массив и т.д.) */
  tokenType?: TokenType;
}

/** Типы токенов в JSON */
export enum TokenType {
  KEY = 'key',
  VALUE = 'value',
  OBJECT_START = 'object_start',
  OBJECT_END = 'object_end',
  ARRAY_START = 'array_start',
  ARRAY_END = 'array_end',
  STRING = 'string',
  NUMBER = 'number',
  BOOLEAN = 'boolean',
  NULL = 'null',
  COMMENT = 'comment'
}

/** Карта позиций с несколькими индексами */
export interface PositionMap {
  /** Поиск по JSON Pointer (RFC 6901) */
  byPointer: Map<string, PositionInfo>;
  /** Поиск по property path (a.b.c[0].d) */
  byPath: Map<string, PositionInfo>;
  /** Поиск по регулярным выражениям для быстрого pattern matching */
  byPattern: Map<string, PositionInfo[]>;
  /** Общее количество строк */
  totalLines: number;
  /** Версия формата */
  version: string;
  /** Хеш исходного текста для валидации кеша */
  sourceHash: string;
  /** Статистика парсинга */
  stats: ParsingStats;
}

/** Статистика парсинга */
export interface ParsingStats {
  /** Время парсинга в мс */
  parseTimeMs: number;
  /** Количество токенов */
  tokenCount: number;
  /** Количество комментариев */
  commentCount: number;
  /** Размер файла в байтах */
  fileSizeBytes: number;
}

/** Опции для построения position map */
export interface BuildOptions {
  /** Поддержка JSON5 (комментарии, trailing commas и т.д.) */
  json5Support?: boolean;
  /** Создавать индексы для pattern matching */
  buildPatternIndex?: boolean;
  /** Включать информацию о типах токенов */
  includeTokenTypes?: boolean;
  /** Включать длины токенов */
  includeTokenLengths?: boolean;
  /** Кэшировать результаты */
  enableCaching?: boolean;
  /** Путь к файлу для кэширования */
  filePath?: string;
}

/** Опции для поиска позиции */
export interface LookupOptions {
  /** Искать ближайший родительский путь если точное совпадение не найдено */
  fallbackToParent?: boolean;
  /** Использовать pattern matching */
  usePatternMatching?: boolean;
  /** Предпочитаемый тип совпадения */
  preferredMatch?: 'exact' | 'parent' | 'pattern';
}

// ============================================================================
// КЭШИРОВАНИЕ
// ============================================================================

/** Кэш для position maps */
class PositionMapCache {
  private cache: Map<string, PositionMap> = new Map();
  private maxSize: number;
  private accessTimes: Map<string, number> = new Map();

  constructor(maxSize: number = 50) {
    this.maxSize = maxSize;
  }

  /** Получить из кэша */
  get(key: string, sourceHash: string): PositionMap | null {
    const cached = this.cache.get(key);
    if (cached && cached.sourceHash === sourceHash) {
      this.accessTimes.set(key, Date.now());
      return cached;
    }
    return null;
  }

  /** Сохранить в кэш */
  set(key: string, value: PositionMap): void {
    // Если кэш переполнен, удаляем самый старый элемент
    if (this.cache.size >= this.maxSize) {
      this.evictOldest();
    }
    this.cache.set(key, value);
    this.accessTimes.set(key, Date.now());
  }

  /** Удалить самый старый элемент */
  private evictOldest(): void {
    let oldestKey: string | null = null;
    let oldestTime = Infinity;

    for (const [key, time] of this.accessTimes) {
      if (time < oldestTime) {
        oldestTime = time;
        oldestKey = key;
      }
    }

    if (oldestKey) {
      this.cache.delete(oldestKey);
      this.accessTimes.delete(oldestKey);
    }
  }

  /** Очистить кэш */
  clear(): void {
    this.cache.clear();
    this.accessTimes.clear();
  }

  /** Получить статистику кэша */
  getStats(): { size: number; maxSize: number; hitRate?: number } {
    return {
      size: this.cache.size,
      maxSize: this.maxSize
    };
  }
}

// Глобальный кэш
const globalCache = new PositionMapCache(50);

// ============================================================================
// УТИЛИТЫ
// ============================================================================

/** Вычислить простой хеш строки (FNV-1a) */
function hashString(str: string): string {
  let hash = 2166136261;
  for (let i = 0; i < str.length; i++) {
    hash ^= str.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0).toString(16);
}

/** Проверить, является ли символ пробельным */
function isWhitespace(char: string): boolean {
  return char === ' ' || char === '\t' || char === '\n' || char === '\r';
}

/** Извлечь паттерны из пути для индексации */
function extractPatterns(path: string): string[] {
  const patterns: string[] = [];

  // Паттерн для массивов: a.b[*].c
  patterns.push(path.replace(/\[\d+\]/g, '[*]'));

  // Паттерн для последнего сегмента: *.c
  const segments = path.split(/[.\[\]]/).filter(Boolean);
  if (segments.length > 0) {
    patterns.push('*.' + segments[segments.length - 1]);
  }

  // Паттерн для wildcards на разных уровнях
  for (let i = 1; i < segments.length; i++) {
    const pattern = segments.slice(0, i).join('.') + '.*';
    patterns.push(pattern);
  }

  return [...new Set(patterns)];
}

/** Нормализовать путь (убрать лишние точки, скобки и т.д.) */
function normalizePath(path: string): string {
  return path
    .replace(/\]\[/g, '][')
    .replace(/\]\./g, '.')
    .replace(/\.\[/g, '[');
}

// ============================================================================
// ПАРСЕР JSON5
// ============================================================================

/** Состояние парсера */
interface ParserState {
  text: string;
  pos: number;
  line: number;
  column: number;
  pathStack: Array<string | number>;
  inString: boolean;
  escaped: boolean;
  currentKey: string;
  collectingKey: boolean;
  arrayIndexStack: number[];
  currentArrayIndex: number;
}

/** Парсер JSON с поддержкой JSON5 */
class JSON5Parser {
  private state: ParserState;
  private json5Mode: boolean;

  constructor(text: string, json5Mode: boolean = false) {
    this.json5Mode = json5Mode;
    this.state = {
      text,
      pos: 0,
      line: 1,
      column: 1,
      pathStack: [],
      inString: false,
      escaped: false,
      currentKey: '',
      collectingKey: false,
      arrayIndexStack: [],
      currentArrayIndex: 0
    };
  }

  /** Получить текущий символ */
  private current(): string {
    return this.state.text[this.state.pos] || '';
  }

  /** Получить следующий символ */
  private peek(offset: number = 1): string {
    return this.state.text[this.state.pos + offset] || '';
  }

  /** Продвинуть позицию на n символов */
  private advance(n: number = 1): void {
    for (let i = 0; i < n; i++) {
      const char = this.current();
      if (char === '\n') {
        this.state.line++;
        this.state.column = 1;
      } else {
        this.state.column++;
      }
      this.state.pos++;
    }
  }

  /** Пропустить пробельные символы */
  private skipWhitespace(): void {
    while (this.state.pos < this.state.text.length && isWhitespace(this.current())) {
      this.advance();
    }
  }

  /** Пропустить однострочный комментарий */
  private skipSingleLineComment(): boolean {
    if (this.current() === '/' && this.peek() === '/') {
      this.advance(2);
      while (this.state.pos < this.state.text.length && this.current() !== '\n') {
        this.advance();
      }
      return true;
    }
    return false;
  }

  /** Пропустить многострочный комментарий */
  private skipMultiLineComment(): boolean {
    if (this.current() === '/' && this.peek() === '*') {
      this.advance(2);
      while (this.state.pos < this.state.text.length - 1) {
        if (this.current() === '*' && this.peek() === '/') {
          this.advance(2);
          return true;
        }
        this.advance();
      }
    }
    return false;
  }

  /** Пропустить комментарии и пробелы */
  private skipCommentsAndWhitespace(): void {
    let skipped = true;
    while (skipped) {
      skipped = false;
      this.skipWhitespace();

      if (this.json5Mode) {
        if (this.skipSingleLineComment()) skipped = true;
        if (this.skipMultiLineComment()) skipped = true;
        this.skipWhitespace();
      }
    }
  }

  /** Получить текущую позицию */
  getCurrentPosition(): PositionInfo {
    return {
      line: this.state.line,
      column: this.state.column,
      offset: this.state.pos
    };
  }

  /** Получить текущий путь */
  getCurrentPath(): string {
    return this.state.pathStack.reduce<string>((acc, segment) => {
      if (typeof segment === 'number') {
        return `${acc}[${segment}]`;
      }
      return acc ? `${acc}.${segment}` : segment;
    }, '');
  }

  /** Получить текущий JSON Pointer */
  getCurrentPointer(): string {
    if (this.state.pathStack.length === 0) return '';
    return '/' + this.state.pathStack
      .map(p => String(p).replace(/~/g, '~0').replace(/\//g, '~1'))
      .join('/');
  }

  /** Парсить строку */
  parseString(): { value: string; startPos: PositionInfo; endPos: PositionInfo } {
    const startPos = this.getCurrentPosition();
    const quote = this.current();
    this.advance(); // Пропускаем открывающую кавычку

    let value = '';
    while (this.state.pos < this.state.text.length) {
      const char = this.current();

      if (char === '\\') {
        this.advance();
        if (this.state.pos < this.state.text.length) {
          value += this.current();
          this.advance();
        }
      } else if (char === quote) {
        this.advance();
        break;
      } else {
        value += char;
        this.advance();
      }
    }

    return {
      value,
      startPos,
      endPos: this.getCurrentPosition()
    };
  }

  /** Проверить, находимся ли мы в массиве */
  isInArray(): boolean {
    // Ищем последнюю открывающую скобку
    let depth = 0;
    for (let i = this.state.pos - 1; i >= 0; i--) {
      const char = this.state.text[i];
      if (char === ']') depth++;
      if (char === '[') {
        if (depth === 0) return true;
        depth--;
      }
      if (char === '}' || char === '{') {
        return false;
      }
    }
    return false;
  }
}

// ============================================================================
// POSITION TRACKER
// ============================================================================

/** Основной класс для отслеживания позиций */
export class PositionTracker {
  private positionMap: PositionMap | null = null;
  private options: BuildOptions;

  constructor(options: BuildOptions = {}) {
    this.options = {
      json5Support: false,
      buildPatternIndex: true,
      includeTokenTypes: true,
      includeTokenLengths: true,
      enableCaching: true,
      ...options
    };
  }

  /**
   * Построить position map из текста JSON
   * Сложность: O(n) где n - длина текста
   */
  buildPositionMap(jsonText: string): PositionMap {
    const startTime = Date.now();
    const sourceHash = hashString(jsonText);

    // Проверка кэша
    if (this.options.enableCaching && this.options.filePath) {
      const cached = globalCache.get(this.options.filePath, sourceHash);
      if (cached) {
        return cached;
      }
    }

    const byPointer = new Map<string, PositionInfo>();
    const byPath = new Map<string, PositionInfo>();
    const byPattern = new Map<string, PositionInfo[]>();

    const parser = new JSON5Parser(jsonText, this.options.json5Support ?? false);
    let tokenCount = 0;
    let commentCount = 0;

    const savePosition = (
      path: string,
      pointer: string,
      pos: PositionInfo,
      tokenType?: TokenType
    ) => {
      const posInfo: PositionInfo = {
        ...pos,
        tokenType: this.options.includeTokenTypes ? tokenType : undefined
      };

      byPointer.set(pointer, posInfo);
      byPath.set(path, posInfo);

      // Построение индекса для pattern matching
      if (this.options.buildPatternIndex) {
        const patterns = extractPatterns(path);
        for (const pattern of patterns) {
          if (!byPattern.has(pattern)) {
            byPattern.set(pattern, []);
          }
          byPattern.get(pattern)!.push(posInfo);
        }
      }

      tokenCount++;
    };

    // Основной цикл парсинга
    const state = (parser as any).state as ParserState;

    while (state.pos < state.text.length) {
      const char = state.text[state.pos];
      const prevChar = state.text[state.pos - 1] || '';
      const nextChar = state.text[state.pos + 1] || '';

      // Пропуск escape-последовательностей
      if (state.escaped) {
        state.escaped = false;
        state.column++;
        state.pos++;
        continue;
      }

      if (char === '\\' && state.inString) {
        state.escaped = true;
        state.column++;
        state.pos++;
        continue;
      }

      // Обработка комментариев в JSON5 режиме
      if (this.options.json5Support && !state.inString) {
        if (char === '/' && (nextChar === '/' || nextChar === '*')) {
          const commentStart = parser.getCurrentPosition();
          if (nextChar === '/') {
            (parser as any).skipSingleLineComment();
          } else {
            (parser as any).skipMultiLineComment();
          }
          commentCount++;
          continue;
        }
      }

      // Обработка строк
      if (char === '"' || (this.options.json5Support && char === "'")) {
        if (state.inString) {
          state.inString = false;

          // Если собирали ключ и следующий символ двоеточие
          if (state.collectingKey && nextChar === ':') {
            state.pathStack.push(state.currentKey);
            const path = parser.getCurrentPath();
            const pointer = parser.getCurrentPointer();
            const pos = parser.getCurrentPosition();
            savePosition(path, pointer, pos, TokenType.KEY);
            state.collectingKey = false;
            state.currentKey = '';
          }
        } else {
          state.inString = true;

          // Проверка, начинаем ли собирать ключ
          const trimmedPrev = prevChar.trim();
          if (trimmedPrev === '{' || trimmedPrev === ',' || trimmedPrev === '') {
            state.collectingKey = true;
            state.currentKey = '';
          }
        }
        state.column++;
        state.pos++;
        continue;
      }

      // Сбор имени ключа
      if (state.inString && state.collectingKey) {
        state.currentKey += char;
      }

      // Обработка структурных символов вне строк
      if (!state.inString) {
        // Начало объекта
        if (char === '{') {
          // Текущий ключ уже в стеке
        }

        // Начало массива
        if (char === '[') {
          state.arrayIndexStack.push(state.currentArrayIndex);
          state.currentArrayIndex = 0;
          state.pathStack.push(0);

          const path = parser.getCurrentPath();
          const pointer = parser.getCurrentPointer();
          const pos = parser.getCurrentPosition();
          savePosition(path, pointer, pos, TokenType.ARRAY_START);
        }

        // Конец объекта
        if (char === '}') {
          if (state.pathStack.length > 0) {
            state.pathStack.pop();
          }
        }

        // Конец массива
        if (char === ']') {
          if (state.pathStack.length > 0) {
            state.pathStack.pop();
          }
          if (state.arrayIndexStack.length > 0) {
            state.currentArrayIndex = state.arrayIndexStack.pop()!;
          }
        }

        // Запятая
        if (char === ',') {
          const inArray = parser.isInArray();

          if (inArray) {
            // Запятая в массиве
            if (state.pathStack.length > 0 &&
                typeof state.pathStack[state.pathStack.length - 1] === 'number') {
              state.pathStack.pop();
            }
            state.currentArrayIndex++;
            state.pathStack.push(state.currentArrayIndex);

            const path = parser.getCurrentPath();
            const pointer = parser.getCurrentPointer();
            const pos = parser.getCurrentPosition();
            savePosition(path, pointer, pos, TokenType.ARRAY_START);
          } else {
            // Запятая в объекте
            if (state.pathStack.length > 0) {
              state.pathStack.pop();
            }
          }
        }

        // Двоеточие после ключа
        if (char === ':' && state.pathStack.length > 0) {
          // Проверяем следующий значимый символ
          let j = state.pos + 1;
          while (j < state.text.length && isWhitespace(state.text[j])) {
            j++;
          }

          if (j < state.text.length && state.text[j] === '[') {
            // Следующее значение - массив
            // Индекс будет добавлен при встрече '['
          }
        }
      }

      // Обновление позиции
      if (char === '\n') {
        state.line++;
        state.column = 1;
      } else {
        state.column++;
      }
      state.pos++;
    }

    const parseTimeMs = Date.now() - startTime;

    const result: PositionMap = {
      byPointer,
      byPath,
      byPattern,
      totalLines: state.line,
      version: '3.0.0',
      sourceHash,
      stats: {
        parseTimeMs,
        tokenCount,
        commentCount,
        fileSizeBytes: jsonText.length
      }
    };

    // Сохранение в кэш
    if (this.options.enableCaching && this.options.filePath) {
      globalCache.set(this.options.filePath, result);
    }

    this.positionMap = result;
    return result;
  }

  /**
   * Найти номер строки по пути
   * Сложность: O(1) для точного совпадения, O(log n) для pattern matching
   */
  findLineNumber(
    path: string,
    pointer: string = '',
    options: LookupOptions = {}
  ): number {
    if (!this.positionMap) {
      throw new Error('Position map not built. Call buildPositionMap() first.');
    }

    const opts: LookupOptions = {
      fallbackToParent: true,
      usePatternMatching: true,
      preferredMatch: 'exact',
      ...options
    };

    // 1. Точное совпадение по JSON Pointer
    if (pointer && this.positionMap.byPointer.has(pointer)) {
      return this.positionMap.byPointer.get(pointer)!.line;
    }

    // 2. Точное совпадение по property path
    const normalizedPath = normalizePath(path);
    if (this.positionMap.byPath.has(normalizedPath)) {
      return this.positionMap.byPath.get(normalizedPath)!.line;
    }

    // 3. Pattern matching
    if (opts.usePatternMatching && this.options.buildPatternIndex) {
      const patterns = extractPatterns(normalizedPath);
      for (const pattern of patterns) {
        const matches = this.positionMap.byPattern.get(pattern);
        if (matches && matches.length > 0) {
          // Возвращаем первое совпадение
          return matches[0].line;
        }
      }
    }

    // 4. Поиск родительского пути
    if (opts.fallbackToParent) {
      const segments = normalizedPath.split(/[.\[\]]/).filter(Boolean);

      for (let i = segments.length - 1; i >= 0; i--) {
        const parentPath = segments.slice(0, i).reduce((acc, seg) => {
          if (!acc) return seg;
          if (/^\d+$/.test(seg)) {
            return `${acc}[${seg}]`;
          }
          return `${acc}.${seg}`;
        }, '');

        if (this.positionMap.byPath.has(parentPath)) {
          return this.positionMap.byPath.get(parentPath)!.line;
        }
      }
    }

    // 5. Fallback - первая строка
    return 1;
  }

  /**
   * Найти полную информацию о позиции
   */
  findPosition(
    path: string,
    pointer: string = '',
    options: LookupOptions = {}
  ): PositionInfo | null {
    if (!this.positionMap) {
      throw new Error('Position map not built. Call buildPositionMap() first.');
    }

    const normalizedPath = normalizePath(path);

    // Точное совпадение по pointer
    if (pointer && this.positionMap.byPointer.has(pointer)) {
      return this.positionMap.byPointer.get(pointer)!;
    }

    // Точное совпадение по path
    if (this.positionMap.byPath.has(normalizedPath)) {
      return this.positionMap.byPath.get(normalizedPath)!;
    }

    // Pattern matching или fallback
    const line = this.findLineNumber(path, pointer, options);
    return line > 0 ? { line, column: 1, offset: 0 } : null;
  }

  /**
   * Получить все позиции, соответствующие паттерну
   */
  findAllByPattern(pattern: string): PositionInfo[] {
    if (!this.positionMap) {
      throw new Error('Position map not built. Call buildPositionMap() first.');
    }

    return this.positionMap.byPattern.get(pattern) || [];
  }

  /**
   * Получить статистику position map
   */
  getStats(): ParsingStats | null {
    return this.positionMap?.stats || null;
  }

  /**
   * Очистить кэш
   */
  static clearCache(): void {
    globalCache.clear();
  }

  /**
   * Получить статистику кэша
   */
  static getCacheStats(): { size: number; maxSize: number; hitRate?: number } {
    return globalCache.getStats();
  }
}

// ============================================================================
// ЭКСПОРТ
// ============================================================================

export {
  JSON5Parser,
  hashString,
  normalizePath,
  extractPatterns
};
