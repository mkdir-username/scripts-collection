/**
 * TypeScript Type Definitions for SDUI Validator v2.3.1
 *
 * Comprehensive type system for:
 * - Validation results and errors
 * - Parser states and tokens
 * - Configuration and options
 * - Performance metrics
 * - Cache entries
 *
 * @version 2.3.1
 * @module types
 */

// ============================================================================
// Validation Results
// ============================================================================

/**
 * Severity levels for validation issues
 */
export enum ValidationSeverity {
  ERROR = 'error',
  WARNING = 'warning',
  INFO = 'info',
  HINT = 'hint'
}

/**
 * Error categories for classification
 */
export enum ErrorCategory {
  SYNTAX = 'syntax',
  STRUCTURE = 'structure',
  SCHEMA = 'schema',
  JINJA = 'jinja',
  COMPATIBILITY = 'compatibility',
  PERFORMANCE = 'performance',
  SECURITY = 'security'
}

/**
 * Individual validation error with detailed location
 */
export interface ValidationError {
  /** Error severity level */
  severity: ValidationSeverity;

  /** Error category for classification */
  category: ErrorCategory;

  /** Human-readable error message */
  message: string;

  /** Detailed error description */
  description?: string;

  /** Line number (1-based) */
  line: number;

  /** Column number (1-based) */
  column: number;

  /** Error code for programmatic handling */
  code?: string;

  /** Suggested fix or correction */
  fix?: string;

  /** Documentation URL */
  docUrl?: string;

  /** Source file path */
  file?: string;

  /** Context snippet around error */
  context?: string;
}

/**
 * Complete validation result
 */
export interface ValidationResult {
  /** Whether validation passed */
  isValid: boolean;

  /** All validation errors */
  errors: ValidationError[];

  /** Validated file path */
  filePath: string;

  /** Validation timestamp */
  timestamp: number;

  /** Validation duration in milliseconds */
  duration: number;

  /** File size in bytes */
  fileSize: number;

  /** Detected file type */
  fileType: FileType;

  /** Performance metrics */
  metrics?: PerformanceMetrics;

  /** Warnings count */
  warningCount: number;

  /** Errors count */
  errorCount: number;
}

// ============================================================================
// File Types
// ============================================================================

/**
 * Supported file types
 */
export enum FileType {
  JSON = 'json',
  JINJA_JSON = 'jinja.json',
  J2_JAVA = 'j2.java',
  UNKNOWN = 'unknown'
}

/**
 * File type detection result
 */
export interface FileTypeInfo {
  type: FileType;
  confidence: number;
  hasJinja: boolean;
  extension: string;
}

// ============================================================================
// Parser Types
// ============================================================================

/**
 * Jinja token types
 */
export enum JinjaTokenType {
  VARIABLE = 'variable',           // {{ var }}
  BLOCK_START = 'block_start',     // {% if %}
  BLOCK_END = 'block_end',         // {% endif %}
  COMMENT = 'comment',             // {# comment #}
  EXPRESSION = 'expression',       // {{ expr }}
  FILTER = 'filter',               // {{ var|filter }}
  TEST = 'test',                   // {% if var is test %}
  UNKNOWN = 'unknown'
}

/**
 * Jinja token
 */
export interface JinjaToken {
  type: JinjaTokenType;
  value: string;
  line: number;
  column: number;
  startOffset: number;
  endOffset: number;
  raw: string;
}

/**
 * Jinja block context
 */
export interface JinjaBlock {
  type: string;
  startLine: number;
  endLine?: number;
  startToken: JinjaToken;
  endToken?: JinjaToken;
  children: JinjaBlock[];
  parent?: JinjaBlock;
}

/**
 * Parser state
 */
export interface ParserState {
  line: number;
  column: number;
  offset: number;
  inJinja: boolean;
  jinjaDepth: number;
  blockStack: JinjaBlock[];
  errors: ValidationError[];
}

