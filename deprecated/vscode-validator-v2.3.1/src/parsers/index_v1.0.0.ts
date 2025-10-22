/**
 * Parser Module Index
 * @version 1.0.0
 * @created 2025-10-07
 */

// Types
export * from './types_v1.0.0.js';

// Parsers
export { JsonParser } from './json-parser_v1.0.0.js';
export type {
  JsonParserConfig,
  JsonParseResult,
  PositionMap,
  PositionInfo,
} from './json-parser_v1.0.0.js';

export { JinjaParser } from './jinja-parser_v1.0.0.js';
export type {
  JinjaParserConfig,
  JinjaParseResult,
  ImportInfo,
  JinjaParsingStats,
  JinjaToken,
  JinjaTokenType,
} from './jinja-parser_v1.0.0.js';

export { ImportResolver } from './import-resolver_v1.0.0.js';
export type {
  ImportResolverConfig,
  ResolvedImport,
  ImportMetadata,
  ImportResolutionResult,
  DependencyGraph,
  DependencyNode,
  DependencyEdge,
  CircularDependency,
  ImportPattern,
  ImportSpec,
} from './import-resolver_v1.0.0.js';

export { VariableReplacer } from './variable-replacer_v1.0.0.js';
export type {
  VariableReplacerConfig,
  VariableReplacementResult,
  Replacement,
  ReplacementSource,
  UndefinedVariable,
  ReplacementStats,
  VariableContext,
  InferenceStrategy,
} from './variable-replacer_v1.0.0.js';

// ============================================================================
// FACTORY FUNCTIONS
// ============================================================================

/**
 * Создает JsonParser с конфигурацией по умолчанию
 */
export function createJsonParser(config?: Partial<import('./json-parser_v1.0.0.js').JsonParserConfig>) {
  const { JsonParser } = require('./json-parser_v1.0.0.js');
  return new JsonParser(config);
}

/**
 * Создает JinjaParser с конфигурацией по умолчанию
 */
export function createJinjaParser(config?: Partial<import('./jinja-parser_v1.0.0.js').JinjaParserConfig>) {
  const { JinjaParser } = require('./jinja-parser_v1.0.0.js');
  return new JinjaParser(config);
}

/**
 * Создает ImportResolver с конфигурацией по умолчанию
 */
export function createImportResolver(config?: Partial<import('./import-resolver_v1.0.0.js').ImportResolverConfig>) {
  const { ImportResolver } = require('./import-resolver_v1.0.0.js');
  return new ImportResolver(config);
}

/**
 * Создает VariableReplacer с конфигурацией по умолчанию
 */
export function createVariableReplacer(config?: Partial<import('./variable-replacer_v1.0.0.js').VariableReplacerConfig>) {
  const { VariableReplacer } = require('./variable-replacer_v1.0.0.js');
  return new VariableReplacer(config);
}

// ============================================================================
// PARSER REGISTRY
// ============================================================================

/**
 * Реестр парсеров
 */
export class ParserRegistry {
  private static parsers = new Map<string, any>();

  /**
   * Регистрирует парсер
   */
  static register(name: string, parser: any): void {
    this.parsers.set(name, parser);
  }

  /**
   * Получает парсер по имени
   */
  static get(name: string): any {
    return this.parsers.get(name);
  }

  /**
   * Проверяет существование парсера
   */
  static has(name: string): boolean {
    return this.parsers.has(name);
  }

  /**
   * Получает все зарегистрированные парсеры
   */
  static getAll(): Map<string, any> {
    return new Map(this.parsers);
  }
}

// Регистрируем стандартные парсеры
ParserRegistry.register('json', JsonParser);
ParserRegistry.register('jinja', JinjaParser);
ParserRegistry.register('import', ImportResolver);
ParserRegistry.register('variable', VariableReplacer);
