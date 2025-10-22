/**
 * Variable Replacer - замена переменных в шаблонах
 * @version 1.0.0
 * @created 2025-10-07
 */

import {
  IParser,
  ParseResult,
  ParseOptions,
  ParserConfig,
  ParseError,
  ParseWarning,
  ParseErrorType,
  ParseWarningType,
  createSuccessResult,
  createErrorResult,
  createPosition,
  SourcePosition,
} from './types_v1.0.0.js';

// ============================================================================
// ТИПЫ
// ============================================================================

/**
 * Конфигурация replacer'а переменных
 */
export interface VariableReplacerConfig extends ParserConfig {
  variablePattern?: RegExp;
  defaultInferenceEnabled?: boolean;
  customDefaults?: Map<string, any>;
  allowUndefined?: boolean;
  escapeOutput?: boolean;
}

/**
 * Результат замены переменных
 */
export interface VariableReplacementResult {
  content: string;
  replacements: Replacement[];
  undefinedVariables: UndefinedVariable[];
  stats: ReplacementStats;
}

/**
 * Информация о замене
 */
export interface Replacement {
  variable: string;
  originalValue: string;
  replacedValue: any;
  position: SourcePosition;
  source: ReplacementSource;
  inferred: boolean;
}

/**
 * Источник значения замены
 */
export enum ReplacementSource {
  CUSTOM_DEFAULTS = 'custom_defaults',
  INFERENCE = 'inference',
  UNDEFINED = 'undefined',
}

/**
 * Неопределенная переменная
 */
export interface UndefinedVariable {
  name: string;
  position: SourcePosition;
  context: string;
}

/**
 * Статистика замен
 */
export interface ReplacementStats {
  totalReplacements: number;
  inferredReplacements: number;
  customReplacements: number;
  undefinedReplacements: number;
  byType: Record<string, number>;
}

/**
 * Контекст переменной
 */
export interface VariableContext {
  name: string;
  position: SourcePosition;
  surroundingText: string;
  expectedType?: string;
}

/**
 * Стратегия вывода типа
 */
export interface InferenceStrategy {
  name: string;
  pattern: RegExp;
  inferValue: (name: string, context?: VariableContext) => any;
  priority: number;
}

// ============================================================================
// VARIABLE REPLACER
// ============================================================================

/**
 * Replacer переменных в шаблонах
 */
