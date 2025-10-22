/**
 * Import Resolver - резолвинг и управление импортами
 * @version 1.0.0
 * @created 2025-10-07
 */

import { readFileSync, existsSync } from 'fs';
import { resolve, isAbsolute, dirname, basename } from 'path';
import {
  IParser,
  ParseResult,
  ParseOptions,
  ParserConfig,
  ParseError,
  ParseWarning,
  ParseErrorType,
  ParseWarningType,
  CircularImportException,
  FileNotFoundException,
  createSuccessResult,
  createErrorResult,
  createPosition,
  SourcePosition,
} from './types_v1.0.0.js';

// ============================================================================
// ТИПЫ
// ============================================================================

/**
 * Конфигурация резолвера импортов
 */
export interface ImportResolverConfig extends ParserConfig {
  basePath?: string;
  maxDepth?: number;
  allowCircular?: boolean;
  cacheImports?: boolean;
  extensions?: string[];
}

/**
 * Результат резолвинга импорта
 */
export interface ResolvedImport {
  originalPath: string;
  resolvedPath: string;
  content: string;
  parsed?: any;
  depth: number;
  parent?: string;
  dependencies: ResolvedImport[];
  metadata: ImportMetadata;
}

/**
 * Метаданные импорта
 */
export interface ImportMetadata {
  fileSize: number;
  mimeType: string;
  lastModified?: Date;
  hash?: string;
  cached: boolean;
}

/**
 * Результат резолвинга всех импортов
 */
export interface ImportResolutionResult {
  imports: ResolvedImport[];
  dependencyGraph: DependencyGraph;
  circularDependencies: CircularDependency[];
  totalSize: number;
}

/**
 * Граф зависимостей
 */
export interface DependencyGraph {
  nodes: Map<string, DependencyNode>;
  edges: DependencyEdge[];
}

/**
 * Узел графа зависимостей
 */
export interface DependencyNode {
  path: string;
  depth: number;
  imports: string[];
  importedBy: string[];
}

/**
 * Ребро графа зависимостей
 */
export interface DependencyEdge {
  from: string;
  to: string;
  position: SourcePosition;
}

/**
 * Циклическая зависимость
 */
export interface CircularDependency {
  cycle: string[];
  startNode: string;
  endNode: string;
}

/**
 * Паттерн импорта
 */
export interface ImportPattern {
  regex: RegExp;
  extractor: (match: RegExpMatchArray) => ImportSpec | null;
  name: string;
}

/**
 * Спецификация импорта
 */
export interface ImportSpec {
  path: string;
  description?: string;
  line: number;
  column: number;
}

// ============================================================================
// IMPORT RESOLVER
// ============================================================================

/**
 * Резолвер импортов
 */
