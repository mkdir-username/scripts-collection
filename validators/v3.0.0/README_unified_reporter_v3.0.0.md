# Unified Error Reporter v3.0.0

Унифицированный репортер ошибок для всех типов валидации SDUI контрактов.

## Возможности

### Поддерживаемые источники валидации

- **Metaschema** — Ruby validator (правила метасхемы)
- **SDUI** — MCP SDUI validator
- **Web Compatibility** — проверка поддержки Web платформы
- **StateAware** — валидация StateAware паттернов
- **Required Fields** — проверка обязательных полей
- **Data Binding** — анализ data binding выражений
- **Custom** — кастомные валидаторы

### Основные возможности

✅ **Множественные источники ошибок** — объединение ошибок из разных валидаторов
✅ **Группировка** — по компонентам, источникам, severity
✅ **Severity levels** — error, warning, info
✅ **Кликабельные ссылки** — формат `file:line:col` для IDE
✅ **Экспорт** — JSON, HTML, Markdown, Text
✅ **Цветной вывод** — в терминал
✅ **Плагинная архитектура** — кастомные форматтеры

## Установка

```bash
# Скопировать файл в проект
cp unified_reporter_v3.0.0.ts /path/to/your/project

# Импорт в TypeScript
import { UnifiedReporter, ValidationError } from './unified_reporter_v3.0.0';
```

## Быстрый старт

### Базовое использование

```typescript
import { UnifiedReporter, ValidationError } from './unified_reporter_v3.0.0';

// Создание репортера
const reporter = new UnifiedReporter();

// Создание ошибок
const errors: ValidationError[] = [
  {
    source: 'metaschema',
    severity: 'error',
    filePath: '/path/to/ButtonView.json',
    path: 'properties.title',
    message: 'Missing required field "title"',
    component: 'ButtonView',
    version: 'v2',
    suggestion: 'Add "title" property',
  },
];

// Создание отчета
const report = reporter.createReport('/path/to/ButtonView.json', errors);

// Вывод в консоль
reporter.print(report);

// Экспорт в JSON
const jsonOutput = await reporter.export(report, 'json');
console.log(jsonOutput);
```

### Интеграция с Ruby валидатором

```typescript
import { ErrorConverter } from './unified_reporter_v3.0.0';

// Вывод Ruby валидатора
const rubyOutput = [
  'SDUI/components/ButtonView/v2/ButtonView.json: invalid_schema: Missing required field "title"',
];

// Конвертация в ValidationError
const errors = rubyOutput
  .map(line => ErrorConverter.fromRuby(line, '/path/to/file.json'))
  .filter(e => e !== null);

const report = reporter.createReport('/path/to/file.json', errors);
reporter.print(report);
```

### Интеграция с MCP валидатором

```typescript
// RequiredFieldsValidator ошибки
const mcpErrors = [
  {
    path: 'root.content',
    component: 'DataView',
    version: 'v1',
    missingFields: ['dataContent'],
    severity: 'error' as const,
    suggestion: 'Add "dataContent" array',
  },
];

const errors = mcpErrors.map(e =>
  ErrorConverter.fromMcpRequiredField(e, '/path/to/contract.json')
);

const report = reporter.createReport('/path/to/contract.json', errors);
reporter.print(report);
```

## Конфигурация

```typescript
const reporter = new UnifiedReporter({
  // Вывод
  colorize: true,           // Цветной вывод в терминал
  verbose: false,           // Подробный режим
  groupBy: 'component',     // Группировка: 'component' | 'source' | 'severity' | 'none'

  // Форматирование
  showPath: true,           // Показывать JSONPath
  showJsonPointer: true,    // Показывать JSON Pointer (RFC 6901)
  showLineNumbers: true,    // Показывать номера строк
  showSuggestions: true,    // Показывать подсказки

  // Фильтрация
  minSeverity: 'info',      // Минимальный уровень: 'error' | 'warning' | 'info'
  includeSources: ['metaschema', 'sdui'], // Только эти источники
  excludeSources: ['data-binding'],       // Исключить эти источники

  // Экспорт
  exportFormats: ['json', 'html', 'markdown'], // Форматы экспорта
  outputDir: './reports',   // Директория для экспорта
});
```

