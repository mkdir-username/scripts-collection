/**
 * Performance Monitoring and Metrics
 *
 * Tracks and analyzes:
 * - Execution timing
 * - Memory usage
 * - Throughput metrics
 * - Performance benchmarks
 *
 * @version 2.3.1
 * @module utils/performance
 */

import { PerformanceMetrics, BenchmarkResult } from '../types';

// ============================================================================
// Performance Timer
// ============================================================================

/**
 * High-resolution performance timer
 */
export class PerformanceTimer {
  private startTime: number;
  private marks: Map<string, number>;
  private measurements: Map<string, number>;

  constructor() {
    this.startTime = this.now();
    this.marks = new Map();
    this.measurements = new Map();
  }

  /**
   * Get current high-resolution time
   */
  private now(): number {
    if (typeof performance !== 'undefined' && performance.now) {
      return performance.now();
    }
    return Date.now();
  }

  /**
   * Start timer
   */
  start(): void {
    this.startTime = this.now();
    this.marks.clear();
    this.measurements.clear();
  }

  /**
   * Mark a point in time
   */
  mark(name: string): void {
    this.marks.set(name, this.now());
  }

  /**
   * Measure duration between two marks
   */
  measure(name: string, startMark: string, endMark: string): number {
    const start = this.marks.get(startMark);
    const end = this.marks.get(endMark);

    if (start === undefined || end === undefined) {
      throw new Error(`Marks not found: ${startMark}, ${endMark}`);
    }

    const duration = end - start;
    this.measurements.set(name, duration);
    return duration;
  }

  /**
   * Get elapsed time since start
   */
  elapsed(): number {
    return this.now() - this.startTime;
  }

  /**
   * Get duration of mark from start
   */
  getDuration(mark: string): number {
    const markTime = this.marks.get(mark);
    if (markTime === undefined) {
      throw new Error(`Mark not found: ${mark}`);
    }
    return markTime - this.startTime;
  }

  /**
   * Get measurement
   */
  getMeasurement(name: string): number | undefined {
    return this.measurements.get(name);
  }

  /**
   * Get all measurements
   */
  getAllMeasurements(): Map<string, number> {
    return new Map(this.measurements);
  }

  /**
   * Reset timer
   */
  reset(): void {
    this.startTime = this.now();
    this.marks.clear();
    this.measurements.clear();
  }

  /**
   * Export timing data
   */
  export(): {
    elapsed: number;
    marks: Record<string, number>;
    measurements: Record<string, number>;
  } {
    return {
      elapsed: this.elapsed(),
      marks: Object.fromEntries(this.marks),
      measurements: Object.fromEntries(this.measurements)
    };
  }
}

// ============================================================================
// Performance Monitor
// ============================================================================

/**
 * Monitor for tracking performance metrics
 */
export class PerformanceMonitor {
  private metrics: PerformanceMetrics;
  private timer: PerformanceTimer;
  private memoryStart: number;

  constructor() {
    this.timer = new PerformanceTimer();
    this.memoryStart = this.getMemoryUsage();
    this.metrics = this.initializeMetrics();
  }

  /**
   * Initialize metrics
   */
  private initializeMetrics(): PerformanceMetrics {
    return {
      totalTime: 0,
      readTime: 0,
      parseTime: 0,
      validationTime: 0,
      jinjaTime: 0,
      cacheHit: false,
      linesPerSecond: 0,
      totalLines: 0
    };
  }

  /**
   * Start monitoring
   */
  start(): void {
    this.timer.start();
    this.memoryStart = this.getMemoryUsage();
    this.metrics = this.initializeMetrics();
  }

  /**
   * Mark timing point
   */
  mark(name: string): void {
    this.timer.mark(name);
  }

  /**
   * Record read time
   */
  recordReadTime(): void {
    this.metrics.readTime = this.timer.getDuration('read-end') || 0;
  }

  /**
   * Record parse time
   */
  recordParseTime(): void {
    const start = this.timer.getDuration('parse-start') || 0;
    const end = this.timer.getDuration('parse-end') || 0;
    this.metrics.parseTime = end - start;
  }

  /**
   * Record validation time
   */
  recordValidationTime(): void {
    const start = this.timer.getDuration('validation-start') || 0;
    const end = this.timer.getDuration('validation-end') || 0;
    this.metrics.validationTime = end - start;
  }

  /**
   * Record Jinja processing time
   */
  recordJinjaTime(): void {
    const start = this.timer.getDuration('jinja-start') || 0;
    const end = this.timer.getDuration('jinja-end') || 0;
    this.metrics.jinjaTime = end - start;
  }

  /**
   * Set cache hit status
   */
  setCacheHit(hit: boolean): void {
    this.metrics.cacheHit = hit;
  }

  /**
   * Set total lines
   */
  setTotalLines(lines: number): void {
    this.metrics.totalLines = lines;
  }

  /**
   * Finalize metrics
   */
  finalize(): PerformanceMetrics {
    this.metrics.totalTime = this.timer.elapsed();
    this.metrics.memoryUsage = this.getMemoryUsage() - this.memoryStart;

    // Calculate throughput
    if (this.metrics.totalTime > 0) {
      this.metrics.linesPerSecond = (this.metrics.totalLines / this.metrics.totalTime) * 1000;
    }

    return this.metrics;
  }

  /**
   * Get current metrics
   */
  getMetrics(): PerformanceMetrics {
    return { ...this.metrics };
  }

  /**
   * Get memory usage
   */
  private getMemoryUsage(): number {
    if (typeof process !== 'undefined' && process.memoryUsage) {
      return process.memoryUsage().heapUsed;
    }
    return 0;
  }

