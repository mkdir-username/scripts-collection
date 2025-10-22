/**
 * Module Resolver v1.0.0
 *
 * Рекурсивный резолвер модульных импортов для Jinja2 Java контрактов.
 * Поддерживает:
 * - Рекурсивную загрузку импортированных модулей
 * - Обработку .json и .j2.java модулей
 * - Детектирование циклических зависимостей
 * - Кеширование загруженных модулей
 *
 * @module module_resolver_v1.0.0
 */

import * as fs from 'fs/promises';
import * as path from 'path';

/**
 * Информация об импортируемом модуле
 */
export interface ModuleImport {
  /** Путь к модулю относительно projectRoot */
  path: string;
  /** Алиас модуля (если указан) */
  alias?: string;
  /** Позиция в исходном файле (для отчетов об ошибках) */
  position?: {
    line: number;
    column: number;
  };
}

/**
 * Разрешенный модуль со всеми зависимостями
 */
export interface ResolvedModule {
  /** Абсолютный путь к файлу модуля */
  filePath: string;
  /** Распарсенный JSON контент */
  content: any;
  /** Список импортов из этого модуля */
  imports: ModuleImport[];
  /** Является ли модуль Jinja2 Java шаблоном */
  isJinja2Java: boolean;
  /** Сырой текстовый контент (до парсинга) */
  rawContent?: string;
}

/**
 * Результат резолвинга всех модулей
 */
export interface ResolveAllResult {
  /** Карта разрешенных модулей: filePath -> ResolvedModule */
  modules: Map<string, ResolvedModule>;
  /** Граф зависимостей для визуализации */
  dependencyGraph: Map<string, Set<string>>;
}

/**
 * Ошибка при резолвинге модулей
 */
export class ModuleResolutionError extends Error {
  constructor(
    message: string,
    public filePath?: string,
    public cause?: Error
  ) {
    super(message);
    this.name = 'ModuleResolutionError';
  }
}

/**
 * Ошибка циклической зависимости
 */
export class CircularDependencyError extends ModuleResolutionError {
  constructor(
    message: string,
    public cycle: string[]
  ) {
    super(message);
    this.name = 'CircularDependencyError';
  }
}

/**
 * Опции для ModuleResolver
 */
export interface ModuleResolverOptions {
  /** Корневая директория проекта */
  projectRoot: string;
  /** Максимальная глубина рекурсии */
  maxDepth?: number;
  /** Разрешить кеширование */
  enableCache?: boolean;
  /** Расширения файлов модулей */
  moduleExtensions?: string[];
}

/**
 * Резолвер модульных импортов для Jinja2 Java контрактов
 */
export class ModuleResolver {
  private projectRoot: string;
  private maxDepth: number;
  private enableCache: boolean;
  private moduleExtensions: string[];

  /** Кеш загруженных модулей: absolutePath -> ResolvedModule */
  private cache: Map<string, ResolvedModule>;

  /** Текущий стек резолвинга для детектирования циклов */
  private resolutionStack: Set<string>;

  /** Граф зависимостей: filePath -> Set<importedFilePaths> */
  private dependencyGraph: Map<string, Set<string>>;

  constructor(options: ModuleResolverOptions) {
    this.projectRoot = path.resolve(options.projectRoot);
    this.maxDepth = options.maxDepth ?? 50;
    this.enableCache = options.enableCache ?? true;
    this.moduleExtensions = options.moduleExtensions ?? ['.json', '.j2.java'];

    this.cache = new Map();
    this.resolutionStack = new Set();
    this.dependencyGraph = new Map();
  }