## Форматтеры

### Встроенные форматтеры

#### 1. Text Formatter (по умолчанию)

```typescript
const report = reporter.createReport(filePath, errors);
reporter.print(report); // Вывод в консоль
```

**Вывод:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 ButtonView.json
📁 SDUI/components/ButtonView/v2/ButtonView.json
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ CONTRACT INVALID

📊 SUMMARY
   Errors   ........... 2
   Warnings ........... 1
   Infos    ........... 0

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ ERRORS: 2
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─ ButtonView ──────────────────────────────────────────────────────────────┐
│ 2 issues                                                                   │
└────────────────────────────────────────────────────────────────────────────┘

  ❌ [1] Missing required field "title"

      Path: properties.title
      JSON Pointer: /properties/title
      💡 Add "title" property with StateAware<string> value

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 2. JSON Formatter

```typescript
const jsonOutput = await reporter.export(report, 'json');
```

**Вывод:**

```json
{
  "filePath": "/path/to/ButtonView.json",
  "valid": false,
  "timestamp": "2025-10-05T10:30:00.000Z",
  "summary": {
    "errors": 2,
    "warnings": 1,
    "infos": 0
  },
  "errors": [
    {
      "source": "metaschema",
      "severity": "error",
      "message": "Missing required field \"title\"",
      "location": {
        "filePath": "/path/to/ButtonView.json",
        "line": 5,
        "path": "properties.title",
        "jsonPointer": "/properties/title"
      },
      "component": "ButtonView",
      "version": "v2",
      "suggestion": "Add \"title\" property"
    }
  ]
}
```

#### 3. Markdown Formatter

```typescript
const mdOutput = await reporter.export(report, 'markdown');
```

**Вывод:**

```markdown
# Validation Report: ButtonView.json

**File:** `/path/to/ButtonView.json`
**Status:** ❌ Invalid
**Date:** 2025-10-05T10:30:00.000Z

## Summary

| Metric | Count |
|--------|-------|
| Errors | 2 |
| Warnings | 1 |
| Infos | 0 |

## Errors

### 1. Missing required field "title"

**Component:** ButtonView (v2)
**Path:** `properties.title`
**Location:** /path/to/ButtonView.json:5

💡 **Suggestion:** Add "title" property with StateAware<string> value
```

#### 4. HTML Formatter

```typescript
const htmlOutput = await reporter.export(report, 'html');
```

Создает полностью стилизованный HTML отчет с:
- Адаптивным дизайном
- Цветовым кодированием severity
- Интерактивными элементами
- Готовым для публикации

### Кастомные форматтеры

Создайте свой форматтер, реализовав интерфейс `ErrorFormatter`:

```typescript
import { ErrorFormatter, ValidationReport, ReporterConfig } from './unified_reporter_v3.0.0';

class SlackFormatter implements ErrorFormatter {
  name = 'slack';
  supportsColor = false;

  format(report: ValidationReport, config: ReporterConfig): string {
    const blocks = [
      {
        type: 'header',
        text: {
          type: 'plain_text',
          text: `📄 Validation Report: ${report.filePath}`,
        },
      },
      {
        type: 'section',
        text: {
          type: 'mrkdwn',
          text: `*Status:* ${report.valid ? ':white_check_mark: Valid' : ':x: Invalid'}`,
        },
      },
      // ... остальные блоки
    ];

    return JSON.stringify({ blocks }, null, 2);
  }
}

// Регистрация
reporter.registerFormatter(new SlackFormatter());

// Использование
const slackOutput = await reporter.export(report, 'slack' as any);
```

## API Reference

### UnifiedReporter

#### Constructor

```typescript
constructor(config?: Partial<ReporterConfig>)
```

#### Методы

##### `createReport(filePath: string, errors: ValidationError[], metadata?: Record<string, any>): ValidationReport`

Создает отчет валидации из массива ошибок.

##### `print(report: ValidationReport, positionMap?: PositionMap): void`

Выводит отчет в консоль.

##### `export(report: ValidationReport, format: 'json' | 'html' | 'markdown' | 'text'): Promise<string>`

