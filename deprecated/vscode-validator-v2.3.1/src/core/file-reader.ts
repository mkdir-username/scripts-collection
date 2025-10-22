/**
 * File Reader Module
 *
 * Модуль для чтения файлов с поддержкой различных форматов и кэширования.
 * Обеспечивает оптимизированное чтение больших файлов и управление памятью.
 *
 * @module core/file-reader
 * @version 2.3.1
 */

import * as fs from 'fs';
import { extname, basename } from 'path';
import type { ConfigManager } from './config';

/**
 * Формат файла
 */
export enum FileFormat {
  JSON = 'json',
  JINJA_JAVA = 'j2.java',
  JINJA_JSON = 'jinja.json',
  UNKNOWN = 'unknown',
}

/**
 * Метаданные файла
 */
export interface FileMetadata {
  /** Полный путь к файлу */
  readonly path: string;
  /** Имя файла */
  readonly name: string;
  /** Размер файла в байтах */
  readonly size: number;
  /** Формат файла */
  readonly format: FileFormat;
  /** Дата последнего изменения */
  readonly lastModified: Date;
  /** Кодировка файла */
  readonly encoding: BufferEncoding;
}

/**
 * Результат чтения файла
 */
export interface FileReadResult {
  /** Содержимое файла */
  readonly content: string;
  /** Метаданные файла */
  readonly metadata: FileMetadata;
  /** Время чтения в миллисекундах */
  readonly readTimeMs: number;
  /** Хэш содержимого (для кэширования) */
  readonly contentHash: string;
}

/**
 * Опции чтения файла
 */
export interface FileReadOptions {
  /** Кодировка файла */
  encoding?: BufferEncoding;
  /** Принудительный формат */
  format?: FileFormat;
  /** Максимальный размер файла (в байтах) */
  maxSize?: number;
  /** Вычислять хэш содержимого */
  computeHash?: boolean;
}

/**
 * Ошибка чтения файла
 */
export class FileReadError extends Error {
  public readonly path: string;
  public readonly cause?: Error;

  constructor(
    message: string,
    path: string,
    cause?: Error
  ) {
    super(message);
    this.name = 'FileReadError';
    this.path = path;
    this.cause = cause;
  }
}

/**
 * File Reader
 *
 * Класс для чтения файлов с различными форматами и оптимизациями.
 * Поддерживает кэширование, валидацию размера и автоопределение формата.
 *
 * @example
 * ```typescript
 * const reader = new FileReader(config);
 *
 * try {
 *   const result = reader.readFile('/path/to/file.json');
 *   console.log(result.content);
 *   console.log(result.metadata.format); // FileFormat.JSON
 * } catch (error) {
 *   if (error instanceof FileReadError) {
 *     console.error(`Failed to read ${error.path}: ${error.message}`);
 *   }
 * }
 * ```
 */
export class FileReader {
  private readonly cache: Map<string, FileReadResult>;
  private readonly defaultMaxSize: number;

  /**
   * @param config - Конфигурация валидатора
   */
  constructor(config: ConfigManager) {
    this.cache = new Map();
    this.defaultMaxSize = config.getPerformanceOptions().fileReadBufferSize;
  }

  /**
   * Прочитать файл
   *
   * @param filePath - Путь к файлу
   * @param options - Опции чтения
   * @returns Результат чтения
   * @throws {FileReadError} Если файл не существует или не может быть прочитан
   */
  public readFile(filePath: string, options: FileReadOptions = {}): FileReadResult {
    const startTime = Date.now();

    // Проверка существования файла
    if (!fs.existsSync(filePath)) {
      throw new FileReadError(`File not found`, filePath);
    }

    // Получение метаданных
    const metadata = this.getMetadata(filePath, options);

    // Проверка размера файла
    const maxSize = options.maxSize || this.defaultMaxSize;
    if (metadata.size > maxSize) {
      throw new FileReadError(
        `File size (${metadata.size} bytes) exceeds maximum allowed size (${maxSize} bytes)`,
        filePath
      );
    }

    // Чтение содержимого
    let content: string;
    try {
      content = fs.readFileSync(filePath, metadata.encoding);
    } catch (error) {
      throw new FileReadError(
        `Failed to read file: ${error instanceof Error ? error.message : String(error)}`,
        filePath,
        error instanceof Error ? error : undefined
      );
    }

    const readTimeMs = Date.now() - startTime;

    // Вычисление хэша (если требуется)
    const contentHash = options.computeHash
      ? this.computeSimpleHash(content)
      : '';

    const result: FileReadResult = {
      content,
      metadata,
      readTimeMs,
      contentHash,
    };

    return result;
  }

  /**
   * Прочитать файл с кэшированием
   *
   * @param filePath - Путь к файлу
   * @param options - Опции чтения
   * @returns Результат чтения (из кэша или свежий)
   */
  public readFileCached(filePath: string, options: FileReadOptions = {}): FileReadResult {
    const cacheKey = this.getCacheKey(filePath, options);

    // Проверка кэша
    if (this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey)!;

      // Проверка актуальности кэша
      if (this.isCacheValid(filePath, cached)) {
        return cached;
      }

      // Инвалидация устаревшего кэша
      this.cache.delete(cacheKey);
    }

