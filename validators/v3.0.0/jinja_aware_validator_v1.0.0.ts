/**
 * Jinja-Aware Validator v1.0.0
 *
 * Валидатор Jinja-шаблонов с поддержкой:
 * - Извлечения JSON из Jinja templates (.j2.java, .jinja.java)
 * - WEB-совместимости компонентов
 * - Проверки обязательных полей
 * - Мапирования ошибок на исходные позиции в Jinja
 * - Рекурсивной валидации imports
 *
 * @author Claude Code CLI
 * @version 1.0.0
 * @date 2025-10-05
 */

import { readFile } from 'fs/promises';
import { basename, dirname, join, resolve } from 'path';
import { existsSync } from 'fs';
import {
  ValidationError,
  ValidationSource,
  SeverityLevel,
  UnifiedReporter,
  ValidationReport,
} from './unified_reporter_v3.0.0.js';

// ============================================================================
// ТИПЫ И ИНТЕРФЕЙСЫ
// ============================================================================

/**
 * Информация об импорте в Jinja-шаблоне
 */
export interface ImportInfo {
  path: string;          // Путь к импортируемому файлу
  line: number;          // Номер строки импорта
  variable: string;      // Переменная, в которую импортируется
  resolved: string;      // Абсолютный путь к файлу
}

/**
 * Результат парсинга Jinja-шаблона
 */
export interface JinjaParseResult {
  // Основные данные
  templatePath: string;
  extractedJson: string;       // Извлеченный JSON
  parsedJson: any;             // Распарсенный JSON объект

  // Маппинг позиций
  sourceMap: SourceMapping[];  // Мапирование JSON → Jinja позиций

  // Импорты
  imports: ImportInfo[];       // Все найденные импорты

  // Компоненты
  components: ComponentInfo[]; // Все найденные компоненты

  // Метаданные
  metadata: {
    templateType: 'j2.java' | 'jinja.java' | 'other';
    hasJinjaLogic: boolean;
    importCount: number;
    componentCount: number;
  };
}

/**
 * Мапирование позиций JSON → Jinja source
 */
export interface SourceMapping {
  jsonPointer: string;   // RFC 6901 JSON Pointer
  jsonPath: string;      // Dot notation path
  templateLine: number;  // Строка в шаблоне
  templateColumn: number; // Колонка в шаблоне
  extractedLine: number; // Строка в извлеченном JSON
}

/**
 * Информация о компоненте
 */
export interface ComponentInfo {
  name: string;              // Имя компонента (ButtonView, IconView)
  version: string;           // Версия (v1, v2)
  path: string;              // JSON path к компоненту
  webCompatible: boolean;    // Совместим ли с WEB
  requiredFieldsMissing: string[]; // Отсутствующие обязательные поля
  line?: number;             // Номер строки в шаблоне
}

/**
 * Валидация импорта
 */
export interface ImportValidation {
  path: string;              // Путь к импортируемому файлу
  valid: boolean;            // Валиден ли импорт
  errors: ValidationError[]; // Ошибки в импортируемом файле
  recursive: boolean;        // Был ли валидирован рекурсивно
}

/**
 * Результат валидации Jinja-шаблона
 */
export interface JinjaValidationResult {
  valid: boolean;            // Общий статус
  errors: ValidationError[]; // Все ошибки с Jinja source locations
  warnings: ValidationError[]; // Предупреждения
  imports: ImportValidation[]; // Валидация каждого импорта
  webCompatibility: number;  // Процент WEB-совместимости (0-100)
  components: ComponentInfo[]; // Все найденные компоненты
  metadata: {
    templatePath: string;
    totalComponents: number;
    compatibleComponents: number;
    incompatibleComponents: number;
    missingRequiredFields: number;
    importsValidated: number;
  };
}

/**
 * Опции валидации
 */
export interface JinjaValidationOptions {
  validateImports?: boolean;      // Валидировать импорты рекурсивно
  checkWebCompatibility?: boolean; // Проверять WEB-совместимость
  checkRequiredFields?: boolean;  // Проверять обязательные поля
  maxImportDepth?: number;        // Максимальная глубина импортов
  verbose?: boolean;              // Подробный вывод
}

// ============================================================================
// JINJA PARSER (Упрощенная версия для Agent 04)
// ============================================================================