  /**
   * Резолвит модуль и все его зависимости
   *
   * @param filePath - Путь к файлу (абсолютный или относительно projectRoot)
   * @returns Разрешенный модуль
   * @throws {ModuleResolutionError} Если модуль не найден или не может быть загружен
   * @throws {CircularDependencyError} Если обнаружена циклическая зависимость
   */
  async resolve(filePath: string): Promise<ResolvedModule> {
    const absolutePath = this.resolveFilePath(filePath);

    // Проверка кеша
    if (this.enableCache && this.cache.has(absolutePath)) {
      return this.cache.get(absolutePath)!;
    }

    // Проверка циклической зависимости
    if (this.resolutionStack.has(absolutePath)) {
      const cycle = this.buildCycleTrace(absolutePath);
      throw new CircularDependencyError(
        `Циклическая зависимость обнаружена: ${cycle.join(' -> ')}`,
        cycle
      );
    }

    // Проверка глубины рекурсии
    if (this.resolutionStack.size >= this.maxDepth) {
      throw new ModuleResolutionError(
        `Превышена максимальная глубина рекурсии (${this.maxDepth})`,
        absolutePath
      );
    }

    // Добавляем в стек резолвинга
    this.resolutionStack.add(absolutePath);

    try {
      // Загрузка файла
      const rawContent = await this.loadFile(absolutePath);

      // Проверка типа файла
      const isJinja2Java = this.isJinja2JavaFile(absolutePath, rawContent);

      // Парсинг контента
      let content: any;
      let imports: ModuleImport[] = [];

      try {
        if (isJinja2Java) {
          // Для Jinja2 Java файлов извлекаем импорты из сырого текста
          imports = this.extractImportsFromJinja2Java(rawContent);
          // Контент пока не парсим (требуется Jinja рендеринг)
          content = null;
        } else {
          // Для обычных JSON файлов парсим сразу
          content = JSON.parse(rawContent);
          // Извлекаем импорты из JSON
          imports = this.extractImportsFromJson(content);
        }
      } catch (parseError) {
        throw new ModuleResolutionError(
          `Ошибка парсинга модуля: ${(parseError as Error).message}`,
          absolutePath,
          parseError as Error
        );
      }

      // Создаем разрешенный модуль
      const resolvedModule: ResolvedModule = {
        filePath: absolutePath,
        content,
        imports,
        isJinja2Java,
        rawContent: isJinja2Java ? rawContent : undefined
      };

      // Кешируем
      if (this.enableCache) {
        this.cache.set(absolutePath, resolvedModule);
      }

      // Обновляем граф зависимостей
      const dependencies = new Set(
        imports.map(imp => this.resolveFilePath(imp.path, path.dirname(absolutePath)))
      );
      this.dependencyGraph.set(absolutePath, dependencies);

      return resolvedModule;
    } finally {
      // Убираем из стека резолвинга
      this.resolutionStack.delete(absolutePath);
    }
  }

  /**
   * Резолвит все импорты рекурсивно
   *
   * @param imports - Список импортов для резолвинга
   * @param baseDir - Базовая директория для относительных путей
   * @returns Карта разрешенных модулей и граф зависимостей
   */
  async resolveAll(
    imports: ModuleImport[],
    baseDir?: string
  ): Promise<ResolveAllResult> {
    const modules = new Map<string, ResolvedModule>();
    const queue: Array<{ import: ModuleImport; baseDir: string }> =
      imports.map(imp => ({
        import: imp,
        baseDir: baseDir ?? this.projectRoot
      }));

    const processed = new Set<string>();

    while (queue.length > 0) {
      const { import: imp, baseDir: currentBaseDir } = queue.shift()!;

      const absolutePath = this.resolveFilePath(imp.path, currentBaseDir);

      // Пропускаем уже обработанные
      if (processed.has(absolutePath)) {
        continue;
      }

      processed.add(absolutePath);

      try {
        // Резолвим модуль
        const resolvedModule = await this.resolve(absolutePath);
        modules.set(absolutePath, resolvedModule);

        // Добавляем импорты этого модуля в очередь
        if (resolvedModule.imports.length > 0) {
          const moduleDir = path.dirname(absolutePath);
          queue.push(
            ...resolvedModule.imports.map(childImport => ({
              import: childImport,
              baseDir: moduleDir
            }))
          );
        }
      } catch (error) {
        // Пробрасываем ошибки резолвинга
        if (error instanceof ModuleResolutionError) {
          throw error;
        }

        throw new ModuleResolutionError(
          `Не удалось резолвить модуль "${imp.path}": ${(error as Error).message}`,
          absolutePath,
          error as Error
        );
      }
    }

    return {
      modules,
      dependencyGraph: new Map(this.dependencyGraph)
    };
  }

