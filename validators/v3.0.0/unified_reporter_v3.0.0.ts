/**
 * Unified Error Reporter v3.0.0
 *
 * Унифицированный репортер ошибок для всех типов валидации:
 * - Metaschema validation (Ruby validator)
 * - SDUI validation (MCP validator)
 * - Web compatibility validation
 * - StateAware validation
 * - Required fields validation
 *
 * Особенности:
 * - Поддержка множественных источников ошибок
 * - Группировка по компонентам и типам
 * - Severity levels (error, warning, info)
 * - Кликабельные ссылки file:line:col
 * - Экспорт в JSON/HTML/Markdown
 * - Цветной вывод в терминал
 * - Плагинная архитектура форматтеров
 */

import { basename, relative } from 'path';

// ============================================================================
// ТИПЫ И ИНТЕРФЕЙСЫ
// ============================================================================

/**
 * Уровень серьезности ошибки
 */
export type SeverityLevel = 'error' | 'warning' | 'info';

/**
 * Источник валидации
 */
export type ValidationSource =
  | 'metaschema'      // Ruby validator
  | 'sdui'            // MCP SDUI validator
  | 'web-compat'      // Web compatibility
  | 'stateaware'      // StateAware patterns
  | 'required-fields' // Required fields
  | 'data-binding'    // Data binding
  | 'custom';         // Кастомные валидаторы

/**
 * Базовая ошибка валидации
 */
export interface ValidationError {
  // Идентификация
  source: ValidationSource;
  severity: SeverityLevel;

  // Локация
  filePath: string;
  line?: number;
  column?: number;
  path?: string;           // JSONPath или dot notation
  jsonPointer?: string;    // RFC 6901 JSON Pointer

  // Содержимое
  message: string;
  code?: string;           // Код ошибки (например, "MISSING_REQUIRED_FIELD")

  // Контекст
  component?: string;      // Имя компонента (ButtonView, IconView)
  version?: string;        // Версия компонента (v1, v2)
  field?: string;          // Конкретное поле с ошибкой

  // Дополнительная информация
  suggestion?: string;     // Подсказка по исправлению
  relatedErrors?: string[]; // Связанные ошибки (например, oneOf branches)
  metadata?: Record<string, any>; // Произвольные метаданные
}

/**
 * Группа ошибок
 */
export interface ErrorGroup {
  name: string;            // Имя группы (компонент, тип ошибки)
  errors: ValidationError[];
  severity: SeverityLevel; // Максимальный severity в группе
  count: number;
}

/**
 * Отчет валидации
 */
export interface ValidationReport {
  // Основная информация
  filePath: string;
  valid: boolean;

  // Ошибки и предупреждения
  errors: ValidationError[];
  warnings: ValidationError[];
  infos: ValidationError[];

  // Статистика
  totalErrors: number;
  totalWarnings: number;
  totalInfos: number;

  // Группировки
  bySource: Map<ValidationSource, ValidationError[]>;
  byComponent: Map<string, ValidationError[]>;
  bySeverity: Map<SeverityLevel, ValidationError[]>;

  // Метаданные
  timestamp: Date;
  duration?: number;
  metadata?: Record<string, any>;
}

/**
 * Конфигурация репортера
 */
export interface ReporterConfig {
  // Вывод
  colorize: boolean;
  verbose: boolean;
  groupBy: 'component' | 'source' | 'severity' | 'none';

  // Форматирование
  showPath: boolean;
  showJsonPointer: boolean;
  showLineNumbers: boolean;
  showSuggestions: boolean;

  // Фильтрация
  minSeverity: SeverityLevel;
  includeSources?: ValidationSource[];
  excludeSources?: ValidationSource[];

  // Экспорт
  exportFormats: Array<'json' | 'html' | 'markdown' | 'text'>;
  outputDir?: string;
}

/**
 * Интерфейс форматтера
 */
export interface ErrorFormatter {
  name: string;
  format(report: ValidationReport, config: ReporterConfig): string;
  supportsColor: boolean;
}

// ============================================================================
// МАППИНГ ПУТЕЙ В СТРОКИ (Position Map)
// ============================================================================

