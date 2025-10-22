/**
 * JSON Parser with position tracking
 * @version 1.0.0
 * @created 2025-10-07
 */

import { readFileSync } from 'fs';
import {
  IParser,
  ParseResult,
  ParseOptions,
  ParserConfig,
  ParseError,
  ParseWarning,
  SyntaxException,
  ParseErrorType,
  createSuccessResult,
  createErrorResult,
  createPosition,
  SourcePosition,
} from './types_v1.0.0.js';

// ============================================================================
// ТИПЫ
// ============================================================================

/**
 * Конфигурация JSON парсера
 */
export interface JsonParserConfig extends ParserConfig {
  allowComments?: boolean;
  allowTrailingCommas?: boolean;
  reviver?: (key: string, value: any) => any;
}

/**
 * Результат парсинга JSON
 */
export interface JsonParseResult {
  json: any;
  positionMap: PositionMap;
  text: string;
}

/**
 * Position Map для быстрого поиска позиций
 */
export interface PositionMap {
  /** Быстрый поиск по JSON Pointer */
  byPointer: Map<string, PositionInfo>;
  /** Быстрый поиск по property path */
  byPath: Map<string, PositionInfo>;
  /** Кэш для вложенных путей */
  nestedCache: Map<string, PositionInfo[]>;
  /** Общее количество строк */
  totalLines: number;
  /** Время построения карты */
  buildTimeMs: number;
}

/**
 * Информация о позиции
 */
export interface PositionInfo extends SourcePosition {
  parent?: string;
}

// ============================================================================
// JSON PARSER
// ============================================================================

/**
 * Парсер JSON с отслеживанием позиций
 */
export class JsonParser implements IParser<string, JsonParseResult, JsonParserConfig> {
  private config: JsonParserConfig;

  constructor(config: JsonParserConfig = {}) {
    this.config = {
      strict: true,
      maxErrors: 100,
      timeout: 30000,
      verbose: false,
      allowComments: false,
      allowTrailingCommas: false,
      ...config,
    };
  }

  /**
   * Парсит JSON из файла
   */
  async parse(
    filePath: string,
    options?: ParseOptions
  ): Promise<ParseResult<JsonParseResult>> {
    const startTime = Date.now();
    const errors: ParseError[] = [];
    const warnings: ParseWarning[] = [];

    try {
      // Читаем файл
      const text = readFileSync(filePath, options?.encoding || 'utf-8');
      const fileSize = Buffer.byteLength(text, 'utf-8');

      // Парсим JSON
      let json: any;
      try {
        json = JSON.parse(text, this.config.reviver);
      } catch (error) {
        const parseError = this.extractJsonError(error as Error, text, filePath);
        errors.push(parseError);

        return createErrorResult(
          errors,
          {
            parseTimeMs: Date.now() - startTime,
            filePath,
            fileSize,
            version: '1.0.0',
          },
          warnings
        );
      }

      // Строим position map
      const positionMap = this.buildPositionMap(text);

      const result: JsonParseResult = {
        json,
        positionMap,
        text,
      };

      return createSuccessResult(
        result,
        {
          parseTimeMs: Date.now() - startTime,
          filePath,
          fileSize,
          version: '1.0.0',
        },
        warnings
      );
    } catch (error) {
      errors.push({
        type: ParseErrorType.UNKNOWN,
        message: `Unexpected error: ${(error as Error).message}`,
        position: createPosition(0, 0, 0),
        filePath,
      });

      return createErrorResult(
        errors,
        {
          parseTimeMs: Date.now() - startTime,
          filePath,
          fileSize: 0,
          version: '1.0.0',
        },
        warnings
      );
    }
  }

  /**
   * Синхронный парсинг
   */
  parseSync(
    filePath: string,
    options?: ParseOptions
  ): ParseResult<JsonParseResult> {
    const startTime = Date.now();
    const errors: ParseError[] = [];
    const warnings: ParseWarning[] = [];

    try {
      const text = readFileSync(filePath, options?.encoding || 'utf-8');
      const fileSize = Buffer.byteLength(text, 'utf-8');

      let json: any;
      try {
        json = JSON.parse(text, this.config.reviver);
      } catch (error) {
        const parseError = this.extractJsonError(error as Error, text, filePath);
        errors.push(parseError);

        return createErrorResult(
          errors,
          {
            parseTimeMs: Date.now() - startTime,
            filePath,
            fileSize,
            version: '1.0.0',
          },
          warnings
        );
      }

      const positionMap = this.buildPositionMap(text);

      const result: JsonParseResult = {
        json,
        positionMap,
        text,
      };

      return createSuccessResult(
        result,
        {
          parseTimeMs: Date.now() - startTime,
          filePath,
          fileSize,
          version: '1.0.0',
        },
        warnings
      );
    } catch (error) {
      errors.push({
        type: ParseErrorType.UNKNOWN,
        message: `Unexpected error: ${(error as Error).message}`,
        position: createPosition(0, 0, 0),
        filePath,
      });

      return createErrorResult(
        errors,
        {
          parseTimeMs: Date.now() - startTime,
          filePath,
          fileSize: 0,
          version: '1.0.0',
        },
        warnings
      );
    }
  }

