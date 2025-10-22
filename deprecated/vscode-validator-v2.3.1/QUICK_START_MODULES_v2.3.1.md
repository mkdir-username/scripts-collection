# Quick Start Guide - Modules v2.3.1

Быстрое руководство по использованию модулей форматирования и утилит.

## Установка

Модули находятся в `/Users/username/Scripts/vscode-validator-v2.3.1/src/`

## Быстрый старт

### 1. Типы (Types)

```typescript
import {
  ValidationResult,
  ValidationError,
  ValidationSeverity,
  ErrorCategory
} from './types';

// Создание результата валидации
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
  fileType: 'json',
  warningCount: 0,
  errorCount: 1
};
```

### 2. Форматтеры (Formatters)

#### Console Output

```typescript
import { consoleFormatter } from './formatters';

// Форматировать результат валидации
const output = consoleFormatter.formatResult(result);
console.log(output);

// Progress bar
const progress = consoleFormatter.formatProgress(50, 100, 'Validating');
console.log(progress);
// Output: Validating [████████████████████░░░░░░░░░░░░░░░░░░░░] 50.0% 50/100
```

#### Colors

```typescript
import { colorFormatter } from './formatters';

console.log(colorFormatter.success('Validation passed!'));  // ✓ Validation passed!
console.log(colorFormatter.failure('Validation failed!')); // ✗ Validation failed!
console.log(colorFormatter.boldRed('Critical error'));
console.log(colorFormatter.green('All tests passed'));
```

#### Links

```typescript
import { linkGenerator } from './formatters';

// Кликабельная ссылка
const link = linkGenerator.generateClickableLink(
  '/path/to/file.ts',
  'file.ts:10:5',
  10,
  5
);
console.log(link); // Кликабельна в iTerm2, VSCode, Hyper

// Из ошибки
const errorLink = linkGenerator.generateErrorLink(error);
```

### 3. Утилиты (Utils)

#### Cache

```typescript
import { validationCache } from './utils';

// Сохранить результат
validationCache.set('file-key', result, 3600000); // TTL: 1 час

// Получить из кэша
const cached = validationCache.get('file-key');

// Статистика
const stats = validationCache.getStats();
console.log(`Hit rate: ${(stats.hitRate * 100).toFixed(2)}%`);
```

#### Logger

```typescript
import { logger } from './utils';

logger.info('Starting validation', { file: 'test.json' });
logger.warn('Deprecated API');
logger.error('Parse failed', new Error('Unexpected token'));

// Измерение времени
const end = logger.startTimer('validation');
// ... validation code
end(); // Logs: Timer: validation {duration: 150}
```

#### Performance

```typescript
import { performanceMonitor, formatDuration } from './utils';

performanceMonitor.start();
performanceMonitor.mark('parse-start');
// ... parsing code
performanceMonitor.mark('parse-end');
performanceMonitor.recordParseTime();

const metrics = performanceMonitor.finalize();
console.log(`Duration: ${formatDuration(metrics.totalTime)}`);
console.log(`Throughput: ${metrics.linesPerSecond} lines/sec`);
```

## Полный пример

```typescript
import {
  ValidationResult,
  ValidationSeverity,
  ErrorCategory
} from './types';

import {
  consoleFormatter,
  colorFormatter,
  linkGenerator
} from './formatters';

import {
  validationCache,
  logger,
  performanceMonitor,
  formatDuration
} from './utils';

async function validateFile(filePath: string): Promise<ValidationResult> {
  // Логирование
  logger.info('Starting validation', { file: filePath });

  // Проверка кэша
  const cacheKey = `validation:${filePath}`;
  const cached = validationCache.get(cacheKey);
  if (cached) {
    logger.debug('Cache hit');
    return cached;
  }

  // Мониторинг производительности
  performanceMonitor.start();
  performanceMonitor.mark('start');

  try {
    // ... ваш код валидации ...

    const result: ValidationResult = {
      isValid: true,
      errors: [],
      filePath,
      timestamp: Date.now(),
      duration: performanceMonitor.elapsed(),
      fileSize: 1024,
      fileType: 'json',
      warningCount: 0,
      errorCount: 0,
      metrics: performanceMonitor.finalize()
    };

    // Сохранить в кэш
    validationCache.set(cacheKey, result, 1800000);

    // Вывод
    console.log(consoleFormatter.formatResult(result));

    logger.info('Validation completed', {
      isValid: result.isValid,
      duration: formatDuration(result.duration)
    });

    return result;
  } catch (error) {
    logger.error('Validation error', error as Error);
    throw error;
  }
}

// Использование
validateFile('/path/to/file.json')
  .then(result => {
    if (result.isValid) {
      console.log(colorFormatter.success('Validation passed!'));
    } else {
      console.log(colorFormatter.failure('Validation failed!'));
      result.errors.forEach(error => {
        const link = linkGenerator.generateErrorLink(error);
        console.log(link);
      });
    }
  });
```

## Конфигурация

### Отключить цвета

```typescript
import { colorFormatter } from './formatters';

colorFormatter.setEnabled(false);

// Или через environment
process.env.NO_COLOR = '1';
```

### Настроить логгер

```typescript
import { Logger, LogLevel } from './utils';

const logger = new Logger({
  level: LogLevel.DEBUG,
  outputFile: '/var/log/validator.log',
  enableConsole: true,
  enableColor: true
});
```

### Настроить кэш

```typescript
import { LRUCache } from './utils';

const cache = new LRUCache(1000, 3600000); // 1000 элементов, TTL 1 час
```

## Полезные команды

### Проверка типов

```bash
cd /Users/username/Scripts/vscode-validator-v2.3.1
tsc --noEmit
```

### Тесты

```bash
npm test
```

### Сборка

```bash
npm run build
```

## Файлы модулей

```
/Users/username/Scripts/vscode-validator-v2.3.1/src/
├── types/
│   ├── index.ts
│   └── README_v2.3.1.md
├── formatters/
│   ├── console-formatter.ts
│   ├── color-formatter.ts
│   ├── link-generator.ts
│   ├── index.ts
│   └── README_v2.3.1.md
└── utils/
    ├── cache.ts
    ├── logger.ts
    ├── performance.ts
    ├── index.ts
    └── README_v2.3.1.md
```

## Документация

- [Types README](/Users/username/Scripts/vscode-validator-v2.3.1/src/types/README_v2.3.1.md)
- [Formatters README](/Users/username/Scripts/vscode-validator-v2.3.1/src/formatters/README_v2.3.1.md)
- [Utils README](/Users/username/Scripts/vscode-validator-v2.3.1/src/utils/README_v2.3.1.md)
- [Delivery Report](/Users/username/Scripts/vscode-validator-v2.3.1/MODULE_DELIVERY_REPORT_v2.3.1.md)

## Поддержка

Все модули полностью типизированы и имеют TSDoc комментарии. Используйте автодополнение IDE для изучения API.
