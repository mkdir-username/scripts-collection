# Utils Module v2.3.1

#B8;8BK 4;O SDUI 20;840B>@0: :MH8@>20=85, ;>38@>20=85 8 <>=8B>@8=3 ?@>872>48B5;L=>AB8.

## 17>@

>4C;L `utils` ?@54>AB02;O5B:

- **LRU Cache** - :MH8@>20=85 @57C;LB0B>2 20;840F88
- **Logger** - AB@C:BC@8@>20==>5 ;>38@>20=85
- **Performance Monitor** - <>=8B>@8=3 ?@>872>48B5;L=>AB8

## >4C;8

### 1. LRU Cache

Least Recently Used :MH A ?>445@6:>9 TTL 8 02B><0B8G5A:>9 M20:C0F859.

#### A?>;L7>20=85

```typescript
import { LRUCache, validationCache } from './utils';

// A?>;L7>20=85 3;>10;L=>3> :MH0
validationCache.set('file-key', validationResult, 3600000); // TTL: 1 G0A
const cached = validationCache.get('file-key');

// !>740=85 A>1AB25==>3> :MH0
const cache = new LRUCache<ValidationResult>(500, 1800000); // 500 M;5<5=B>2, TTL: 30 <8=

// 07>2K5 >?5@0F88
cache.set('key1', value1);
cache.set('key2', value2, 600000); // Custom TTL: 10 <8=

const value = cache.get('key1');
const exists = cache.has('key1');
cache.delete('key1');
cache.clear();

// Batch >?5@0F88
const values = cache.getMany(['key1', 'key2', 'key3']);
cache.setMany(new Map([
  ['key1', value1],
  ['key2', value2]
]));
cache.deleteMany(['key1', 'key2']);

// Maintenance
const purged = cache.purgeExpired(); // #40;8BL ?@>A@>G5==K5
const stats = cache.getStats();
console.log(`Hit rate: ${stats.hitRate * 100}%`);

// >=D83C@0F8O
cache.setMaxSize(1000);
cache.setDefaultTTL(7200000); // 2 G0A0

// -:A?>@B/8<?>@B
const json = cache.toJSON();
cache.fromJSON(json);
```

#### API

##### >=AB@C:B>@

```typescript
new LRUCache<T>(maxSize?: number, defaultTTL?: number)
```
- `maxSize` - <0:A8<0;L=>5 :>;8G5AB2> M;5<5=B>2 (default: 1000)
- `defaultTTL` - 2@5<O 687=8 2 <8;;8A5:C=40E (default: 3600000 = 1 G0A)

##### A=>2=K5 <5B>4K

###### `get(key: string): T | undefined`
>;CG8BL 7=0G5=85 87 :MH0. 1=>2;O5B LRU ?>@O4>:.

###### `set(key: string, value: T, ttl?: number): void`
!>E@0=8BL 7=0G5=85 2 :MH. @8 ?@52KH5=88 @07<5@0 C40;O5B LRU M;5<5=B.

###### `delete(key: string): boolean`
#40;8BL M;5<5=B. >72@0I05B `true` 5A;8 M;5<5=B ACI5AB2>20;.

###### `has(key: string): boolean`
@>25@8BL ACI5AB2>20=85 M;5<5=B0 (=5 >1=>2;O5B LRU).

###### `clear(): void`
G8AB8BL 25AL :MH.

##### Batch >?5@0F88

###### `getMany(keys: string[]): Map<string, T>`
>;CG8BL =5A:>;L:> 7=0G5=89.

###### `setMany(entries: Map<string, T>, ttl?: number): void`
!>E@0=8BL =5A:>;L:> 7=0G5=89.

###### `deleteMany(keys: string[]): number`
#40;8BL =5A:>;L:> M;5<5=B>2. >72@0I05B :>;8G5AB2> C40;5==KE.

##### Maintenance

###### `purgeExpired(): number`
#40;8BL 2A5 ?@>A@>G5==K5 M;5<5=BK. >72@0I05B :>;8G5AB2> C40;5==KE.

###### `getStats(): CacheStats`
>;CG8BL AB0B8AB8:C:
```typescript
{
  hits: number;        // >;8G5AB2> ?>?040=89
  misses: number;      // >;8G5AB2> ?@><0E>2
  size: number;        // "5:CI89 @07<5@
  maxSize: number;     // 0:A8<0;L=K9 @07<5@
  hitRate: number;     // @>F5=B ?>?040=89 (0-1)
  evictions: number;   // >;8G5AB2> M20:C0F89
}
```

