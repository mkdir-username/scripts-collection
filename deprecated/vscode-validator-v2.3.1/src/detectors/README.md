# Detectors Module v1.0.0

Система детекторов ошибок для SDUI валидатора с поддержкой различных форматов запросов и путей.

## 📦 Компоненты

### 1. Error Field Detector (`error-field-detector.ts`)

Умный детектор полей с ошибками в SDUI контрактах.

**Возможности:**
- Определение точного поля ошибки из сообщения
- 12 паттернов распознавания ошибок
- Оценка уверенности (high/medium/low)
- Поддержка SDUI-специфичных ошибок
- Кэширование результатов
- Singleton паттерн

**Использование:**
```typescript
import { detectErrorField } from './detectors';

const result = detectErrorField(
  "Component ButtonView not found",
  "components[0]"
);

console.log(result.field);       // "type"
console.log(result.path);        // "components[0].type"
console.log(result.confidence);  // "high"
console.log(result.reason);      // "Component type error"
```

**Метрики:**
```typescript
import { getDetectorMetrics } from './detectors';

const metrics = getDetectorMetrics();
console.log(metrics.successfulDetections);
console.log(metrics.cacheHitRate);
console.log(metrics.byConfidence.high);
```

### 2. JQ Integration (`jq-integration.ts`)

Интеграция с jq для сложных JSON запросов.

**Возможности:**
- Выполнение jq запросов через shell
- Graceful fallback на нативный JavaScript
- Кэширование результатов
- Поддержка сложных фильтров
- Метрики производительности

**Требования:**
- jq должен быть установлен в системе (`brew install jq`)
- Для fallback режима зависимости не требуются

**Использование:**
```typescript
import { jq, isJQAvailable } from './detectors';

// Проверка доступности
if (await isJQAvailable()) {
  // Простой запрос
  const types = await jq(contract, '.components[].type');

  // Сложный фильтр
  const filtered = await jq(
    contract,
    '.components | map(select(.type == "ButtonView"))'
  );
}

// С fallback функцией
import { jqWithFallback } from './detectors';

const result = await jqWithFallback(
  contract,
  '.data.field',
  (obj) => obj.data?.field,
  { timeout: 3000 }
);
```

**Опции:**
```typescript
interface JQOptions {
  timeout?: number;      // Таймаут в мс (по умолчанию 5000)
  compact?: boolean;     // Компактный вывод
  raw?: boolean;         // Raw output (без кавычек)
  nullInput?: boolean;   // Не передавать JSON на вход
  forceFallback?: boolean; // Принудительно использовать fallback
}
```

### 3. JSONPath Integration (`jsonpath-integration.ts`)

Интеграция с JSONPath для точного поиска элементов.

**Возможности:**
- Стандартный синтаксис JSONPath
- Рекурсивный поиск
- Фильтрация элементов
- Кэширование результатов
- Нативная реализация (без внешних зависимостей)

**Поддерживаемый синтаксис:**
```
$                            // Корневой элемент
$.store.book                 // Дочерние элементы
$.store.book[0]              // Элемент массива
$.store.book[*]              // Все элементы массива
$..author                    // Рекурсивный поиск
$.store.*                    // Все дочерние элементы
$.store.book[?(@.price < 10)] // Фильтрация (базовая)
```

**Использование:**
```typescript
import { queryJSONPath } from './detectors';

// Простой запрос
const authors = queryJSONPath(data, '$.store.book[*].author');

// Рекурсивный поиск
const allPrices = queryJSONPath(data, '$..price');

// С фильтрацией
const cheap = queryJSONPath(
  data,
  '$.store.book[?(@.price < 10)]'
);

console.log(authors.data);    // Массив результатов
console.log(authors.count);   // Количество найденных
console.log(authors.method);  // 'native' | 'cache'
```

**С fallback:**
```typescript
import { queryJSONPathWithFallback } from './detectors';

const result = queryJSONPathWithFallback(
  data,
  '$.components[?(@.type == "ButtonView")]',
  (d) => d.components.filter(c => c.type === 'ButtonView')
);
```

### 4. Path Converter (`path-converter.ts`)

Конвертация между различными форматами путей.

**Поддерживаемые форматы:**
- JSON Pointer (RFC 6901): `/components/0/type`
- Property Path: `components[0].type`
- JSONPath: `$.components[0].type`
- jq: `.components[0].type`
- Dot notation: `components.0.type`

