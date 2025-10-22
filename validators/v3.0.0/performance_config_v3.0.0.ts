/**
 * Performance Configuration for SDUI Web Validator v3.0.0
 * TypeScript конфигурация производительности
 *
 * @version 3.0.0
 * @author Performance Engineer Agent
 * @date 2025-10-05
 */

export interface PerformanceTargets {
  /** Целевое время для файлов <100KB (мс) */
  smallFile: number;
  /** Целевое время для файлов 100KB-1MB (мс) */
  mediumFile: number;
  /** Целевое время для файлов >1MB (мс) */
  largeFile: number;
  /** Целевое время для batch валидации 100 файлов (мс) */
  batch100Files: number;
}

export interface CacheConfig {
  /** Включить кэширование схем */
  schemaCache: boolean;
  /** Максимальный размер кэша схем */
  schemaCacheMaxSize: number;
  /** Включить кэширование position map */
  positionMapCache: boolean;
  /** Максимальный размер кэша position map */
  positionMapCacheMaxSize: number;
  /** TTL (Time To Live) для кэша в секундах */
  cacheTTL: number;
}

export interface FileProcessingConfig {
  /** Включить ленивую загрузку */
  lazyLoading: boolean;
  /** Потоковая обработка больших файлов */
  streamLargeFiles: boolean;
  /** Порог размера файла для потоковой обработки (KB) */
  largeFileThresholdKB: number;
  /** Размер буфера чтения (KB) */
  readBufferSizeKB: number;
}

export interface ParallelConfig {
  /** Включить параллельную валидацию */
  enabled: boolean;
  /** Максимальное количество воркеров (null = CPU count) */
  maxWorkers: number | null;
  /** Размер батча для параллельной обработки */
  batchSize: number;
  /** Стратегия распределения задач */
  schedulingStrategy: 'round-robin' | 'work-stealing' | 'dynamic';
}

export interface MemoryConfig {
  /** Включить memory pooling */
  poolingEnabled: boolean;
  /** Максимальный размер памяти (MB) */
  maxMemoryMB: number;
  /** Порог для сборки мусора (количество файлов) */
  gcThreshold: number;
  /** Включить агрессивную сборку мусора */
  aggressiveGC: boolean;
}

export interface OptimizationFlags {
  /** Использовать скомпилированные регулярные выражения */
  useCompiledRegex: boolean;
  /** Использовать индекс строк */
  useLineIndex: boolean;
  /** Использовать индекс схем */
  useSchemaIndex: boolean;
  /** Пропускать валидацию при попадании в кэш */
  skipValidationOnCacheHit: boolean;
  /** Включить профилирование производительности */
  enableProfiling: boolean;
}

export interface MonitoringConfig {
  /** Включить мониторинг производительности */
  enabled: boolean;
  /** Порог предупреждения (мс) */
  warningThresholdMS: number;
  /** Порог ошибки (мс) */
  errorThresholdMS: number;
  /** Логировать медленные операции */
  logSlowOperations: boolean;
  /** Экспортировать метрики */
  exportMetrics: boolean;
  /** Формат экспорта метрик */
  metricsFormat: 'json' | 'prometheus' | 'csv';
}

export interface PerformanceConfig {
  /** Целевые метрики производительности */
  targets: PerformanceTargets;
  /** Настройки кэширования */
  cache: CacheConfig;
  /** Настройки обработки файлов */
  fileProcessing: FileProcessingConfig;
  /** Настройки параллелизма */
  parallel: ParallelConfig;
  /** Настройки управления памятью */
  memory: MemoryConfig;
  /** Флаги оптимизаций */
  optimizations: OptimizationFlags;
  /** Настройки мониторинга */
  monitoring: MonitoringConfig;
}

/**
 * Production конфигурация - максимальная производительность
 */
export const productionConfig: PerformanceConfig = {
  targets: {
    smallFile: 100,
    mediumFile: 500,
    largeFile: 2000,
    batch100Files: 10000,
  },
  cache: {
    schemaCache: true,
    schemaCacheMaxSize: 512,
    positionMapCache: true,
    positionMapCacheMaxSize: 256,
    cacheTTL: 3600,
  },
  fileProcessing: {
    lazyLoading: true,
    streamLargeFiles: true,
    largeFileThresholdKB: 500,
    readBufferSizeKB: 64,
  },
  parallel: {
    enabled: true,
    maxWorkers: null, // auto-detect CPU count
    batchSize: 10,
    schedulingStrategy: 'work-stealing',
  },
  memory: {
    poolingEnabled: true,
    maxMemoryMB: 1024,
    gcThreshold: 100,
    aggressiveGC: false,
  },
  optimizations: {
    useCompiledRegex: true,
    useLineIndex: true,
    useSchemaIndex: true,
    skipValidationOnCacheHit: false,
    enableProfiling: false,
  },
  monitoring: {
    enabled: true,
    warningThresholdMS: 100,
    errorThresholdMS: 500,
    logSlowOperations: true,
    exportMetrics: true,
    metricsFormat: 'json',
  },
};

