/**
 * Core Module Index
 *
 * Экспорт всех публичных API модулей валидатора.
 * Централизованная точка импорта для внешних модулей.
 *
 * @module core
 * @version 2.3.1
 */

// Internal imports for factory functions
import { ConfigManager as ConfigManagerClass } from './config';
import { FileReader as FileReaderClass } from './file-reader';
import { PositionMapBuilder as PositionMapBuilderClass } from './position-map';
import { SDUIValidator as SDUIValidatorClass } from './validator';

// ============================================================================
// CONFIG MODULE
// ============================================================================

export {
  ConfigManager,
  config,
  type ProjectPaths,
  type ValidationOptions,
  type JinjaParsingOptions,
  type OutputOptions,
  type PerformanceOptions,
  type ValidatorConfig,
} from './config';

// ============================================================================
// FILE READER MODULE
// ============================================================================

export {
  FileReader,
  FileFormat,
  FileReadError,
  readFileSync,
  fileExists,
  getFileSize,
  type FileMetadata,
  type FileReadResult,
  type FileReadOptions,
} from './file-reader';

// ============================================================================
// POSITION MAP MODULE
// ============================================================================

export {
  PositionMap,
  PositionMapBuilder,
  type PositionInfo,
  type PositionMapStats,
  type PositionSearchResult,
} from './position-map';

// ============================================================================
// VALIDATOR MODULE
// ============================================================================

export {
  SDUIValidator,
  ValidationError,
  ErrorType,
  Severity,
  type ValidationIssue,
  type DataBindingInfo,
  type DataBindingStats,
  type ComponentVersionStats,
  type ValidationReport,
  type ValidationContext,
  type ValidateOptions,
  type IValidator,
} from './validator';

// ============================================================================
// VERSION INFO
// ============================================================================

/**
 * Версия валидатора
 */
export const VERSION = '2.3.1';

/**
 * Дата сборки
 */
export const BUILD_DATE = '2025-10-07';

/**
 * Информация о валидаторе
 */
export const VALIDATOR_INFO = {
  name: 'SDUI Validator',
  version: VERSION,
  buildDate: BUILD_DATE,
  description: 'Modular TypeScript validator for SDUI contracts',
} as const;

// ============================================================================
// FACTORY FUNCTIONS
// ============================================================================

/**
 * Создать полностью настроенный валидатор с дефолтной конфигурацией
 *
 * @param configOverrides - Переопределения конфигурации (опционально)
 * @returns Настроенный instance SDUIValidator
 *
 * @example
 * ```typescript
 * import { createValidator } from './core';
 *
 * const validator = createValidator({
 *   output: { verbose: true }
 * });
 *
 * const report = await validator.validateFile('/path/to/contract.json');
 * ```
 */
export function createValidator(
  configOverrides?: Partial<import('./config').ValidatorConfig>
): import('./validator').SDUIValidator {
  const configManager = configOverrides
    ? ConfigManagerClass.create(configOverrides)
    : ConfigManagerClass.getInstance();

  const fileReader = new FileReaderClass(configManager);
  const positionMapBuilder = new PositionMapBuilderClass(configManager);

  return new SDUIValidatorClass(configManager, fileReader, positionMapBuilder);
}

/**
 * Создать валидатор с кастомными зависимостями
 *
 * @param config - Конфигурация
 * @param fileReader - Читатель файлов
 * @param positionMapBuilder - Построитель position map
 * @param validators - Дополнительные валидаторы (опционально)
 * @returns Настроенный instance SDUIValidator
 *
 * @example
 * ```typescript
 * import { createValidatorWithDeps, ConfigManager, FileReader, PositionMapBuilder } from './core';
 *
 * const config = ConfigManager.getInstance();
 * const fileReader = new FileReader(config);
 * const positionMapBuilder = new PositionMapBuilder(config);
 *
 * const validator = createValidatorWithDeps(config, fileReader, positionMapBuilder);
 * ```
 */
export function createValidatorWithDeps(
  config: import('./config').ConfigManager,
  fileReader: import('./file-reader').FileReader,
  positionMapBuilder: import('./position-map').PositionMapBuilder,
  validators?: import('./validator').IValidator[]
): import('./validator').SDUIValidator {
  return new SDUIValidatorClass(config, fileReader, positionMapBuilder, validators);
}
