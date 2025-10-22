/**
 * Structured Logger
 *
 * Advanced logging system with:
 * - Log levels
 * - Structured context
 * - File output
 * - Performance tracking
 * - Error tracking
 *
 * @version 2.3.1
 * @module utils/logger
 */

import * as fs from 'fs';
import * as path from 'path';
import { LogLevel, LogEntry } from '../types';
import { ColorFormatter } from '../formatters/color-formatter';

// ============================================================================
// Logger Configuration
// ============================================================================

/**
 * Logger configuration options
 */
export interface LoggerConfig {
  level: LogLevel;
  outputFile?: string;
  enableConsole: boolean;
  enableColor: boolean;
  enableTimestamp: boolean;
  maxFileSize: number; // bytes
  maxFiles: number;
  context?: Record<string, unknown>;
}

/**
 * Default logger configuration
 */
const DEFAULT_CONFIG: LoggerConfig = {
  level: LogLevel.INFO,
  enableConsole: true,
  enableColor: true,
  enableTimestamp: true,
  maxFileSize: 10 * 1024 * 1024, // 10MB
  maxFiles: 5
};

// ============================================================================
// Logger Class
// ============================================================================

/**
 * Structured logger with multiple output targets
 */
export class Logger {
  private config: LoggerConfig;
  private colorFormatter: ColorFormatter;
  private logBuffer: LogEntry[] = [];
  private fileStream?: fs.WriteStream;

  // Log level hierarchy
  private static readonly LEVEL_PRIORITY = {
    [LogLevel.DEBUG]: 0,
    [LogLevel.INFO]: 1,
    [LogLevel.WARN]: 2,
    [LogLevel.ERROR]: 3,
    [LogLevel.FATAL]: 4
  };

  constructor(config?: Partial<LoggerConfig>) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.colorFormatter = new ColorFormatter(this.config.enableColor);

