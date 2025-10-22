/**
 * SDUI Validator Module
 *
 * Главный класс валидатора с dependency injection и расширяемой архитектурой.
 * Обеспечивает комплексную валидацию SDUI контрактов с детальной диагностикой.
 *
 * @module core/validator
 * @version 2.3.1
 */

import type { ConfigManager } from './config';
import type { FileReader, FileReadResult } from './file-reader';
import type { PositionMap, PositionMapBuilder } from './position-map';

/**
 * Тип валидационной ошибки
 */
export enum ErrorType {
  PARSE_ERROR = 'parse_error',
  SCHEMA_ERROR = 'schema_error',
  COMPONENT_NOT_FOUND = 'component_not_found',
  MISSING_REQUIRED_FIELD = 'missing_required_field',
  INVALID_VALUE = 'invalid_value',
  UNEXPECTED_FIELD = 'unexpected_field',
  TYPE_MISMATCH = 'type_mismatch',
  WEB_INCOMPATIBLE = 'web_incompatible',
  VERSION_ERROR = 'version_error',
  STATE_AWARE_ERROR = 'state_aware_error',
}

/**
 * Уровень серьезности проблемы
 */
export enum Severity {
  ERROR = 'error',
  WARNING = 'warning',
  INFO = 'info',
}

/**
 * Информация о валидационной проблеме
 */
export interface ValidationIssue {
  /** Тип ошибки */
  readonly type: ErrorType;
  /** Уровень серьезности */
  readonly severity: Severity;
  /** Человекочитаемое сообщение */
  readonly message: string;
  /** JSON Pointer на проблемное место */
  readonly pointer: string;
  /** Property path (lodash-style) */
  readonly path: string;
  /** Номер строки в файле */
  readonly line: number;
  /** Номер колонки в файле */
  readonly column: number;
  /** Имя компонента (если применимо) */
  readonly component?: string;
  /** Поле с ошибкой (если применимо) */
  readonly field?: string;
  /** Исходный файл (для модульных контрактов) */
  readonly sourceFile?: string;
  /** Дополнительный контекст */
  readonly context?: Record<string, any>;
}

/**
 * Информация о data binding
 */
export interface DataBindingInfo {
  /** Тип binding */
  readonly type: 'state' | 'data' | 'computed';
  /** Путь к binding */
  readonly path: string;
  /** Выражение binding */
  readonly expression: string;
}

/**
 * Статистика data bindings
 */
export interface DataBindingStats {
  /** Есть ли bindings */
  readonly hasBindings: boolean;
  /** Общее количество bindings */
  readonly totalBindings: number;
  /** Количество по типам */
  readonly byType: {
    readonly state: number;
    readonly data: number;
    readonly computed: number;
  };
  /** Список всех bindings */
  readonly bindings: readonly DataBindingInfo[];
}

/**
 * Статистика версий компонентов
 */
export interface ComponentVersionStats {
  /** Общее количество компонентов */
  readonly totalComponents: number;
  /** Количество по версиям */
  readonly byVersion: Readonly<Record<string, number>>;
  /** Список уникальных типов компонентов */
  readonly uniqueTypes: readonly string[];
}

/**
 * Результат валидации
 */
export interface ValidationReport {
  /** Валиден ли контракт */
  readonly valid: boolean;
  /** Список ошибок */
  readonly errors: readonly ValidationIssue[];
  /** Список предупреждений */
  readonly warnings: readonly ValidationIssue[];
  /** Процент веб-совместимости */
  readonly webCompatibility: number;
  /** Статистика data bindings */
  readonly dataBindings?: DataBindingStats;
  /** Статистика версий компонентов */
  readonly versions?: ComponentVersionStats;
  /** Время валидации в миллисекундах */
  readonly validationTimeMs: number;
  /** Путь к файлу */
  readonly filePath: string;
  /** Дополнительная информация */
  readonly metadata?: Record<string, any>;
}

/**
 * Контекст валидации
 */