/**
 * Development конфигурация - баланс производительности и отладки
 */
export const developmentConfig: PerformanceConfig = {
  targets: {
    smallFile: 100,
    mediumFile: 500,
    largeFile: 2000,
    batch100Files: 10000,
  },
  cache: {
    schemaCache: true,
    schemaCacheMaxSize: 128,
    positionMapCache: true,
    positionMapCacheMaxSize: 64,
    cacheTTL: 1800,
  },
  fileProcessing: {
    lazyLoading: true,
    streamLargeFiles: false,
    largeFileThresholdKB: 500,
    readBufferSizeKB: 32,
  },
  parallel: {
    enabled: false, // отключено для упрощения отладки
    maxWorkers: 2,
    batchSize: 5,
    schedulingStrategy: 'round-robin',
  },
  memory: {
    poolingEnabled: false,
    maxMemoryMB: 512,
    gcThreshold: 50,
    aggressiveGC: false,
  },
  optimizations: {
    useCompiledRegex: true,
    useLineIndex: true,
    useSchemaIndex: true,
    skipValidationOnCacheHit: false,
    enableProfiling: true,
  },
  monitoring: {
    enabled: true,
    warningThresholdMS: 50,
    errorThresholdMS: 200,
    logSlowOperations: true,
    exportMetrics: false,
    metricsFormat: 'json',
  },
};

/**
 * Minimal конфигурация - без оптимизаций (для тестирования)
 */
export const minimalConfig: PerformanceConfig = {
  targets: {
    smallFile: 100,
    mediumFile: 500,
    largeFile: 2000,
    batch100Files: 10000,
  },
  cache: {
    schemaCache: false,
    schemaCacheMaxSize: 0,
    positionMapCache: false,
    positionMapCacheMaxSize: 0,
    cacheTTL: 0,
  },
  fileProcessing: {
    lazyLoading: false,
    streamLargeFiles: false,
    largeFileThresholdKB: 0,
    readBufferSizeKB: 16,
  },
  parallel: {
    enabled: false,
    maxWorkers: 1,
    batchSize: 1,
    schedulingStrategy: 'round-robin',
  },
  memory: {
    poolingEnabled: false,
    maxMemoryMB: 256,
    gcThreshold: 10,
    aggressiveGC: false,
  },
  optimizations: {
    useCompiledRegex: false,
    useLineIndex: false,
    useSchemaIndex: false,
    skipValidationOnCacheHit: false,
    enableProfiling: false,
  },
  monitoring: {
    enabled: false,
    warningThresholdMS: 1000,
    errorThresholdMS: 5000,
    logSlowOperations: false,
    exportMetrics: false,
    metricsFormat: 'json',
  },
};

/**
 * CI/CD конфигурация - для автоматизированного тестирования
 */
export const ciConfig: PerformanceConfig = {
  targets: {
    smallFile: 100,
    mediumFile: 500,
    largeFile: 2000,
    batch100Files: 10000,
  },
  cache: {
    schemaCache: true,
    schemaCacheMaxSize: 256,
    positionMapCache: true,
    positionMapCacheMaxSize: 128,
    cacheTTL: 300,
  },
  fileProcessing: {
    lazyLoading: true,
    streamLargeFiles: true,
    largeFileThresholdKB: 500,
    readBufferSizeKB: 64,
  },
  parallel: {
    enabled: true,
    maxWorkers: 4, // фиксированное количество для стабильности
    batchSize: 10,
    schedulingStrategy: 'round-robin',
  },
  memory: {
    poolingEnabled: true,
    maxMemoryMB: 512,
    gcThreshold: 50,
    aggressiveGC: true,
  },
  optimizations: {
    useCompiledRegex: true,
    useLineIndex: true,
    useSchemaIndex: true,
    skipValidationOnCacheHit: false,
    enableProfiling: true,
  },
  monitoring: {
    enabled: true,
    warningThresholdMS: 100,
    errorThresholdMS: 500,
    logSlowOperations: true,
    exportMetrics: true,
    metricsFormat: 'json',
  },
};

/**
 * Benchmark статистика
 */
export interface BenchmarkStats {
  category: 'small' | 'medium' | 'large';
  count: number;
  mean: number;
  median: number;
  min: number;
  max: number;
  p95: number;
  p99: number;
}

/**
 * Результаты валидации метрик
 */
export interface MetricValidationResult {
  category: string;
  target: number;
  actual: number;
  passed: boolean;
  margin?: number;
}

/**
 * Проверяет соответствие фактических метрик целевым
 */
export function validateTargets(
  config: PerformanceConfig,
  actualStats: Record<string, BenchmarkStats>
): MetricValidationResult[] {
  const results: MetricValidationResult[] = [];

  const categoryTargets: Record<string, number> = {
    small: config.targets.smallFile,
    medium: config.targets.mediumFile,
    large: config.targets.largeFile,
  };

  for (const [category, targetMS] of Object.entries(categoryTargets)) {
    if (category in actualStats) {
      const actualMS = actualStats[category].median;
      const passed = actualMS <= targetMS;
      const margin = passed ? ((targetMS - actualMS) / targetMS) * 100 : undefined;

      results.push({
        category,
        target: targetMS,
        actual: actualMS,
        passed,
        margin,
      });
    }
  }

  return results;
}