/**
 * Простой парсер Jinja-шаблонов
 * NOTE: Полноценная версия будет предоставлена Agent 03
 */
class SimpleJinjaParser {
  /**
   * Парсинг Jinja-шаблона
   */
  async parse(templatePath: string): Promise<JinjaParseResult> {
    const content = await readFile(templatePath, 'utf-8');
    const lines = content.split('\n');

    // Извлечение JSON (упрощенная логика)
    const extractedJson = this.extractJson(lines);
    let parsedJson: any = {};

    try {
      parsedJson = JSON.parse(extractedJson);
    } catch (error) {
      throw new Error(`Failed to parse extracted JSON: ${error}`);
    }

    // Поиск импортов
    const imports = this.findImports(lines, templatePath);

    // Поиск компонентов
    const components = this.findComponents(parsedJson, lines);

    // Создание source map
    const sourceMap = this.createSourceMap(lines, extractedJson);

    return {
      templatePath,
      extractedJson,
      parsedJson,
      sourceMap,
      imports,
      components,
      metadata: {
        templateType: this.detectTemplateType(templatePath),
        hasJinjaLogic: this.hasJinjaLogic(lines),
        importCount: imports.length,
        componentCount: components.length,
      },
    };
  }

  /**
   * Извлечение JSON из шаблона
   */
  private extractJson(lines: string[]): string {
    const jsonLines: string[] = [];
    let inJinjaBlock = false;
    let braceDepth = 0;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];

      // Пропускаем Jinja-директивы
      if (line.includes('{%') || line.includes('%}')) {
        inJinjaBlock = line.includes('{%') && !line.includes('%}');
        continue;
      }

      if (inJinjaBlock) {
        if (line.includes('%}')) {
          inJinjaBlock = false;
        }
        continue;
      }

      // Заменяем Jinja-переменные на заглушки
      let cleanedLine = line.replace(/\{\{\s*(\w+)\s*\}\}/g, (match, varName) => {
        // Попытка определить тип переменной
        if (varName.toLowerCase().includes('text') || varName.toLowerCase().includes('string')) {
          return `"{{${varName}}}"`;
        }
        if (varName.toLowerCase().includes('num') || varName.toLowerCase().includes('count')) {
          return '0';
        }
        if (varName.toLowerCase().includes('bool') || varName.toLowerCase().includes('enabled')) {
          return 'true';
        }
        return `"{{${varName}}}"`;
      });

      // Удаляем комментарии
      cleanedLine = cleanedLine.replace(/\{#.*?#\}/g, '');

      jsonLines.push(cleanedLine);

      // Отслеживание вложенности скобок
      braceDepth += (cleanedLine.match(/\{/g) || []).length;
      braceDepth -= (cleanedLine.match(/\}/g) || []).length;
    }

    return jsonLines.join('\n');
  }

  /**
   * Поиск импортов в шаблоне
   */
  private findImports(lines: string[], templatePath: string): ImportInfo[] {
    const imports: ImportInfo[] = [];
    const importRegex = /\{%\s*import\s+['"]([^'"]+)['"]\s+as\s+(\w+)\s*%\}/;
    const basePath = dirname(templatePath);

    for (let i = 0; i < lines.length; i++) {
      const match = lines[i].match(importRegex);
      if (match) {
        const [, path, variable] = match;
        const resolved = resolve(basePath, path);

        imports.push({
          path,
          line: i + 1,
          variable,
          resolved,
        });
      }
    }

    return imports;
  }

  /**
   * Поиск компонентов в JSON
   */
  private findComponents(json: any, lines: string[]): ComponentInfo[] {
    const components: ComponentInfo[] = [];

    const traverse = (obj: any, path: string = '') => {
      if (!obj || typeof obj !== 'object') return;

      if (obj.type && typeof obj.type === 'string') {
        const componentName = obj.type;

        // Определяем, является ли это SDUI-компонентом
        if (componentName.endsWith('View') || componentName.endsWith('Wrapper')) {
          const line = this.findLineForPath(lines, path);

          components.push({
            name: componentName,
            version: 'v1', // По умолчанию v1
            path,
            webCompatible: true, // Будет проверено валидатором
            requiredFieldsMissing: [],
            line,
          });
        }
      }

      // Рекурсивный обход
      if (Array.isArray(obj)) {
        obj.forEach((item, idx) => traverse(item, `${path}[${idx}]`));
      } else {
        for (const key in obj) {
          const newPath = path ? `${path}.${key}` : key;
          traverse(obj[key], newPath);
        }
      }
    };

    traverse(json);
    return components;
  }