    if (this.config.outputFile) {
      this.initFileOutput(this.config.outputFile);
    }
  }

  // ========================================================================
  // Logging Methods
  // ========================================================================

  /**
   * Log debug message
   */
  debug(message: string, context?: Record<string, unknown>): void {
    this.log(LogLevel.DEBUG, message, context);
  }

  /**
   * Log info message
   */
  info(message: string, context?: Record<string, unknown>): void {
    this.log(LogLevel.INFO, message, context);
  }

  /**
   * Log warning message
   */
  warn(message: string, context?: Record<string, unknown>): void {
    this.log(LogLevel.WARN, message, context);
  }

  /**
   * Log error message
   */
  error(message: string, error?: Error, context?: Record<string, unknown>): void {
    this.log(LogLevel.ERROR, message, { ...context, error: error?.message, stack: error?.stack });
  }

  /**
   * Log fatal error
   */
  fatal(message: string, error?: Error, context?: Record<string, unknown>): void {
    this.log(LogLevel.FATAL, message, { ...context, error: error?.message, stack: error?.stack });
  }

  /**
   * Core logging method
   */
  private log(level: LogLevel, message: string, context?: Record<string, unknown>): void {
    // Check log level
    if (!this.shouldLog(level)) {
      return;
    }

    // Create log entry
    const entry: LogEntry = {
      level,
      message,
      timestamp: Date.now(),
      context: { ...this.config.context, ...context }
    };

    // Add to buffer
    this.logBuffer.push(entry);

    // Output to console
    if (this.config.enableConsole) {
      this.writeToConsole(entry);
    }

    // Output to file
    if (this.fileStream) {
      this.writeToFile(entry);
    }

    // Rotate logs if needed
    this.rotateLogsIfNeeded();
  }

  // ========================================================================
  // Output Methods
  // ========================================================================

  /**
   * Write to console
   */
  private writeToConsole(entry: LogEntry): void {
    const formatted = this.formatEntry(entry, true);
    console.log(formatted);
  }

  /**
   * Write to file
   */
  private writeToFile(entry: LogEntry): void {
    if (!this.fileStream) {
      return;
    }

    const formatted = this.formatEntry(entry, false);
    this.fileStream.write(formatted + '\n');
  }

  /**
   * Format log entry
   */
  private formatEntry(entry: LogEntry, useColor: boolean): string {
    const parts: string[] = [];

    // Timestamp
    if (this.config.enableTimestamp) {
      const timestamp = new Date(entry.timestamp).toISOString();
      parts.push(useColor ? this.colorFormatter.gray(timestamp) : timestamp);
    }

    // Level
    const levelStr = this.formatLevel(entry.level, useColor);
    parts.push(levelStr);

    // Message
    parts.push(entry.message);

    // Context
    if (entry.context && Object.keys(entry.context).length > 0) {
      const contextStr = this.formatContext(entry.context);
      parts.push(useColor ? this.colorFormatter.dim(contextStr) : contextStr);
    }

    return parts.join(' ');
  }

  /**
   * Format log level
   */
  private formatLevel(level: LogLevel, useColor: boolean): string {
    const levelStr = `[${level.toUpperCase()}]`.padEnd(7);

    if (!useColor) {
      return levelStr;
    }

    switch (level) {
      case LogLevel.DEBUG:
        return this.colorFormatter.gray(levelStr);
      case LogLevel.INFO:
        return this.colorFormatter.blue(levelStr);
      case LogLevel.WARN:
        return this.colorFormatter.yellow(levelStr);
      case LogLevel.ERROR:
        return this.colorFormatter.red(levelStr);
      case LogLevel.FATAL:
        return this.colorFormatter.boldRed(levelStr);
      default:
        return levelStr;
    }
  }

  /**
   * Format context object
   */
  private formatContext(context: Record<string, unknown>): string {
    const pairs: string[] = [];

    for (const [key, value] of Object.entries(context)) {
      if (value === undefined) continue;

      let valueStr: string;
      if (typeof value === 'object') {
        valueStr = JSON.stringify(value);
      } else {
        valueStr = String(value);
      }

      pairs.push(`${key}=${valueStr}`);
    }

    return pairs.length > 0 ? `{${pairs.join(', ')}}` : '';
  }

  // ========================================================================
  // Performance Tracking
  // ========================================================================

  /**
   * Start performance timer
   */
  startTimer(label: string): () => void {
    const start = Date.now();

    return () => {
      const duration = Date.now() - start;
      this.debug(`Timer: ${label}`, { duration });
    };
  }

  /**
   * Measure async function execution
   */
  async measure<T>(label: string, fn: () => Promise<T>): Promise<T> {
    const start = Date.now();

    try {
      const result = await fn();
      const duration = Date.now() - start;
      this.debug(`Measure: ${label}`, { duration, status: 'success' });
      return result;
    } catch (error) {
      const duration = Date.now() - start;
      this.error(`Measure: ${label}`, error as Error, { duration, status: 'error' });
      throw error;
    }
  }

  // ========================================================================
  // File Management
  // ========================================================================

  /**
   * Initialize file output
   */
  private initFileOutput(filePath: string): void {
    try {
      const dir = path.dirname(filePath);

      // Create directory if it doesn't exist
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }

      // Create write stream
      this.fileStream = fs.createWriteStream(filePath, { flags: 'a' });

      // Handle stream errors
      this.fileStream.on('error', (err) => {
        console.error('Logger file stream error:', err);
        this.fileStream = undefined;
      });
    } catch (error) {
      console.error('Failed to initialize log file:', error);
    }
  }

  /**
   * Rotate logs if file size exceeds limit
   */
  private rotateLogsIfNeeded(): void {
    if (!this.config.outputFile || !this.fileStream) {
      return;
    }

    try {
      const stats = fs.statSync(this.config.outputFile);

      if (stats.size >= this.config.maxFileSize) {
        this.rotateLogs();
      }
    } catch {
      // File doesn't exist or can't be read
    }
  }

  /**
   * Rotate log files
   */
  private rotateLogs(): void {
    if (!this.config.outputFile) {
      return;
    }

    // Close current stream
    this.fileStream?.end();

    // Rotate files
    const basePath = this.config.outputFile;
    const ext = path.extname(basePath);
    const nameWithoutExt = basePath.slice(0, -ext.length);

    // Delete oldest file
    const oldestFile = `${nameWithoutExt}.${this.config.maxFiles}${ext}`;
    if (fs.existsSync(oldestFile)) {
      fs.unlinkSync(oldestFile);
    }

    // Rotate existing files
    for (let i = this.config.maxFiles - 1; i > 0; i--) {
      const from = i === 1 ? basePath : `${nameWithoutExt}.${i}${ext}`;
      const to = `${nameWithoutExt}.${i + 1}${ext}`;

      if (fs.existsSync(from)) {
        fs.renameSync(from, to);
      }
    }

    // Create new stream
    this.initFileOutput(basePath);
  }

  // ========================================================================
  // Utility Methods
  // ========================================================================

  /**
   * Check if should log at level
   */
  private shouldLog(level: LogLevel): boolean {
    return Logger.LEVEL_PRIORITY[level] >= Logger.LEVEL_PRIORITY[this.config.level];
  }

  /**
   * Set log level
   */
  setLevel(level: LogLevel): void {
    this.config.level = level;
  }

  /**
   * Get log level
   */
  getLevel(): LogLevel {
    return this.config.level;
  }

  /**
   * Set global context
   */
  setContext(context: Record<string, unknown>): void {
    this.config.context = { ...this.config.context, ...context };
  }

  /**
   * Clear global context
   */
  clearContext(): void {
    this.config.context = {};
  }

  /**
   * Get log buffer
   */
  getBuffer(): LogEntry[] {
    return [...this.logBuffer];
  }

  /**
   * Clear log buffer
   */
  clearBuffer(): void {
    this.logBuffer = [];
  }

  /**
   * Export logs as JSON
   */
  exportJSON(): string {
    return JSON.stringify(this.logBuffer, null, 2);
  }

  /**
   * Close logger and cleanup
   */
  close(): void {
    if (this.fileStream) {
      this.fileStream.end();
      this.fileStream = undefined;
    }
  }

  /**
   * Create child logger with inherited context
   */
  child(context: Record<string, unknown>): Logger {
    return new Logger({
      ...this.config,
      context: { ...this.config.context, ...context }
    });
  }
}

// ============================================================================
// Default Instance
// ============================================================================

/**
 * Default logger instance
 */
export const logger = new Logger({
  level: process.env.LOG_LEVEL ? (process.env.LOG_LEVEL as LogLevel) : LogLevel.INFO,
  enableConsole: true,
  enableColor: true
});

// ============================================================================
// Exports
// ============================================================================

export default Logger;