Экспортирует отчет в указанный формат.

##### `registerFormatter(formatter: ErrorFormatter): void`

Регистрирует кастомный форматтер.

##### Helper методы

```typescript
// Добавление ошибки из Ruby валидатора
addRubyError(filePath: string, path: string, ruleName: string, error: string): ValidationError

// Добавление ошибки из MCP валидатора
addMcpError(filePath: string, error: {...}): ValidationError

// Добавление ошибки web compatibility
addWebCompatError(filePath: string, path: string, message: string, component?: string): ValidationError
```

### ErrorConverter

Утилита для конвертации ошибок из разных форматов.

#### Методы

```typescript
// Ruby validator format: "path: rule_name: error"
static fromRuby(text: string, filePath: string): ValidationError | null

// MCP RequiredFieldError
static fromMcpRequiredField(error: {...}, filePath: string): ValidationError

// MCP StateAwareValidationError
static fromMcpStateAware(error: {...}, filePath: string): ValidationError
```

### Utility Functions

```typescript
// Извлечение компонента из сообщения
extractComponentFromMessage(message: string): string | null

// Извлечение поля ошибки из сообщения
extractErrorField(message: string): string | null

// Конвертация path -> JSON Pointer (RFC 6901)
pathToJsonPointer(path: string): string
```

## Типы

### ValidationError

```typescript
interface ValidationError {
  // Идентификация
  source: ValidationSource;
  severity: SeverityLevel;

  // Локация
  filePath: string;
  line?: number;
  column?: number;
  path?: string;           // JSONPath или dot notation
  jsonPointer?: string;    // RFC 6901 JSON Pointer

  // Содержимое
  message: string;
  code?: string;           // Код ошибки

  // Контекст
  component?: string;      // Имя компонента
  version?: string;        // Версия компонента
  field?: string;          // Конкретное поле

  // Дополнительная информация
  suggestion?: string;     // Подсказка
  relatedErrors?: string[]; // Связанные ошибки
  metadata?: Record<string, any>;
}
```

### ValidationReport

```typescript
interface ValidationReport {
  filePath: string;
  valid: boolean;

  errors: ValidationError[];
  warnings: ValidationError[];
  infos: ValidationError[];

  totalErrors: number;
  totalWarnings: number;
  totalInfos: number;

  bySource: Map<ValidationSource, ValidationError[]>;
  byComponent: Map<string, ValidationError[]>;
  bySeverity: Map<SeverityLevel, ValidationError[]>;

  timestamp: Date;
  duration?: number;
  metadata?: Record<string, any>;
}
```

## Примеры использования

### 1. Комбинированный отчет (все источники)

```typescript
const errors: ValidationError[] = [
  // Ruby validator
  {
    source: 'metaschema',
    severity: 'error',
    filePath: '/path/to/contract.json',
    path: 'root.type',
    message: 'Component ButtonView not found',
    line: 5,
  },

  // Required fields
  {
    source: 'required-fields',
    severity: 'error',
    filePath: '/path/to/contract.json',
    path: 'root.content',
    component: 'ButtonView',
    message: 'Missing required fields: title, content',
    line: 8,
  },

  // StateAware
  {
    source: 'stateaware',
    severity: 'warning',
    filePath: '/path/to/contract.json',
    path: 'root.backgroundColor',
    message: 'Incomplete Control pattern',
    line: 15,
  },
];

const report = reporter.createReport('/path/to/contract.json', errors);
reporter.print(report);
```

### 2. Фильтрация по severity

```typescript
// Показываем только errors
const reporter = new UnifiedReporter({
  minSeverity: 'error',
});

const report = reporter.createReport(filePath, allErrors);
// В отчете будут только errors, warnings и infos отфильтрованы
```

### 3. Группировка по источнику

```typescript
const reporter = new UnifiedReporter({
  groupBy: 'source',
});

const report = reporter.createReport(filePath, errors);
reporter.print(report);
// Ошибки сгруппированы по источникам: metaschema, sdui, web-compat, etc.
```

### 4. Экспорт в несколько форматов