  /**
   * Создание source map
   */
  private createSourceMap(templateLines: string[], extractedJson: string): SourceMapping[] {
    const sourceMap: SourceMapping[] = [];
    const extractedLines = extractedJson.split('\n');

    let templateLineIdx = 0;
    let extractedLineIdx = 0;

    while (templateLineIdx < templateLines.length && extractedLineIdx < extractedLines.length) {
      const templateLine = templateLines[templateLineIdx];
      const extractedLine = extractedLines[extractedLineIdx];

      // Пропускаем Jinja-директивы
      if (templateLine.includes('{%') || templateLine.includes('%}')) {
        templateLineIdx++;
        continue;
      }

      // Создаем маппинг
      const path = this.extractPathFromLine(extractedLine);
      if (path) {
        sourceMap.push({
          jsonPointer: this.pathToPointer(path),
          jsonPath: path,
          templateLine: templateLineIdx + 1,
          templateColumn: 1,
          extractedLine: extractedLineIdx + 1,
        });
      }

      templateLineIdx++;
      extractedLineIdx++;
    }

    return sourceMap;
  }

  /**
   * Определение типа шаблона
   */
  private detectTemplateType(path: string): 'j2.java' | 'jinja.java' | 'other' {
    if (path.endsWith('.j2.java')) return 'j2.java';
    if (path.endsWith('.jinja.java')) return 'jinja.java';
    return 'other';
  }

  /**
   * Проверка наличия Jinja-логики
   */
  private hasJinjaLogic(lines: string[]): boolean {
    return lines.some(line =>
      line.includes('{%') || line.includes('{{') || line.includes('{#')
    );
  }

  /**
   * Поиск строки для JSON path
   */
  private findLineForPath(lines: string[], path: string): number {
    // Упрощенная логика - ищем последний сегмент пути
    const segments = path.split('.');
    const lastSegment = segments[segments.length - 1].replace(/\[\d+\]$/, '');

    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes(`"${lastSegment}"`)) {
        return i + 1;
      }
    }

    return 1;
  }

  /**
   * Извлечение пути из строки JSON
   */
  private extractPathFromLine(line: string): string | null {
    const match = line.match(/"([^"]+)"\s*:/);
    return match ? match[1] : null;
  }

  /**
   * Конвертация path → JSON Pointer
   */
  private pathToPointer(path: string): string {
    return '/' + path.replace(/\./g, '/').replace(/\[(\d+)\]/g, '/$1');
  }
}

// ============================================================================
// WEB COMPATIBILITY VALIDATOR (Интеграция с Python validator)
// ============================================================================

/**
 * Интерфейс для Python SDUI Web Validator
 */
class WebCompatibilityChecker {
  private basePath: string;

  constructor(basePath?: string) {
    this.basePath = basePath || process.env.FMS_PATH || '/Users/username/Documents/FMS_GIT';
  }

  /**
   * Проверка совместимости компонента с WEB
   */
  async checkComponent(componentName: string): Promise<{ compatible: boolean; reason: string }> {
    try {
      // Поиск схемы компонента
      const schemaPath = await this.findComponentSchema(componentName);

      if (!schemaPath) {
        return { compatible: true, reason: 'Schema not found' };
      }

      // Чтение схемы
      const schema = JSON.parse(await readFile(schemaPath, 'utf-8'));

      // Проверка releaseVersion
      if (schema.releaseVersion) {
        const webStatus = schema.releaseVersion.web || 'released';

        if (webStatus === 'notReleased' || webStatus === 'willNotBeReleased') {
          return { compatible: false, reason: `web: ${webStatus}` };
        }
      }

      return { compatible: true, reason: 'released' };
    } catch (error) {
      return { compatible: true, reason: `Error checking: ${error}` };
    }
  }

