/**
 * Detectors Module v1.0.0
 *
 * Система детекторов ошибок для SDUI валидатора
 *
 * КОМПОНЕНТЫ:
 * ===========
 * - ErrorFieldDetector: Определение полей с ошибками
 * - JQIntegration: Выполнение jq запросов
 * - JSONPathIntegration: Выполнение JSONPath запросов
 * - PathConverter: Конвертация форматов путей
 *
 * ИСПОЛЬЗОВАНИЕ:
 * ==============
 * ```typescript
 * import {
 *   detectErrorField,
 *   jq,
 *   queryJSONPath,
 *   toJSONPointer,
 *   getAllMetrics
 * } from './detectors';
 *
 * // Детекция поля ошибки
 * const fieldInfo = detectErrorField("Component ButtonView not found", "components[0]");
 *
 * // jq запрос
 * const result = await jq(contract, '.components[].type');
 *
 * // JSONPath запрос
 * const authors = queryJSONPath(data, '$.store.book[*].author');
 *
 * // Конвертация путей
 * const pointer = toJSONPointer('components[0].type');
 *
 * // Получение всех метрик
 * const metrics = getAllMetrics();
 * ```
 */

// ============================================================================
// ЭКСПОРТ МОДУЛЕЙ
// ============================================================================

export {
  ErrorFieldDetector,
  detectErrorField,
  getDetectorMetrics,
  resetDetector,
  type ErrorFieldInfo,
  type ConfidenceLevel,
  type DetectorMetrics,
} from './error-field-detector';

export {
  JQIntegration,
  jq,
  jqWithFallback,
  isJQAvailable,
  getJQMetrics,
  type JQResult,
  type JQOptions,
  type FallbackFunction,
  type JQMetrics,
} from './jq-integration';

export {
  JSONPathIntegration,
  queryJSONPath,
  queryJSONPathWithFallback,
  isValidJSONPath,
  getJSONPathMetrics,
  type JSONPathResult,
  type JSONPathOptions,
  type JSONPathFallback,
  type JSONPathMetrics,
} from './jsonpath-integration';

export {
  PathConverter,
  toJSONPointer,
  toPropertyPath,
  toJSONPath,
  toJQ,
  normalizePath,
  detectPathFormat,
  validatePath,
  getConverterMetrics,
  type PathFormat,
  type ConversionResult,
  type ConversionOptions,
  type PathSegment,
  type ConverterMetrics,
} from './path-converter';

// ============================================================================
// АГРЕГИРОВАННЫЕ МЕТРИКИ
// ============================================================================

/**
 * Все метрики детекторов
 */
export interface AllDetectorMetrics {
  errorFieldDetector: ReturnType<typeof ErrorFieldDetector.prototype.getMetrics>;
  jqIntegration: ReturnType<typeof JQIntegration.prototype.getMetrics>;
  jsonPathIntegration: ReturnType<typeof JSONPathIntegration.prototype.getMetrics>;
  pathConverter: ReturnType<typeof PathConverter.prototype.getMetrics>;
}

/**
 * Получение всех метрик
 */
export function getAllMetrics(): AllDetectorMetrics {
  return {
    errorFieldDetector: ErrorFieldDetector.getInstance().getMetrics(),
    jqIntegration: JQIntegration.getInstance().getMetrics(),
    jsonPathIntegration: JSONPathIntegration.getInstance().getMetrics(),
    pathConverter: PathConverter.getInstance().getMetrics(),
  };
}

/**
 * Сброс всех метрик
 */
export function resetAllMetrics(): void {
  ErrorFieldDetector.getInstance().resetMetrics();
  JQIntegration.getInstance().resetMetrics();
  JSONPathIntegration.getInstance().resetMetrics();
  PathConverter.getInstance().resetMetrics();
}

/**
 * Очистка всех кэшей
 */
export function clearAllCaches(): void {
  ErrorFieldDetector.getInstance().clearCache();
  JQIntegration.getInstance().clearCache();
  JSONPathIntegration.getInstance().clearCache();
  PathConverter.getInstance().clearCache();
}

/**
 * Получение размеров всех кэшей
 */
export interface CacheSizes {
  errorFieldDetector: number;
  jqIntegration: number;
  jsonPathIntegration: number;
  pathConverter: number;
  total: number;
}

export function getAllCacheSizes(): CacheSizes {
  const errorFieldSize = ErrorFieldDetector.getInstance().getCacheSize();
  const jqSize = JQIntegration.getInstance().getCacheSize();
  const jsonPathSize = JSONPathIntegration.getInstance().getCacheSize();
  const pathConverterSize = PathConverter.getInstance().getCacheSize();

  return {
    errorFieldDetector: errorFieldSize,
    jqIntegration: jqSize,
    jsonPathIntegration: jsonPathSize,
    pathConverter: pathConverterSize,
    total: errorFieldSize + jqSize + jsonPathSize + pathConverterSize,
  };
}

// ============================================================================
// УТИЛИТЫ ДИАГНОСТИКИ
// ============================================================================

/**
 * Полный отчет по всем детекторам
 */
export interface DiagnosticReport {
  timestamp: string;
  metrics: AllDetectorMetrics;
  cacheSizes: CacheSizes;
  systemInfo: {
    jqAvailable: boolean;
  };
}