  /**
   * Проверяет наличие циклических зависимостей
   *
   * @param filePath - Путь к файлу для проверки
   * @returns Массив файлов в цикле или null если циклов нет
   */
  detectCycles(filePath: string): string[] | null {
    const absolutePath = this.resolveFilePath(filePath);
    const visited = new Set<string>();
    const recursionStack = new Set<string>();

    const hasCycle = (currentPath: string, path: string[]): string[] | null => {
      if (!visited.has(currentPath)) {
        visited.add(currentPath);
        recursionStack.add(currentPath);

        const dependencies = this.dependencyGraph.get(currentPath);
        if (dependencies) {
          for (const dep of dependencies) {
            if (!visited.has(dep)) {
              const cycle = hasCycle(dep, [...path, currentPath]);
              if (cycle) return cycle;
            } else if (recursionStack.has(dep)) {
              // Нашли цикл
              const cycleStart = path.indexOf(dep);
              return [...path.slice(cycleStart), currentPath, dep];
            }
          }
        }
      }

      recursionStack.delete(currentPath);
      return null;
    };

    return hasCycle(absolutePath, []);
  }

  /**
   * Очищает кеш модулей
   */
  clearCache(): void {
    this.cache.clear();
    this.dependencyGraph.clear();
  }

  /**
   * Получает статистику кеша
   */
  getCacheStats(): { size: number; modules: string[] } {
    return {
      size: this.cache.size,
      modules: Array.from(this.cache.keys())
    };
  }

  /**
   * Получает граф зависимостей в виде объекта
   */
  getDependencyGraph(): Record<string, string[]> {
    const graph: Record<string, string[]> = {};
    for (const [file, deps] of this.dependencyGraph.entries()) {
      graph[file] = Array.from(deps);
    }
    return graph;
  }

  // ========== Private Methods ==========

  /**
   * Резолвит путь к файлу (абсолютный или относительный)
   */
  private resolveFilePath(filePath: string, baseDir?: string): string {
    // Если путь абсолютный, возвращаем как есть
    if (path.isAbsolute(filePath)) {
      return path.normalize(filePath);
    }

    // Если указана базовая директория, резолвим относительно нее
    if (baseDir) {
      return path.resolve(baseDir, filePath);
    }

    // Иначе резолвим относительно projectRoot
    return path.resolve(this.projectRoot, filePath);
  }

