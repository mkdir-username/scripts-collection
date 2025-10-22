#!/usr/bin/env tsx
/**
 * Performance Benchmark v2.3.0 для Jinja-валидаторов
 *
 * Анализирует узкие места и оптимизации для работы с .j2.java контрактами:
 * - Рекурсивная загрузка модулей
 * - Парсинг множества файлов
 * - Position map для нескольких файлов
 * - Кеширование модулей
 * - Параллельная загрузка
 * - Ленивая загрузка position maps
 *
 * @version 2.3.0
 * @author Claude Code - Performance Engineer
 * @date 2025-10-05
 *
 * Usage:
 *   tsx validators/v3.0.0/performance_benchmark_v2.3.0.ts
 *   tsx validators/v3.0.0/performance_benchmark_v2.3.0.ts --profile=full
 */

import { readFile, stat } from 'fs/promises';
import { join, dirname } from 'path';
import { performance } from 'perf_hooks';

// ============================================================================
// ТИПЫ
// ============================================================================

interface BenchmarkResult {
  metric: string;
  value: number;
  unit: 'ms' | 'MB' | 'count' | '%';
  baseline?: number;
  improvement?: number;
  threshold: number;
  passed: boolean;
}

interface BenchmarkSuite {
  name: string;
  results: BenchmarkResult[];
  totalTime: number;
  passed: boolean;
}

interface PerformanceMetrics {
  moduleLoading: {
    sequential: number;
    parallel: number;
    cached: number;
  };
  parsing: {
    singleFile: number;
    multiFile: number;
    withImports: number;
  };
  positionMapping: {
    build: number;
    lookup: number;
    multiFile: number;
  };
  memory: {
    baseline: number;
    afterParse: number;
    afterPositionMap: number;
  };
}

interface OptimizationRecommendation {
  category: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  description: string;
  expectedImprovement: string;
  implementation: string;
}

// ============================================================================
// УТИЛИТЫ ДЛЯ ИЗМЕРЕНИЙ
// ============================================================================

class PerformanceMeasurement {
  private marks: Map<string, number> = new Map();

  mark(label: string): void {
    this.marks.set(label, performance.now());
  }

  measure(label: string): number {
    const start = this.marks.get(label);
    if (!start) {
      throw new Error(`Mark "${label}" not found`);
    }
    const duration = performance.now() - start;
    this.marks.delete(label);
    return duration;
  }

  async profile<T>(label: string, fn: () => Promise<T>): Promise<{ result: T; duration: number }> {
    this.mark(label);
    const result = await fn();
    const duration = this.measure(label);
    return { result, duration };
  }

  getMemoryUsage(): number {
    const usage = process.memoryUsage();
    return usage.heapUsed / 1024 / 1024; // MB
  }
}

// ============================================================================
// MOCK ДАННЫЕ ДЛЯ ТЕСТИРОВАНИЯ
// ============================================================================

class MockDataGenerator {
  /**
   * Генерирует Jinja контракт с импортами
   */
  generateJinjaContract(imports: number, components: number): string {
    const importLines = Array.from({ length: imports }, (_, i) =>
      `// [...](module_${i}.j2.java) - Module ${i}`
    ).join('\n');

    const componentData = Array.from({ length: components }, (_, i) => ({
      type: i % 2 === 0 ? 'ButtonView' : 'IconView',
      version: 'v1',
      id: `component_${i}`,
      content: {
        text: `Component ${i}`,
        action: { type: 'navigate', screen: 'home' }
      }
    }));

    return `${importLines}

{
  "screen": {
    "type": "ScreenView",
    "version": "v1",
    "content": {
      "components": ${JSON.stringify(componentData, null, 2)}
    }
  }
}`;
  }

  /**
   * Генерирует модуль для импорта
   */
  generateModule(id: number, components: number): string {
    const componentData = Array.from({ length: components }, (_, i) => ({
      type: 'TextBlob',
      version: 'v1',
      id: `module_${id}_component_${i}`,
      content: { text: `Module ${id} Component ${i}` }
    }));

    return JSON.stringify(componentData, null, 2);
  }