###### `resetStats(): void`
!1@>A8BL AB0B8AB8:C.

##### #B8;8BK

###### `keys(): string[]`
>;CG8BL 2A5 :;NG8.

###### `size(): number`
"5:CI89 @07<5@ :MH0.

###### `getEntry(key: string): CacheEntry<T> | undefined`
>;CG8BL ?>;=CN 8=D>@<0F8N >1 M;5<5=B5:
```typescript
{
  value: T;
  timestamp: number;
  hits: number;
  size: number;
  ttl: number;
}
```

###### `getTotalSize(): number`
F5=:0 8A?>;L7>20=8O ?0<OB8 2 109B0E.

###### `setMaxSize(maxSize: number): void`
#AB0=>28BL <0:A8<0;L=K9 @07<5@. -20:C8@C5B ;8H=85 M;5<5=BK.

###### `setDefaultTTL(ttl: number): void`
#AB0=>28BL TTL ?> C<>;G0=8N.

###### `toJSON(): object`
-:A?>@B8@>20BL :MH 2 JSON.

###### `fromJSON(data: object): void`
<?>@B8@>20BL :MH 87 JSON.

#### @8<5@ 8A?>;L7>20=8O

```typescript
// MH8@>20=85 @57C;LB0B>2 20;840F88
async function validateWithCache(filePath: string): Promise<ValidationResult> {
  const cacheKey = `validation:${filePath}`;

  // @>25@O5< :MH
  const cached = validationCache.get(cacheKey);
  if (cached) {
    return cached;
  }

  // 0;840F8O
  const result = await validateFile(filePath);

  // !>E@0=O5< 2 :MH
  validationCache.set(cacheKey, result, 1800000); // 30 <8=

  return result;
}

// >=8B>@8=3 :MH0
setInterval(() => {
  const stats = validationCache.getStats();
  console.log(`Cache: ${stats.size}/${stats.maxSize}, Hit rate: ${(stats.hitRate * 100).toFixed(2)}%`);

  // G8AB:0 ?@>A@>G5==KE
  const purged = validationCache.purgeExpired();
  if (purged > 0) {
    console.log(`Purged ${purged} expired entries`);
  }
}, 60000); // 064CN <8=CBC
```

### 2. Logger

!B@C:BC@8@>20==>5 ;>38@>20=85 A ?>445@6:>9 D09;>2>3> 2K2>40 8 @>B0F88.

#### A?>;L7>20=85

```typescript
import { logger, Logger, LogLevel } from './utils';

// A?>;L7>20=85 3;>10;L=>3> ;>335@0
logger.info('Validation started', { file: 'test.json' });
logger.warn('Deprecated API usage');
logger.error('Validation failed', new Error('Parse error'), { line: 10 });

// !>740=85 A>1AB25==>3> ;>335@0
const fileLogger = new Logger({
  level: LogLevel.DEBUG,
  outputFile: '/var/log/validator.log',
  enableConsole: true,
  enableColor: true,
  maxFileSize: 10 * 1024 * 1024, // 10MB
  maxFiles: 5
});

// >38@>20=85 A :>=B5:AB><
fileLogger.debug('Parsing file', { size: 1024 });
fileLogger.info('Validation passed', { errors: 0, warnings: 2 });
fileLogger.warn('Large file detected', { size: 5242880 });
fileLogger.error('Parse error', error, { line: 42, column: 15 });
fileLogger.fatal('System error', error);

// 7<5@5=85 ?@>872>48B5;L=>AB8
const endTimer = logger.startTimer('validation');
// ... validation code
endTimer(); // Logs: Timer: validation {duration: 150}

// A8=E@>==K5 >?5@0F88
await logger.measure('parse-file', async () => {
  return await parseFile(filePath);
});

// >G5@=89 ;>335@ A =0A;54>20=85< :>=B5:AB0
const moduleLogger = logger.child({ module: 'parser' });
moduleLogger.info('Starting parse'); // 2B><0B8G5A:8 4>102;O5BAO module: 'parser'
```

#### API

##### >=AB@C:B>@

```typescript
new Logger(config?: Partial<LoggerConfig>)

interface LoggerConfig {
  level: LogLevel;
  outputFile?: string;
  enableConsole: boolean;
  enableColor: boolean;
  enableTimestamp: boolean;
  maxFileSize: number;
  maxFiles: number;
  context?: Record<string, unknown>;
}
```