  /**
   * Загружает содержимое файла
   */
  private async loadFile(absolutePath: string): Promise<string> {
    try {
      // Проверяем существование файла
      await fs.access(absolutePath);

      // Читаем файл
      const content = await fs.readFile(absolutePath, 'utf-8');
      return content;
    } catch (error) {
      // Если файл не найден, пробуем добавить расширения
      if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
        for (const ext of this.moduleExtensions) {
          const pathWithExt = absolutePath + ext;
          try {
            await fs.access(pathWithExt);
            const content = await fs.readFile(pathWithExt, 'utf-8');
            return content;
          } catch {
            // Пробуем следующее расширение
            continue;
          }
        }
      }

      throw new ModuleResolutionError(
        `Не удалось загрузить модуль: ${(error as Error).message}`,
        absolutePath,
        error as Error
      );
    }
  }

  /**
   * Проверяет, является ли файл Jinja2 Java шаблоном
   */
  private isJinja2JavaFile(filePath: string, content: string): boolean {
    // Проверяем расширение
    if (filePath.endsWith('.j2.java')) {
      return true;
    }

    // Проверяем наличие Jinja2 синтаксиса в первых 500 символах
    const preview = content.substring(0, 500);
    const jinjaPatterns = [
      /\{%\s*(if|for|block|extends|include|import|set|macro)/,
      /\{\{.*\}\}/,
      /\{#.*#\}/
    ];

    return jinjaPatterns.some(pattern => pattern.test(preview));
  }

  /**
   * Извлекает импорты из Jinja2 Java файла
   */
  private extractImportsFromJinja2Java(content: string): ModuleImport[] {
    const imports: ModuleImport[] = [];
    const lines = content.split('\n');

    // Паттерны для импортов
    const importPatterns = [
      // {% import "path/to/module.json" as alias %}
      /\{%\s*import\s+["']([^"']+)["']\s+as\s+(\w+)\s*%\}/g,
      // {% import "path/to/module.json" %}
      /\{%\s*import\s+["']([^"']+)["']\s*%\}/g,
      // {% include "path/to/module.json" %}
      /\{%\s*include\s+["']([^"']+)["']\s*%\}/g
    ];

    lines.forEach((line, lineIndex) => {
      for (const pattern of importPatterns) {
        let match;
        pattern.lastIndex = 0; // Сбрасываем состояние regex

        while ((match = pattern.exec(line)) !== null) {
          const importPath = match[1];
          const alias = match[2] || undefined;

          imports.push({
            path: importPath,
            alias,
            position: {
              line: lineIndex + 1,
              column: match.index + 1
            }
          });
        }
      }
    });

    return imports;
  }

  /**
   * Извлекает импорты из JSON объекта
   */
  private extractImportsFromJson(obj: any): ModuleImport[] {
    const imports: ModuleImport[] = [];

    // Ищем поле "imports" или "modules"
    if (obj && typeof obj === 'object') {
      const importsField = obj.imports || obj.modules;

      if (Array.isArray(importsField)) {
        importsField.forEach((item: any) => {
          if (typeof item === 'string') {
            imports.push({ path: item });
          } else if (item && typeof item === 'object' && item.path) {
            imports.push({
              path: item.path,
              alias: item.alias || item.as
            });
          }
        });
      }
    }

    return imports;
  }

  /**
   * Строит трейс цикла зависимостей
   */
  private buildCycleTrace(targetPath: string): string[] {
    const stack = Array.from(this.resolutionStack);
    const cycleStart = stack.indexOf(targetPath);

    if (cycleStart === -1) {
      return [targetPath];
    }

    return [...stack.slice(cycleStart), targetPath];
  }
}

/**
 * Утилиты для работы с модулями
 */
export class ModuleUtils {
  /**
   * Визуализирует граф зависимостей в виде дерева
   */
  static visualizeDependencyGraph(
    graph: Map<string, Set<string>>,
    rootPath: string,
    options: { maxDepth?: number; indent?: string } = {}
  ): string {
    const maxDepth = options.maxDepth ?? 10;
    const indent = options.indent ?? '  ';
    const visited = new Set<string>();

    const buildTree = (filePath: string, depth: number): string[] => {
      if (depth >= maxDepth) {
        return [`${indent.repeat(depth)}... (max depth reached)`];
      }

      const lines: string[] = [];
      const relativePath = path.relative(process.cwd(), filePath);

      if (visited.has(filePath)) {
        lines.push(`${indent.repeat(depth)}${relativePath} (circular)`);
        return lines;
      }

      visited.add(filePath);
      lines.push(`${indent.repeat(depth)}${relativePath}`);

      const dependencies = graph.get(filePath);
      if (dependencies && dependencies.size > 0) {
        for (const dep of dependencies) {
          lines.push(...buildTree(dep, depth + 1));
        }
      }

      visited.delete(filePath);
      return lines;
    };

    return buildTree(rootPath, 0).join('\n');
  }

  /**
   * Топологическая сортировка модулей
   * Возвращает модули в порядке, безопасном для загрузки
   */
  static topologicalSort(graph: Map<string, Set<string>>): string[] {
    const sorted: string[] = [];
    const visited = new Set<string>();
    const recursionStack = new Set<string>();

    const visit = (node: string): void => {
      if (recursionStack.has(node)) {
        throw new Error(`Циклическая зависимость обнаружена на узле: ${node}`);
      }

      if (!visited.has(node)) {
        recursionStack.add(node);

        const dependencies = graph.get(node);
        if (dependencies) {
          for (const dep of dependencies) {
            visit(dep);
          }
        }

        recursionStack.delete(node);
        visited.add(node);
        sorted.push(node);
      }
    };

    for (const node of graph.keys()) {
      if (!visited.has(node)) {
        visit(node);
      }
    }

    return sorted;
  }

  /**
   * Находит все листовые модули (без зависимостей)
   */
  static findLeafModules(graph: Map<string, Set<string>>): string[] {
    const leaves: string[] = [];

    for (const [file, deps] of graph.entries()) {
      if (deps.size === 0) {
        leaves.push(file);
      }
    }

    return leaves;
  }

  /**
   * Находит все корневые модули (на которые никто не ссылается)
   */
  static findRootModules(graph: Map<string, Set<string>>): string[] {
    const allFiles = new Set(graph.keys());
    const referenced = new Set<string>();

    for (const deps of graph.values()) {
      for (const dep of deps) {
        referenced.add(dep);
      }
    }

    const roots: string[] = [];
    for (const file of allFiles) {
      if (!referenced.has(file)) {
        roots.push(file);
      }
    }

    return roots;
  }
}

// Export для удобного использования
export default ModuleResolver;