  /**
   * Валидация без полного парсинга
   */
  async validate(filePath: string): Promise<boolean> {
    try {
      const text = readFileSync(filePath, 'utf-8');
      JSON.parse(text);
      return true;
    } catch {
      return false;
    }
  }

  getConfig(): Readonly<JsonParserConfig> {
    return { ...this.config };
  }

  updateConfig(config: Partial<JsonParserConfig>): void {
    this.config = { ...this.config, ...config };
  }

  // ============================================================================
  // POSITION MAP BUILDER
  // ============================================================================

  /**
   * Строит position map за один проход по тексту JSON
   *
   * Сложность: O(n) где n - длина текста
   * Память: O(k) где k - количество ключей в JSON
   */
  private buildPositionMap(jsonText: string): PositionMap {
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

    const savePosition = (path: Array<string | number>, tokenLength: number = 0) => {
      if (path.length === 0) return;

      const pointer = this.pathToJsonPointer(path);
      const propertyPath = this.pathToPropertyPath(path);
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
    };

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
            const tokenLength = offset - keyStartOffset + 1;
            pathStack.push(currentKey);

            const currentPath = this.pathToPropertyPath(pathStack);
            parentStack.push(currentPath);

            savePosition(pathStack, tokenLength);
            collectingKey = false;
            currentKey = '';
          }
        } else {
          inString = true;
          keyStartOffset = offset;
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
        if (char === '[') {
          arrayStack.push(arrayIndex);
          arrayIndex = 0;
        }

        if (char === '}') {
          if (pathStack.length > 0) {
            pathStack.pop();
            if (parentStack.length > 0) {
              parentStack.pop();
            }
          }
        }

        if (char === ']') {
          if (pathStack.length > 0) {
            pathStack.pop();
          }
          if (arrayStack.length > 0) {
            arrayIndex = arrayStack.pop()!;
          }
        }

        if (char === ',') {
          const parent = pathStack[pathStack.length - 1];
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
            if (pathStack.length > 0) {
              pathStack.pop();
              if (parentStack.length > 0) {
                parentStack.pop();
              }
            }
          }
        }

        if (char === ':' && pathStack.length > 0) {
          let j = i + 1;
          while (
            j < jsonText.length &&
            (jsonText[j] === ' ' || jsonText[j] === '\n')
          ) {
            j++;
          }

          if (j < jsonText.length && jsonText[j] === '[') {
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

    return {
      byPointer,
      byPath,
      nestedCache,
      totalLines: line,
      buildTimeMs,
    };
  }

  // ============================================================================
  // УТИЛИТЫ
  // ============================================================================

  /**
   * Извлекает информацию об ошибке из JSON.parse
   */
  private extractJsonError(error: Error, text: string, filePath: string): ParseError {
    const errorMessage = error.message;
    const positionMatch = errorMessage.match(/at position (\d+)/);
    const position = positionMatch ? parseInt(positionMatch[1], 10) : 0;

    const linesUpToError = text.substring(0, position).split('\n');
    const line = linesUpToError.length;
    const column = linesUpToError[linesUpToError.length - 1].length + 1;

    // Извлекаем контекст
    const lines = text.split('\n');
    const contextStart = Math.max(0, line - 2);
    const contextEnd = Math.min(lines.length, line + 1);
    const context = lines.slice(contextStart, contextEnd).join('\n');

    return {
      type: ParseErrorType.INVALID_JSON,
      message: `JSON parse error: ${errorMessage}`,
      position: createPosition(line, column, position),
      filePath,
      context,
      suggestion: 'Check JSON syntax near this position',
    };
  }

  /**
   * Конвертирует path массив в JSON Pointer
   */
  private pathToJsonPointer(path: Array<string | number>): string {
    if (path.length === 0) return '';
    return (
      '/' +
      path
        .map((p) => String(p).replace(/~/g, '~0').replace(/\//g, '~1'))
        .join('/')
    );
  }

  /**
   * Конвертирует path массив в property path
   */
  private pathToPropertyPath(path: Array<string | number>): string {
    return path.reduce<string>((acc, segment) => {
      if (typeof segment === 'number') {
        return `${acc}[${segment}]`;
      }
      return acc ? `${acc}.${segment}` : String(segment);
    }, '');
  }

  /**
   * Поиск позиции по пути
   */
  findPosition(positionMap: PositionMap, path: string): PositionInfo | null {
    // 1. Прямой поиск по property path
    if (positionMap.byPath.has(path)) {
      return positionMap.byPath.get(path)!;
    }

    // 2. Поиск по JSON Pointer
    const pointer = this.pathToJsonPointer(path.split(/[.\[\]]/).filter(Boolean));
    if (positionMap.byPointer.has(pointer)) {
      return positionMap.byPointer.get(pointer)!;
    }

    // 3. Поиск через nestedCache
    const segments = path.split(/[.\[\]]/).filter(Boolean);
    for (let i = segments.length; i > 0; i--) {
      const partialPath = segments.slice(0, i).join('.');
      if (positionMap.nestedCache.has(partialPath)) {
        const positions = positionMap.nestedCache.get(partialPath)!;
        if (positions.length > 0) {
          return positions[0];
        }
      }
    }

    return null;
  }
}