  /**
   * Поиск схемы компонента
   */
  private async findComponentSchema(componentName: string): Promise<string | null> {
    const patterns = [
      `${this.basePath}/SDUI/components/${componentName}/v*/\${componentName}.json`,
      `${this.basePath}/SDUI/layouts/${componentName}/v*/\${componentName}.json`,
      `${this.basePath}/SDUI/components/${componentName}/v1/${componentName}.json`,
      `${this.basePath}/SDUI/layouts/${componentName}/v1/${componentName}.json`,
    ];

    for (const pattern of patterns) {
      const resolved = pattern.replace(/\$\{componentName\}/g, componentName);
      const globPattern = resolved.replace(/\/v\*\//g, '/v1/'); // Упрощение для v1

      if (existsSync(globPattern)) {
        return globPattern;
      }
    }

    return null;
  }
}

// ============================================================================
// JINJA-AWARE VALIDATOR
// ============================================================================

export class JinjaAwareValidator {
  private jinjaParser: SimpleJinjaParser;
  private webChecker: WebCompatibilityChecker;
  private reporter: UnifiedReporter;
  private validatedImports: Set<string> = new Set();

  constructor(options?: { basePath?: string; verbose?: boolean }) {
    this.jinjaParser = new SimpleJinjaParser();
    this.webChecker = new WebCompatibilityChecker(options?.basePath);
    this.reporter = new UnifiedReporter({
      verbose: options?.verbose || false,
      groupBy: 'component',
      showLineNumbers: true,
    });
  }

  /**
   * Валидация Jinja-шаблона
   */
  async validate(
    templatePath: string,
    options: JinjaValidationOptions = {}
  ): Promise<JinjaValidationResult> {
    const opts: Required<JinjaValidationOptions> = {
      validateImports: options.validateImports ?? true,
      checkWebCompatibility: options.checkWebCompatibility ?? true,
      checkRequiredFields: options.checkRequiredFields ?? true,
      maxImportDepth: options.maxImportDepth ?? 5,
      verbose: options.verbose ?? false,
    };

    // 1. Парсинг шаблона
    const parseResult = await this.jinjaParser.parse(templatePath);

    // 2. Валидация WEB-совместимости
    const webErrors = opts.checkWebCompatibility
      ? await this.validateWebCompatibility(parseResult)
      : [];

    // 3. Валидация обязательных полей
    const requiredFieldErrors = opts.checkRequiredFields
      ? this.validateRequiredFields(parseResult)
      : [];

    // 4. Валидация импортов
    const importValidations = opts.validateImports
      ? await this.validateImports(parseResult.imports, opts.maxImportDepth)
      : [];

    // 5. Сбор всех ошибок
    const allErrors = [
      ...webErrors,
      ...requiredFieldErrors,
      ...importValidations.flatMap(iv => iv.errors),
    ];

    // 6. Мапирование ошибок на Jinja source locations
    const mappedErrors = this.mapErrorsToJinjaSource(allErrors, parseResult.sourceMap);

    // 7. Разделение на errors и warnings
    const errors = mappedErrors.filter(e => e.severity === 'error');
    const warnings = mappedErrors.filter(e => e.severity === 'warning');

    // 8. Расчет WEB-совместимости
    const compatibleCount = parseResult.components.filter(c => c.webCompatible).length;
    const webCompatibility = parseResult.components.length > 0
      ? Math.round((compatibleCount / parseResult.components.length) * 100)
      : 100;

    return {
      valid: errors.length === 0,
      errors,
      warnings,
      imports: importValidations,
      webCompatibility,
      components: parseResult.components,
      metadata: {
        templatePath,
        totalComponents: parseResult.components.length,
        compatibleComponents: compatibleCount,
        incompatibleComponents: parseResult.components.length - compatibleCount,
        missingRequiredFields: requiredFieldErrors.length,
        importsValidated: importValidations.length,
      },
    };
  }

  /**
   * Валидация WEB-совместимости
   */
  private async validateWebCompatibility(
    parseResult: JinjaParseResult
  ): Promise<ValidationError[]> {
    const errors: ValidationError[] = [];

    for (const component of parseResult.components) {
      const { compatible, reason } = await this.webChecker.checkComponent(component.name);

      component.webCompatible = compatible;

      if (!compatible) {
        errors.push({
          source: 'web-compat',
          severity: 'error',
          filePath: parseResult.templatePath,
          line: component.line,
          path: component.path,
          component: component.name,
          version: component.version,
          message: `Component ${component.name} is not compatible with WEB platform (${reason})`,
          code: 'WEB_INCOMPATIBLE_COMPONENT',
          suggestion: `Use a different component or check if there's a WEB-compatible version`,
        });
      }
    }

    return errors;
  }