// ============================================================================
// Configuration
// ============================================================================

/**
 * Validator configuration options
 */
export interface ValidatorConfig {
  /** Enable strict mode */
  strict: boolean;

  /** Maximum file size in bytes */
  maxFileSize: number;

  /** Enable caching */
  cacheEnabled: boolean;

  /** Cache TTL in milliseconds */
  cacheTTL: number;

  /** Enable performance tracking */
  trackPerformance: boolean;

  /** Output format */
  outputFormat: OutputFormat;

  /** Enable color output */
  colorOutput: boolean;

  /** VSCode integration mode */
  vscodeMode: boolean;

  /** Custom schema path */
  schemaPath?: string;

  /** Enable auto-fix suggestions */
  autoFix: boolean;

  /** Parallel validation workers */
  workers: number;
}

/**
 * Output format options
 */
export enum OutputFormat {
  CONSOLE = 'console',
  JSON = 'json',
  HTML = 'html',
  MARKDOWN = 'markdown',
  JUNIT = 'junit'
}

// ============================================================================
// Performance Metrics
// ============================================================================

/**
 * Performance metrics for validation
 */
export interface PerformanceMetrics {
  /** Total validation time */
  totalTime: number;

  /** File reading time */
  readTime: number;

  /** Parsing time */
  parseTime: number;

  /** Validation time */
  validationTime: number;

  /** Jinja processing time */
  jinjaTime: number;

  /** Cache hit/miss */
  cacheHit: boolean;

  /** Memory usage in bytes */
  memoryUsage?: number;

  /** Lines processed per second */
  linesPerSecond: number;

  /** Total lines processed */
  totalLines: number;
}

/**
 * Performance benchmark result
 */
export interface BenchmarkResult {
  fileName: string;
  fileSize: number;
  duration: number;
  throughput: number;
  errorCount: number;
  timestamp: number;
}

// ============================================================================
// Cache Types
// ============================================================================

/**
 * Cache entry
 */
export interface CacheEntry<T> {
  value: T;
  timestamp: number;
  hits: number;
  size: number;
  ttl: number;
}

/**
 * Cache statistics
 */
export interface CacheStats {
  hits: number;
  misses: number;
  size: number;
  maxSize: number;
  hitRate: number;
  evictions: number;
}

// ============================================================================
// Logging Types
// ============================================================================

/**
 * Log levels
 */
export enum LogLevel {
  DEBUG = 'debug',
  INFO = 'info',
  WARN = 'warn',
  ERROR = 'error',
  FATAL = 'fatal'
}

/**
 * Log entry
 */
export interface LogEntry {
  level: LogLevel;
  message: string;
  timestamp: number;
  context?: Record<string, unknown>;
  error?: Error;
  file?: string;
  line?: number;
}

// ============================================================================
// VSCode Integration Types
// ============================================================================

/**
 * VSCode diagnostic
 */
export interface VscodeDiagnostic {
  range: {
    start: { line: number; character: number };
    end: { line: number; character: number };
  };
  message: string;
  severity: 0 | 1 | 2 | 3; // Error, Warning, Info, Hint
  code?: string;
  source: string;
}

/**
 * VSCode link
 */
export interface VscodeLink {
  file: string;
  line: number;
  column: number;
  text: string;
}

// ============================================================================
// Utility Types
// ============================================================================

/**
 * Deep readonly type
 */
export type DeepReadonly<T> = {
  readonly [P in keyof T]: T[P] extends object ? DeepReadonly<T[P]> : T[P];
};

/**
 * Deep partial type
 */
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

/**
 * Required fields type
 */
export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>;

/**
 * Async function type
 */
export type AsyncFunction<T = void> = () => Promise<T>;

// ============================================================================
// Exports
// ============================================================================

export default {
  ValidationSeverity,
  ErrorCategory,
  FileType,
  JinjaTokenType,
  OutputFormat,
  LogLevel
};
