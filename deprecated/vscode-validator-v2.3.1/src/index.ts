/**
 * SDUI JSON Validator v2.3.1 - Main Export Module
 *
 * Главная точка экспорта всех модулей валидатора
 *
 * @module index
 * @version 2.3.1
 */

// ============================================================================
// Main Validation Functions
// ============================================================================

export { validateFile, validateFiles, validateDirectory } from './main';

// ============================================================================
// Type Exports
// ============================================================================

export type {
  // Validation Types
  ValidationError,
  ValidationResult,
  ValidationSeverity,
  // Error Categories
  ErrorCategory,
  // File Types
  FileType,
  FileTypeInfo,
  // Jinja Types
  JinjaTokenType,
  JinjaToken,
  JinjaBlock,
  // Configuration
  ValidatorConfig,
  OutputFormat,
  // Performance
  PerformanceMetrics,
  BenchmarkResult,
  // Cache
  CacheEntry,
  CacheStats,
  // Logging
  LogLevel,
  LogEntry,
  // VSCode Integration
  VscodeDiagnostic,
  VscodeLink,
  // Parser
  ParserState,
  // Utility Types
  DeepReadonly,
  DeepPartial,
  RequiredFields,
  AsyncFunction
} from './types';

// ============================================================================
// Version Information
// ============================================================================

export const VERSION = '2.3.1';
export const PACKAGE_NAME = 'vscode-sdui-validator';

// ============================================================================
// Default Export
// ============================================================================

import { validateFile } from './main';

export default validateFile;

// ============================================================================
// Module Information
// ============================================================================

/**
 * SDUI JSON Validator
 *
 * Функции:
 * - Валидация JSON синтаксиса
 * - Поддержка Jinja2 шаблонов (.jinja.json, .j2.java)
 * - Детальная диагностика ошибок
 * - Метрики производительности
 * - CLI интерфейс
 * - VSCode интеграция
 *
 * Использование:
 * ```typescript
 * import { validateFile } from 'vscode-sdui-validator';
 *
 * const result = await validateFile('path/to/file.json', {
 *   jinjaAware: true,
 *   strict: true
 * });
 *
 * if (!result.isValid) {
 *   result.errors.forEach(error => {
 *     console.error(`Line ${error.line}: ${error.message}`);
 *   });
 * }
 * ```
 *
 * CLI:
 * ```bash
 * vscode-validator file.json --verbose --jinja-aware
 * vscode-validator *.json -r --output json
 * ```
 *
 * @packageDocumentation
 */