export interface ValidationContext {
  /** Путь к файлу */
  readonly filePath: string;
  /** Результат чтения файла */
  readonly fileResult: FileReadResult;
  /** Распарсенный JSON */
  readonly contract: any;
  /** Position Map */
  readonly positionMap: PositionMap;
  /** Текущий путь валидации */
  currentPath: string[];
  /** Флаг Jinja шаблона */
  readonly isJinjaTemplate: boolean;
}

/**
 * Опции валидации
 */
export interface ValidateOptions {
  /** Принудительный режим Jinja */
  forceJinjaMode?: boolean;
  /** Дополнительные валидаторы */
  additionalValidators?: Array<IValidator>;
  /** Пропустить веб-совместимость */
  skipWebCompatCheck?: boolean;
  /** Пропустить анализ bindings */
  skipBindingsAnalysis?: boolean;
}

/**
 * Интерфейс валидатора
 *
 * Позволяет создавать дополнительные валидаторы и расширять функциональность
 */
export interface IValidator {
  /**
   * Валидировать контракт
   *
   * @param context - Контекст валидации
   * @returns Список найденных проблем
   */
  validate(context: ValidationContext): Promise<ValidationIssue[]> | ValidationIssue[];
}

/**
 * SDUI Validator
 *
 * Главный класс валидатора с dependency injection.
 * Координирует процесс валидации и агрегирует результаты.
 *
 * АРХИТЕКТУРА:
 * - Dependency Injection для всех зависимостей
 * - Расширяемая через IValidator интерфейс
 * - Immutable результаты валидации
 * - Type-safe API
 *
 * @example
 * ```typescript
 * const validator = new SDUIValidator(
 *   config,
 *   fileReader,
 *   positionMapBuilder
 * );
 *
 * try {
 *   const report = await validator.validateFile('/path/to/contract.json');
 *   if (!report.valid) {
 *     console.error(`Found ${report.errors.length} errors`);
 *   }
 * } catch (error) {
 *   console.error('Validation failed:', error);
 * }
 * ```
 */
export class SDUIValidator {
  private readonly fileReader: FileReader;
  private readonly positionMapBuilder: PositionMapBuilder;
  private readonly validators: IValidator[];

  /**
   * @param _config - Конфигурация валидатора
   * @param fileReader - Читатель файлов
   * @param positionMapBuilder - Построитель position map
   * @param validators - Дополнительные валидаторы (опционально)
   */
  constructor(
    _config: ConfigManager,
    fileReader: FileReader,
    positionMapBuilder: PositionMapBuilder,
    validators: IValidator[] = []
  ) {
    this.fileReader = fileReader;
    this.positionMapBuilder = positionMapBuilder;
    this.validators = validators;
  }

  /**
   * Валидировать файл
   *
   * @param filePath - Путь к файлу
   * @param options - Опции валидации
   * @returns Отчет о валидации
   * @throws {FileReadError} Если файл не может быть прочитан
   * @throws {ValidationError} Если валидация не может быть выполнена
   */
  public async validateFile(
    filePath: string,
    options: ValidateOptions = {}
  ): Promise<ValidationReport> {
    const startTime = Date.now();

    // Чтение файла
    const fileResult = this.fileReader.readFile(filePath);

    // Определение типа файла
    const isJinjaTemplate = options.forceJinjaMode ||
      this.fileReader.isJinjaTemplate(filePath);

    // Парсинг контракта
    let contract: any;
    let content: string;

    if (isJinjaTemplate) {
      // TODO: Интеграция Jinja парсера
      throw new Error('Jinja templates are not yet supported in modular version');
    } else {
      content = fileResult.content;
      try {
        contract = JSON.parse(content);
      } catch (error) {
        // Возвращаем отчет с ошибкой парсинга
        return this.createParseErrorReport(
          filePath,
          error instanceof Error ? error.message : String(error),
          Date.now() - startTime
        );
      }
    }

    // Построение position map
    const positionMap = this.positionMapBuilder.build(content);

    // Создание контекста валидации
    const context: ValidationContext = {
      filePath,
      fileResult,
      contract,
      positionMap,
      currentPath: [],
      isJinjaTemplate,
    };

    // Запуск валидаторов
    const allIssues: ValidationIssue[] = [];

    for (const validator of this.getActiveValidators(options)) {
      const issues = await validator.validate(context);
      allIssues.push(...issues);
    }

    // Разделение на errors и warnings
    const errors = allIssues.filter((issue) => issue.severity === Severity.ERROR);
    const warnings = allIssues.filter((issue) => issue.severity === Severity.WARNING);

    // Анализ веб-совместимости
    const webCompatibility = options.skipWebCompatCheck
      ? 100
      : this.calculateWebCompatibility(allIssues);

    // Анализ data bindings
    const dataBindings = options.skipBindingsAnalysis
      ? undefined
      : this.analyzeDataBindings(contract);

    // Статистика версий компонентов
    const versions = this.analyzeComponentVersions(contract);

    const validationTimeMs = Date.now() - startTime;

    return {
      valid: errors.length === 0,
      errors: Object.freeze(errors),
      warnings: Object.freeze(warnings),
      webCompatibility,
      dataBindings,
      versions,
      validationTimeMs,
      filePath,
    };
  }

