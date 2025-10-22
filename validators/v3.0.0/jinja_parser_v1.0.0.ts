/**
 * Jinja2/Java Template Parser v1.0.0
 * Parses .j2.java and jinja.java files, extracts JSON, resolves imports
 *
 * @version 1.0.0
 * @author Claude Code (Agent 03)
 * @date 2025-10-05
 */

import * as fs from 'fs';
import * as path from 'path';

// ============================================================================
// ТИПЫ И ИНТЕРФЕЙСЫ
// ============================================================================

/** Результат парсинга Jinja шаблона */
export interface JinjaParseResult {
  /** Извлеченный чистый JSON объект */
  extractedJson: any;
  /** Все разрешенные импорты */
  imports: ImportInfo[];
  /** Маппинг позиций Jinja → JSON */
  sourceMap: SourceMapping[];
  /** Ошибки парсинга (если есть) */
  errors: ParseError[];
  /** Статистика парсинга */
  stats: ParsingStats;
}

/** Информация об импорте */
export interface ImportInfo {
  /** Путь импорта из // [...](path) */
  path: string;
  /** Разрешенный абсолютный путь */
  resolvedPath: string;
  /** Спарсенное содержимое */
  content: any;
  /** Номер строки в родительском файле */
  line: number;
  /** Колонка в родительском файле */
  column: number;
  /** Описание импорта из комментария */
  description: string;
  /** Является ли рекурсивным импортом */
  isRecursive: boolean;
}

/** Маппинг позиций источника */
export interface SourceMapping {
  /** Номер строки в Jinja файле */
  jinjaLine: number;
  /** Колонка в Jinja файле */
  jinjaColumn: number;
  /** JSON Pointer (RFC 6901) */
  jsonPointer: string;
  /** Исходный файл (для импортов) */
  sourceFile: string;
  /** Тип токена */
  tokenType: 'import' | 'variable' | 'control' | 'json';
}

/** Ошибка парсинга */
export interface ParseError {
  /** Тип ошибки */
  type: 'circular_import' | 'file_not_found' | 'parse_error' | 'invalid_syntax';
  /** Сообщение об ошибке */
  message: string;
  /** Номер строки */
  line: number;
  /** Колонка */
  column: number;
  /** Путь к файлу */
  filePath: string;
}

/** Статистика парсинга */
export interface ParsingStats {
  /** Время парсинга в мс */
  parseTimeMs: number;
  /** Количество импортов */
  importCount: number;
  /** Количество Jinja переменных */
  variableCount: number;
  /** Количество управляющих конструкций */
  controlCount: number;
  /** Общий размер в байтах */
  totalSizeBytes: number;
}

/** Опции парсера */
export interface JinjaParserOptions {
  /** Разрешать рекурсивные импорты */
  allowRecursiveImports?: boolean;
  /** Максимальная глубина импортов */
  maxImportDepth?: number;
  /** Базовый путь для относительных импортов */
  basePath?: string;
  /** Значения по умолчанию для Jinja переменных */
  defaultValues?: Record<string, any>;
  /** Строить source map */
  buildSourceMap?: boolean;
}

// ============================================================================
// ОСНОВНОЙ КЛАСС ПАРСЕРА
// ============================================================================

export class JinjaParser {
  private options: Required<JinjaParserOptions>;
  private importDepth: number = 0;
  private importChain: Set<string> = new Set();
  private errors: ParseError[] = [];
  private imports: ImportInfo[] = [];
  private sourceMap: SourceMapping[] = [];
  private stats: ParsingStats = {
    parseTimeMs: 0,
    importCount: 0,
    variableCount: 0,
    controlCount: 0,
    totalSizeBytes: 0
  };

  constructor(options: JinjaParserOptions = {}) {
    this.options = {
      allowRecursiveImports: false,
      maxImportDepth: 10,
      basePath: process.cwd(),
      defaultValues: {},
      buildSourceMap: true,
      ...options
    };
  }