export class ImportResolver
  implements IParser<string, ImportResolutionResult, ImportResolverConfig>
{
  private config: ImportResolverConfig;
  private importCache: Map<string, ResolvedImport>;
  private importChain: string[];
  private patterns: ImportPattern[];

  constructor(config: ImportResolverConfig = {}) {
    this.config = {
      strict: true,
      maxErrors: 100,
      timeout: 30000,
      verbose: false,
      basePath: process.cwd(),
      maxDepth: 10,
      allowCircular: false,
      cacheImports: true,
      extensions: ['.json', '.j2.java', '.jinja.json'],
      ...config,
    };

    this.importCache = new Map();
    this.importChain = [];
    this.patterns = this.initializePatterns();
  }

  /**
   * Резолвит все импорты в файле
   */
  async parse(
    filePath: string,
    options?: ParseOptions
  ): Promise<ParseResult<ImportResolutionResult>> {
    const startTime = Date.now();
    const errors: ParseError[] = [];
    const warnings: ParseWarning[] = [];

    try {
      // Читаем файл
      const content = readFileSync(filePath, options?.encoding || 'utf-8');
      const fileSize = Buffer.byteLength(content, 'utf-8');

      // Резолвим импорты
      const imports = await this.resolveImports(
        content,
        filePath,
        0,
        errors,
        warnings
      );

      // Строим граф зависимостей
      const dependencyGraph = this.buildDependencyGraph(imports);

      // Находим циклические зависимости
      const circularDependencies = this.findCircularDependencies(dependencyGraph);

      if (circularDependencies.length > 0 && !this.config.allowCircular) {
        for (const circular of circularDependencies) {
          errors.push({
            type: ParseErrorType.CIRCULAR_IMPORT,
            message: `Circular dependency detected: ${circular.cycle.join(' -> ')}`,
            position: createPosition(0, 0, 0),
            filePath,
          });
        }
      }

      // Вычисляем общий размер
      const totalSize = imports.reduce(
        (sum, imp) => sum + imp.metadata.fileSize,
        fileSize
      );

      const result: ImportResolutionResult = {
        imports,
        dependencyGraph,
        circularDependencies,
        totalSize,
      };

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
   * Валидация без полного резолвинга
   */
  async validate(filePath: string): Promise<boolean> {
    try {
      const content = readFileSync(filePath, 'utf-8');
      const specs = this.extractImportSpecs(content, filePath);

      for (const spec of specs) {
        const resolvedPath = this.resolvePath(spec.path, dirname(filePath));
        if (!existsSync(resolvedPath)) {
          return false;
        }
      }

      return true;
    } catch {
      return false;
    }
  }

  getConfig(): Readonly<ImportResolverConfig> {
    return { ...this.config };
  }

  updateConfig(config: Partial<ImportResolverConfig>): void {
    this.config = { ...this.config, ...config };
    if (config.cacheImports === false) {
      this.importCache.clear();
    }
  }

  // ============================================================================
  // RESOLUTION
  // ============================================================================

  /**
   * Резолвит все импорты рекурсивно
   */
  private async resolveImports(
    content: string,
    filePath: string,
    depth: number,
    errors: ParseError[],
    warnings: ParseWarning[]
  ): Promise<ResolvedImport[]> {
    // Проверка глубины
    if (depth >= this.config.maxDepth!) {
      errors.push({
        type: ParseErrorType.IMPORT_ERROR,
        message: `Maximum import depth exceeded (${this.config.maxDepth})`,
        position: createPosition(0, 0, 0),
        filePath,
      });
      return [];
    }

    // Извлекаем спецификации импортов
    const specs = this.extractImportSpecs(content, filePath);
    const resolvedImports: ResolvedImport[] = [];

    for (const spec of specs) {
      try {
        // Резолвим путь
        const resolvedPath = this.resolvePath(spec.path, dirname(filePath));

        // Проверка циклических зависимостей
        if (this.importChain.includes(resolvedPath)) {
          const cycle = [...this.importChain, resolvedPath];
          throw new CircularImportException(
            `Circular import detected`,
            createPosition(spec.line, spec.column, 0),
            filePath,
            resolvedPath,
            cycle
          );
        }

        // Проверка существования файла
        if (!existsSync(resolvedPath)) {
          throw new FileNotFoundException(
            resolvedPath,
            createPosition(spec.line, spec.column, 0),
            filePath
          );
        }

        // Проверка кэша
        if (this.config.cacheImports && this.importCache.has(resolvedPath)) {
          const cached = this.importCache.get(resolvedPath)!;
          resolvedImports.push(cached);

          warnings.push({
            type: ParseWarningType.PERFORMANCE,
            message: `Using cached import: ${basename(resolvedPath)}`,
            position: createPosition(spec.line, spec.column, 0),
            filePath,
          });

          continue;
        }

        // Читаем файл
        const importContent = readFileSync(resolvedPath, 'utf-8');
        const fileSize = Buffer.byteLength(importContent, 'utf-8');

        // Парсим содержимое (если JSON)
        let parsed: any = undefined;
        if (resolvedPath.endsWith('.json')) {
          try {
            parsed = JSON.parse(importContent);
          } catch (e) {
            errors.push({
              type: ParseErrorType.INVALID_JSON,
              message: `Failed to parse imported JSON: ${(e as Error).message}`,
              position: createPosition(spec.line, spec.column, 0),
              filePath: resolvedPath,
            });
          }
        }

        // Рекурсивно резолвим вложенные импорты
        this.importChain.push(resolvedPath);
        const dependencies = await this.resolveImports(
          importContent,
          resolvedPath,
          depth + 1,
          errors,
          warnings
        );
        this.importChain.pop();

        // Создаем resolved import
        const resolvedImport: ResolvedImport = {
          originalPath: spec.path,
          resolvedPath,
          content: importContent,
          parsed,
          depth,
          parent: filePath,
          dependencies,
          metadata: {
            fileSize,
            mimeType: this.getMimeType(resolvedPath),
            cached: false,
          },
        };

        // Сохраняем в кэш
        if (this.config.cacheImports) {
          this.importCache.set(resolvedPath, resolvedImport);
        }

        resolvedImports.push(resolvedImport);
      } catch (error) {
        if (error instanceof CircularImportException) {
          if (!this.config.allowCircular) {
            errors.push(error.toParseError());
          } else {
            warnings.push({
              type: ParseWarningType.DEPRECATED_SYNTAX,
              message: error.message,
              position: error.position!,
              filePath: error.filePath!,
            });
          }
        } else if (error instanceof FileNotFoundException) {
          errors.push(error.toParseError());
        } else {
          errors.push({
            type: ParseErrorType.IMPORT_ERROR,
            message: `Import error: ${(error as Error).message}`,
            position: createPosition(spec.line, spec.column, 0),
            filePath,
          });
        }
      }
    }

    return resolvedImports;
  }

  // ============================================================================
  // EXTRACTION
  // ============================================================================

  /**
   * Извлекает спецификации импортов из контента
   */
  private extractImportSpecs(content: string, filePath: string): ImportSpec[] {
    const specs: ImportSpec[] = [];
    const lines = content.split('\n');

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const lineNumber = i + 1;

      for (const pattern of this.patterns) {
        const match = line.match(pattern.regex);
        if (match) {
          const spec = pattern.extractor(match);
          if (spec) {
            specs.push({
              ...spec,
              line: lineNumber,
              column: line.indexOf(match[0]) + 1,
            });
          }
        }
      }
    }

    return specs;
  }

  /**
   * Инициализирует паттерны импортов
   */
  private initializePatterns(): ImportPattern[] {
    return [
      {
        name: 'file-protocol',
        regex: /\/\/\s*\[(.*?)\]\((file:\/\/.*?)\)/,
        extractor: (match) => ({
          path: match[2].replace('file://', ''),
          description: match[1],
          line: 0,
          column: 0,
        }),
      },
      {
        name: 'relative-import',
        regex: /import\s+['"](.+?)['"]/,
        extractor: (match) => ({
          path: match[1],
          line: 0,
          column: 0,
        }),
      },
      {
        name: 'require',
        regex: /require\s*\(['"](.+?)['"]\)/,
        extractor: (match) => ({
          path: match[1],
          line: 0,
          column: 0,
        }),
      },
    ];
  }

  // ============================================================================
  // DEPENDENCY GRAPH
  // ============================================================================

  /**
   * Строит граф зависимостей
   */
  private buildDependencyGraph(imports: ResolvedImport[]): DependencyGraph {
    const nodes = new Map<string, DependencyNode>();
    const edges: DependencyEdge[] = [];

    const processImport = (imp: ResolvedImport) => {
      const path = imp.resolvedPath;

      // Создаем узел если не существует
      if (!nodes.has(path)) {
        nodes.set(path, {
          path,
          depth: imp.depth,
          imports: [],
          importedBy: [],
        });
      }

      const node = nodes.get(path)!;

      // Добавляем зависимости
      for (const dep of imp.dependencies) {
        node.imports.push(dep.resolvedPath);

        // Добавляем обратную связь
        if (!nodes.has(dep.resolvedPath)) {
          nodes.set(dep.resolvedPath, {
            path: dep.resolvedPath,
            depth: dep.depth,
            imports: [],
            importedBy: [],
          });
        }
        nodes.get(dep.resolvedPath)!.importedBy.push(path);

        // Добавляем ребро
        edges.push({
          from: path,
          to: dep.resolvedPath,
          position: createPosition(0, 0, 0),
        });

        // Рекурсивно обрабатываем зависимости
        processImport(dep);
      }
    };

    for (const imp of imports) {
      processImport(imp);
    }

    return { nodes, edges };
  }

  /**
   * Находит циклические зависимости
   */
  private findCircularDependencies(graph: DependencyGraph): CircularDependency[] {
    const cycles: CircularDependency[] = [];
    const visited = new Set<string>();
    const recStack = new Set<string>();

    const dfs = (node: string, path: string[]): boolean => {
      if (recStack.has(node)) {
        // Нашли цикл
        const cycleStart = path.indexOf(node);
        const cycle = [...path.slice(cycleStart), node];
        cycles.push({
          cycle,
          startNode: node,
          endNode: path[path.length - 1],
        });
        return true;
      }

      if (visited.has(node)) {
        return false;
      }

      visited.add(node);
      recStack.add(node);
      path.push(node);

      const nodeData = graph.nodes.get(node);
      if (nodeData) {
        for (const neighbor of nodeData.imports) {
          dfs(neighbor, path);
        }
      }

      path.pop();
      recStack.delete(node);

      return false;
    };

    for (const [node] of graph.nodes) {
      if (!visited.has(node)) {
        dfs(node, []);
      }
    }

    return cycles;
  }

  // ============================================================================
  // UTILITIES
  // ============================================================================

  /**
   * Резолвит путь относительно базового пути
   */
  private resolvePath(importPath: string, basePath: string): string {
    if (isAbsolute(importPath)) {
      return importPath;
    }

    // Пробуем без расширения
    let resolved = resolve(basePath, importPath);
    if (existsSync(resolved)) {
      return resolved;
    }

    // Пробуем с расширениями
    for (const ext of this.config.extensions!) {
      const withExt = importPath.endsWith(ext) ? importPath : `${importPath}${ext}`;
      resolved = resolve(basePath, withExt);
      if (existsSync(resolved)) {
        return resolved;
      }
    }

    return resolve(basePath, importPath);
  }

  /**
   * Определяет MIME type файла
   */
  private getMimeType(filePath: string): string {
    if (filePath.endsWith('.json')) return 'application/json';
    if (filePath.endsWith('.j2.java')) return 'text/x-jinja';
    if (filePath.endsWith('.jinja.json')) return 'text/x-jinja';
    return 'text/plain';
  }

  /**
   * Очищает кэш импортов
   */
  clearCache(): void {
    this.importCache.clear();
  }

  /**
   * Получает статистику кэша
   */
  getCacheStats(): { size: number; paths: string[] } {
    return {
      size: this.importCache.size,
      paths: Array.from(this.importCache.keys()),
    };
  }
}