/**
 * Генерация диагностического отчета
 */
export async function generateDiagnosticReport(): Promise<DiagnosticReport> {
  const jqAvailable = await isJQAvailable();

  return {
    timestamp: new Date().toISOString(),
    metrics: getAllMetrics(),
    cacheSizes: getAllCacheSizes(),
    systemInfo: {
      jqAvailable,
    },
  };
}

/**
 * Печать отчета в консоль
 */
export async function printDiagnosticReport(): Promise<void> {
  const report = await generateDiagnosticReport();

  console.log('\n╔═══════════════════════════════════════════════════════════════╗');
  console.log('║         DETECTORS DIAGNOSTIC REPORT                           ║');
  console.log('╚═══════════════════════════════════════════════════════════════╝\n');

  console.log(`Timestamp: ${report.timestamp}\n`);

  // Error Field Detector
  console.log('┌─ Error Field Detector ──────────────────────────────────────┐');
  const efd = report.metrics.errorFieldDetector;
  console.log(`│ Total requests:        ${efd.totalRequests.toString().padStart(8)}`);
  console.log(`│ Successful detections: ${efd.successfulDetections.toString().padStart(8)}`);
  console.log(`│ Cache hits:            ${efd.cacheHits.toString().padStart(8)}`);
  console.log(`│ Cache hit rate:        ${efd.cacheHitRate.toFixed(2).padStart(7)}%`);
  console.log(`│ By confidence:`);
  console.log(`│   - High:              ${efd.byConfidence.high.toString().padStart(8)}`);
  console.log(`│   - Medium:            ${efd.byConfidence.medium.toString().padStart(8)}`);
  console.log(`│   - Low:               ${efd.byConfidence.low.toString().padStart(8)}`);
  console.log('└─────────────────────────────────────────────────────────────┘\n');

  // JQ Integration
  console.log('┌─ JQ Integration ────────────────────────────────────────────┐');
  const jqi = report.metrics.jqIntegration;
  console.log(`│ Total queries:         ${jqi.totalQueries.toString().padStart(8)}`);
  console.log(`│ JQ usage:              ${jqi.jqUsage.toString().padStart(8)}`);
  console.log(`│ Fallback usage:        ${jqi.fallbackUsage.toString().padStart(8)}`);
  console.log(`│ Cache hits:            ${jqi.cacheHits.toString().padStart(8)}`);
  console.log(`│ Errors:                ${jqi.errors.toString().padStart(8)}`);
  console.log(`│ Avg query time:        ${jqi.averageQueryTime.toFixed(2).padStart(7)}ms`);
  console.log(`│ JQ available:          ${report.systemInfo.jqAvailable ? 'Yes' : 'No'}`);
  console.log('└─────────────────────────────────────────────────────────────┘\n');

  // JSONPath Integration
  console.log('┌─ JSONPath Integration ──────────────────────────────────────┐');
  const jpi = report.metrics.jsonPathIntegration;
  console.log(`│ Total queries:         ${jpi.totalQueries.toString().padStart(8)}`);
  console.log(`│ Native usage:          ${jpi.nativeUsage.toString().padStart(8)}`);
  console.log(`│ Fallback usage:        ${jpi.fallbackUsage.toString().padStart(8)}`);
  console.log(`│ Cache hit rate:        ${jpi.cacheHitRate.toFixed(2).padStart(7)}%`);
  console.log(`│ Errors:                ${jpi.errors.toString().padStart(8)}`);
  console.log(`│ Avg query time:        ${jpi.averageQueryTime.toFixed(2).padStart(7)}ms`);
  console.log('└─────────────────────────────────────────────────────────────┘\n');

  // Path Converter
  console.log('┌─ Path Converter ────────────────────────────────────────────┐');
  const pc = report.metrics.pathConverter;
  console.log(`│ Total conversions:     ${pc.totalConversions.toString().padStart(8)}`);
  console.log(`│ Cache hit rate:        ${pc.cacheHitRate.toFixed(2).padStart(7)}%`);
  console.log(`│ Errors:                ${pc.errors.toString().padStart(8)}`);
  console.log(`│ Avg conversion time:   ${pc.averageConversionTime.toFixed(2).padStart(7)}ms`);
  console.log('└─────────────────────────────────────────────────────────────┘\n');

  // Cache Sizes
  console.log('┌─ Cache Sizes ───────────────────────────────────────────────┐');
  const cs = report.cacheSizes;
  console.log(`│ Error Field Detector:  ${cs.errorFieldDetector.toString().padStart(8)} entries`);
  console.log(`│ JQ Integration:        ${cs.jqIntegration.toString().padStart(8)} entries`);
  console.log(`│ JSONPath Integration:  ${cs.jsonPathIntegration.toString().padStart(8)} entries`);
  console.log(`│ Path Converter:        ${cs.pathConverter.toString().padStart(8)} entries`);
  console.log(`│ ─────────────────────────────────────────────────────────────`);
  console.log(`│ TOTAL:                 ${cs.total.toString().padStart(8)} entries`);
  console.log('└─────────────────────────────────────────────────────────────┘\n');
}
