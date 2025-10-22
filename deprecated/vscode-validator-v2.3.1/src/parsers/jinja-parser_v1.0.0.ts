/**
 * Jinja2/Java Template Parser
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
  ParseErrorType,
  ParseWarningType,
  SyntaxException,
  createSuccessResult,
  createErrorResult,
  createPosition,
  SourcePosition,
  SourceMapping,
  TokenType,
} from './types_v1.0.0.js';

// ============================================================================
// ТИПЫ
// ============================================================================

/**
 * Конфигурация Jinja парсера
 */
export interface JinjaParserConfig extends ParserConfig {
  allowRecursiveImports?: boolean;
  maxImportDepth?: number;
  basePath?: string;
  buildSourceMap?: boolean;
  variableDefaults?: Map<string, any>;
}

/**
 * Результат парсинга Jinja шаблона
 */
export interface JinjaParseResult {
  extractedJson: any;
  imports: ImportInfo[];
  sourceMap: SourceMapping[];
  stats: JinjaParsingStats;
}

/**
 * Информация об импорте
 */
export interface ImportInfo {
  path: string;
  resolvedPath: string;
  content: any;
  position: SourcePosition;
  description: string;
  isRecursive: boolean;
}

/**
 * Статистика парсинга
 */
export interface JinjaParsingStats {
  parseTimeMs: number;
  importCount: number;
  variableCount: number;
  controlCount: number;
  totalSizeBytes: number;
}

/**
 * Тип Jinja токена
 */
export type JinjaTokenType = 'import' | 'variable' | 'control' | 'comment' | 'raw';

/**
 * Jinja токен
 */
export interface JinjaToken {
  type: JinjaTokenType;
  value: string;
  position: SourcePosition;
  raw: string;
}

// ============================================================================
// JINJA PARSER
// ============================================================================

/**
 * Парсер Jinja2/Java шаблонов
 */
export class JinjaParser implements IParser<string, JinjaParseResult, JinjaParserConfig> {
  private config: JinjaParserConfig;
  private importDepth: number = 0;
  private importChain: string[] = [];

  constructor(config: JinjaParserConfig = {}) {
    this.config = {
      strict: true,
      maxErrors: 100,
      timeout: 30000,
      verbose: false,
      allowRecursiveImports: false,
      maxImportDepth: 10,
      basePath: process.cwd(),
      buildSourceMap: true,
      variableDefaults: new Map(),
      ...config,
    };
  }

