# Core Module

Ядро модульного SDUI валидатора v2.3.1 с полной типизацией и dependency injection.

## Архитектура

```
core/
├── config.ts              # Управление конфигурацией
├── file-reader.ts         # Чтение файлов с кэшированием
├── position-map.ts        # Enhanced Position Map
├── validator.ts           # Главный класс валидатора
├── index.ts               # Публичный API
└── README.md              # Этот файл
```

## Основные компоненты

### ConfigManager

Централизованное управление конфигурацией с поддержкой переопределения.

```typescript
import { ConfigManager } from './core';

// Singleton instance с дефолтной конфигурацией
const config = ConfigManager.getInstance();

// Создание кастомной конфигурации
const customConfig = ConfigManager.create({
  output: { verbose: true, noColor: false },
  validation: { strictTypes: true }
});

// Доступ к настройкам
const projectRoot = config.get<string>('paths.projectRoot');
const isVerbose = config.isVerbose();
```

**Особенности:**
- Immutable конфигурация (deep freeze)
- Type-safe API
- Поддержка переменных окружения
- Singleton и factory patterns

### FileReader

Оптимизированное чтение файлов с автоопределением формата и кэшированием.

```typescript
import { FileReader } from './core';

const reader = new FileReader(config);

// Чтение файла
const result = reader.readFile('/path/to/contract.json');
console.log(result.content);
console.log(result.metadata.format); // FileFormat.JSON
console.log(result.readTimeMs);      // 5ms

// Чтение с кэшированием
const cachedResult = reader.readFileCached('/path/to/contract.json');

// Определение формата
const format = reader.detectFormat('/path/to/file.j2.java');
// => FileFormat.JINJA_JAVA

// Проверка Jinja шаблона
if (reader.isJinjaTemplate(filePath)) {
  // обработка Jinja
}
```

**Особенности:**
- Автоопределение формата (JSON, Jinja2/Java)
- Кэширование с валидацией актуальности
- Проверка размера файла
- Вычисление хэша содержимого
- Детальные метаданные

**Поддерживаемые форматы:**
- `.json` - стандартные JSON файлы
- `.j2.java` - Jinja2/Java шаблоны
- `.jinja.json` - Jinja2 JSON шаблоны

### PositionMap

Оптимизированная карта позиций для быстрого поиска строк/колонок по JSON paths.

```typescript
import { PositionMapBuilder } from './core';

const builder = new PositionMapBuilder(config);
const positionMap = builder.build(jsonText);

// Поиск по JSON Pointer (RFC 6901)
const result1 = positionMap.findByPointer('/components/0/type');
console.log(result1.position?.line);      // 42
console.log(result1.confidence);          // 'exact'

// Поиск по property path (lodash-style)
const result2 = positionMap.findByPath('components[0].type');
console.log(result2.position?.line);      // 42

// Упрощенный API
const lineNumber = positionMap.getLineNumber('components[0].type');
const posInfo = positionMap.getPositionInfo('components[0].type');

// Статистика
const stats = positionMap.getStats();
console.log(stats.pointerCount);          // 150
console.log(stats.buildTimeMs);           // 12ms
```

**Особенности:**
- O(n) построение за один проход
- O(1) поиск через Map
- Кэширование вложенных путей
- Отслеживание родительских связей
- Сохранение длины токенов
- Поддержка JSON Pointer и property paths

**Алгоритм:**
1. Посимвольный проход по JSON тексту
2. Отслеживание текущего пути через стек
3. Сохранение позиций с метаданными
4. Построение кэша для быстрого поиска
5. Индексация через Map для O(1) lookup

### SDUIValidator

Главный класс валидатора с dependency injection и расширяемой архитектурой.

```typescript
import { createValidator } from './core';

const validator = createValidator({
  output: { verbose: true }
});

// Валидация файла
const report = await validator.validateFile('/path/to/contract.json');

if (!report.valid) {
  console.error(`Found ${report.errors.length} errors:`);
  for (const error of report.errors) {
    console.error(`  ${error.line}:${error.column} - ${error.message}`);
  }
}

// Валидация JSON напрямую
const jsonReport = await validator.validateJSON(jsonObject);

// Добавление кастомного валидатора
class MyValidator implements IValidator {
  validate(context: ValidationContext): ValidationIssue[] {
    // кастомная логика валидации
    return [];
  }
}

validator.addValidator(new MyValidator());
```

**Особенности:**
- Dependency injection для всех зависимостей
- Расширяемость через IValidator интерфейс
- Immutable результаты
- Type-safe API
- Поддержка async валидаторов
- Детальная диагностика

**ValidationReport структура:**
```typescript
{
  valid: boolean,
  errors: ValidationIssue[],
  warnings: ValidationIssue[],
  webCompatibility: number,
  dataBindings?: DataBindingStats,
  versions?: ComponentVersionStats,
  validationTimeMs: number,
  filePath: string
}
```

## Factory Functions

### createValidator()

Создать валидатор с дефолтной конфигурацией:

```typescript
import { createValidator } from './core';

const validator = createValidator();
// или с переопределениями
const validator = createValidator({
  output: { verbose: true, noColor: false }
});
```

### createValidatorWithDeps()

Создать валидатор с кастомными зависимостями:

```typescript
import {
  createValidatorWithDeps,
  ConfigManager,
  FileReader,
  PositionMapBuilder
} from './core';

const config = ConfigManager.create({ /* ... */ });
const fileReader = new FileReader(config);
const positionMapBuilder = new PositionMapBuilder(config);

const validator = createValidatorWithDeps(
  config,
  fileReader,
  positionMapBuilder
);
```