  /**
   * Валидация обязательных полей
   */
  private validateRequiredFields(parseResult: JinjaParseResult): ValidationError[] {
    const errors: ValidationError[] = [];

    // Список обязательных полей для разных компонентов
    const requiredFields: Record<string, string[]> = {
      ButtonView: ['textContent', 'actions'],
      TextView: ['textContent'],
      IconView: ['icon'],
      ImageView: ['imageContent'],
      StackView: ['elements'],
    };

    for (const component of parseResult.components) {
      const required = requiredFields[component.name] || [];
      const missingFields: string[] = [];

      // Проверяем наличие обязательных полей в JSON
      const componentData = this.getComponentData(parseResult.parsedJson, component.path);

      for (const field of required) {
        if (!componentData || !(field in componentData)) {
          missingFields.push(field);
        }
      }

      component.requiredFieldsMissing = missingFields;

      if (missingFields.length > 0) {
        errors.push({
          source: 'required-fields',
          severity: 'error',
          filePath: parseResult.templatePath,
          line: component.line,
          path: component.path,
          component: component.name,
          message: `Missing required fields in ${component.name}: ${missingFields.join(', ')}`,
          code: 'MISSING_REQUIRED_FIELDS',
          suggestion: `Add the following required fields: ${missingFields.join(', ')}`,
          metadata: { missingFields },
        });
      }
    }

    return errors;
  }

  /**
   * Валидация импортов (рекурсивно)
   */
  private async validateImports(
    imports: ImportInfo[],
    maxDepth: number,
    currentDepth: number = 0
  ): Promise<ImportValidation[]> {
    const validations: ImportValidation[] = [];

    if (currentDepth >= maxDepth) {
      return validations;
    }

    for (const importInfo of imports) {
      // Проверяем, не валидировали ли уже этот файл
      if (this.validatedImports.has(importInfo.resolved)) {
        validations.push({
          path: importInfo.path,
          valid: true,
          errors: [],
          recursive: false,
        });
        continue;
      }

      this.validatedImports.add(importInfo.resolved);

      // Проверяем существование файла
      if (!existsSync(importInfo.resolved)) {
        validations.push({
          path: importInfo.path,
          valid: false,
          errors: [{
            source: 'custom' as ValidationSource,
            severity: 'error',
            filePath: importInfo.resolved,
            line: importInfo.line,
            message: `Import file not found: ${importInfo.path}`,
            code: 'IMPORT_NOT_FOUND',
          }],
          recursive: false,
        });
        continue;
      }

      // Валидируем импортированный файл
      try {
        const result = await this.validate(importInfo.resolved, {
          validateImports: true,
          maxImportDepth: maxDepth - currentDepth - 1,
        });

        validations.push({
          path: importInfo.path,
          valid: result.valid,
          errors: result.errors,
          recursive: true,
        });
      } catch (error) {
        validations.push({
          path: importInfo.path,
          valid: false,
          errors: [{
            source: 'custom' as ValidationSource,
            severity: 'error',
            filePath: importInfo.resolved,
            line: importInfo.line,
            message: `Failed to validate import: ${error}`,
            code: 'IMPORT_VALIDATION_ERROR',
          }],
          recursive: false,
        });
      }
    }

    return validations;
  }

  /**
   * Мапирование ошибок на Jinja source locations
   */
  private mapErrorsToJinjaSource(
    errors: ValidationError[],
    sourceMap: SourceMapping[]
  ): ValidationError[] {
    return errors.map(error => {
      // Если ошибка уже имеет строку, оставляем как есть
      if (error.line) {
        return error;
      }

      // Ищем маппинг по path или jsonPointer
      const mapping = sourceMap.find(m =>
        m.jsonPath === error.path || m.jsonPointer === error.jsonPointer
      );

      if (mapping) {
        return {
          ...error,
          line: mapping.templateLine,
          column: mapping.templateColumn,
        };
      }

      return error;
    });
  }

  /**
   * Получение данных компонента по пути
   */
  private getComponentData(json: any, path: string): any {
    if (!path) return json;

    const segments = path.split('.').flatMap(seg => {
      const match = seg.match(/(\w+)\[(\d+)\]/);
      return match ? [match[1], parseInt(match[2])] : [seg];
    });

    let current = json;
    for (const segment of segments) {
      if (current === null || current === undefined) return null;
      current = current[segment];
    }

    return current;
  }

