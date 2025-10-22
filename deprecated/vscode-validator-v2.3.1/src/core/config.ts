/**
 * Configuration Module
 *
 * Централизованное управление конфигурацией валидатора.
 * Поддерживает переопределение через переменные окружения и параметры CLI.
 *
 * @module core/config
 * @version 2.3.1
 */

/**
 * Основные пути проекта
 */
export interface ProjectPaths {
  /** Корень проекта FMS_GIT */
  readonly projectRoot: string;
  /** Корень MCP валидаторов */
  readonly mcpRoot: string;
  /** Директория SDUI компонентов */
  readonly sduiRoot: string;
  /** Директория метасхем */
  readonly metaschemaRoot: string;
}

/**
 * Настройки валидации
 */
export interface ValidationOptions {
  /** Максимальная глубина вложенности JSON */
  readonly maxDepth: number;
  /** Timeout валидации в миллисекундах */
  readonly timeout: number;
  /** Включить строгую валидацию типов */
  readonly strictTypes: boolean;
  /** Включить проверку веб-совместимости */
  readonly checkWebCompat: boolean;
  /** Включить анализ data bindings */
  readonly analyzeBindings: boolean;
}

/**
 * Настройки парсинга Jinja
 */
export interface JinjaParsingOptions {
  /** Разрешить рекурсивные импорты */
  readonly allowRecursiveImports: boolean;
  /** Максимальная глубина импортов */
  readonly maxImportDepth: number;
  /** Строить source map */
  readonly buildSourceMap: boolean;
  /** Timeout парсинга в миллисекундах */
  readonly parseTimeout: number;
}

/**
 * Настройки форматирования вывода
 */
export interface OutputOptions {
  /** Отключить цвета в выводе */
  readonly noColor: boolean;
  /** Verbose режим с отладочной информацией */
  readonly verbose: boolean;
  /** Показывать номера колонок */
  readonly showColumns: boolean;
  /** Показывать контекст кода при ошибках */
  readonly showContext: boolean;
  /** Количество строк контекста */
  readonly contextLines: number;
}

/**
 * Настройки производительности
 */
export interface PerformanceOptions {
  /** Использовать кэш для position map */
  readonly enablePositionMapCache: boolean;
  /** Использовать инкрементальную валидацию */
  readonly enableIncrementalValidation: boolean;
  /** Размер буфера для чтения файлов (в байтах) */
  readonly fileReadBufferSize: number;
}

/**
 * Полная конфигурация валидатора
 */
export interface ValidatorConfig {
  readonly paths: ProjectPaths;
  readonly validation: ValidationOptions;
  readonly jinja: JinjaParsingOptions;
  readonly output: OutputOptions;
  readonly performance: PerformanceOptions;
  readonly version: string;
  readonly buildDate: string;
}

/**
 * Конфигурация по умолчанию
 */
const DEFAULT_CONFIG: ValidatorConfig = {
  paths: {
    projectRoot: process.env.PROJECT_ROOT || '/Users/username/Documents/FMS_GIT',
    mcpRoot: process.env.MCP_ROOT || '/Users/username/Scripts/alfa-sdui-mcp',
    sduiRoot: process.env.SDUI_ROOT || '/Users/username/Documents/FMS_GIT/SDUI',
    metaschemaRoot: process.env.METASCHEMA_ROOT || '/Users/username/Documents/FMS_GIT/metaschema',
  },
  validation: {
    maxDepth: 50,
    timeout: 30000,
    strictTypes: true,
    checkWebCompat: true,
    analyzeBindings: true,
  },
  jinja: {
    allowRecursiveImports: false,
    maxImportDepth: 10,
    buildSourceMap: true,
    parseTimeout: 10000,
  },
  output: {
    noColor: process.env.NO_COLOR === '1',
    verbose: process.env.VERBOSE === '1',
    showColumns: true,
    showContext: false,
    contextLines: 2,
  },
  performance: {
    enablePositionMapCache: true,
    enableIncrementalValidation: true,
    fileReadBufferSize: 1024 * 1024, // 1MB
  },
  version: '2.3.1',
  buildDate: '2025-10-07',
};

