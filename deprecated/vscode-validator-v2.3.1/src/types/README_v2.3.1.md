# Types Module v2.3.1

>;=0O A8AB5<0 B8?>2 TypeScript 4;O SDUI 20;840B>@0.

## 17>@

>4C;L `types` ?@54>AB02;O5B 2A5 TypeScript B8?K 8 8=B5@D59AK 4;O:

-  57C;LB0B>2 20;840F88
- H81>: 8 ?@54C?@5645=89
- 0@A8=30 Jinja H01;>=>2
- >=D83C@0F88 20;840B>@0
- 5B@8: ?@>872>48B5;L=>AB8
- MH8@>20=8O
- >38@>20=8O
- VSCode 8=B53@0F88

## A=>2=K5 B8?K

### Validation Types

#### `ValidationResult`
```typescript
interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  filePath: string;
  timestamp: number;
  duration: number;
  fileSize: number;
  fileType: FileType;
  metrics?: PerformanceMetrics;
  warningCount: number;
  errorCount: number;
}
```

#### `ValidationError`
```typescript
interface ValidationError {
  severity: ValidationSeverity;
  category: ErrorCategory;
  message: string;
  description?: string;
  line: number;
  column: number;
  code?: string;
  fix?: string;
  docUrl?: string;
  file?: string;
  context?: string;
}
```

#### `ValidationSeverity`
```typescript
enum ValidationSeverity {
  ERROR = 'error',
  WARNING = 'warning',
  INFO = 'info',
  HINT = 'hint'
}
```

#### `ErrorCategory`
```typescript
enum ErrorCategory {
  SYNTAX = 'syntax',
  STRUCTURE = 'structure',
  SCHEMA = 'schema',
  JINJA = 'jinja',
  COMPATIBILITY = 'compatibility',
  PERFORMANCE = 'performance',
  SECURITY = 'security'
}
```

### File Types

#### `FileType`
```typescript
enum FileType {
  JSON = 'json',
  JINJA_JSON = 'jinja.json',
  J2_JAVA = 'j2.java',
  UNKNOWN = 'unknown'
}
```

#### `FileTypeInfo`
```typescript
interface FileTypeInfo {
  type: FileType;
  confidence: number;
  hasJinja: boolean;
  extension: string;
}
```

### Jinja Types

#### `JinjaTokenType`
```typescript
enum JinjaTokenType {
  VARIABLE = 'variable',       // {{ var }}
  BLOCK_START = 'block_start', // {% if %}
  BLOCK_END = 'block_end',     // {% endif %}
  COMMENT = 'comment',         // {# comment #}
  EXPRESSION = 'expression',   // {{ expr }}
  FILTER = 'filter',           // {{ var|filter }}
  TEST = 'test',               // {% if var is test %}
  UNKNOWN = 'unknown'
}
```

#### `JinjaToken`
```typescript
interface JinjaToken {
  type: JinjaTokenType;
  value: string;
  line: number;
  column: number;
  startOffset: number;
  endOffset: number;
  raw: string;
}
```

#### `JinjaBlock`
```typescript
interface JinjaBlock {
  type: string;
  startLine: number;
  endLine?: number;
  startToken: JinjaToken;
  endToken?: JinjaToken;
  children: JinjaBlock[];
  parent?: JinjaBlock;
}
```

### Configuration Types

#### `ValidatorConfig`
```typescript
interface ValidatorConfig {
  strict: boolean;
  maxFileSize: number;
  cacheEnabled: boolean;
  cacheTTL: number;
  trackPerformance: boolean;
  outputFormat: OutputFormat;
  colorOutput: boolean;
  vscodeMode: boolean;
  schemaPath?: string;
  autoFix: boolean;
  workers: number;
}
```

#### `OutputFormat`
```typescript
enum OutputFormat {
  CONSOLE = 'console',
  JSON = 'json',
  HTML = 'html',
  MARKDOWN = 'markdown',
  JUNIT = 'junit'
}
```

### Performance Types

#### `PerformanceMetrics`
```typescript
interface PerformanceMetrics {
  totalTime: number;
  readTime: number;
  parseTime: number;
  validationTime: number;
  jinjaTime: number;
  cacheHit: boolean;
  memoryUsage?: number;
  linesPerSecond: number;
  totalLines: number;
}
```

#### `BenchmarkResult`
```typescript
interface BenchmarkResult {
  fileName: string;
  fileSize: number;
  duration: number;
  throughput: number;
  errorCount: number;
  timestamp: number;
}
```

### Cache Types

#### `CacheEntry<T>`
```typescript
interface CacheEntry<T> {
  value: T;
  timestamp: number;
  hits: number;
  size: number;
  ttl: number;
}
```