    // Чтение файла
    const result = this.readFile(filePath, { ...options, computeHash: true });

    // Сохранение в кэш
    this.cache.set(cacheKey, result);

    return result;
  }

  /**
   * Определить формат файла
   *
   * @param filePath - Путь к файлу
   * @returns Формат файла
   */
  public detectFormat(filePath: string): FileFormat {
    const ext = extname(filePath).toLowerCase();
    const name = basename(filePath).toLowerCase();

    // Проверка специфичных паттернов
    if (name.includes('.j2.java')) {
      return FileFormat.JINJA_JAVA;
    }

    if (name.endsWith('.jinja.json') || name.endsWith('.jinja.java')) {
      return FileFormat.JINJA_JSON;
    }

    // Проверка расширений
    switch (ext) {
      case '.json':
        return FileFormat.JSON;
      case '.java':
        if (name.includes('.j2.')) {
          return FileFormat.JINJA_JAVA;
        }
        return FileFormat.UNKNOWN;
      default:
        return FileFormat.UNKNOWN;
    }
  }

  /**
   * Проверить является ли файл Jinja шаблоном
   *
   * @param filePath - Путь к файлу
   * @returns true если файл является Jinja шаблоном
   */
  public isJinjaTemplate(filePath: string): boolean {
    const format = this.detectFormat(filePath);
    return format === FileFormat.JINJA_JAVA || format === FileFormat.JINJA_JSON;
  }

  /**
   * Очистить кэш
   *
   * @param filePath - Путь к конкретному файлу (опционально)
   */
  public clearCache(filePath?: string): void {
    if (filePath) {
      // Удалить все записи для конкретного файла
      for (const [key] of this.cache) {
        if (key.startsWith(filePath)) {
          this.cache.delete(key);
        }
      }
    } else {
      // Очистить весь кэш
      this.cache.clear();
    }
  }

  /**
   * Получить размер кэша
   *
   * @returns Количество закэшированных файлов
   */
  public getCacheSize(): number {
    return this.cache.size;
  }

  /**
   * Получить метаданные файла
   */
  private getMetadata(filePath: string, options: FileReadOptions): FileMetadata {
    const stats = fs.statSync(filePath);
    const format = options.format || this.detectFormat(filePath);
    const encoding = options.encoding || 'utf-8';

    return {
      path: filePath,
      name: basename(filePath),
      size: stats.size,
      format,
      lastModified: stats.mtime,
      encoding,
    };
  }

  /**
   * Проверить валидность кэша
   */
  private isCacheValid(filePath: string, cached: FileReadResult): boolean {
    try {
      const stats = fs.statSync(filePath);
      return stats.mtime <= cached.metadata.lastModified;
    } catch {
      return false;
    }
  }

  /**
   * Получить ключ для кэша
   */
  private getCacheKey(filePath: string, options: FileReadOptions): string {
    const encoding = options.encoding || 'utf-8';
    const format = options.format || 'auto';
    return `${filePath}:${encoding}:${format}`;
  }

  /**
   * Вычислить простой хэш строки
   *
   * Использует алгоритм djb2 для быстрого хэширования
   */
  private computeSimpleHash(content: string): string {
    let hash = 5381;
    for (let i = 0; i < content.length; i++) {
      hash = ((hash << 5) + hash) + content.charCodeAt(i);
      hash = hash & hash; // Convert to 32-bit integer
    }
    return hash.toString(16);
  }
}

/**
 * Утилита для синхронного чтения файла (без кэширования)
 *
 * @param filePath - Путь к файлу
 * @param encoding - Кодировка (по умолчанию utf-8)
 * @returns Содержимое файла
 * @throws {FileReadError} Если файл не может быть прочитан
 */
export function readFileSync(filePath: string, encoding: BufferEncoding = 'utf-8'): string {
  if (!fs.existsSync(filePath)) {
    throw new FileReadError(`File not found`, filePath);
  }

  try {
    return fs.readFileSync(filePath, encoding);
  } catch (error) {
    throw new FileReadError(
      `Failed to read file: ${error instanceof Error ? error.message : String(error)}`,
      filePath,
      error instanceof Error ? error : undefined
    );
  }
}

/**
 * Проверить существование файла
 *
 * @param filePath - Путь к файлу
 * @returns true если файл существует
 */
export function fileExists(filePath: string): boolean {
  return fs.existsSync(filePath);
}

/**
 * Получить размер файла
 *
 * @param filePath - Путь к файлу
 * @returns Размер в байтах или null если файл не существует
 */
export function getFileSize(filePath: string): number | null {
  try {
    const stats = fs.statSync(filePath);
    return stats.size;
  } catch {
    return null;
  }
}