  /**
   * Парсит Jinja шаблон и извлекает JSON
   * @param templatePath - Путь к .j2.java или jinja.java файлу
   * @param options - Опции парсера
   */
  parse(templatePath: string, options?: JinjaParserOptions): JinjaParseResult {
    const startTime = Date.now();

    // Сброс состояния
    this.errors = [];
    this.imports = [];
    this.sourceMap = [];
    this.importDepth = 0;
    this.importChain.clear();
    this.stats = {
      parseTimeMs: 0,
      importCount: 0,
      variableCount: 0,
      controlCount: 0,
      totalSizeBytes: 0
    };

    if (options) {
      this.options = { ...this.options, ...options };
    }

    // Проверка существования файла
    if (!fs.existsSync(templatePath)) {
      this.errors.push({
        type: 'file_not_found',
        message: `Файл не найден: ${templatePath}`,
        line: 0,
        column: 0,
        filePath: templatePath
      });
      return this.buildResult({}, startTime);
    }

    // Чтение файла
    const templateContent = fs.readFileSync(templatePath, 'utf-8');
    this.stats.totalSizeBytes += Buffer.byteLength(templateContent);

    // Добавление в цепочку импортов
    const absolutePath = path.resolve(templatePath);
    this.importChain.add(absolutePath);

    // Извлечение JSON
    const extractedJson = this.extractJson(templateContent, templatePath);

    this.stats.parseTimeMs = Date.now() - startTime;

    return this.buildResult(extractedJson, startTime);
  }

  /**
   * Разрешает импорт рекурсивно
   * @param importDirective - Путь импорта из шаблона
   * @param basePath - Базовый путь для относительного разрешения
   * @param line - Номер строки
   * @param column - Колонка
   * @param description - Описание импорта
   */
  private resolveImport(
    importDirective: string,
    basePath: string,
    line: number,
    column: number,
    description: string
  ): ImportInfo | null {
    // Извлечение пути из file:// URI
    let importPath = importDirective;
    if (importPath.startsWith('file://')) {
      importPath = importPath.replace('file://', '');
    }

    // Разрешение относительного пути
    const resolvedPath = path.isAbsolute(importPath)
      ? importPath
      : path.resolve(basePath, importPath);

    // Проверка циклических импортов
    if (this.importChain.has(resolvedPath)) {
      this.errors.push({
        type: 'circular_import',
        message: `Обнаружен циклический импорт: ${resolvedPath}`,
        line,
        column,
        filePath: basePath
      });
      return null;
    }

    // Проверка максимальной глубины
    if (this.importDepth >= this.options.maxImportDepth) {
      this.errors.push({
        type: 'parse_error',
        message: `Превышена максимальная глубина импортов: ${this.options.maxImportDepth}`,
        line,
        column,
        filePath: basePath
      });
      return null;
    }

    // Проверка существования файла
    if (!fs.existsSync(resolvedPath)) {
      this.errors.push({
        type: 'file_not_found',
        message: `Импортируемый файл не найден: ${resolvedPath}`,
        line,
        column,
        filePath: basePath
      });
      return null;
    }

    // Чтение импортируемого файла
    const content = fs.readFileSync(resolvedPath, 'utf-8');
    this.stats.totalSizeBytes += Buffer.byteLength(content);

    // Парсинг содержимого
    this.importDepth++;
    this.importChain.add(resolvedPath);

    const parsedContent = this.parseJsonContent(content, resolvedPath);

    this.importDepth--;
    this.importChain.delete(resolvedPath);

    const importInfo: ImportInfo = {
      path: importDirective,
      resolvedPath,
      content: parsedContent,
      line,
      column,
      description,
      isRecursive: this.importDepth > 0
    };

    this.imports.push(importInfo);
    this.stats.importCount++;

    return importInfo;
  }