  /**
   * Парсит Jinja шаблон из файла
   */
  async parse(
    filePath: string,
    options?: ParseOptions
  ): Promise<ParseResult<JinjaParseResult>> {
    const startTime = Date.now();
    const errors: ParseError[] = [];
    const warnings: ParseWarning[] = [];

    try {
      // Читаем файл
      const content = readFileSync(filePath, options?.encoding || 'utf-8');
      const fileSize = Buffer.byteLength(content, 'utf-8');

      // Парсим шаблон
      const result = this.parseTemplate(content, filePath, errors, warnings);

      if (errors.length > 0) {
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
      const content = readFileSync(filePath, 'utf-8');
      const errors: ParseError[] = [];
      const warnings: ParseWarning[] = [];
      this.parseTemplate(content, filePath, errors, warnings);
      return errors.length === 0;
    } catch {
      return false;
    }
  }

  getConfig(): Readonly<JinjaParserConfig> {
    return { ...this.config };
  }

  updateConfig(config: Partial<JinjaParserConfig>): void {
    this.config = { ...this.config, ...config };
  }

  // ============================================================================
  // TEMPLATE PARSING
  // ============================================================================

  /**
   * Парсит Jinja шаблон
   */
  private parseTemplate(
    content: string,
    filePath: string,
    errors: ParseError[],
    warnings: ParseWarning[]
  ): JinjaParseResult {
    const lines = content.split('\n');
    const processedLines: string[] = [];
    const imports: ImportInfo[] = [];
    const sourceMap: SourceMapping[] = [];

    let totalSizeBytes = Buffer.byteLength(content);
    let importCount = 0;
    let variableCount = 0;
    let controlCount = 0;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const lineNumber = i + 1;
      let processedLine = line;

      // 1. Обработка импортов
      const importResult = this.processImport(
        line,
        lineNumber,
        filePath,
        errors,
        warnings
      );
      if (importResult) {
        imports.push(importResult.import);
        totalSizeBytes += importResult.sizeBytes;
        importCount++;

        if (this.config.buildSourceMap) {
          sourceMap.push({
            originalLine: lineNumber,
            originalColumn: importResult.column,
            transformedLine: processedLines.length + 1,
            transformedColumn: 1,
            sourceFile: filePath,
            tokenType: 'import',
          });
        }

        processedLines.push(importResult.processedContent);
        continue;
      }

      // 2. Обработка переменных
      const variableResult = this.processVariables(
        processedLine,
        lineNumber,
        filePath,
        warnings
      );
      if (variableResult) {
        processedLine = variableResult.processedLine;
        variableCount += variableResult.variableCount;

        if (this.config.buildSourceMap && variableResult.positions.length > 0) {
          for (const pos of variableResult.positions) {
            sourceMap.push({
              originalLine: lineNumber,
              originalColumn: pos.column,
              transformedLine: processedLines.length + 1,
              transformedColumn: pos.column,
              sourceFile: filePath,
              tokenType: 'variable',
            });
          }
        }
      }

      // 3. Обработка управляющих конструкций
      const controlResult = this.processControl(processedLine, lineNumber, filePath);
      if (controlResult) {
        processedLine = controlResult.processedLine;
        controlCount++;

        if (this.config.buildSourceMap) {
          sourceMap.push({
            originalLine: lineNumber,
            originalColumn: controlResult.column,
            transformedLine: processedLines.length + 1,
            transformedColumn: 1,
            sourceFile: filePath,
            tokenType: 'control',
          });
        }
      }

      // 4. Удаление комментариев (не импортов)
      processedLine = processedLine.replace(/\/\/(?!\s*\[).*$/, '').trim();

      if (processedLine) {
        processedLines.push(processedLine);
      }
    }

    // Объединяем и парсим JSON
    const jsonText = processedLines.join('\n');
    let extractedJson: any = null;

    try {
      extractedJson = JSON.parse(jsonText);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      const positionMatch = errorMessage.match(/at position (\d+)/);
      const position = positionMatch ? parseInt(positionMatch[1], 10) : 0;

      const linesUpToError = jsonText.substring(0, position).split('\n');
      const errorLine = linesUpToError.length;
      const errorColumn = linesUpToError[linesUpToError.length - 1].length + 1;

      errors.push({
        type: ParseErrorType.INVALID_JSON,
        message: `JSON parse error after template processing: ${errorMessage}`,
        position: createPosition(errorLine, errorColumn, position),
        filePath,
      });
    }

    return {
      extractedJson,
      imports,
      sourceMap,
      stats: {
        parseTimeMs: 0, // Заполняется в parse()
        importCount,
        variableCount,
        controlCount,
        totalSizeBytes,
      },
    };
  }

  // ============================================================================
  // PROCESSORS
  // ============================================================================

  /**
   * Обработка импорта
   */
  private processImport(
    line: string,
    lineNumber: number,
    sourceFile: string,
    errors: ParseError[],
    warnings: ParseWarning[]
  ): { import: ImportInfo; processedContent: string; column: number; sizeBytes: number } | null {
    // Паттерн: // [Описание](file://path)
    const importMatch = line.match(/^\s*\/\/\s*\[(.*?)\]\((file:\/\/.*?)\)\s*$/);
    if (!importMatch) return null;

    const description = importMatch[1];
    const importPath = importMatch[2].replace('file://', '');
    const column = line.indexOf('//') + 1;

    // Проверка глубины импорта
    if (this.importDepth >= this.config.maxImportDepth!) {
      errors.push({
        type: ParseErrorType.IMPORT_ERROR,
        message: `Import depth limit exceeded (max: ${this.config.maxImportDepth})`,
        position: createPosition(lineNumber, column, 0),
        filePath: sourceFile,
      });
      return null;
    }

    // Проверка циклического импорта
    if (this.importChain.includes(importPath)) {
      errors.push({
        type: ParseErrorType.CIRCULAR_IMPORT,
        message: `Circular import detected: ${this.importChain.join(' -> ')} -> ${importPath}`,
        position: createPosition(lineNumber, column, 0),
        filePath: sourceFile,
      });
      return null;
    }

    // Резолвим путь
    const { resolve, isAbsolute } = require('path');
    const { existsSync } = require('fs');
    const { dirname } = require('path');

    const resolvedPath = isAbsolute(importPath)
      ? importPath
      : resolve(this.config.basePath || dirname(sourceFile), importPath);

    if (!existsSync(resolvedPath)) {
      errors.push({
        type: ParseErrorType.FILE_NOT_FOUND,
        message: `Import file not found: ${resolvedPath}`,
        position: createPosition(lineNumber, column, 0),
        filePath: sourceFile,
      });
      return null;
    }

    try {
      // Читаем импортированный файл
      const importedContent = readFileSync(resolvedPath, 'utf-8');
      const sizeBytes = Buffer.byteLength(importedContent);

      let importedJson: any;
      try {
        importedJson = JSON.parse(importedContent);
      } catch (e) {
        errors.push({
          type: ParseErrorType.INVALID_JSON,
          message: `Failed to parse imported file: ${resolvedPath}`,
          position: createPosition(lineNumber, column, 0),
          filePath: resolvedPath,
        });
        return null;
      }

      // Встраиваем импортированное содержимое
      const importedJsonStr = JSON.stringify(importedJson, null, 2);
      const indentMatch = line.match(/^(\s*)/);
      const indent = indentMatch ? indentMatch[1] : '';

      const indentedJson = importedJsonStr
        .split('\n')
        .map((l, idx) => (idx === 0 ? indent + l : indent + l))
        .join('\n');

      const importInfo: ImportInfo = {
        path: importMatch[2],
        resolvedPath,
        content: importedJson,
        position: createPosition(lineNumber, column, 0),
        description,
        isRecursive: false,
      };

      return {
        import: importInfo,
        processedContent: indentedJson + ',',
        column,
        sizeBytes,
      };
    } catch (e) {
      errors.push({
        type: ParseErrorType.IMPORT_ERROR,
        message: `Error processing import: ${(e as Error).message}`,
        position: createPosition(lineNumber, column, 0),
        filePath: sourceFile,
      });
      return null;
    }
  }

  /**
   * Обработка переменных
   */
  private processVariables(
    line: string,
    lineNumber: number,
    filePath: string,
    warnings: ParseWarning[]
  ): { processedLine: string; variableCount: number; positions: { column: number }[] } | null {
    const variableRegex = /\{\{\s*([^}]+?)\s*\}\}/g;
    let processedLine = line;
    let match;
    let variableCount = 0;
    const positions: { column: number }[] = [];

    while ((match = variableRegex.exec(line)) !== null) {
      const variableName = match[1].trim();
      const column = match.index + 1;

      positions.push({ column });
      variableCount++;

      // Получаем значение по умолчанию
      const defaultValue = this.config.variableDefaults?.get(variableName)
        || this.inferDefaultValue(variableName);

      processedLine = processedLine.replace(match[0], JSON.stringify(defaultValue));

      // Предупреждение о неразрешенной переменной
      if (!this.config.variableDefaults?.has(variableName)) {
        warnings.push({
          type: ParseWarningType.IMPLICIT_CONVERSION,
          message: `Variable '${variableName}' replaced with inferred default: ${JSON.stringify(defaultValue)}`,
          position: createPosition(lineNumber, column, 0),
          filePath,
        });
      }
    }

    return variableCount > 0 ? { processedLine, variableCount, positions } : null;
  }