  /**
   * Валидировать JSON напрямую
   *
   * @param json - JSON объект или строка
   * @param filePath - Путь к файлу (для отчета)
   * @param options - Опции валидации
   * @returns Отчет о валидации
   */
  public async validateJSON(
    json: any | string,
    filePath: string = '<unknown>',
    options: ValidateOptions = {}
  ): Promise<ValidationReport> {
    const startTime = Date.now();

    // Парсинг если это строка
    let contract: any;
    let content: string;

    if (typeof json === 'string') {
      content = json;
      try {
        contract = JSON.parse(content);
      } catch (error) {
        return this.createParseErrorReport(
          filePath,
          error instanceof Error ? error.message : String(error),
          Date.now() - startTime
        );
      }
    } else {
      contract = json;
      content = JSON.stringify(json, null, 2);
    }

    // Построение position map
    const positionMap = this.positionMapBuilder.build(content);

    // Создание фейкового FileReadResult
    const fileResult: FileReadResult = {
      content,
      metadata: {
        path: filePath,
        name: '<unknown>',
        size: Buffer.byteLength(content),
        format: 'json' as any,
        lastModified: new Date(),
        encoding: 'utf-8',
      },
      readTimeMs: 0,
      contentHash: '',
    };

    // Создание контекста
    const context: ValidationContext = {
      filePath,
      fileResult,
      contract,
      positionMap,
      currentPath: [],
      isJinjaTemplate: false,
    };

    // Запуск валидаторов
    const allIssues: ValidationIssue[] = [];

    for (const validator of this.getActiveValidators(options)) {
      const issues = await validator.validate(context);
      allIssues.push(...issues);
    }

    const errors = allIssues.filter((issue) => issue.severity === Severity.ERROR);
    const warnings = allIssues.filter((issue) => issue.severity === Severity.WARNING);

    const webCompatibility = options.skipWebCompatCheck
      ? 100
      : this.calculateWebCompatibility(allIssues);

    const dataBindings = options.skipBindingsAnalysis
      ? undefined
      : this.analyzeDataBindings(contract);

    const versions = this.analyzeComponentVersions(contract);

    const validationTimeMs = Date.now() - startTime;

    return {
      valid: errors.length === 0,
      errors: Object.freeze(errors),
      warnings: Object.freeze(warnings),
      webCompatibility,
      dataBindings,
      versions,
      validationTimeMs,
      filePath,
    };
  }

  /**
   * Добавить кастомный валидатор
   *
   * @param validator - Валидатор
   */
  public addValidator(validator: IValidator): void {
    this.validators.push(validator);
  }

  /**
   * Получить список активных валидаторов
   */
  private getActiveValidators(options: ValidateOptions): IValidator[] {
    const validators = [...this.validators];

    if (options.additionalValidators) {
      validators.push(...options.additionalValidators);
    }

    return validators;
  }