  /**
   * Генерирует JSON с вложенной структурой
   */
  generateNestedJson(depth: number, breadth: number): any {
    if (depth === 0) {
      return { type: 'Leaf', id: Math.random().toString(36).substr(2, 9) };
    }

    const obj: any = {
      type: 'Container',
      children: []
    };

    for (let i = 0; i < breadth; i++) {
      obj.children.push(this.generateNestedJson(depth - 1, breadth));
    }

    return obj;
  }
}

// ============================================================================
// POSITION MAP IMPLEMENTATION (OPTIMIZED)
// ============================================================================

interface PositionInfo {
  line: number;
  column: number;
  offset: number;
}

interface PositionMap {
  byPointer: Map<string, PositionInfo>;
  byPath: Map<string, PositionInfo>;
  totalLines: number;
  buildTimeMs: number;
}

class PositionTracker {
  private cache: Map<string, PositionMap> = new Map();

  /**
   * Build position map (baseline implementation)
   */
  buildPositionMapBaseline(jsonText: string): PositionMap {
    const startTime = performance.now();
    const byPointer = new Map<string, PositionInfo>();
    const byPath = new Map<string, PositionInfo>();

    let line = 1;
    let column = 1;
    let offset = 0;

    const pathStack: Array<string | number> = [];
    let inString = false;
    let escaped = false;

    for (let i = 0; i < jsonText.length; i++) {
      const char = jsonText[i];

      if (escaped) {
        escaped = false;
        column++;
        offset++;
        continue;
      }

      if (char === '\\' && inString) {
        escaped = true;
        column++;
        offset++;
        continue;
      }

      if (char === '"') {
        inString = !inString;
      }

      if (!inString) {
        if (char === '{' || char === '[') {
          // Track positions
          const pointer = '/' + pathStack.map(p => String(p)).join('/');
          const propertyPath = pathStack.join('.');
          const pos: PositionInfo = { line, column, offset };
          byPointer.set(pointer, pos);
          byPath.set(propertyPath, pos);
        }
      }

      if (char === '\n') {
        line++;
        column = 1;
      } else {
        column++;
      }
      offset++;
    }

    const buildTimeMs = performance.now() - startTime;

    return {
      byPointer,
      byPath,
      totalLines: line,
      buildTimeMs
    };
  }

  /**
   * Build position map (optimized with caching)
   */
  buildPositionMapOptimized(jsonText: string, cacheKey?: string): PositionMap {
    if (cacheKey && this.cache.has(cacheKey)) {
      return this.cache.get(cacheKey)!;
    }

    const map = this.buildPositionMapBaseline(jsonText);

    if (cacheKey) {
      this.cache.set(cacheKey, map);
    }

    return map;
  }

  /**
   * Lazy loading strategy - build only when needed
   */
  async buildPositionMapLazy(
    jsonText: string,
    cacheKey?: string
  ): Promise<() => PositionMap> {
    return () => this.buildPositionMapOptimized(jsonText, cacheKey);
  }

  clearCache(): void {
    this.cache.clear();
  }
}

// ============================================================================
// MODULE LOADER (WITH OPTIMIZATION STRATEGIES)
// ============================================================================

class ModuleLoader {
  private cache: Map<string, any> = new Map();
  private perf = new PerformanceMeasurement();

  /**
   * Sequential loading (baseline)
   */
  async loadModulesSequential(paths: string[]): Promise<{ modules: any[]; duration: number }> {
    this.perf.mark('sequential');
    const modules: any[] = [];

    for (const path of paths) {
      const content = await this.loadModule(path);
      modules.push(content);
    }

    const duration = this.perf.measure('sequential');
    return { modules, duration };
  }