/**
 * Форматирует результаты валидации в читаемый вид
 */
export function formatValidationResults(results: MetricValidationResult[]): string {
  const lines: string[] = [
    '## Target Metrics Validation',
    '',
    '| Category | Target | Actual | Status | Margin |',
    '|----------|--------|--------|--------|--------|',
  ];

  for (const result of results) {
    const status = result.passed ? '✅ PASS' : '❌ FAIL';
    const margin = result.margin !== undefined ? `${result.margin.toFixed(1)}%` : 'N/A';

    lines.push(
      `| ${result.category.padEnd(8)} | ${result.target.toString().padStart(6)}ms | ${result.actual
        .toFixed(2)
        .padStart(8)}ms | ${status} | ${margin.padStart(6)} |`
    );
  }

  return lines.join('\n');
}

/**
 * Экспортирует конфигурацию в формат для Python валидатора
 */
export function exportToPython(config: PerformanceConfig): string {
  return `# Auto-generated from performance_config_v3.0.0.ts
# Do not edit manually

PERFORMANCE_CONFIG = {
    'targets': {
        'small_file': ${config.targets.smallFile},
        'medium_file': ${config.targets.mediumFile},
        'large_file': ${config.targets.largeFile},
        'batch_100_files': ${config.targets.batch100Files},
    },
    'cache': {
        'schema_cache': ${config.cache.schemaCache},
        'schema_cache_max_size': ${config.cache.schemaCacheMaxSize},
        'position_map_cache': ${config.cache.positionMapCache},
        'position_map_cache_max_size': ${config.cache.positionMapCacheMaxSize},
        'cache_ttl': ${config.cache.cacheTTL},
    },
    'file_processing': {
        'lazy_loading': ${config.fileProcessing.lazyLoading},
        'stream_large_files': ${config.fileProcessing.streamLargeFiles},
        'large_file_threshold_kb': ${config.fileProcessing.largeFileThresholdKB},
        'read_buffer_size_kb': ${config.fileProcessing.readBufferSizeKB},
    },
    'parallel': {
        'enabled': ${config.parallel.enabled},
        'max_workers': ${config.parallel.maxWorkers === null ? 'None' : config.parallel.maxWorkers},
        'batch_size': ${config.parallel.batchSize},
        'scheduling_strategy': '${config.parallel.schedulingStrategy}',
    },
    'memory': {
        'pooling_enabled': ${config.memory.poolingEnabled},
        'max_memory_mb': ${config.memory.maxMemoryMB},
        'gc_threshold': ${config.memory.gcThreshold},
        'aggressive_gc': ${config.memory.aggressiveGC},
    },
    'optimizations': {
        'use_compiled_regex': ${config.optimizations.useCompiledRegex},
        'use_line_index': ${config.optimizations.useLineIndex},
        'use_schema_index': ${config.optimizations.useSchemaIndex},
        'skip_validation_on_cache_hit': ${config.optimizations.skipValidationOnCacheHit},
        'enable_profiling': ${config.optimizations.enableProfiling},
    },
    'monitoring': {
        'enabled': ${config.monitoring.enabled},
        'warning_threshold_ms': ${config.monitoring.warningThresholdMS},
        'error_threshold_ms': ${config.monitoring.errorThresholdMS},
        'log_slow_operations': ${config.monitoring.logSlowOperations},
        'export_metrics': ${config.monitoring.exportMetrics},
        'metrics_format': '${config.monitoring.metricsFormat}',
    },
}
`;
}

/**
 * Пример использования
 */
export function example() {
  // Production режим
  console.log('Production Config:');
  console.log(`  Schema Cache: ${productionConfig.cache.schemaCacheMaxSize}`);
  console.log(`  Parallel: ${productionConfig.parallel.enabled}`);
  console.log(`  Memory Pool: ${productionConfig.memory.poolingEnabled}`);

  // Валидация метрик
  const actualStats: Record<string, BenchmarkStats> = {
    small: {
      category: 'small',
      count: 10,
      mean: 0.62,
      median: 0.52,
      min: 0.04,
      max: 1.67,
      p95: 1.67,
      p99: 1.67,
    },
    medium: {
      category: 'medium',
      count: 5,
      mean: 2.63,
      median: 3.32,
      min: 1.51,
      max: 3.41,
      p95: 3.41,
      p99: 3.41,
    },
  };

  const validation = validateTargets(productionConfig, actualStats);
  console.log('\n' + formatValidationResults(validation));

  // Экспорт в Python
  console.log('\nPython export:');
  console.log(exportToPython(developmentConfig));
}

// Default export
export default {
  production: productionConfig,
  development: developmentConfig,
  minimal: minimalConfig,
  ci: ciConfig,
  validateTargets,
  formatValidationResults,
  exportToPython,
};
