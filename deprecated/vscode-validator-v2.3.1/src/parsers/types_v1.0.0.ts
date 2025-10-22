/**
 * Common types for parser modules
 * @version 1.0.0
 * @created 2025-10-07
 */

// ============================================================================
// БАЗОВЫЕ ТИПЫ
// ============================================================================

/**
 * Position в исходном файле
 */
export interface SourcePosition {
  readonly line: number;
  readonly column: number;
  readonly offset: number;
  readonly length?: number;
}

/**
 * Source mapping для отслеживания трансформаций
 */
export interface SourceMapping {
  readonly originalLine: number;
  readonly originalColumn: number;
  readonly transformedLine: number;
  readonly transformedColumn: number;
  readonly sourceFile: string;
  readonly tokenType: TokenType;
}

/**
 * Тип токена
 */
export type TokenType = 'import' | 'variable' | 'control' | 'json' | 'comment';

// ============================================================================
// РЕЗУЛЬТАТЫ ПАРСИНГА
// ============================================================================

/**
 * Базовый результат парсинга
 */
export interface ParseResult<T = any> {
  readonly success: boolean;
  readonly data: T | null;
  readonly errors: ParseError[];
  readonly warnings: ParseWarning[];
  readonly metadata: ParseMetadata;
}

/**
 * Метаданные парсинга
 */
export interface ParseMetadata {
  readonly parseTimeMs: number;
  readonly filePath: string;
  readonly fileSize: number;
  readonly version: string;
}

// ============================================================================
// ОШИБКИ И ПРЕДУПРЕЖДЕНИЯ
// ============================================================================

/**
 * Типизированная ошибка парсинга
 */
export interface ParseError {
  readonly type: ParseErrorType;
  readonly message: string;
  readonly position: SourcePosition;
  readonly filePath: string;
  readonly context?: string;
  readonly suggestion?: string;
}

/**
 * Типы ошибок парсинга
 */
export enum ParseErrorType {
  SYNTAX_ERROR = 'syntax_error',
  CIRCULAR_IMPORT = 'circular_import',
  FILE_NOT_FOUND = 'file_not_found',
  INVALID_TEMPLATE = 'invalid_template',
  INVALID_JSON = 'invalid_json',
  UNRESOLVED_VARIABLE = 'unresolved_variable',
  IMPORT_ERROR = 'import_error',
  UNKNOWN = 'unknown',
}

/**
 * Предупреждение парсинга
 */
export interface ParseWarning {
  readonly type: ParseWarningType;
  readonly message: string;
  readonly position: SourcePosition;
  readonly filePath: string;
}

/**
 * Типы предупреждений
 */
export enum ParseWarningType {
  UNUSED_IMPORT = 'unused_import',
  UNUSED_VARIABLE = 'unused_variable',
  DEPRECATED_SYNTAX = 'deprecated_syntax',
  IMPLICIT_CONVERSION = 'implicit_conversion',
  PERFORMANCE = 'performance',
}

// ============================================================================
// КОНФИГУРАЦИЯ ПАРСЕРОВ
// ============================================================================

/**
 * Базовая конфигурация парсера
 */
export interface ParserConfig {
  readonly strict?: boolean;
  readonly maxErrors?: number;
  readonly timeout?: number;
  readonly verbose?: boolean;
}

/**
 * Опции парсинга
 */
export interface ParseOptions extends ParserConfig {
  readonly encoding?: BufferEncoding;
  readonly sourceMap?: boolean;
}

// ============================================================================
// ИНТЕРФЕЙС ПАРСЕРА
// ============================================================================

/**
 * Базовый интерфейс для всех парсеров
 */
export interface IParser<TInput, TOutput, TConfig extends ParserConfig = ParserConfig> {
  /**
   * Парсит входные данные
   */
  parse(input: TInput, options?: ParseOptions): Promise<ParseResult<TOutput>>;

  /**
   * Синхронная версия парсинга (если поддерживается)
   */
  parseSync?(input: TInput, options?: ParseOptions): ParseResult<TOutput>;

  /**
   * Валидирует входные данные без полного парсинга
   */
  validate(input: TInput): Promise<boolean>;

  /**
   * Получить конфигурацию парсера
   */
  getConfig(): Readonly<TConfig>;

  /**
   * Обновить конфигурацию парсера
   */
  updateConfig(config: Partial<TConfig>): void;
}

// ============================================================================
// EXCEPTION CLASSES
// ============================================================================

/**
 * Базовый класс для ошибок парсинга
 */
export class ParserException extends Error {
  constructor(
    message: string,
    public readonly type: ParseErrorType,
    public readonly position?: SourcePosition,
    public readonly filePath?: string,
    public readonly cause?: Error
  ) {
    super(message);
    this.name = 'ParserException';
    Object.setPrototypeOf(this, ParserException.prototype);
  }

  toParseError(): ParseError {
    return {
      type: this.type,
      message: this.message,
      position: this.position || { line: 0, column: 0, offset: 0 },
      filePath: this.filePath || 'unknown',
      context: this.cause?.message,
    };
  }
}

/**
 * Ошибка синтаксиса
 */
export class SyntaxException extends ParserException {
  constructor(
    message: string,
    position: SourcePosition,
    filePath: string,
    cause?: Error
  ) {
    super(message, ParseErrorType.SYNTAX_ERROR, position, filePath, cause);
    this.name = 'SyntaxException';
    Object.setPrototypeOf(this, SyntaxException.prototype);
  }
}

/**
 * Ошибка импорта
 */
export class ImportException extends ParserException {
  constructor(
    message: string,
    position: SourcePosition,
    filePath: string,
    public readonly importPath: string,
    cause?: Error
  ) {
    super(message, ParseErrorType.IMPORT_ERROR, position, filePath, cause);
    this.name = 'ImportException';
    Object.setPrototypeOf(this, ImportException.prototype);
  }
}

/**
 * Циклический импорт
 */
export class CircularImportException extends ImportException {
  constructor(
    message: string,
    position: SourcePosition,
    filePath: string,
    importPath: string,
    public readonly importChain: string[]
  ) {
    super(message, position, filePath, importPath);
    this.type = ParseErrorType.CIRCULAR_IMPORT;
    this.name = 'CircularImportException';
    Object.setPrototypeOf(this, CircularImportException.prototype);
  }
}

/**
 * Файл не найден
 */
export class FileNotFoundException extends ImportException {
  constructor(
    filePath: string,
    position: SourcePosition,
    sourceFile: string
  ) {
    super(
      `File not found: ${filePath}`,
      position,
      sourceFile,
      filePath
    );
    this.type = ParseErrorType.FILE_NOT_FOUND;
    this.name = 'FileNotFoundException';
    Object.setPrototypeOf(this, FileNotFoundException.prototype);
  }
}

// ============================================================================
// УТИЛИТЫ
// ============================================================================

/**
 * Создает успешный результат парсинга
 */
export function createSuccessResult<T>(
  data: T,
  metadata: ParseMetadata,
  warnings: ParseWarning[] = []
): ParseResult<T> {
  return {
    success: true,
    data,
    errors: [],
    warnings,
    metadata,
  };
}

/**
 * Создает результат с ошибкой
 */
export function createErrorResult<T>(
  errors: ParseError[],
  metadata: ParseMetadata,
  warnings: ParseWarning[] = []
): ParseResult<T> {
  return {
    success: false,
    data: null,
    errors,
    warnings,
    metadata,
  };
}

/**
 * Создает позицию в исходном файле
 */
export function createPosition(
  line: number,
  column: number,
  offset: number,
  length?: number
): SourcePosition {
  return { line, column, offset, length };
}