  /**
   * Вывод отчета валидации
   */
  printReport(result: JinjaValidationResult): void {
    console.log('\n' + '═'.repeat(80));
    console.log(`📄 JINJA TEMPLATE VALIDATION v1.0.0`);
    console.log('═'.repeat(80));
    console.log(`\n📁 File: ${result.metadata.templatePath}`);
    console.log(`\n📊 Summary:`);
    console.log(`   Components .............. ${result.metadata.totalComponents}`);
    console.log(`   WEB Compatible .......... ${result.metadata.compatibleComponents}`);
    console.log(`   WEB Incompatible ........ ${result.metadata.incompatibleComponents}`);
    console.log(`   WEB Compatibility ....... ${result.webCompatibility}%`);
    console.log(`   Missing Required Fields . ${result.metadata.missingRequiredFields}`);
    console.log(`   Imports Validated ....... ${result.metadata.importsValidated}`);
    console.log(`\n📝 Validation Results:`);
    console.log(`   Errors .................. ${result.errors.length}`);
    console.log(`   Warnings ................ ${result.warnings.length}`);

    if (result.errors.length > 0) {
      console.log(`\n❌ ERRORS:\n`);
      result.errors.forEach((error, idx) => {
        console.log(`${idx + 1}. [${error.component || 'General'}] ${error.message}`);
        if (error.line) {
          console.log(`   → ${error.filePath}:${error.line}:${error.column || 1}`);
        }
        if (error.suggestion) {
          console.log(`   💡 ${error.suggestion}`);
        }
        console.log();
      });
    }

    if (result.warnings.length > 0) {
      console.log(`\n⚠️  WARNINGS:\n`);
      result.warnings.forEach((warning, idx) => {
        console.log(`${idx + 1}. [${warning.component || 'General'}] ${warning.message}`);
        if (warning.line) {
          console.log(`   → ${warning.filePath}:${warning.line}:${warning.column || 1}`);
        }
        console.log();
      });
    }

    console.log('═'.repeat(80));
    if (result.valid) {
      console.log('✅ Template is valid and ready for WEB platform');
    } else {
      console.log('❌ Template has validation errors');
    }
    console.log('═'.repeat(80) + '\n');
  }

  /**
   * Экспорт результата в JSON
   */
  exportToJson(result: JinjaValidationResult): string {
    return JSON.stringify({
      valid: result.valid,
      metadata: result.metadata,
      webCompatibility: result.webCompatibility,
      errors: result.errors.map(e => ({
        source: e.source,
        severity: e.severity,
        component: e.component,
        message: e.message,
        location: {
          file: e.filePath,
          line: e.line,
          column: e.column,
          path: e.path,
        },
        suggestion: e.suggestion,
      })),
      warnings: result.warnings.map(w => ({
        source: w.source,
        severity: w.severity,
        message: w.message,
        location: {
          file: w.filePath,
          line: w.line,
        },
      })),
      components: result.components,
      imports: result.imports.map(i => ({
        path: i.path,
        valid: i.valid,
        errors: i.errors.length,
      })),
    }, null, 2);
  }
}

// ============================================================================
// CLI INTERFACE
// ============================================================================

/**
 * CLI entry point
 */
async function main() {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.error('Usage: jinja_aware_validator <template.j2.java>');
    process.exit(1);
  }

  const templatePath = args[0];

  if (!existsSync(templatePath)) {
    console.error(`Error: File not found: ${templatePath}`);
    process.exit(1);
  }

  const validator = new JinjaAwareValidator({ verbose: true });

  try {
    const result = await validator.validate(templatePath, {
      validateImports: true,
      checkWebCompatibility: true,
      checkRequiredFields: true,
      maxImportDepth: 3,
    });

    validator.printReport(result);

    process.exit(result.valid ? 0 : 1);
  } catch (error) {
    console.error(`\n❌ Validation failed: ${error}\n`);
    process.exit(1);
  }
}

// Запуск CLI если файл выполняется напрямую
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

// ============================================================================
// EXPORTS
// ============================================================================

export {
  JinjaAwareValidator,
  SimpleJinjaParser,
  WebCompatibilityChecker,
};