  /**
   * Обработка управляющих конструкций
   */
  private processControl(
    line: string,
    lineNumber: number,
    filePath: string
  ): { processedLine: string; column: number } | null {
    const controlMatch = line.match(/\{%\s*(\w+)\s*(.*?)\s*%\}/);
    if (!controlMatch) return null;

    const column = line.indexOf('{%') + 1;
    const processedLine = line.replace(/\{%.*?%\}/g, '');

    return { processedLine, column };
  }

  /**
   * Выводит значение по умолчанию на основе имени переменной
   */
  private inferDefaultValue(variableName: string): any {
    const lowerName = variableName.toLowerCase();

    if (
      lowerName.startsWith('is') ||
      lowerName.startsWith('has') ||
      lowerName.includes('enabled') ||
      lowerName.includes('show')
    ) {
      return false;
    }

    if (
      lowerName.includes('count') ||
      lowerName.includes('size') ||
      lowerName.includes('length') ||
      lowerName.includes('index')
    ) {
      return 0;
    }

    if (
      lowerName.includes('list') ||
      lowerName.includes('items') ||
      lowerName.includes('array')
    ) {
      return [];
    }

    if (
      lowerName.includes('data') ||
      lowerName.includes('config') ||
      lowerName.includes('options')
    ) {
      return {};
    }

    if (lowerName.includes('null') || lowerName === 'none') {
      return null;
    }

    return '';
  }
}