  /**
   * Reset monitor
   */
  reset(): void {
    this.timer.reset();
    this.memoryStart = this.getMemoryUsage();
    this.metrics = this.initializeMetrics();
  }
}

// ============================================================================
// Performance Benchmark
// ============================================================================

/**
 * Benchmark runner for performance testing
 */
export class PerformanceBenchmark {
  private results: BenchmarkResult[] = [];

  /**
   * Run benchmark
   */
  async run<T>(name: string, fn: () => Promise<T>): Promise<T> {
    const monitor = new PerformanceMonitor();
    monitor.start();

    try {
      const result = await fn();
      const metrics = monitor.finalize();

      this.results.push({
        fileName: name,
        fileSize: 0,
        duration: metrics.totalTime,
        throughput: metrics.linesPerSecond,
        errorCount: 0,
        timestamp: Date.now()
      });

      return result;
    } catch (error) {
      const metrics = monitor.finalize();

      this.results.push({
        fileName: name,
        fileSize: 0,
        duration: metrics.totalTime,
        throughput: 0,
        errorCount: 1,
        timestamp: Date.now()
      });

      throw error;
    }
  }

  /**
   * Run multiple iterations
   */
  async runIterations<T>(name: string, iterations: number, fn: () => Promise<T>): Promise<T[]> {
    const results: T[] = [];

    for (let i = 0; i < iterations; i++) {
      const result = await this.run(`${name} (iteration ${i + 1})`, fn);
      results.push(result);
    }

    return results;
  }

  /**
   * Get benchmark results
   */
  getResults(): BenchmarkResult[] {
    return [...this.results];
  }

  /**
   * Get statistics
   */
  getStatistics(): {
    count: number;
    totalDuration: number;
    averageDuration: number;
    minDuration: number;
    maxDuration: number;
    averageThroughput: number;
  } {
    if (this.results.length === 0) {
      return {
        count: 0,
        totalDuration: 0,
        averageDuration: 0,
        minDuration: 0,
        maxDuration: 0,
        averageThroughput: 0
      };
    }

    const durations = this.results.map((r) => r.duration);
    const throughputs = this.results.map((r) => r.throughput);

    return {
      count: this.results.length,
      totalDuration: durations.reduce((a, b) => a + b, 0),
      averageDuration: durations.reduce((a, b) => a + b, 0) / durations.length,
      minDuration: Math.min(...durations),
      maxDuration: Math.max(...durations),
      averageThroughput: throughputs.reduce((a, b) => a + b, 0) / throughputs.length
    };
  }

  /**
   * Clear results
   */
  clear(): void {
    this.results = [];
  }

  /**
   * Export results
   */
  export(): string {
    return JSON.stringify(
      {
        results: this.results,
        statistics: this.getStatistics()
      },
      null,
      2
    );
  }
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Measure async function execution time
 */
export async function measureAsync<T>(fn: () => Promise<T>): Promise<{ result: T; duration: number }> {
  const timer = new PerformanceTimer();
  timer.start();

  const result = await fn();
  const duration = timer.elapsed();

  return { result, duration };
}

/**
 * Measure sync function execution time
 */
export function measure<T>(fn: () => T): { result: T; duration: number } {
  const timer = new PerformanceTimer();
  timer.start();

  const result = fn();
  const duration = timer.elapsed();

  return { result, duration };
}

/**
 * Create throttled function
 */
export function throttle<T extends (...args: unknown[]) => void>(fn: T, delay: number): T {
  let lastCall = 0;

  return ((...args: unknown[]) => {
    const now = Date.now();

    if (now - lastCall >= delay) {
      lastCall = now;
      fn(...args);
    }
  }) as T;
}

/**
 * Create debounced function
 */
export function debounce<T extends (...args: unknown[]) => void>(fn: T, delay: number): T {
  let timeoutId: NodeJS.Timeout | null = null;

  return ((...args: unknown[]) => {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }

    timeoutId = setTimeout(() => {
      fn(...args);
    }, delay);
  }) as T;
}

/**
 * Format duration for display
 */
export function formatDuration(ms: number): string {
  if (ms < 1) {
    return `${(ms * 1000).toFixed(0)}μs`;
  } else if (ms < 1000) {
    return `${ms.toFixed(2)}ms`;
  } else if (ms < 60000) {
    return `${(ms / 1000).toFixed(2)}s`;
  } else {
    const minutes = Math.floor(ms / 60000);
    const seconds = ((ms % 60000) / 1000).toFixed(0);
    return `${minutes}m ${seconds}s`;
  }
}

/**
 * Format throughput
 */
export function formatThroughput(linesPerSecond: number): string {
  if (linesPerSecond < 1000) {
    return `${linesPerSecond.toFixed(0)} lines/sec`;
  } else if (linesPerSecond < 1000000) {
    return `${(linesPerSecond / 1000).toFixed(2)}K lines/sec`;
  } else {
    return `${(linesPerSecond / 1000000).toFixed(2)}M lines/sec`;
  }
}

/**
 * Format memory size
 */
export function formatMemory(bytes: number): string {
  const units = ['B', 'KB', 'MB', 'GB'];
  let value = bytes;
  let unitIndex = 0;

  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex++;
  }

  return `${value.toFixed(2)} ${units[unitIndex]}`;
}

// ============================================================================
// Default Instances
// ============================================================================

/**
 * Default performance monitor
 */
export const performanceMonitor = new PerformanceMonitor();

/**
 * Default benchmark runner
 */
export const benchmark = new PerformanceBenchmark();

// ============================================================================
// Exports
// ============================================================================

export default {
  PerformanceTimer,
  PerformanceMonitor,
  PerformanceBenchmark,
  measureAsync,
  measure,
  throttle,
  debounce,
  formatDuration,
  formatThroughput,
  formatMemory
};