  /**
   * Создать отчет с ошибкой парсинга
   */
  private createParseErrorReport(
    filePath: string,
    errorMessage: string,
    validationTimeMs: number
  ): ValidationReport {
    const parseError: ValidationIssue = {
      type: ErrorType.PARSE_ERROR,
      severity: Severity.ERROR,
      message: `JSON parse error: ${errorMessage}`,
      pointer: '/',
      path: '',
      line: 1,
      column: 1,
    };

    return {
      valid: false,
      errors: Object.freeze([parseError]),
      warnings: Object.freeze([]),
      webCompatibility: 0,
      validationTimeMs,
      filePath,
    };
  }

  /**
   * Вычислить процент веб-совместимости
   */
  private calculateWebCompatibility(issues: ValidationIssue[]): number {
    const webIncompatibleCount = issues.filter(
      (issue) => issue.type === ErrorType.WEB_INCOMPATIBLE
    ).length;

    if (issues.length === 0) {
      return 100;
    }

    const compatibilityRatio = 1 - (webIncompatibleCount / issues.length);
    return Math.max(0, Math.min(100, compatibilityRatio * 100));
  }

  /**
   * Анализировать data bindings
   */
  private analyzeDataBindings(contract: any): DataBindingStats {
    const bindings: DataBindingInfo[] = [];

    // Рекурсивный поиск bindings
    const findBindings = (obj: any, path: string = ''): void => {
      if (!obj || typeof obj !== 'object') {
        return;
      }

      for (const [key, value] of Object.entries(obj)) {
        const currentPath = path ? `${path}.${key}` : key;

        // Проверка на binding паттерны
        if (typeof value === 'string') {
          // State binding: ${state.xxx}
          if (value.includes('${state.')) {
            bindings.push({
              type: 'state',
              path: currentPath,
              expression: value,
            });
          }
          // Data binding: ${data.xxx}
          else if (value.includes('${data.')) {
            bindings.push({
              type: 'data',
              path: currentPath,
              expression: value,
            });
          }
          // Computed binding: ${computed.xxx}
          else if (value.includes('${computed.')) {
            bindings.push({
              type: 'computed',
              path: currentPath,
              expression: value,
            });
          }
        }

        // Рекурсивный обход
        if (typeof value === 'object') {
          findBindings(value, currentPath);
        }
      }
    };

    findBindings(contract);

    // Подсчет по типам
    const byType = {
      state: bindings.filter((b) => b.type === 'state').length,
      data: bindings.filter((b) => b.type === 'data').length,
      computed: bindings.filter((b) => b.type === 'computed').length,
    };

    return {
      hasBindings: bindings.length > 0,
      totalBindings: bindings.length,
      byType,
      bindings: Object.freeze(bindings),
    };
  }

  /**
   * Анализировать версии компонентов
   */
  private analyzeComponentVersions(contract: any): ComponentVersionStats {
    const versionCounts: Record<string, number> = {};
    const uniqueTypes = new Set<string>();
    let totalComponents = 0;

    // Рекурсивный поиск компонентов
    const findComponents = (obj: any): void => {
      if (!obj || typeof obj !== 'object') {
        return;
      }

      // Проверка наличия type (признак компонента)
      if ('type' in obj && typeof obj.type === 'string') {
        totalComponents++;
        uniqueTypes.add(obj.type);

        // Извлечение версии из releaseVersion
        if (obj.releaseVersion && typeof obj.releaseVersion === 'object') {
          for (const [platform, version] of Object.entries(obj.releaseVersion)) {
            if (typeof version === 'string') {
              const key = `${platform}:${version}`;
              versionCounts[key] = (versionCounts[key] || 0) + 1;
            }
          }
        }
      }

      // Рекурсивный обход
      for (const value of Object.values(obj)) {
        if (typeof value === 'object') {
          findComponents(value);
        }
      }
    };

    findComponents(contract);

    return {
      totalComponents,
      byVersion: Object.freeze(versionCounts),
      uniqueTypes: Object.freeze(Array.from(uniqueTypes)),
    };
  }
}

/**
 * Ошибка валидации
 */
export class ValidationError extends Error {
  public readonly filePath: string;
  public readonly cause?: Error;

  constructor(
    message: string,
    filePath: string,
    cause?: Error
  ) {
    super(message);
    this.name = 'ValidationError';
    this.filePath = filePath;
    this.cause = cause;
  }
}