##### #@>2=8 ;>38@>20=8O

```typescript
enum LogLevel {
  DEBUG = 'debug',
  INFO = 'info',
  WARN = 'warn',
  ERROR = 'error',
  FATAL = 'fatal'
}
```

##### 5B>4K ;>38@>20=8O

###### `debug(message: string, context?: Record<string, unknown>): void`
Debug A>>1I5=8O.

###### `info(message: string, context?: Record<string, unknown>): void`
=D>@<0F8>==K5 A>>1I5=8O.

###### `warn(message: string, context?: Record<string, unknown>): void`
@54C?@5645=8O.

###### `error(message: string, error?: Error, context?: Record<string, unknown>): void`
H81:8 A >?F8>=0;L=K< Error >1J5:B><.

###### `fatal(message: string, error?: Error, context?: Record<string, unknown>): void`
@8B8G5A:85 >H81:8.

##### Performance <5B>4K

###### `startTimer(label: string): () => void`
!>7405B B09<5@. >72@0I05B DC=:F8N 4;O >AB0=>2:8:
```typescript
const end = logger.startTimer('operation');
// ... code
end(); // Logs duration
```

###### `measure<T>(label: string, fn: () => Promise<T>): Promise<T>`
7<5@O5B 2@5<O 2K?>;=5=8O 0A8=E@>==>9 DC=:F88:
```typescript
const result = await logger.measure('fetch-data', async () => {
  return await fetchData();
});
```

##### >=D83C@0F8O

###### `setLevel(level: LogLevel): void`
#AB0=>28BL C@>25=L ;>38@>20=8O.

###### `getLevel(): LogLevel`
>;CG8BL B5:CI89 C@>25=L.

###### `setContext(context: Record<string, unknown>): void`
#AB0=>28BL 3;>10;L=K9 :>=B5:AB.

###### `clearContext(): void`
G8AB8BL 3;>10;L=K9 :>=B5:AB.

##### #B8;8BK

###### `getBuffer(): LogEntry[]`
>;CG8BL 1CD5@ ;>3>2.

###### `clearBuffer(): void`
G8AB8BL 1CD5@.

###### `exportJSON(): string`
-:A?>@B8@>20BL ;>38 2 JSON.

###### `close(): void`
0:@KBL D09;>2K9 stream.

###### `child(context: Record<string, unknown>): Logger`
!>740BL 4>G5@=89 ;>335@ A =0A;54>20==K< :>=B5:AB><.

#### $>@<0B8@>20=85

$>@<0B 2K2>40:
```
2025-10-07T14:30:45.123Z [INFO ] Validation started {file: test.json}
2025-10-07T14:30:45.234Z [ERROR] Parse error {line: 10, error: Unexpected token}
```

####  >B0F8O D09;>2

@8 4>AB865=88 `maxFileSize`:
```
validator.log      (B5:CI89)
validator.1.log    (?@54K4CI89)
validator.2.log
validator.3.log
validator.4.log
validator.5.log    (C40;O5BAO)
```

#### @8<5@ 8A?>;L7>20=8O

```typescript
// 0AB@>9:0 ;>38@>20=8O
const logger = new Logger({
  level: process.env.NODE_ENV === 'production' ? LogLevel.INFO : LogLevel.DEBUG,
  outputFile: '/var/log/validator.log',
  enableConsole: true,
  enableColor: process.stdout.isTTY,
  context: {
    version: '2.3.1',
    environment: process.env.NODE_ENV
  }
});

// 0;840F8O A ;>38@>20=85<
async function validateWithLogging(filePath: string): Promise<ValidationResult> {
  const fileLogger = logger.child({ file: filePath });

  fileLogger.info('Starting validation');

  const result = await logger.measure('validation', async () => {
    try {
      return await validateFile(filePath);
    } catch (error) {
      fileLogger.error('Validation failed', error as Error);
      throw error;
    }
  });

  if (result.isValid) {
    fileLogger.info('Validation passed', {
      errors: result.errorCount,
      warnings: result.warningCount
    });
  } else {
    fileLogger.warn('Validation failed', {
      errors: result.errorCount,
      warnings: result.warningCount
    });
  }

  return result;
}
```

### 3. Performance Monitor

>=8B>@8=3 8 15=G<0@:8=3 ?@>872>48B5;L=>AB8.

#### A?>;L7>20=85