#### `CacheStats`
```typescript
interface CacheStats {
  hits: number;
  misses: number;
  size: number;
  maxSize: number;
  hitRate: number;
  evictions: number;
}
```

### Logging Types

#### `LogLevel`
```typescript
enum LogLevel {
  DEBUG = 'debug',
  INFO = 'info',
  WARN = 'warn',
  ERROR = 'error',
  FATAL = 'fatal'
}
```

#### `LogEntry`
```typescript
interface LogEntry {
  level: LogLevel;
  message: string;
  timestamp: number;
  context?: Record<string, unknown>;
  error?: Error;
  file?: string;
  line?: number;
}
```

### VSCode Types

#### `VscodeDiagnostic`
```typescript
interface VscodeDiagnostic {
  range: {
    start: { line: number; character: number };
    end: { line: number; character: number };
  };
  message: string;
  severity: 0 | 1 | 2 | 3; // Error, Warning, Info, Hint
  code?: string;
  source: string;
}
```

#### `VscodeLink`
```typescript
interface VscodeLink {
  file: string;
  line: number;
  column: number;
  text: string;
}
```

## Utility Types

### `DeepReadonly<T>`
 5:C@A82=K9 readonly B8?:
```typescript
type DeepReadonly<T> = {
  readonly [P in keyof T]: T[P] extends object ? DeepReadonly<T[P]> : T[P];
};
```

### `DeepPartial<T>`
 5:C@A82=K9 partial B8?:
```typescript
type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};
```

### `RequiredFields<T, K>`
5;05B >?@545;5==K5 ?>;O >1O70B5;L=K<8:
```typescript
type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>;
```

### `AsyncFunction<T>`
"8? 4;O 0A8=E@>==KE DC=:F89:
```typescript
type AsyncFunction<T = void> = () => Promise<T>;
```

## A?>;L7>20=85

### <?>@B B8?>2

```typescript
import {
  ValidationResult,
  ValidationError,
  ValidationSeverity,
  ErrorCategory,
  FileType,
  PerformanceMetrics
} from './types';
```

### !>740=85 @57C;LB0B0 20;840F88

```typescript
const result: ValidationResult = {
  isValid: false,
  errors: [
    {
      severity: ValidationSeverity.ERROR,
      category: ErrorCategory.SYNTAX,
      message: 'Unexpected token',
      line: 10,
      column: 5
    }
  ],
  filePath: '/path/to/file.json',
  timestamp: Date.now(),
  duration: 150,
  fileSize: 1024,
  fileType: FileType.JSON,
  warningCount: 0,
  errorCount: 1
};
```

### Type Guards

```typescript
function isValidationError(error: unknown): error is ValidationError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'severity' in error &&
    'message' in error &&
    'line' in error &&
    'column' in error
  );
}
```

### Generic Validators

```typescript
function validateConfig<T extends ValidatorConfig>(
  config: DeepPartial<T>
): RequiredFields<T, 'strict' | 'maxFileSize'> {
  // Validation logic
  return config as RequiredFields<T, 'strict' | 'maxFileSize'>;
}
```

## CGH85 ?@0:B8:8

### 1. A5340 8A?>;L7C9B5 AB@>385 B8?K
```typescript
// Good
function validate(file: string): ValidationResult {
  // ...
}

// Bad
function validate(file: any): any {
  // ...
}
```

### 2. A?>;L7C9B5 ?5@5G8A;5=8O 4;O :>=AB0=B=KE 7=0G5=89
```typescript
// Good
severity: ValidationSeverity.ERROR

// Bad
severity: 'error'
```

### 3. A?>;L7C9B5 type guards
```typescript
if (isValidationError(error)) {
  console.log(error.line, error.column);
}
```

### 4. A?>;L7C9B5 utility types
```typescript
type ReadonlyConfig = DeepReadonly<ValidatorConfig>;
type PartialMetrics = DeepPartial<PerformanceMetrics>;
```

## 5@A8>=8@>20=85

5@A8O: **2.3.1**

A5 B8?K A;54CNB A5<0=B8G5A:><C 25@A8>=8@>20=8N:
- **MAJOR**: Breaking changes 2 B8?0E
- **MINOR**: >2K5 B8?K 8;8 =5>1O70B5;L=K5 ?>;O
- **PATCH**: A?@02;5=8O 4>:C<5=B0F88

## !<. B0:65

- [Formatters](../formatters/README_v2.3.1.md)
- [Utils](../utils/README_v2.3.1.md)
- [Core](../core/README_v2.3.1.md)