/**
 * Менеджер конфигурации
 *
 * Предоставляет централизованный доступ к настройкам валидатора.
 * Поддерживает иммутабельность и валидацию конфигурации.
 *
 * @example
 * ```typescript
 * const config = ConfigManager.getInstance();
 * const projectRoot = config.get('paths.projectRoot');
 *
 * // Создание кастомной конфигурации
 * const customConfig = ConfigManager.create({
 *   output: { verbose: true }
 * });
 * ```
 */
export class ConfigManager {
  private static instance: ConfigManager | null = null;
  private readonly config: ValidatorConfig;

  /**
   * Приватный конструктор для Singleton
   */
  private constructor(config: ValidatorConfig) {
    this.config = Object.freeze(this.deepFreeze(config));
  }

  /**
   * Получить singleton instance конфигурации
   */
  public static getInstance(): ConfigManager {
    if (!ConfigManager.instance) {
      ConfigManager.instance = new ConfigManager(DEFAULT_CONFIG);
    }
    return ConfigManager.instance;
  }

  /**
   * Создать новый instance с кастомной конфигурацией
   *
   * @param overrides - Частичная конфигурация для переопределения
   * @returns Новый instance ConfigManager
   */
  public static create(overrides: Partial<ValidatorConfig>): ConfigManager {
    const merged = ConfigManager.mergeConfig(DEFAULT_CONFIG, overrides);
    return new ConfigManager(merged);
  }

  /**
   * Сброс singleton instance (для тестов)
   */
  public static reset(): void {
    ConfigManager.instance = null;
  }

  /**
   * Получить значение из конфигурации по пути
   *
   * @param path - Путь к значению (например, 'paths.projectRoot')
   * @returns Значение или undefined
   */
  public get<T = any>(path: string): T | undefined {
    const segments = path.split('.');
    let current: any = this.config;

    for (const segment of segments) {
      if (current[segment] === undefined) {
        return undefined;
      }
      current = current[segment];
    }

    return current as T;
  }

  /**
   * Получить полную конфигурацию
   */
  public getAll(): ValidatorConfig {
    return this.config;
  }

  /**
   * Получить пути проекта
   */
  public getPaths(): ProjectPaths {
    return this.config.paths;
  }

  /**
   * Получить настройки валидации
   */
  public getValidationOptions(): ValidationOptions {
    return this.config.validation;
  }

  /**
   * Получить настройки Jinja
   */
  public getJinjaOptions(): JinjaParsingOptions {
    return this.config.jinja;
  }

  /**
   * Получить настройки вывода
   */
  public getOutputOptions(): OutputOptions {
    return this.config.output;
  }

  /**
   * Получить настройки производительности
   */
  public getPerformanceOptions(): PerformanceOptions {
    return this.config.performance;
  }

  /**
   * Получить версию валидатора
   */
  public getVersion(): string {
    return this.config.version;
  }

  /**
   * Получить дату сборки
   */
  public getBuildDate(): string {
    return this.config.buildDate;
  }

  /**
   * Проверка включен ли verbose режим
   */
  public isVerbose(): boolean {
    return this.config.output.verbose;
  }

  /**
   * Проверка включены ли цвета
   */
  public isColorEnabled(): boolean {
    return !this.config.output.noColor;
  }

  /**
   * Глубокая заморозка объекта
   */
  private deepFreeze<T>(obj: T): T {
    Object.freeze(obj);

    Object.getOwnPropertyNames(obj).forEach((prop) => {
      const value = (obj as any)[prop];
      if (
        value !== null &&
        (typeof value === 'object' || typeof value === 'function') &&
        !Object.isFrozen(value)
      ) {
        this.deepFreeze(value);
      }
    });

    return obj;
  }

  /**
   * Глубокое слияние конфигураций
   */
  private static mergeConfig(
    base: ValidatorConfig,
    overrides: Partial<ValidatorConfig>
  ): ValidatorConfig {
    const result = { ...base };

    for (const key in overrides) {
      const override = overrides[key as keyof ValidatorConfig];
      if (override !== undefined) {
        if (typeof override === 'object' && !Array.isArray(override)) {
          (result as any)[key] = {
            ...(base as any)[key],
            ...override,
          };
        } else {
          (result as any)[key] = override;
        }
      }
    }

    return result;
  }
}

/**
 * Экспорт дефолтного instance для удобства
 */
export const config = ConfigManager.getInstance();