```typescript
import {
  performanceMonitor,
  PerformanceTimer,
  PerformanceBenchmark,
  measureAsync,
  measure,
  formatDuration
} from './utils';

// A?>;L7>20=85 3;>10;L=>3> <>=8B>@0
performanceMonitor.start();
performanceMonitor.mark('read-end');
performanceMonitor.mark('parse-start');
performanceMonitor.mark('parse-end');
performanceMonitor.recordParseTime();

const metrics = performanceMonitor.finalize();
console.log(`Total: ${formatDuration(metrics.totalTime)}`);

// Performance Timer
const timer = new PerformanceTimer();
timer.start();
timer.mark('step1');
// ... code
timer.mark('step2');
// ... code
const duration = timer.measure('step1-to-step2', 'step1', 'step2');
console.log(`Duration: ${duration}ms`);

// Async measurement
const { result, duration } = await measureAsync(async () => {
  return await parseFile(filePath);
});

// Sync measurement
const { result, duration } = measure(() => {
  return JSON.parse(content);
});

// Benchmarking
const benchmark = new PerformanceBenchmark();

await benchmark.run('parse-small', async () => {
  await parseFile('small.json');
});

await benchmark.run('parse-large', async () => {
  await parseFile('large.json');
});

const stats = benchmark.getStatistics();
console.log(`Average: ${formatDuration(stats.averageDuration)}`);
console.log(`Min: ${formatDuration(stats.minDuration)}`);
console.log(`Max: ${formatDuration(stats.maxDuration)}`);

// Iterations
await benchmark.runIterations('parse-test', 100, async () => {
  await parseFile('test.json');
});
```

#### API

##### PerformanceTimer

###### `start(): void`
0?CAB8BL/?5@570?CAB8BL B09<5@.

###### `mark(name: string): void`
B<5B8BL B>G:C 2@5<5=8.

###### `measure(name: string, startMark: string, endMark: string): number`
7<5@8BL 4;8B5;L=>ABL <564C <5B:0<8.

###### `elapsed(): number`
@5<O A <><5=B0 AB0@B0.

###### `getDuration(mark: string): number`
;8B5;L=>ABL >B AB0@B0 4> <5B:8.

###### `getMeasurement(name: string): number | undefined`
>;CG8BL A>E@0=5==>5 87<5@5=85.

###### `reset(): void`
!1@>A8BL B09<5@.

###### `export(): object`
-:A?>@B8@>20BL 40==K5 B09<5@0.

##### PerformanceMonitor

###### `start(): void`
0G0BL <>=8B>@8=3.

###### `mark(name: string): void`
B<5B8BL 2@5<5==CN B>G:C.

###### `recordReadTime(): void`
0?8A0BL 2@5<O GB5=8O.

###### `recordParseTime(): void`
0?8A0BL 2@5<O ?0@A8=30.

###### `recordValidationTime(): void`
0?8A0BL 2@5<O 20;840F88.

###### `recordJinjaTime(): void`
0?8A0BL 2@5<O Jinja >1@01>B:8.

###### `setCacheHit(hit: boolean): void`
#AB0=>28BL AB0BCA :MH0.

###### `setTotalLines(lines: number): void`
#AB0=>28BL :>;8G5AB2> AB@>:.

###### `finalize(): PerformanceMetrics`
025@H8BL <>=8B>@8=3 8 ?>;CG8BL <5B@8:8.

###### `getMetrics(): PerformanceMetrics`
>;CG8BL B5:CI85 <5B@8:8.

###### `reset(): void`
!1@>A8BL <>=8B>@.

##### PerformanceBenchmark

###### `run<T>(name: string, fn: () => Promise<T>): Promise<T>`
0?CAB8BL 15=G<0@:.

###### `runIterations<T>(name: string, iterations: number, fn: () => Promise<T>): Promise<T[]>`
0?CAB8BL =5A:>;L:> 8B5@0F89.

###### `getResults(): BenchmarkResult[]`
>;CG8BL 2A5 @57C;LB0BK.

###### `getStatistics(): object`
>;CG8BL AB0B8AB8:C:
```typescript
{
  count: number;
  totalDuration: number;
  averageDuration: number;
  minDuration: number;
  maxDuration: number;
  averageThroughput: number;
}
```

###### `clear(): void`
G8AB8BL @57C;LB0BK.

###### `export(): string`
-:A?>@B8@>20BL 2 JSON.

##### #B8;8BK