## Типы и интерфейсы

### ErrorType

Типы валидационных ошибок:

```typescript
enum ErrorType {
  PARSE_ERROR = 'parse_error',
  SCHEMA_ERROR = 'schema_error',
  COMPONENT_NOT_FOUND = 'component_not_found',
  MISSING_REQUIRED_FIELD = 'missing_required_field',
  INVALID_VALUE = 'invalid_value',
  UNEXPECTED_FIELD = 'unexpected_field',
  TYPE_MISMATCH = 'type_mismatch',
  WEB_INCOMPATIBLE = 'web_incompatible',
  VERSION_ERROR = 'version_error',
  STATE_AWARE_ERROR = 'state_aware_error',
}
```

### Severity

Уровни серьезности:

```typescript
enum Severity {
  ERROR = 'error',
  WARNING = 'warning',
  INFO = 'info',
}
```

### ValidationIssue

Информация о проблеме:

```typescript
interface ValidationIssue {
  type: ErrorType;
  severity: Severity;
  message: string;
  pointer: string;        // JSON Pointer
  path: string;           // Property path
  line: number;
  column: number;
  component?: string;
  field?: string;
  sourceFile?: string;
  context?: Record<string, any>;
}
```

### IValidator

Интерфейс для создания кастомных валидаторов:

```typescript
interface IValidator {
  validate(context: ValidationContext):
    Promise<ValidationIssue[]> | ValidationIssue[];
}
```

## Примеры использования

### Базовая валидация

```typescript
import { createValidator } from './core';

const validator = createValidator();

try {
  const report = await validator.validateFile('./contract.json');

  if (report.valid) {
    console.log('✅ Contract is valid');
  } else {
    console.error('❌ Found errors:');
    report.errors.forEach(err => {
      console.error(`  Line ${err.line}: ${err.message}`);
    });
  }
} catch (error) {
  console.error('Validation failed:', error);
}
```

### Verbose режим

```typescript
const validator = createValidator({
  output: {
    verbose: true,
    showContext: true,
    contextLines: 3
  }
});

const report = await validator.validateFile('./contract.json');
// Детальный вывод с контекстом кода
```

### Кастомный валидатор

```typescript
import { IValidator, ValidationContext, ValidationIssue, ErrorType, Severity } from './core';

class BusinessRulesValidator implements IValidator {
  validate(context: ValidationContext): ValidationIssue[] {
    const issues: ValidationIssue[] = [];

    // Проверка бизнес-правил
    if (context.contract.amount && context.contract.amount > 1000000) {
      issues.push({
        type: ErrorType.INVALID_VALUE,
        severity: Severity.WARNING,
        message: 'Amount exceeds business limit',
        pointer: '/amount',
        path: 'amount',
        line: context.positionMap.getLineNumber('amount'),
        column: 1,
      });
    }

    return issues;
  }
}

const validator = createValidator();
validator.addValidator(new BusinessRulesValidator());
```

### Анализ data bindings

```typescript
const report = await validator.validateFile('./contract.json');

if (report.dataBindings?.hasBindings) {
  console.log(`Found ${report.dataBindings.totalBindings} bindings:`);
  console.log(`  - State: ${report.dataBindings.byType.state}`);
  console.log(`  - Data: ${report.dataBindings.byType.data}`);
  console.log(`  - Computed: ${report.dataBindings.byType.computed}`);
}
```

### Статистика компонентов

```typescript
const report = await validator.validateFile('./contract.json');

if (report.versions) {
  console.log(`Total components: ${report.versions.totalComponents}`);
  console.log('Unique types:', report.versions.uniqueTypes);
  console.log('By version:', report.versions.byVersion);
}
```

## Производительность

### Position Map

- Построение: O(n) где n - длина текста
- Поиск: O(1) через Map lookup
- Память: O(k) где k - количество ключей

**Benchmark:**
- 100KB JSON: ~10ms построение, ~0.1ms поиск
- 1MB JSON: ~50ms построение, ~0.1ms поиск

### File Reader

- Чтение с кэшем: ~0ms (cache hit)
- Чтение без кэша: зависит от размера файла
- Кэш инвалидируется по mtime

### Validator

- Зависит от количества и сложности валидаторов
- Типичная валидация: 10-100ms для средних контрактов

## Ограничения

1. **Jinja шаблоны**: Требуется интеграция Jinja парсера (TODO)
2. **Максимальный размер файла**: 1MB по умолчанию (настраивается)
3. **Максимальная глубина JSON**: 50 уровней (настраивается)

## Расширение функциональности

### Добавление нового валидатора

1. Реализовать интерфейс `IValidator`
2. Добавить через `validator.addValidator()`
3. Или передать в конструктор через dependency injection

### Добавление нового формата файлов

1. Расширить enum `FileFormat`
2. Обновить `detectFormat()` в FileReader
3. Добавить логику обработки в валидатор

### Кастомная конфигурация

1. Создать конфигурацию через `ConfigManager.create()`
2. Передать в конструкторы модулей
3. Использовать factory функции для удобства

## Best Practices

1. **Используйте factory functions** для создания валидаторов
2. **Переиспользуйте instances** ConfigManager, FileReader
3. **Добавляйте типы** для всех кастомных валидаторов
4. **Обрабатывайте ошибки** через try-catch
5. **Проверяйте report.valid** перед использованием
6. **Используйте кэширование** для повторных валидаций

## Версионирование

Следует семантическому версионированию (semver):
- **2** - major version
- **3** - minor version
- **1** - patch version

## Лицензия

Внутренний проект Альфа-Банка.