  /**
   * Извлекает JSON из Jinja шаблона
   * @param templateContent - Сырое содержимое шаблона
   * @param filePath - Путь к файлу для отчетов об ошибках
   */
  private extractJson(templateContent: string, filePath: string): any {
    const lines = templateContent.split('\n');
    const processedLines: string[] = [];
    const basePath = path.dirname(filePath);

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const lineNumber = i + 1;

      // Обработка комментариев с импортами: // [Описание](file://path)
      const importMatch = line.match(/^\s*\/\/\s*\[(.*?)\]\((file:\/\/.*?)\)\s*$/);
      if (importMatch) {
        const description = importMatch[1];
        const importPath = importMatch[2];
        const column = line.indexOf('//') + 1;

        if (this.options.buildSourceMap) {
          this.sourceMap.push({
            jinjaLine: lineNumber,
            jinjaColumn: column,
            jsonPointer: '',
            sourceFile: filePath,
            tokenType: 'import'
          });
        }

        const importInfo = this.resolveImport(
          importPath,
          basePath,
          lineNumber,
          column,
          description
        );

        if (importInfo && importInfo.content) {
          // Встраивание импортированного содержимого
          const importedJson = JSON.stringify(importInfo.content, null, 2);
          const indentMatch = line.match(/^(\s*)/);
          const indent = indentMatch ? indentMatch[1] : '';

          // Добавляем импортированный JSON с правильным отступом
          const indentedJson = importedJson
            .split('\n')
            .map((l, idx) => idx === 0 ? indent + l : indent + l)
            .join('\n');

          processedLines.push(indentedJson + (i < lines.length - 1 ? ',' : ''));
        }
        continue;
      }

      // Обработка Jinja переменных: {{ variable }}
      let processedLine = line;
      const variableRegex = /\{\{\s*([^}]+?)\s*\}\}/g;
      let match;

      while ((match = variableRegex.exec(line)) !== null) {
        const variableName = match[1].trim();
        const column = match.index + 1;

        if (this.options.buildSourceMap) {
          this.sourceMap.push({
            jinjaLine: lineNumber,
            jinjaColumn: column,
            jsonPointer: '',
            sourceFile: filePath,
            tokenType: 'variable'
          });
        }

        this.stats.variableCount++;

        // Замена переменной на значение по умолчанию
        const defaultValue = this.getDefaultValue(variableName);
        processedLine = processedLine.replace(match[0], JSON.stringify(defaultValue));
      }

      // Обработка управляющих конструкций Jinja: {% if %}, {% for %}, etc.
      const controlMatch = processedLine.match(/\{%\s*(\w+)\s*(.*?)\s*%\}/);
      if (controlMatch) {
        const controlType = controlMatch[1];
        const column = processedLine.indexOf('{%') + 1;

        if (this.options.buildSourceMap) {
          this.sourceMap.push({
            jinjaLine: lineNumber,
            jinjaColumn: column,
            jsonPointer: '',
            sourceFile: filePath,
            tokenType: 'control'
          });
        }

        this.stats.controlCount++;

        // Для простоты, игнорируем управляющие конструкции
        // В реальной реализации нужна полноценная логика
        processedLine = processedLine.replace(/\{%.*?%\}/g, '');
      }

      // Удаление обычных комментариев (не импортов)
      processedLine = processedLine.replace(/\/\/(?!\s*\[).*$/, '').trim();

      if (processedLine) {
        processedLines.push(processedLine);
      }
    }