**Использование:**
```typescript
import {
  toJSONPointer,
  toPropertyPath,
  toJSONPath,
  toJQ,
  normalizePath,
  detectPathFormat
} from './detectors';

// Конвертация
const pointer = toJSONPointer('components[0].type');
// => "/components/0/type"

const propPath = toPropertyPath('/components/0/type');
// => "components[0].type"

const jsonPath = toJSONPath('components[0].type');
// => "$.components[0].type"

const jqPath = toJQ('components[0].type');
// => ".components[0].type"

// Нормализация (в Property Path)
const normalized = normalizePath('components.0.type');
// => "components[0].type"

// Определение формата
const format = detectPathFormat('/components/0/type');
// => "json-pointer"
```

**Опции:**
```typescript
interface ConversionOptions {
  validate?: boolean;   // Валидировать результат
  normalize?: boolean;  // Нормализовать перед конвертацией
  escape?: boolean;     // Экранировать спецсимволы
}

const pointer = toJSONPointer('path/with/slash', {
  escape: true,
  validate: true
});
```

## 🎯 Паттерны использования

### Интеграция всех детекторов

```typescript
import {
  detectErrorField,
  jq,
  queryJSONPath,
  toJSONPointer,
  getAllMetrics,
  clearAllCaches
} from './detectors';

// 1. Детекция поля ошибки
const errorInfo = detectErrorField(
  "Missing required field 'type'",
  "components[0]"
);

// 2. Конвертация пути
const pointer = toJSONPointer(errorInfo.path);

// 3. JQ запрос для получения значения
const value = await jq(contract, `.${errorInfo.path}`);

// 4. JSONPath для поиска всех похожих
const similar = queryJSONPath(
  contract,
  `$..${errorInfo.field}`
);

// 5. Получение метрик
const metrics = getAllMetrics();
console.log('Error detector:', metrics.errorFieldDetector);
console.log('JQ integration:', metrics.jqIntegration);

// 6. Очистка кэшей (при необходимости)
clearAllCaches();
```

### Graceful fallback pattern

```typescript
import { jqWithFallback, queryJSONPathWithFallback } from './detectors';

// Попытка через jq, fallback на нативный код
const result = await jqWithFallback(
  data,
  '.components | map(select(.type == "ButtonView"))',
  (d) => d.components.filter(c => c.type === 'ButtonView')
);

// Попытка через JSONPath, fallback на простой код
const authors = queryJSONPathWithFallback(
  data,
  '$.store.book[*].author',
  (d) => d.store.book.map(b => b.author)
);
```

## 📊 Метрики и диагностика

### Получение всех метрик

```typescript
import { getAllMetrics } from './detectors';

const metrics = getAllMetrics();

// Error Field Detector
console.log(`Детекций: ${metrics.errorFieldDetector.successfulDetections}`);
console.log(`Точность: ${metrics.errorFieldDetector.byConfidence.high}`);

// JQ
console.log(`JQ запросов: ${metrics.jqIntegration.jqUsage}`);
console.log(`Fallback: ${metrics.jqIntegration.fallbackUsage}`);

// JSONPath
console.log(`JSONPath запросов: ${metrics.jsonPathIntegration.totalQueries}`);
console.log(`Cache hit rate: ${metrics.jsonPathIntegration.cacheHitRate}%`);

// Path Converter
console.log(`Конвертаций: ${metrics.pathConverter.totalConversions}`);
```

### Диагностический отчет

```typescript
import { printDiagnosticReport } from './detectors';

// Печать полного отчета в консоль
await printDiagnosticReport();
```

Вывод:
```
╔═══════════════════════════════════════════════════════════════╗
║         DETECTORS DIAGNOSTIC REPORT                           ║
╚═══════════════════════════════════════════════════════════════╝

Timestamp: 2025-10-07T14:30:00.000Z

┌─ Error Field Detector ──────────────────────────────────────┐
│ Total requests:             127
│ Successful detections:      119
│ Cache hits:                  45
│ Cache hit rate:           35.43%
│ By confidence:
│   - High:                    87
│   - Medium:                  32
│   - Low:                      8
└─────────────────────────────────────────────────────────────┘

┌─ JQ Integration ────────────────────────────────────────────┐
│ Total queries:               42
│ JQ usage:                    38
│ Fallback usage:               4
│ Cache hits:                  12
│ Errors:                       0
│ Avg query time:           23.45ms
│ JQ available:                Yes
└─────────────────────────────────────────────────────────────┘

...
```