export class VariableReplacer
  implements IParser<string, VariableReplacementResult, VariableReplacerConfig>
{
  private config: VariableReplacerConfig;
  private strategies: InferenceStrategy[];

  constructor(config: VariableReplacerConfig = {}) {
    this.config = {
      strict: false,
      maxErrors: 100,
      timeout: 30000,
      verbose: false,
      variablePattern: /\{\{\s*([^}]+?)\s*\}\}/g,
      defaultInferenceEnabled: true,
      customDefaults: new Map(),
      allowUndefined: false,
      escapeOutput: true,
      ...config,
    };

    this.strategies = this.initializeStrategies();
  }

  /**
   * Заменяет переменные в контенте
   */
  async parse(
    content: string,
    options?: ParseOptions
  ): Promise<ParseResult<VariableReplacementResult>> {
    const startTime = Date.now();
    const errors: ParseError[] = [];
    const warnings: ParseWarning[] = [];

    try {
      const result = this.replaceVariables(content, '', errors, warnings);

      if (errors.length > 0 && this.config.strict) {
        return createErrorResult(
          errors,
          {
            parseTimeMs: Date.now() - startTime,
            filePath: '',
            fileSize: Buffer.byteLength(content, 'utf-8'),
            version: '1.0.0',
          },
          warnings
        );
      }

      return createSuccessResult(
        result,
        {
          parseTimeMs: Date.now() - startTime,
          filePath: '',
          fileSize: Buffer.byteLength(content, 'utf-8'),
          version: '1.0.0',
        },
        warnings
      );
    } catch (error) {
      errors.push({
        type: ParseErrorType.UNKNOWN,
        message: `Unexpected error: ${(error as Error).message}`,
        position: createPosition(0, 0, 0),
        filePath: '',
      });

      return createErrorResult(
        errors,
        {
          parseTimeMs: Date.now() - startTime,
          filePath: '',
          fileSize: 0,
          version: '1.0.0',
        },
        warnings
      );
    }
  }

  /**
   * Синхронная замена переменных
   */
  parseSync(content: string, options?: ParseOptions): ParseResult<VariableReplacementResult> {
    const startTime = Date.now();
    const errors: ParseError[] = [];
    const warnings: ParseWarning[] = [];

    try {
      const result = this.replaceVariables(content, '', errors, warnings);

      if (errors.length > 0 && this.config.strict) {
        return createErrorResult(
          errors,
          {
            parseTimeMs: Date.now() - startTime,
            filePath: '',
            fileSize: Buffer.byteLength(content, 'utf-8'),
            version: '1.0.0',
          },
          warnings
        );
      }

      return createSuccessResult(
        result,
        {
          parseTimeMs: Date.now() - startTime,
          filePath: '',
          fileSize: Buffer.byteLength(content, 'utf-8'),
          version: '1.0.0',
        },
        warnings
      );
    } catch (error) {
      errors.push({
        type: ParseErrorType.UNKNOWN,
        message: `Unexpected error: ${(error as Error).message}`,
        position: createPosition(0, 0, 0),
        filePath: '',
      });

      return createErrorResult(
        errors,
        {
          parseTimeMs: Date.now() - startTime,
          filePath: '',
          fileSize: 0,
          version: '1.0.0',
        },
        warnings
      );
    }
  }

  /**
   * Валидация переменных
   */
  async validate(content: string): Promise<boolean> {
    const errors: ParseError[] = [];
    const warnings: ParseWarning[] = [];
    const result = this.replaceVariables(content, '', errors, warnings);
    return errors.length === 0 && result.undefinedVariables.length === 0;
  }

  getConfig(): Readonly<VariableReplacerConfig> {
    return { ...this.config };
  }

  updateConfig(config: Partial<VariableReplacerConfig>): void {
    this.config = { ...this.config, ...config };
  }

  // ============================================================================
  // REPLACEMENT
  // ============================================================================

  /**
   * Заменяет все переменные в контенте
   */
  private replaceVariables(
    content: string,
    filePath: string,
    errors: ParseError[],
    warnings: ParseWarning[]
  ): VariableReplacementResult {
    const replacements: Replacement[] = [];
    const undefinedVariables: UndefinedVariable[] = [];
    const stats: ReplacementStats = {
      totalReplacements: 0,
      inferredReplacements: 0,
      customReplacements: 0,
      undefinedReplacements: 0,
      byType: {},
    };

    let processedContent = content;
    const lines = content.split('\n');

    // Обрабатываем построчно для точного определения позиций
    for (let lineIndex = 0; lineIndex < lines.length; lineIndex++) {
      const line = lines[lineIndex];
      const lineNumber = lineIndex + 1;
      let processedLine = line;

      const matches = Array.from(line.matchAll(this.config.variablePattern!));

      for (const match of matches) {
        const fullMatch = match[0];
        const variableName = match[1].trim();
        const column = match.index! + 1;
        const offset = content.indexOf(line) + match.index!;

        // Создаем контекст
        const context: VariableContext = {
          name: variableName,
          position: createPosition(lineNumber, column, offset, fullMatch.length),
          surroundingText: this.extractContext(line, match.index!),
        };

        // Получаем значение замены
        const replacement = this.getReplacementValue(
          variableName,
          context,
          filePath,
          warnings
        );

        if (replacement === undefined) {
          // Неопределенная переменная
          undefinedVariables.push({
            name: variableName,
            position: context.position,
            context: context.surroundingText,
          });

          stats.undefinedReplacements++;

          if (!this.config.allowUndefined) {
            errors.push({
              type: ParseErrorType.UNRESOLVED_VARIABLE,
              message: `Unresolved variable: ${variableName}`,
              position: context.position,
              filePath,
              suggestion: 'Define this variable in customDefaults or enable inference',
            });
          }

          continue;
        }

        // Выполняем замену
        const replacedValue = this.config.escapeOutput
          ? this.escapeValue(replacement.value)
          : replacement.value;

        const serialized = JSON.stringify(replacedValue);
        processedLine = processedLine.replace(fullMatch, serialized);

        replacements.push({
          variable: variableName,
          originalValue: fullMatch,
          replacedValue,
          position: context.position,
          source: replacement.source,
          inferred: replacement.inferred,
        });

        stats.totalReplacements++;
        if (replacement.inferred) {
          stats.inferredReplacements++;
        } else {
          stats.customReplacements++;
        }

        // Подсчет по типам
        const valueType = typeof replacedValue;
        stats.byType[valueType] = (stats.byType[valueType] || 0) + 1;

        // Предупреждение о выводе типа
        if (replacement.inferred && this.config.verbose) {
          warnings.push({
            type: ParseWarningType.IMPLICIT_CONVERSION,
            message: `Variable '${variableName}' inferred as ${valueType}: ${serialized}`,
            position: context.position,
            filePath,
          });
        }
      }

      lines[lineIndex] = processedLine;
    }

    processedContent = lines.join('\n');

    return {
      content: processedContent,
      replacements,
      undefinedVariables,
      stats,
    };
  }

  // ============================================================================
  // VALUE RESOLUTION
  // ============================================================================

  /**
   * Получает значение замены для переменной
   */
  private getReplacementValue(
    variableName: string,
    context: VariableContext,
    filePath: string,
    warnings: ParseWarning[]
  ): { value: any; source: ReplacementSource; inferred: boolean } | undefined {
    // 1. Проверяем custom defaults
    if (this.config.customDefaults?.has(variableName)) {
      return {
        value: this.config.customDefaults.get(variableName),
        source: ReplacementSource.CUSTOM_DEFAULTS,
        inferred: false,
      };
    }

    // 2. Применяем стратегии вывода
    if (this.config.defaultInferenceEnabled) {
      const inferred = this.inferValue(variableName, context);
      if (inferred !== undefined) {
        return {
          value: inferred,
          source: ReplacementSource.INFERENCE,
          inferred: true,
        };
      }
    }

    // 3. Неопределенная переменная
    return undefined;
  }

  /**
   * Выводит значение на основе имени переменной
   */
  private inferValue(variableName: string, context?: VariableContext): any {
    // Сортируем стратегии по приоритету
    const sortedStrategies = [...this.strategies].sort((a, b) => b.priority - a.priority);

    for (const strategy of sortedStrategies) {
      if (strategy.pattern.test(variableName)) {
        return strategy.inferValue(variableName, context);
      }
    }

    // Fallback - пустая строка
    return '';
  }

  /**
   * Инициализирует стратегии вывода
   */
  private initializeStrategies(): InferenceStrategy[] {
    return [
      {
        name: 'boolean',
        pattern: /^(is|has|should|enable|show|hide|allow|disable)[A-Z]/,
        inferValue: () => false,
        priority: 100,
      },
      {
        name: 'number',
        pattern: /(count|size|length|width|height|index|id|num|number)$/i,
        inferValue: () => 0,
        priority: 90,
      },
      {
        name: 'array',
        pattern: /(list|items|array|collection|elements)$/i,
        inferValue: () => [],
        priority: 80,
      },
      {
        name: 'object',
        pattern: /(data|config|options|settings|params|props)$/i,
        inferValue: () => ({}),
        priority: 70,
      },
      {
        name: 'null',
        pattern: /(null|none|empty)$/i,
        inferValue: () => null,
        priority: 60,
      },
      {
        name: 'string',
        pattern: /(name|title|text|label|description|message|content)$/i,
        inferValue: () => '',
        priority: 50,
      },
    ];
  }

  // ============================================================================
  // UTILITIES
  // ============================================================================

  /**
   * Извлекает контекст вокруг позиции
   */
  private extractContext(line: string, position: number, contextLength: number = 20): string {
    const start = Math.max(0, position - contextLength);
    const end = Math.min(line.length, position + contextLength);
    return line.substring(start, end);
  }

  /**
   * Экранирует значение для безопасного вывода
   */
  private escapeValue(value: any): any {
    if (typeof value === 'string') {
      return value
        .replace(/\\/g, '\\\\')
        .replace(/"/g, '\\"')
        .replace(/\n/g, '\\n')
        .replace(/\r/g, '\\r')
        .replace(/\t/g, '\\t');
    }
    return value;
  }

  /**
   * Добавляет кастомное значение по умолчанию
   */
  setCustomDefault(variableName: string, value: any): void {
    if (!this.config.customDefaults) {
      this.config.customDefaults = new Map();
    }
    this.config.customDefaults.set(variableName, value);
  }

  /**
   * Добавляет кастомную стратегию вывода
   */
  addInferenceStrategy(strategy: InferenceStrategy): void {
    this.strategies.push(strategy);
  }

  /**
   * Получает статистику по переменным
   */
  getVariableStats(content: string): {
    total: number;
    unique: string[];
    byOccurrence: Map<string, number>;
  } {
    const variables = new Set<string>();
    const occurrences = new Map<string, number>();

    const matches = Array.from(content.matchAll(this.config.variablePattern!));

    for (const match of matches) {
      const variableName = match[1].trim();
      variables.add(variableName);
      occurrences.set(variableName, (occurrences.get(variableName) || 0) + 1);
    }

    return {
      total: matches.length,
      unique: Array.from(variables),
      byOccurrence: occurrences,
    };
  }

  /**
   * Извлекает все переменные без замены
   */
  extractVariables(content: string): VariableContext[] {
    const variables: VariableContext[] = [];
    const lines = content.split('\n');

    for (let lineIndex = 0; lineIndex < lines.length; lineIndex++) {
      const line = lines[lineIndex];
      const lineNumber = lineIndex + 1;

      const matches = Array.from(line.matchAll(this.config.variablePattern!));

      for (const match of matches) {
        const variableName = match[1].trim();
        const column = match.index! + 1;
        const offset = content.indexOf(line) + match.index!;

        variables.push({
          name: variableName,
          position: createPosition(lineNumber, column, offset, match[0].length),
          surroundingText: this.extractContext(line, match.index!),
        });
      }
    }

    return variables;
  }
}