    // Объединение строк и парсинг JSON
    const jsonText = processedLines.join('\n');
    return this.parseJsonContent(jsonText, filePath);
  }

  /**
   * Парсит JSON содержимое с обработкой ошибок
   * @param jsonText - Текст JSON
   * @param filePath - Путь к файлу для отчетов
   */
  private parseJsonContent(jsonText: string, filePath: string): any {
    try {
      return JSON.parse(jsonText);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);

      // Извлечение номера строки из ошибки JSON.parse
      const lineMatch = errorMessage.match(/at position (\d+)/);
      const position = lineMatch ? parseInt(lineMatch[1], 10) : 0;

      // Подсчет строки и колонки из позиции
      const lines = jsonText.substring(0, position).split('\n');
      const line = lines.length;
      const column = lines[lines.length - 1].length + 1;

      this.errors.push({
        type: 'parse_error',
        message: `Ошибка парсинга JSON: ${errorMessage}`,
        line,
        column,
        filePath
      });

      return null;
    }
  }

  /**
   * Получает значение по умолчанию для Jinja переменной
   * @param variableName - Имя переменной
   */
  private getDefaultValue(variableName: string): any {
    // Проверка в предоставленных значениях
    if (variableName in this.options.defaultValues) {
      return this.options.defaultValues[variableName];
    }

    // Обработка вложенных переменных: obj.field
    const parts = variableName.split('.');
    let current = this.options.defaultValues;

    for (const part of parts) {
      if (current && typeof current === 'object' && part in current) {
        current = current[part];
      } else {
        // Значение по умолчанию на основе имени
        return this.inferDefaultValue(variableName);
      }
    }

    return current;
  }

  /**
   * Выводит значение по умолчанию на основе имени переменной
   * @param variableName - Имя переменной
   */
  private inferDefaultValue(variableName: string): any {
    const lowerName = variableName.toLowerCase();

    // Булевы значения
    if (lowerName.startsWith('is') || lowerName.startsWith('has') ||
        lowerName.includes('enabled') || lowerName.includes('show')) {
      return false;
    }

    // Числовые значения
    if (lowerName.includes('count') || lowerName.includes('size') ||
        lowerName.includes('length') || lowerName.includes('index')) {
      return 0;
    }

    // Массивы
    if (lowerName.includes('list') || lowerName.includes('items') ||
        lowerName.includes('array')) {
      return [];
    }

    // Объекты
    if (lowerName.includes('data') || lowerName.includes('config') ||
        lowerName.includes('options')) {
      return {};
    }

    // Null значения
    if (lowerName.includes('null') || lowerName === 'none') {
      return null;
    }

    // Строки по умолчанию
    return '';
  }

  /**
   * Строит финальный результат парсинга
   * @param extractedJson - Извлеченный JSON
   * @param startTime - Время начала парсинга
   */
  private buildResult(extractedJson: any, startTime: number): JinjaParseResult {
    this.stats.parseTimeMs = Date.now() - startTime;

    return {
      extractedJson,
      imports: this.imports,
      sourceMap: this.sourceMap,
      errors: this.errors,
      stats: this.stats
    };
  }

  /**
   * Построение source map для маппинга ошибок
   * @param templateContent - Сырое содержимое шаблона
   * @param extractedJson - Извлеченный JSON объект
   */
  private buildSourceMap(templateContent: string, extractedJson: any): SourceMapping[] {
    // Эта функция должна строить детальный source map
    // Для простоты возвращаем уже собранную карту из extractJson
    return this.sourceMap;
  }
}

// ============================================================================
// УТИЛИТЫ
// ============================================================================

/**
 * Быстрая проверка, является ли файл Jinja шаблоном
 * @param filePath - Путь к файлу
 */
export function isJinjaTemplate(filePath: string): boolean {
  return filePath.endsWith('.j2.java') || filePath.endsWith('.jinja.java');
}

/**
 * Нормализация пути импорта
 * @param importPath - Путь из директивы импорта
 */
export function normalizeImportPath(importPath: string): string {
  if (importPath.startsWith('file://')) {
    return importPath.replace('file://', '');
  }
  return importPath;
}

/**
 * Экспорт результата парсинга в JSON
 * @param result - Результат парсинга
 * @param outputPath - Путь для сохранения
 */
export function exportParseResult(result: JinjaParseResult, outputPath: string): void {
  const output = {
    json: result.extractedJson,
    imports: result.imports.map(imp => ({
      path: imp.path,
      resolvedPath: imp.resolvedPath,
      description: imp.description,
      line: imp.line
    })),
    errors: result.errors,
    stats: result.stats
  };

  fs.writeFileSync(outputPath, JSON.stringify(output, null, 2), 'utf-8');
}

// ============================================================================
// ЭКСПОРТ
// ============================================================================

export default JinjaParser;