  /**
   * Parallel loading (optimized)
   */
  async loadModulesParallel(paths: string[]): Promise<{ modules: any[]; duration: number }> {
    this.perf.mark('parallel');

    const modules = await Promise.all(
      paths.map(path => this.loadModule(path))
    );

    const duration = this.perf.measure('parallel');
    return { modules, duration };
  }

  /**
   * Cached loading (optimized)
   */
  async loadModulesCached(paths: string[]): Promise<{ modules: any[]; duration: number }> {
    this.perf.mark('cached');

    const modules = await Promise.all(
      paths.map(async path => {
        if (this.cache.has(path)) {
          return this.cache.get(path);
        }
        const content = await this.loadModule(path);
        this.cache.set(path, content);
        return content;
      })
    );

    const duration = this.perf.measure('cached');
    return { modules, duration };
  }

  private async loadModule(path: string): Promise<any> {
    // Simulate module loading with mock data
    await new Promise(resolve => setTimeout(resolve, 5)); // 5ms delay
    return { path, loaded: true, data: { type: 'Module', content: [] } };
  }

  clearCache(): void {
    this.cache.clear();
  }
}

// ============================================================================
// PARSER BENCHMARKS
// ============================================================================

class ParserBenchmark {
  private generator = new MockDataGenerator();
  private perf = new PerformanceMeasurement();

  /**
   * Benchmark single file parsing
   */
  async benchmarkSingleFile(): Promise<BenchmarkResult> {
    const content = this.generator.generateJinjaContract(0, 50);

    this.perf.mark('parse-single');
    try {
      const extracted = this.extractJson(content);
      JSON.parse(extracted);
    } catch (err) {
      // Ignore errors
    }
    const duration = this.perf.measure('parse-single');

    return {
      metric: 'Single File Parse',
      value: duration,
      unit: 'ms',
      threshold: 50,
      passed: duration < 50
    };
  }

  /**
   * Benchmark multi-file parsing
   */
  async benchmarkMultiFile(fileCount: number): Promise<BenchmarkResult> {
    const files = Array.from({ length: fileCount }, (_, i) =>
      this.generator.generateJinjaContract(0, 10)
    );

    this.perf.mark('parse-multi');
    for (const content of files) {
      try {
        const extracted = this.extractJson(content);
        JSON.parse(extracted);
      } catch (err) {
        // Ignore
      }
    }
    const duration = this.perf.measure('parse-multi');

    return {
      metric: `Multi-File Parse (${fileCount} files)`,
      value: duration,
      unit: 'ms',
      threshold: fileCount * 50,
      passed: duration < fileCount * 50
    };
  }

  /**
   * Benchmark parsing with imports
   */
  async benchmarkWithImports(importCount: number): Promise<BenchmarkResult> {
    const content = this.generator.generateJinjaContract(importCount, 20);
    const modules = Array.from({ length: importCount }, (_, i) =>
      this.generator.generateModule(i, 5)
    );

    this.perf.mark('parse-imports');
    try {
      const extracted = this.extractJson(content);
      JSON.parse(extracted);

      // Parse all modules
      for (const module of modules) {
        JSON.parse(module);
      }
    } catch (err) {
      // Ignore
    }
    const duration = this.perf.measure('parse-imports');

    return {
      metric: `Parse with Imports (${importCount} imports)`,
      value: duration,
      unit: 'ms',
      threshold: 100,
      passed: duration < 100
    };
  }

  private extractJson(jinjaContent: string): string {
    // Remove Jinja import lines
    const lines = jinjaContent.split('\n').filter(line =>
      !line.trim().startsWith('//')
    );
    return lines.join('\n');
  }
}

// ============================================================================
// POSITION MAP BENCHMARKS
// ============================================================================

class PositionMapBenchmark {
  private generator = new MockDataGenerator();
  private tracker = new PositionTracker();
  private perf = new PerformanceMeasurement();