interface PositionMap {
  pathToLine: Map<string, number>;
  pointerToLine: Map<string, number>;
}

/**
 * Конвертация path -> JSON Pointer (RFC 6901)
 */
function pathToJsonPointer(path: string): string {
  if (!path) return '';

  const segments: string[] = [];
  let current = '';
  let inBracket = false;

  for (let i = 0; i < path.length; i++) {
    const char = path[i];

    if (char === '[' && path[i + 1] === "'") {
      if (current) {
        segments.push(current);
        current = '';
      }
      inBracket = true;
      i++; // skip '
      continue;
    }

    if (char === "'" && path[i + 1] === ']' && inBracket) {
      segments.push(current);
      current = '';
      inBracket = false;
      i++; // skip ]
      continue;
    }

    if (char === '[' && !inBracket) {
      if (current) {
        segments.push(current);
        current = '';
      }
      continue;
    }

    if (char === ']' && !inBracket) {
      segments.push(current);
      current = '';
      continue;
    }

    if (char === '.' && !inBracket) {
      if (current) {
        segments.push(current);
        current = '';
      }
      continue;
    }

    current += char;
  }

  if (current) {
    segments.push(current);
  }

  // Экранирование по RFC 6901: ~ -> ~0, / -> ~1
  const escaped = segments.map((seg) =>
    seg.replace(/~/g, '~0').replace(/\//g, '~1')
  );

  return '/' + escaped.join('/');
}

/**
 * Поиск номера строки по path/pointer
 */
function findLineNumber(
  positionMap: PositionMap,
  path: string,
  pointer: string
): number {
  // Проверяем по pointer
  if (positionMap.pointerToLine.has(pointer)) {
    return positionMap.pointerToLine.get(pointer)!;
  }

  // Проверяем по path
  if (positionMap.pathToLine.has(path)) {
    return positionMap.pathToLine.get(path)!;
  }

  // Ищем ближайший родительский путь
  const pathParts = path.split('.');
  while (pathParts.length > 0) {
    pathParts.pop();
    const parentPath = pathParts.join('.');
    if (positionMap.pathToLine.has(parentPath)) {
      return positionMap.pathToLine.get(parentPath)!;
    }
  }

  return 1; // fallback
}

// ============================================================================
// UNIFIED REPORTER
// ============================================================================

export class UnifiedReporter {
  private config: ReporterConfig;
  private formatters: Map<string, ErrorFormatter> = new Map();

  constructor(config: Partial<ReporterConfig> = {}) {
    this.config = {
      colorize: true,
      verbose: false,
      groupBy: 'component',
      showPath: true,
      showJsonPointer: true,
      showLineNumbers: true,
      showSuggestions: true,
      minSeverity: 'info',
      exportFormats: ['text'],
      ...config,
    };

    // Регистрируем стандартные форматтеры
    this.registerFormatter(new TextFormatter());
    this.registerFormatter(new JsonFormatter());
    this.registerFormatter(new MarkdownFormatter());
    this.registerFormatter(new HtmlFormatter());
  }

  /**
   * Регистрация кастомного форматтера
   */
  registerFormatter(formatter: ErrorFormatter): void {
    this.formatters.set(formatter.name, formatter);
  }

  /**
   * Создание отчета из массива ошибок
   */
  createReport(
    filePath: string,
    errors: ValidationError[],
    metadata?: Record<string, any>
  ): ValidationReport {
    // Фильтрация по severity
    const filteredErrors = this.filterBySeverity(errors);

    // Разделение по severity
    const errorsList = filteredErrors.filter(e => e.severity === 'error');
    const warningsList = filteredErrors.filter(e => e.severity === 'warning');
    const infosList = filteredErrors.filter(e => e.severity === 'info');

    // Группировка
    const bySource = this.groupBySource(filteredErrors);
    const byComponent = this.groupByComponent(filteredErrors);
    const bySeverity = this.groupBySeverity(filteredErrors);

    return {
      filePath,
      valid: errorsList.length === 0,
      errors: errorsList,
      warnings: warningsList,
      infos: infosList,
      totalErrors: errorsList.length,
      totalWarnings: warningsList.length,
      totalInfos: infosList.length,
      bySource,
      byComponent,
      bySeverity,
      timestamp: new Date(),
      metadata,
    };
  }

  /**
   * Добавление ошибки из Ruby валидатора
   */
  addRubyError(
    filePath: string,
    path: string,
    ruleName: string,
    error: string
  ): ValidationError {
    return {
      source: 'metaschema',
      severity: 'error',
      filePath,
      path,
      message: `${ruleName}: ${error}`,
      code: ruleName,
    };
  }

  /**
   * Добавление ошибки из MCP валидатора
   */
  addMcpError(
    filePath: string,
    error: {
      path: string;
      component?: string;
      version?: string;
      message: string;
      severity?: SeverityLevel;
      suggestion?: string;
      missingFields?: string[];
    }
  ): ValidationError {
    return {
      source: 'sdui',
      severity: error.severity || 'error',
      filePath,
      path: error.path,
      component: error.component,
      version: error.version,
      message: error.message,
      suggestion: error.suggestion,
      metadata: error.missingFields ? { missingFields: error.missingFields } : undefined,
    };
  }

  /**
   * Добавление ошибки из текущего TypeScript валидатора
   */
  addWebCompatError(
    filePath: string,
    path: string,
    message: string,
    component?: string
  ): ValidationError {
    return {
      source: 'web-compat',
      severity: 'warning',
      filePath,
      path,
      component,
      message,
    };
  }

  /**
   * Вывод отчета
   */
  print(report: ValidationReport, positionMap?: PositionMap): void {
    const formatter = this.formatters.get('text');
    if (!formatter) {
      console.error('Text formatter not found');
      return;
    }

    const output = formatter.format(report, this.config);
    console.log(output);

    // Детальный вывод с номерами строк
    if (positionMap && this.config.showLineNumbers) {
      this.printDetailedErrors(report, positionMap);
    }
  }

  /**
   * Экспорт в файл
   */
  async export(report: ValidationReport, format: 'json' | 'html' | 'markdown' | 'text'): Promise<string> {
    const formatter = this.formatters.get(format);
    if (!formatter) {
      throw new Error(`Formatter '${format}' not found`);
    }

    return formatter.format(report, this.config);
  }

  /**
   * Фильтрация по severity
   */
  private filterBySeverity(errors: ValidationError[]): ValidationError[] {
    const severityOrder: Record<SeverityLevel, number> = {
      error: 2,
      warning: 1,
      info: 0,
    };

    const minLevel = severityOrder[this.config.minSeverity];
    return errors.filter(e => severityOrder[e.severity] >= minLevel);
  }

  /**
   * Группировка по источнику
   */
  private groupBySource(errors: ValidationError[]): Map<ValidationSource, ValidationError[]> {
    const grouped = new Map<ValidationSource, ValidationError[]>();

    for (const error of errors) {
      if (!grouped.has(error.source)) {
        grouped.set(error.source, []);
      }
      grouped.get(error.source)!.push(error);
    }

    return grouped;
  }

  /**
   * Группировка по компоненту
   */
  private groupByComponent(errors: ValidationError[]): Map<string, ValidationError[]> {
    const grouped = new Map<string, ValidationError[]>();

    for (const error of errors) {
      const key = error.component || 'Other';
      if (!grouped.has(key)) {
        grouped.set(key, []);
      }
      grouped.get(key)!.push(error);
    }

    return grouped;
  }

  /**
   * Группировка по severity
   */
  private groupBySeverity(errors: ValidationError[]): Map<SeverityLevel, ValidationError[]> {
    const grouped = new Map<SeverityLevel, ValidationError[]>();

    for (const error of errors) {
      if (!grouped.has(error.severity)) {
        grouped.set(error.severity, []);
      }
      grouped.get(error.severity)!.push(error);
    }

    return grouped;
  }

  /**
   * Детальный вывод ошибок с номерами строк
   */
  private printDetailedErrors(report: ValidationReport, positionMap: PositionMap): void {
    const allErrors = [...report.errors, ...report.warnings, ...report.infos];

    for (const error of allErrors) {
      const pointer = error.jsonPointer || pathToJsonPointer(error.path || '');
      const line = error.line || findLineNumber(positionMap, error.path || '', pointer);
      const col = error.column || 1;

      console.log(`      -> ${error.filePath}:${line}:${col}`);
    }
  }
}

// ============================================================================
// TEXT FORMATTER
// ============================================================================

class TextFormatter implements ErrorFormatter {
  name = 'text';
  supportsColor = true;

  format(report: ValidationReport, config: ReporterConfig): string {
    const lines: string[] = [];
    const fileName = basename(report.filePath);
    const relativePath = relative(process.cwd(), report.filePath);

    // HEADER
    lines.push('━'.repeat(80));
    lines.push(`📄 ${fileName}`);
    lines.push(`📁 ${relativePath}`);
    lines.push('━'.repeat(80));
    lines.push('');

    // STATUS
    if (report.valid) {
      lines.push('✅ CONTRACT VALID');
    } else {
      lines.push('❌ CONTRACT INVALID');
    }
    lines.push('');

    // SUMMARY
    lines.push('📊 SUMMARY');
    lines.push(`   Errors   ${''.padEnd(10, '.')} ${report.totalErrors}`);
    lines.push(`   Warnings ${''.padEnd(10, '.')} ${report.totalWarnings}`);
    lines.push(`   Infos    ${''.padEnd(10, '.')} ${report.totalInfos}`);
    lines.push('');

    // ERRORS BY SOURCE
    if (report.bySource.size > 0) {
      lines.push('📦 BY SOURCE');
      for (const [source, errors] of report.bySource) {
        lines.push(`   ${source} ${''.padEnd(15 - source.length, '.')} ${errors.length} issue${errors.length !== 1 ? 's' : ''}`);
      }
      lines.push('');
    }

    // ERRORS
    if (report.errors.length > 0) {
      lines.push('━'.repeat(80));
      lines.push(`❌ ERRORS: ${report.errors.length}`);
      lines.push('━'.repeat(80));
      lines.push('');

      const grouped = this.groupErrors(report.errors, config.groupBy);
      lines.push(...this.formatGroups(grouped, '❌', config));
    }

    // WARNINGS
    if (report.warnings.length > 0) {
      lines.push('━'.repeat(80));
      lines.push(`⚠️  WARNINGS: ${report.warnings.length}`);
      lines.push('━'.repeat(80));
      lines.push('');

      const grouped = this.groupErrors(report.warnings, config.groupBy);
      lines.push(...this.formatGroups(grouped, '⚠️ ', config));
    }

    // FOOTER
    lines.push('━'.repeat(80));
    if (report.valid) {
      lines.push('✅ Контракт готов к использованию');
    } else {
      lines.push('❌ Контракт требует исправления');
    }
    lines.push('━'.repeat(80));
    lines.push('');

    return lines.join('\n');
  }

  private groupErrors(
    errors: ValidationError[],
    groupBy: 'component' | 'source' | 'severity' | 'none'
  ): ErrorGroup[] {
    if (groupBy === 'none') {
      return [{
        name: 'All',
        errors,
        severity: 'error',
        count: errors.length,
      }];
    }

    const grouped = new Map<string, ValidationError[]>();

    for (const error of errors) {
      let key: string;
      switch (groupBy) {
        case 'component':
          key = error.component || 'Other';
          break;
        case 'source':
          key = error.source;
          break;
        case 'severity':
          key = error.severity;
          break;
        default:
          key = 'Other';
      }

      if (!grouped.has(key)) {
        grouped.set(key, []);
      }
      grouped.get(key)!.push(error);
    }

    return Array.from(grouped.entries()).map(([name, errors]) => ({
      name,
      errors,
      severity: errors[0].severity,
      count: errors.length,
    }));
  }

  private formatGroups(groups: ErrorGroup[], icon: string, config: ReporterConfig): string[] {
    const lines: string[] = [];

    for (const group of groups) {
      // Component box
      lines.push(this.formatComponentBox(group.name, group.count));

      // Errors
      let index = 1;
      for (const error of group.errors) {
        lines.push('');
        lines.push(`  ${icon} [${index}] ${error.message}`);
        lines.push('');

        if (config.showPath && error.path) {
          lines.push(`      Path: ${error.path}`);
        }

        if (config.showJsonPointer && error.jsonPointer) {
          lines.push(`      JSON Pointer: ${error.jsonPointer}`);
        }

        if (config.showSuggestions && error.suggestion) {
          lines.push(`      💡 ${error.suggestion}`);
        }

        if (error.relatedErrors && error.relatedErrors.length > 0) {
          lines.push(`      Related errors:`);
          error.relatedErrors.forEach(re => {
            lines.push(`        - ${re}`);
          });
        }

        lines.push('');

        if (index < group.errors.length) {
          lines.push('─'.repeat(80));
        }

        index++;
      }

      lines.push('━'.repeat(80));
      lines.push('');
    }

    return lines;
  }

  private formatComponentBox(componentName: string, count: number): string {
    const maxWidth = 78;
    const info = `${count} issue${count !== 1 ? 's' : ''}`;

    const titleLine = `┌─ ${componentName} `;
    const titlePadding = maxWidth - titleLine.length - 1;
    const topBorder = titleLine + '─'.repeat(titlePadding) + '┐';

    const infoLine = `│ ${info} `;
    const infoPadding = maxWidth - infoLine.length - 1;
    const middleLine = infoLine + ' '.repeat(infoPadding) + '│';

    const bottomBorder = '└' + '─'.repeat(maxWidth) + '┘';

    return [topBorder, middleLine, bottomBorder].join('\n');
  }
}

// ============================================================================
// JSON FORMATTER
// ============================================================================

class JsonFormatter implements ErrorFormatter {
  name = 'json';
  supportsColor = false;

  format(report: ValidationReport, config: ReporterConfig): string {
    const output = {
      filePath: report.filePath,
      valid: report.valid,
      timestamp: report.timestamp.toISOString(),
      summary: {
        errors: report.totalErrors,
        warnings: report.totalWarnings,
        infos: report.totalInfos,
      },
      errors: report.errors.map(e => this.serializeError(e)),
      warnings: report.warnings.map(e => this.serializeError(e)),
      infos: report.infos.map(e => this.serializeError(e)),
      metadata: report.metadata,
    };

    return JSON.stringify(output, null, 2);
  }

  private serializeError(error: ValidationError): any {
    return {
      source: error.source,
      severity: error.severity,
      message: error.message,
      code: error.code,
      location: {
        filePath: error.filePath,
        line: error.line,
        column: error.column,
        path: error.path,
        jsonPointer: error.jsonPointer,
      },
      component: error.component,
      version: error.version,
      field: error.field,
      suggestion: error.suggestion,
      relatedErrors: error.relatedErrors,
      metadata: error.metadata,
    };
  }
}

// ============================================================================
// MARKDOWN FORMATTER
// ============================================================================

class MarkdownFormatter implements ErrorFormatter {
  name = 'markdown';
  supportsColor = false;

  format(report: ValidationReport, config: ReporterConfig): string {
    const lines: string[] = [];
    const fileName = basename(report.filePath);

    // HEADER
    lines.push(`# Validation Report: ${fileName}`);
    lines.push('');
    lines.push(`**File:** \`${report.filePath}\``);
    lines.push(`**Status:** ${report.valid ? '✅ Valid' : '❌ Invalid'}`);
    lines.push(`**Date:** ${report.timestamp.toISOString()}`);
    lines.push('');

    // SUMMARY
    lines.push('## Summary');
    lines.push('');
    lines.push('| Metric | Count |');
    lines.push('|--------|-------|');
    lines.push(`| Errors | ${report.totalErrors} |`);
    lines.push(`| Warnings | ${report.totalWarnings} |`);
    lines.push(`| Infos | ${report.totalInfos} |`);
    lines.push('');

    // ERRORS
    if (report.errors.length > 0) {
      lines.push('## Errors');
      lines.push('');

      report.errors.forEach((error, idx) => {
        lines.push(`### ${idx + 1}. ${error.message}`);
        lines.push('');

        if (error.component) {
          lines.push(`**Component:** ${error.component}${error.version ? ` (${error.version})` : ''}`);
        }

        if (error.path) {
          lines.push(`**Path:** \`${error.path}\``);
        }

        if (error.line) {
          lines.push(`**Location:** ${error.filePath}:${error.line}${error.column ? `:${error.column}` : ''}`);
        }

        if (error.suggestion) {
          lines.push('');
          lines.push(`💡 **Suggestion:** ${error.suggestion}`);
        }

        lines.push('');
      });
    }

    // WARNINGS
    if (report.warnings.length > 0) {
      lines.push('## Warnings');
      lines.push('');

      report.warnings.forEach((warning, idx) => {
        lines.push(`### ${idx + 1}. ${warning.message}`);
        lines.push('');

        if (warning.path) {
          lines.push(`**Path:** \`${warning.path}\``);
        }

        lines.push('');
      });
    }

    return lines.join('\n');
  }
}

// ============================================================================
// HTML FORMATTER
// ============================================================================

class HtmlFormatter implements ErrorFormatter {
  name = 'html';
  supportsColor = false;

  format(report: ValidationReport, config: ReporterConfig): string {
    const fileName = basename(report.filePath);

    return `
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Validation Report: ${fileName}</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
      line-height: 1.6;
      max-width: 1200px;
      margin: 0 auto;
      padding: 20px;
      background: #f5f5f5;
    }
    .header {
      background: white;
      padding: 20px;
      border-radius: 8px;
      margin-bottom: 20px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .status {
      display: inline-block;
      padding: 4px 12px;
      border-radius: 4px;
      font-weight: 600;
      margin-left: 10px;
    }
    .status.valid { background: #d4edda; color: #155724; }
    .status.invalid { background: #f8d7da; color: #721c24; }
    .summary {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 15px;
      margin: 20px 0;
    }
    .summary-card {
      background: white;
      padding: 15px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .error-section {
      background: white;
      padding: 20px;
      border-radius: 8px;
      margin: 20px 0;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .error-item {
      border-left: 4px solid #dc3545;
      padding: 15px;
      margin: 10px 0;
      background: #fff5f5;
      border-radius: 4px;
    }
    .warning-item {
      border-left: 4px solid #ffc107;
      padding: 15px;
      margin: 10px 0;
      background: #fffef5;
      border-radius: 4px;
    }
    .error-meta {
      font-size: 0.9em;
      color: #6c757d;
      margin-top: 8px;
    }
    code {
      background: #f4f4f4;
      padding: 2px 6px;
      border-radius: 3px;
      font-family: 'Monaco', 'Menlo', monospace;
      font-size: 0.9em;
    }
    .suggestion {
      background: #e7f3ff;
      border-left: 4px solid #0066cc;
      padding: 10px;
      margin-top: 10px;
      border-radius: 4px;
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>📄 ${fileName}</h1>
    <p><strong>Path:</strong> <code>${report.filePath}</code></p>
    <p><strong>Status:</strong> <span class="status ${report.valid ? 'valid' : 'invalid'}">${report.valid ? '✅ Valid' : '❌ Invalid'}</span></p>
    <p><strong>Date:</strong> ${report.timestamp.toLocaleString()}</p>
  </div>

  <div class="summary">
    <div class="summary-card">
      <h3>❌ Errors</h3>
      <p style="font-size: 2em; margin: 0; font-weight: bold; color: #dc3545;">${report.totalErrors}</p>
    </div>
    <div class="summary-card">
      <h3>⚠️ Warnings</h3>
      <p style="font-size: 2em; margin: 0; font-weight: bold; color: #ffc107;">${report.totalWarnings}</p>
    </div>
    <div class="summary-card">
      <h3>ℹ️ Infos</h3>
      <p style="font-size: 2em; margin: 0; font-weight: bold; color: #17a2b8;">${report.totalInfos}</p>
    </div>
  </div>

  ${this.renderErrors(report.errors, 'Errors', 'error-item')}
  ${this.renderErrors(report.warnings, 'Warnings', 'warning-item')}

</body>
</html>
    `.trim();
  }

  private renderErrors(errors: ValidationError[], title: string, className: string): string {
    if (errors.length === 0) return '';

    return `
  <div class="error-section">
    <h2>${title} (${errors.length})</h2>
    ${errors.map((error, idx) => `
      <div class="${className}">
        <strong>${idx + 1}. ${error.message}</strong>
        <div class="error-meta">
          ${error.component ? `<div>Component: <code>${error.component}${error.version ? ` (${error.version})` : ''}</code></div>` : ''}
          ${error.path ? `<div>Path: <code>${error.path}</code></div>` : ''}
          ${error.line ? `<div>Location: <code>${error.filePath}:${error.line}${error.column ? `:${error.column}` : ''}</code></div>` : ''}
        </div>
        ${error.suggestion ? `<div class="suggestion">💡 <strong>Suggestion:</strong> ${error.suggestion}</div>` : ''}
      </div>
    `).join('\n')}
  </div>
    `;
  }
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Извлечение компонента из сообщения ошибки
 */
export function extractComponentFromMessage(message: string): string | null {
  // "in ComponentName (v1):"
  const match1 = message.match(/in\s+(\w+)(?:\s+\(v\d+\))?/);
  if (match1) {
    return match1[1];
  }

  // "ComponentName is notReleased"
  const match2 = message.match(/^(\w+)\s+is\s+notReleased/);
  if (match2) {
    return match2[1];
  }

  return null;
}

/**
 * Извлечение поля ошибки из сообщения
 */
export function extractErrorField(message: string): string | null {
  // "Component XXX not found" -> поле type
  if (message.includes('Component') && message.includes('not found')) {
    return 'type';
  }

  // "Missing required field 'xxx'"
  const requiredMatch = message.match(/Missing required field ['"](\w+)['"]/i);
  if (requiredMatch) {
    return requiredMatch[1];
  }

  // "Invalid value for 'xxx'"
  const invalidMatch = message.match(/Invalid value for ['"](\w+)['"]/i);
  if (invalidMatch) {
    return invalidMatch[1];
  }

  // "Unexpected field 'xxx'"
  const unexpectedMatch = message.match(/Unexpected field(?:s)? (?:found )?['"]?(\w+)['"]?/i);
  if (unexpectedMatch) {
    return unexpectedMatch[1];
  }

  return null;
}

/**
 * Конвертация ошибок из разных форматов в ValidationError
 */
export class ErrorConverter {
  /**
   * Ruby validator format: "path: rule_name: error"
   */
  static fromRuby(text: string, filePath: string): ValidationError | null {
    const match = text.match(/^(.*?):\s*(\w+):\s*(.+)$/);
    if (!match) return null;

    const [, path, ruleName, error] = match;

    return {
      source: 'metaschema',
      severity: 'error',
      filePath,
      path,
      message: error,
      code: ruleName,
      component: extractComponentFromMessage(error),
    };
  }

  /**
   * MCP validator format (RequiredFieldError)
   */
  static fromMcpRequiredField(error: {
    path: string;
    component: string;
    version: string;
    missingFields: string[];
    severity: 'error' | 'warning';
    suggestion?: string;
  }, filePath: string): ValidationError {
    return {
      source: 'required-fields',
      severity: error.severity,
      filePath,
      path: error.path,
      component: error.component,
      version: error.version,
      message: `Missing required fields: ${error.missingFields.join(', ')}`,
      code: 'MISSING_REQUIRED_FIELD',
      suggestion: error.suggestion,
      metadata: { missingFields: error.missingFields },
    };
  }

  /**
   * MCP validator format (StateAwareValidationError)
   */
  static fromMcpStateAware(error: {
    field: string;
    pattern: string;
    message: string;
    severity: 'error' | 'warning';
    missingFields?: string[];
    unexpectedFields?: string[];
  }, filePath: string): ValidationError {
    return {
      source: 'stateaware',
      severity: error.severity,
      filePath,
      path: error.field,
      field: error.field,
      message: error.message,
      code: 'STATEAWARE_PATTERN_ERROR',
      metadata: {
        pattern: error.pattern,
        missingFields: error.missingFields,
        unexpectedFields: error.unexpectedFields,
      },
    };
  }
}

// ============================================================================
// EXPORTS
// ============================================================================

export {
  TextFormatter,
  JsonFormatter,
  MarkdownFormatter,
  HtmlFormatter,
  pathToJsonPointer,
  findLineNumber,
};
