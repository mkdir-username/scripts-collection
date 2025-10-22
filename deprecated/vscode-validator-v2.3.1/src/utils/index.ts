/**
 * Utils Module - Index
 *
 * Exports all utility modules:
 * - Cache
 * - Logger
 * - Performance
 *
 * @version 2.3.1
 * @module utils
 */

// Cache utilities
export { LRUCache, validationCache } from './cache';
export type { CacheEntry, CacheStats } from '../types';

// Logger utilities
export { Logger, logger } from './logger';
export type { LoggerConfig } from './logger';
export type { LogLevel, LogEntry } from '../types';

// Performance utilities
export {
  PerformanceTimer,
  PerformanceMonitor,
  PerformanceBenchmark,
  performanceMonitor,
  benchmark,
  measureAsync,
  measure,
  throttle,
  debounce,
  formatDuration,
  formatThroughput,
  formatMemory
} from './performance';

export type { PerformanceMetrics, BenchmarkResult } from '../types';

// Default exports
export { default as LRUCacheDefault } from './cache';
export { default as LoggerDefault } from './logger';
export { default as PerformanceDefault } from './performance';