### Программный доступ к отчету

```typescript
import { generateDiagnosticReport } from './detectors';

const report = await generateDiagnosticReport();

// Сохранение в файл
import { writeFileSync } from 'fs';
writeFileSync(
  'diagnostic-report.json',
  JSON.stringify(report, null, 2)
);
```

## 🔧 Производительность

### Кэширование

Все детекторы используют кэширование для оптимизации:

```typescript
import { getAllCacheSizes } from './detectors';

const sizes = getAllCacheSizes();
console.log(`Total cache entries: ${sizes.total}`);
console.log(`Error detector: ${sizes.errorFieldDetector}`);
console.log(`JQ: ${sizes.jqIntegration}`);
console.log(`JSONPath: ${sizes.jsonPathIntegration}`);
console.log(`Path converter: ${sizes.pathConverter}`);
```

### Очистка кэшей

```typescript
import { clearAllCaches } from './detectors';

// Очистить все кэши
clearAllCaches();

// Или выборочно
import {
  ErrorFieldDetector,
  JQIntegration,
  JSONPathIntegration,
  PathConverter
} from './detectors';

ErrorFieldDetector.getInstance().clearCache();
JQIntegration.getInstance().clearCache();
```

### Сброс метрик

```typescript
import { resetAllMetrics } from './detectors';

resetAllMetrics();
```

## 🏗️ Архитектура

### Singleton паттерн

Все детекторы используют Singleton для:
- Единого состояния кэша
- Аккумуляции метрик
- Переиспользования экземпляров

```typescript
// Получение единственного экземпляра
const detector = ErrorFieldDetector.getInstance();

// Использование convenience функций (внутри используют getInstance)
const result = detectErrorField(message, path);
```

### Graceful fallback

Интеграции с внешними инструментами (jq) используют graceful fallback:

```typescript
// JQ
if (jq доступен в системе) {
  выполнить через shell
} else {
  использовать встроенную реализацию
}

// JSONPath
try {
  нативная реализация
} catch {
  fallback функция пользователя
}
```

### Метрики производительности

Все операции отслеживают:
- Время выполнения
- Количество запросов
- Использование кэша
- Ошибки

## 📝 TypeScript типы

Все модули полностью типизированы:

```typescript
// Error Field Detector
interface ErrorFieldInfo {
  field: string | null;
  path: string;
  confidence: 'high' | 'medium' | 'low';
  reason: string;
}

// JQ
interface JQResult<T = any> {
  data: T;
  method: 'jq' | 'fallback' | 'cache';
  executionTime: number;
  error?: string;
}

// JSONPath
interface JSONPathResult<T = any> {
  data: T[];
  method: 'native' | 'fallback' | 'cache';
  executionTime: number;
  count: number;
  error?: string;
}

// Path Converter
type PathFormat =
  | 'json-pointer'
  | 'property-path'
  | 'jsonpath'
  | 'jq'
  | 'dot-notation';
```

## 🧪 Тестирование

Примеры юнит-тестов:

```typescript
import {
  detectErrorField,
  toJSONPointer,
  queryJSONPath
} from './detectors';

describe('Error Field Detector', () => {
  it('should detect component type errors', () => {
    const result = detectErrorField(
      'Component ButtonView not found',
      'components[0]'
    );

    expect(result.field).toBe('type');
    expect(result.confidence).toBe('high');
  });
});

describe('Path Converter', () => {
  it('should convert property path to JSON pointer', () => {
    const pointer = toJSONPointer('components[0].type');
    expect(pointer).toBe('/components/0/type');
  });
});

describe('JSONPath Integration', () => {
  it('should find all elements by path', () => {
    const data = {
      store: {
        book: [
          { author: 'Author 1' },
          { author: 'Author 2' }
        ]
      }
    };

    const result = queryJSONPath(data, '$.store.book[*].author');
    expect(result.data).toEqual(['Author 1', 'Author 2']);
  });
});
```

## 📄 Лицензия

Часть проекта FMS SDUI Validator v2.3.1