###### `measureAsync<T>(fn: () => Promise<T>): Promise<{result: T, duration: number}>`
7<5@8BL 0A8=E@>==CN DC=:F8N.

###### `measure<T>(fn: () => T): {result: T, duration: number}`
7<5@8BL A8=E@>==CN DC=:F8N.

###### `throttle<T>(fn: T, delay: number): T`
!>740BL throttled DC=:F8N.

###### `debounce<T>(fn: T, delay: number): T`
!>740BL debounced DC=:F8N.

###### `formatDuration(ms: number): string`
$>@<0B8@>20BL 4;8B5;L=>ABL: `15.42ms`, `1.5s`, `2m 30s`

###### `formatThroughput(linesPerSecond: number): string`
$>@<0B8@>20BL throughput: `3247 lines/sec`, `1.5K lines/sec`

###### `formatMemory(bytes: number): string`
$>@<0B8@>20BL ?0<OBL: `1.24 KB`, `15.8 MB`

#### @8<5@ 8A?>;L7>20=8O

```typescript
// >;=K9 <>=8B>@8=3 20;840F88
async function validateWithMetrics(filePath: string): Promise<ValidationResult> {
  const monitor = new PerformanceMonitor();
  monitor.start();

  // 'B5=85 D09;0
  monitor.mark('read-start');
  const content = await fs.promises.readFile(filePath, 'utf-8');
  monitor.mark('read-end');
  monitor.recordReadTime();

  // 0@A8=3
  monitor.mark('parse-start');
  const parsed = JSON.parse(content);
  monitor.mark('parse-end');
  monitor.recordParseTime();

  // 0;840F8O
  monitor.mark('validation-start');
  const errors = validateSchema(parsed);
  monitor.mark('validation-end');
  monitor.recordValidationTime();

  // $8=0;870F8O
  monitor.setTotalLines(content.split('\n').length);
  const metrics = monitor.finalize();

  return {
    isValid: errors.length === 0,
    errors,
    filePath,
    metrics,
    // ...
  };
}

// 5=G<0@:8=3
const benchmark = new PerformanceBenchmark();

const files = ['small.json', 'medium.json', 'large.json'];
for (const file of files) {
  await benchmark.run(file, async () => {
    await validateFile(file);
  });
}

const stats = benchmark.getStatistics();
console.log(`
Benchmark Results:
  Files: ${stats.count}
  Total time: ${formatDuration(stats.totalDuration)}
  Average: ${formatDuration(stats.averageDuration)}
  Min: ${formatDuration(stats.minDuration)}
  Max: ${formatDuration(stats.maxDuration)}
  Throughput: ${formatThroughput(stats.averageThroughput)}
`);
```

## =B53@0F8O <>4C;59

### >;=K9 workflow

```typescript
import { validationCache, logger, performanceMonitor, formatDuration } from './utils';

async function validateWithFullMonitoring(filePath: string): Promise<ValidationResult> {
  // >38@>20=85
  logger.info('Starting validation', { file: filePath });

  // @>25@:0 :MH0
  const cacheKey = `validation:${filePath}`;
  const cached = validationCache.get(cacheKey);
  if (cached) {
    logger.debug('Cache hit', { file: filePath });
    return cached;
  }

  // >=8B>@8=3 ?@>872>48B5;L=>AB8
  performanceMonitor.start();
  performanceMonitor.mark('start');

  try {
    const result = await logger.measure('validation', async () => {
      // 0;840F8O A <5B@8:0<8
      performanceMonitor.mark('parse-start');
      const parsed = await parseFile(filePath);
      performanceMonitor.mark('parse-end');
      performanceMonitor.recordParseTime();

      performanceMonitor.mark('validation-start');
      const errors = await validateSchema(parsed);
      performanceMonitor.mark('validation-end');
      performanceMonitor.recordValidationTime();

      return {
        isValid: errors.length === 0,
        errors,
        filePath,
        metrics: performanceMonitor.finalize()
      };
    });

    // !>E@0=5=85 2 :MH
    validationCache.set(cacheKey, result, 1800000);

    logger.info('Validation completed', {
      file: filePath,
      isValid: result.isValid,
      duration: formatDuration(result.metrics!.totalTime)
    });

    return result;
  } catch (error) {
    logger.error('Validation error', error as Error, { file: filePath });
    throw error;
  }
}
```

## !<. B0:65

- [Types](../types/README_v2.3.1.md)
- [Formatters](../formatters/README_v2.3.1.md)
- [Core](../core/README_v2.3.1.md)