```typescript
const report = reporter.createReport(filePath, errors);

// JSON для CI/CD
const jsonOutput = await reporter.export(report, 'json');
await fs.writeFile('./reports/report.json', jsonOutput);

// HTML для просмотра в браузере
const htmlOutput = await reporter.export(report, 'html');
await fs.writeFile('./reports/report.html', htmlOutput);

// Markdown для документации
const mdOutput = await reporter.export(report, 'markdown');
await fs.writeFile('./reports/report.md', mdOutput);
```

## Интеграция с существующими валидаторами

### Ruby validator (FMS metaschema)

```typescript
import { execSync } from 'child_process';
import { ErrorConverter } from './unified_reporter_v3.0.0';

// Запуск Ruby валидатора
const output = execSync('ruby validator/validator.rb', { encoding: 'utf-8' });

// Парсинг вывода
const lines = output.split('\n').filter(line => line.trim());
const errors = lines
  .map(line => ErrorConverter.fromRuby(line, filePath))
  .filter(e => e !== null);

const report = reporter.createReport(filePath, errors);
reporter.print(report);
```

### MCP SDUI Validator

```typescript
import { RequiredFieldsValidator } from './validators/required-fields-validator';
import { StateAwareValidator } from './validators/stateaware-validator';
import { ErrorConverter } from './unified_reporter_v3.0.0';

// Required fields валидация
const requiredValidator = new RequiredFieldsValidator(schemaIndex);
const requiredReport = requiredValidator.validateContract(contract);

// StateAware валидация
const stateAwareValidator = new StateAwareValidator();
const stateAwareResults = stateAwareValidator.validateComponentStateAware(contract, 'ButtonView');

// Конвертация в ValidationError
const errors: ValidationError[] = [
  ...requiredReport.errors.map(e =>
    ErrorConverter.fromMcpRequiredField(e, filePath)
  ),
  ...stateAwareResults.flatMap(r =>
    r.errors.map(e => ErrorConverter.fromMcpStateAware(e, filePath))
  ),
];

const report = reporter.createReport(filePath, errors);
reporter.print(report);
```

## Best Practices

### 1. Группировка ошибок

Выбирайте группировку в зависимости от контекста:

- **`groupBy: 'component'`** — для разработчиков (по компонентам)
- **`groupBy: 'source'`** — для анализа валидаторов
- **`groupBy: 'severity'`** — для приоритизации исправлений
- **`groupBy: 'none'`** — для простого списка

### 2. Severity levels

Используйте правильные уровни:

- **`error`** — контракт невалиден, требует исправления
- **`warning`** — потенциальные проблемы, рекомендуется исправить
- **`info`** — информационные сообщения (data bindings, статистика)

### 3. Подсказки (suggestions)

Всегда добавляйте подсказки для критичных ошибок:

```typescript
{
  severity: 'error',
  message: 'Missing required field "title"',
  suggestion: 'Add "title" property with StateAware<string> value',
}
```

### 4. Метаданные

Используйте метаданные для дополнительного контекста:

```typescript
{
  message: 'Missing required fields: title, content',
  metadata: {
    missingFields: ['title', 'content'],
    componentVersion: 'v2',
  },
}
```

## Производительность

- **Position Map** — кэшируется для быстрого поиска строк
- **Группировка** — O(n) по количеству ошибок
- **Экспорт** — ленивый (создается только при вызове `export()`)

## Совместимость

- **TypeScript** — 4.5+
- **Node.js** — 16+
- **ES Modules** — поддерживается

## Changelog

### v3.0.0 (2025-10-05)

- ✅ Первый релиз
- ✅ Поддержка множественных источников валидации
- ✅ Плагинная архитектура форматтеров
- ✅ Экспорт в JSON/HTML/Markdown/Text
- ✅ Группировка по component/source/severity
- ✅ Интеграция с Ruby и MCP валидаторами

## Roadmap

- [ ] CSV formatter
- [ ] JUnit XML formatter (для CI/CD)
- [ ] Коллекция severity (автоматическое повышение)
- [ ] Дедупликация ошибок
- [ ] Diff между двумя отчетами
- [ ] Web UI для просмотра отчетов

## Авторы

Unified Error Reporter v3.0.0
Created: 2025-10-05

## Лицензия

MIT