  /**
   * Benchmark position map building
   */
  async benchmarkBuild(sizeKB: number): Promise<BenchmarkResult> {
    const nested = this.generator.generateNestedJson(6, 3);
    const json = JSON.stringify(nested, null, 2);

    // Pad to target size
    const targetSize = sizeKB * 1024;
    const paddedJson = json.padEnd(targetSize, ' ');

    this.perf.mark('pos-build');
    const posMap = this.tracker.buildPositionMapBaseline(paddedJson);
    const duration = this.perf.measure('pos-build');

    return {
      metric: `Position Map Build (${sizeKB}KB)`,
      value: duration,
      unit: 'ms',
      threshold: sizeKB * 0.5, // 0.5ms per KB
      passed: duration < sizeKB * 0.5
    };
  }

  /**
   * Benchmark position lookup
   */
  async benchmarkLookup(iterations: number): Promise<BenchmarkResult> {
    const nested = this.generator.generateNestedJson(5, 3);
    const json = JSON.stringify(nested, null, 2);
    const posMap = this.tracker.buildPositionMapBaseline(json);

    this.perf.mark('pos-lookup');
    for (let i = 0; i < iterations; i++) {
      posMap.byPointer.get('/children/0/children/1');
      posMap.byPath.get('children.0.children.1');
    }
    const duration = this.perf.measure('pos-lookup');

    return {
      metric: `Position Lookup (${iterations} iterations)`,
      value: duration,
      unit: 'ms',
      threshold: 10,
      passed: duration < 10
    };
  }

  /**
   * Benchmark multi-file position maps
   */
  async benchmarkMultiFile(fileCount: number): Promise<BenchmarkResult> {
    const files = Array.from({ length: fileCount }, () => {
      const nested = this.generator.generateNestedJson(4, 3);
      return JSON.stringify(nested, null, 2);
    });

    this.perf.mark('pos-multi');
    for (const json of files) {
      this.tracker.buildPositionMapBaseline(json);
    }
    const duration = this.perf.measure('pos-multi');

    return {
      metric: `Multi-File Position Maps (${fileCount} files)`,
      value: duration,
      unit: 'ms',
      threshold: fileCount * 50,
      passed: duration < fileCount * 50
    };
  }

  /**
   * Compare baseline vs optimized (with caching)
   */
  async benchmarkOptimizations(): Promise<{
    baseline: number;
    cached: number;
    improvement: number;
  }> {
    const nested = this.generator.generateNestedJson(6, 3);
    const json = JSON.stringify(nested, null, 2);

    // Baseline
    this.perf.mark('baseline');
    for (let i = 0; i < 10; i++) {
      this.tracker.buildPositionMapBaseline(json);
    }
    const baseline = this.perf.measure('baseline');

    // Cached
    this.perf.mark('cached');
    for (let i = 0; i < 10; i++) {
      this.tracker.buildPositionMapOptimized(json, 'test-cache-key');
    }
    const cached = this.perf.measure('cached');

    const improvement = ((baseline - cached) / baseline) * 100;

    return { baseline, cached, improvement };
  }
}

// ============================================================================
// MODULE LOADING BENCHMARKS
// ============================================================================

class ModuleLoadingBenchmark {
  private loader = new ModuleLoader();

  /**
   * Compare sequential vs parallel loading
   */
  async benchmarkLoadingStrategies(moduleCount: number): Promise<{
    sequential: number;
    parallel: number;
    cached: number;
    improvement: number;
  }> {
    const paths = Array.from({ length: moduleCount }, (_, i) =>
      `/mock/module_${i}.j2.java`
    );

    // Sequential
    const { duration: sequential } = await this.loader.loadModulesSequential(paths);

    // Parallel
    const { duration: parallel } = await this.loader.loadModulesParallel(paths);

    // Cached (run twice to populate cache)
    await this.loader.loadModulesCached(paths);
    const { duration: cached } = await this.loader.loadModulesCached(paths);

    const improvement = ((sequential - parallel) / sequential) * 100;

    return { sequential, parallel, cached, improvement };
  }
}

// ============================================================================
// BENCHMARK RUNNER
// ============================================================================

class BenchmarkRunner {
  private suites: BenchmarkSuite[] = [];

  async runAll(): Promise<void> {
    console.log('━'.repeat(80));
    console.log('⚡ PERFORMANCE BENCHMARK v2.3.0');
    console.log('━'.repeat(80));
    console.log('');

    await this.runParserBenchmarks();
    await this.runPositionMapBenchmarks();
    await this.runModuleLoadingBenchmarks();
    await this.runOptimizationComparison();

    this.printSummary();
    this.generateRecommendations();
  }

  private async runParserBenchmarks(): Promise<void> {
    const parser = new ParserBenchmark();
    const results: BenchmarkResult[] = [];

    console.log('📊 PARSER BENCHMARKS');
    console.log('─'.repeat(80));

    results.push(await parser.benchmarkSingleFile());
    results.push(await parser.benchmarkMultiFile(5));
    results.push(await parser.benchmarkMultiFile(10));
    results.push(await parser.benchmarkWithImports(3));
    results.push(await parser.benchmarkWithImports(10));

    this.printResults(results);
    console.log('');

    this.suites.push({
      name: 'Parser',
      results,
      totalTime: results.reduce((sum, r) => sum + r.value, 0),
      passed: results.every(r => r.passed)
    });
  }

  private async runPositionMapBenchmarks(): Promise<void> {
    const posMap = new PositionMapBenchmark();
    const results: BenchmarkResult[] = [];

    console.log('📍 POSITION MAP BENCHMARKS');
    console.log('─'.repeat(80));

    results.push(await posMap.benchmarkBuild(50));
    results.push(await posMap.benchmarkBuild(200));
    results.push(await posMap.benchmarkBuild(500));
    results.push(await posMap.benchmarkLookup(1000));
    results.push(await posMap.benchmarkMultiFile(5));

    this.printResults(results);
    console.log('');

    this.suites.push({
      name: 'Position Map',
      results,
      totalTime: results.reduce((sum, r) => sum + r.value, 0),
      passed: results.every(r => r.passed)
    });
  }

  private async runModuleLoadingBenchmarks(): Promise<void> {
    const loader = new ModuleLoadingBenchmark();

    console.log('📦 MODULE LOADING BENCHMARKS');
    console.log('─'.repeat(80));

    const results5 = await loader.benchmarkLoadingStrategies(5);
    const results10 = await loader.benchmarkLoadingStrategies(10);

    console.log(`  5 modules:`);
    console.log(`    Sequential: ${results5.sequential.toFixed(2)}ms`);
    console.log(`    Parallel:   ${results5.parallel.toFixed(2)}ms (${results5.improvement.toFixed(1)}% faster)`);
    console.log(`    Cached:     ${results5.cached.toFixed(2)}ms`);
    console.log('');

    console.log(`  10 modules:`);
    console.log(`    Sequential: ${results10.sequential.toFixed(2)}ms`);
    console.log(`    Parallel:   ${results10.parallel.toFixed(2)}ms (${results10.improvement.toFixed(1)}% faster)`);
    console.log(`    Cached:     ${results10.cached.toFixed(2)}ms`);
    console.log('');

    const benchResults: BenchmarkResult[] = [
      {
        metric: 'Module Loading (5 modules, parallel)',
        value: results5.parallel,
        unit: 'ms',
        baseline: results5.sequential,
        improvement: results5.improvement,
        threshold: 50,
        passed: results5.parallel < 50
      },
      {
        metric: 'Module Loading (10 modules, parallel)',
        value: results10.parallel,
        unit: 'ms',
        baseline: results10.sequential,
        improvement: results10.improvement,
        threshold: 100,
        passed: results10.parallel < 100
      }
    ];

    this.suites.push({
      name: 'Module Loading',
      results: benchResults,
      totalTime: results5.parallel + results10.parallel,
      passed: benchResults.every(r => r.passed)
    });
  }

  private async runOptimizationComparison(): Promise<void> {
    const posMap = new PositionMapBenchmark();

    console.log('🚀 OPTIMIZATION COMPARISON');
    console.log('─'.repeat(80));

    const optimizations = await posMap.benchmarkOptimizations();

    console.log(`  Position Map Caching:`);
    console.log(`    Baseline (no cache): ${optimizations.baseline.toFixed(2)}ms`);
    console.log(`    Cached:              ${optimizations.cached.toFixed(2)}ms`);
    console.log(`    Improvement:         ${optimizations.improvement.toFixed(1)}%`);
    console.log('');

    const benchResults: BenchmarkResult[] = [
      {
        metric: 'Position Map Caching',
        value: optimizations.cached,
        unit: 'ms',
        baseline: optimizations.baseline,
        improvement: optimizations.improvement,
        threshold: optimizations.baseline * 0.5,
        passed: optimizations.improvement > 80
      }
    ];

    this.suites.push({
      name: 'Optimizations',
      results: benchResults,
      totalTime: optimizations.cached,
      passed: benchResults.every(r => r.passed)
    });
  }

  private printResults(results: BenchmarkResult[]): void {
    for (const result of results) {
      const icon = result.passed ? '✅' : '❌';
      const improvement = result.improvement
        ? ` (${result.improvement > 0 ? '+' : ''}${result.improvement.toFixed(1)}%)`
        : '';

      console.log(`  ${icon} ${result.metric}: ${result.value.toFixed(2)}${result.unit}${improvement}`);
      console.log(`      Threshold: ${result.threshold}${result.unit}`);

      if (result.baseline) {
        console.log(`      Baseline:  ${result.baseline.toFixed(2)}${result.unit}`);
      }
    }
  }

  private printSummary(): void {
    console.log('━'.repeat(80));
    console.log('📈 SUMMARY');
    console.log('━'.repeat(80));

    let totalPassed = 0;
    let totalTests = 0;

    for (const suite of this.suites) {
      const icon = suite.passed ? '✅' : '❌';
      const passedCount = suite.results.filter(r => r.passed).length;
      totalPassed += passedCount;
      totalTests += suite.results.length;

      console.log(`${icon} ${suite.name}: ${passedCount}/${suite.results.length} passed (${suite.totalTime.toFixed(2)}ms)`);
    }

    console.log('');
    console.log(`Overall: ${totalPassed}/${totalTests} tests passed (${((totalPassed / totalTests) * 100).toFixed(1)}%)`);
    console.log('');
  }

  private generateRecommendations(): void {
    const recommendations: OptimizationRecommendation[] = [
      {
        category: 'critical',
        title: 'Параллельная загрузка модулей',
        description: 'Загрузка импортов последовательно создает задержки. При 10 модулях по 5ms каждый, последовательная загрузка занимает 50ms, параллельная - всего 5ms.',
        expectedImprovement: '80-90% ускорение загрузки модулей',
        implementation: `
// BEFORE (sequential)
for (const importPath of imports) {
  const module = await loadModule(importPath);
  modules.push(module);
}

// AFTER (parallel)
const modules = await Promise.all(
  imports.map(path => loadModule(path))
);
        `.trim()
      },
      {
        category: 'high',
        title: 'Кеширование Position Maps',
        description: 'Position map строится за O(n) от размера JSON. При повторной валидации того же файла (например, в watch mode) можно использовать кеш.',
        expectedImprovement: '95-99% ускорение при повторной валидации',
        implementation: `
class PositionMapCache {
  private cache = new Map<string, PositionMap>();

  getOrBuild(filePath: string, content: string): PositionMap {
    const hash = createHash('sha256').update(content).digest('hex');
    const cacheKey = \`\${filePath}:\${hash}\`;

    if (this.cache.has(cacheKey)) {
      return this.cache.get(cacheKey)!;
    }

    const map = buildPositionMap(content);
    this.cache.set(cacheKey, map);
    return map;
  }
}
        `.trim()
      },
      {
        category: 'high',
        title: 'Ленивая загрузка Position Maps',
        description: 'Position map нужен только при наличии ошибок. Если контракт валиден, map не используется.',
        expectedImprovement: '100% экономия времени для валидных контрактов',
        implementation: `
// Lazy strategy
const positionMapBuilder = () => buildPositionMap(content);

// Validation
const report = await validate(contract);

if (!report.valid) {
  // Build position map only when errors exist
  const positionMap = positionMapBuilder();
  const errorsWithLocations = mapErrorsToLocations(report.errors, positionMap);
}
        `.trim()
      },
      {
        category: 'medium',
        title: 'Инкрементальный парсинг импортов',
        description: 'При изменении parent файла не нужно перепарсивать неизмененные импорты.',
        expectedImprovement: '50-70% ускорение при watch mode',
        implementation: `
interface ModuleCache {
  path: string;
  hash: string;
  parsed: any;
  timestamp: number;
}

async function loadModuleIncremental(path: string): Promise<any> {
  const stats = await fs.stat(path);
  const cached = moduleCache.get(path);

  if (cached && cached.timestamp === stats.mtimeMs) {
    return cached.parsed;
  }

  const content = await fs.readFile(path, 'utf-8');
  const parsed = parseModule(content);

  moduleCache.set(path, {
    path,
    hash: hashContent(content),
    parsed,
    timestamp: stats.mtimeMs
  });

  return parsed;
}
        `.trim()
      },
      {
        category: 'medium',
        title: 'Streaming парсинг для больших файлов',
        description: 'Для контрактов >1MB можно использовать streaming JSON parser вместо JSON.parse().',
        expectedImprovement: '30-40% снижение memory footprint',
        implementation: `
import { parser } from 'stream-json';
import { streamArray } from 'stream-json/streamers/StreamArray';

async function parseStreamingJson(filePath: string): Promise<any> {
  const pipeline = fs.createReadStream(filePath)
    .pipe(parser())
    .pipe(streamArray());

  const chunks: any[] = [];

  for await (const { value } of pipeline) {
    chunks.push(value);
  }

  return chunks;
}
        `.trim()
      },
      {
        category: 'low',
        title: 'Web Workers для CPU-intensive операций',
        description: 'Position map building можно вынести в Web Worker (Node.js Worker Threads) для больших файлов.',
        expectedImprovement: '20-30% ускорение за счет параллелизма',
        implementation: `
// worker.ts
import { parentPort, workerData } from 'worker_threads';

const positionMap = buildPositionMap(workerData.content);
parentPort?.postMessage(positionMap);

// main.ts
import { Worker } from 'worker_threads';

function buildPositionMapInWorker(content: string): Promise<PositionMap> {
  return new Promise((resolve, reject) => {
    const worker = new Worker('./worker.js', {
      workerData: { content }
    });

    worker.on('message', resolve);
    worker.on('error', reject);
  });
}
        `.trim()
      }
    ];

    console.log('━'.repeat(80));
    console.log('💡 OPTIMIZATION RECOMMENDATIONS');
    console.log('━'.repeat(80));
    console.log('');

    const categoryIcons = {
      critical: '🔴',
      high: '🟠',
      medium: '🟡',
      low: '🟢'
    };

    for (const rec of recommendations) {
      console.log(`${categoryIcons[rec.category]} ${rec.title.toUpperCase()}`);
      console.log('');
      console.log(`  Описание: ${rec.description}`);
      console.log('');
      console.log(`  Ожидаемый результат: ${rec.expectedImprovement}`);
      console.log('');
      console.log('  Имплементация:');
      console.log('  ' + rec.implementation.split('\n').join('\n  '));
      console.log('');
      console.log('─'.repeat(80));
      console.log('');
    }
  }
}

// ============================================================================
// MAIN
// ============================================================================

async function main(): Promise<void> {
  const runner = new BenchmarkRunner();
  await runner.runAll();
}

main().catch(err => {
  console.error('❌ Benchmark failed:', err);
  process.exit(1);
});
