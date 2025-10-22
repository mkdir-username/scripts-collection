# Product Requirements Document: VSCode Validator v2.3.0

**Проект:** VSCode On-Save SDUI Validator
**Версия:** v2.3.0
**Дата:** 2025-10-05
**Автор:** Requirements Analysis
**Статус:** Draft для утверждения

---

## Оглавление

1. [Executive Summary](#executive-summary)
2. [Problem Statement](#problem-statement)
3. [Stakeholders](#stakeholders)
4. [Requirements](#requirements)
   - [Functional Requirements](#functional-requirements)
   - [Non-Functional Requirements](#non-functional-requirements)
   - [Architecture Requirements](#architecture-requirements)
   - [Testing Requirements](#testing-requirements)
5. [Success Metrics](#success-metrics)
6. [Scope & Timeline](#scope--timeline)
7. [Risks & Mitigation](#risks--mitigation)
8. [Assumptions](#assumptions)
9. [Open Questions](#open-questions)

---

## Executive Summary

Валидатор vscode-validate-on-save нуждается в расширении для поддержки нового формата файлов `.j2.json` (JSON + Jinja2 + комментарии-импорты). Текущая версия v2.2.0 работает только с pure JSON, что блокирует валидацию модульных SDUI контрактов с динамическими зависимостями.

**Ключевые цели v2.3.0:**
- Поддержка формата `.j2.json` с Jinja2 шаблонами
- Обработка комментариев-импортов вида `// [Title](file:///path/to/file.json)`
- Интеграция с существующим Jinja Hot Reload pipeline
- Сохранение обратной совместимости с pure JSON
- Точное position tracking для смешанного формата

---

## Problem Statement

### Current Situation

**v2.2.0 Ограничения:**
- ❌ Не поддерживает `.j2.json` формат
- ❌ Не обрабатывает Jinja2 синтаксис (`{{ variable }}`, `{% if %}`, `{% include %}`)
- ❌ Игнорирует комментарии-импорты `// [Title](file:///path)`
- ❌ Не может валидировать модульные контракты с зависимостями
- ❌ JSON.parse() падает на смешанном формате

**Пример проблемного файла:**

```json
{
  // [Стопка монет](file:///Users/username/Documents/FMS_GIT/_JSON/WEB/payroll/1.0_main_screen/desktop/parts/Coins.json)
  "rootElement": {
    "type": "StackView",
    "content": {
      "children": [
        {% include 'parts/header.j2' %},
        {{ dynamic_content }},
        // [Footer](file:///path/to/footer.json)
      ]
    }
  }
}
```

### Impact

**Блокируемые workflow:**
1. Невозможность валидировать модульные контракты перед сохранением
2. Разработчики вынуждены вручную запускать `jinja_hot_reload_v3.7.0.py` + валидатор
3. Отсутствие моментальной обратной связи в VSCode
4. Рост числа ошибок в production контрактах

**Частота проблемы:**
- 70% контрактов в `/payroll/` используют `.j2.json` формат
- ~200 файлов требуют валидации с Jinja2 обработкой

### Desired Outcome

**После внедрения v2.3.0:**
- ✅ Автоматическая валидация `.j2.json` при сохранении в VSCode
- ✅ Прозрачная обработка Jinja2 → JSON → валидация
- ✅ Кликабельные ссылки на ошибки с учетом Jinja2 преобразований
- ✅ Совместимость с существующими `.json` файлами
- ✅ Интеграция с `jinja_hot_reload_v3.7.0.py` pipeline

---

## Stakeholders

### Primary Stakeholders

| Role | Name | Needs | Concerns |
|------|------|-------|----------|
| SDUI Developer | Команда разработки | Моментальная валидация .j2.json, точные error positions | Производительность, не сломать текущий workflow |
| Product Owner | Tech Lead | Снижение числа ошибок в контрактах, ускорение разработки | ROI, timeline, риски регрессии |
| DevOps | CI/CD Team | Интеграция в build pipeline, автоматизация | Стабильность, версионирование |

### Secondary Stakeholders

| Stakeholder | Interest | Impact |
|-------------|----------|--------|
| QA Team | Раннее выявление ошибок в контрактах | High |
| Support Team | Меньше багов в production | Medium |
| Documentation Team | Обновление README и руководств | Low |

### Stakeholder Communication Plan

- **Weekly:** Status updates в Slack #sdui-validators
- **Bi-weekly:** Demo v2.3.0 прототипа
- **Before release:** Sign-off от Tech Lead + QA

---

## Requirements

### Functional Requirements

#### FR-1: Jinja2 Template Processing

**Priority:** CRITICAL
**User Story:** Как SDUI разработчик, я хочу, чтобы валидатор автоматически обрабатывал Jinja2 синтаксис, чтобы валидировать .j2.json файлы без ручных шагов.

**Acceptance Criteria:**

**Scenario 1: Pure Jinja2 Template Detection**
- Given файл начинается с `{# comment #}` или содержит `{% ... %}`
- When валидатор читает файл
- Then валидатор определяет формат как Jinja2
- And вызывает Jinja2 renderer ПЕРЕД JSON парсингом

**Scenario 2: Mixed Jinja+JSON Processing**
- Given файл содержит `{{ variable }}` внутри JSON структуры
- When валидатор обрабатывает файл
- Then валидатор рендерит Jinja2 теги с контекстом
- And парсит результат как валидный JSON
- And сохраняет mapping между original positions и rendered positions

**Scenario 3: Include Directives Resolution**
- Given файл содержит `{% include 'parts/header.j2' %}`
- When валидатор обрабатывает файл
- Then валидатор резолвит include относительно parent directory
- And отслеживает зависимости для dependency graph

**Dependencies:**
- Интеграция с `jinja_hot_reload_v3.7.0.py` (Jinja2 engine + filters)
- FileSystemLoader для резолва include paths

**Constraints:**
- Jinja2 рендеринг должен быть < 100ms для 50KB файла
- Поддержка всех custom filters из v3.7.0 (`now`, `formatCurrency`, `tojson`, etc.)

**Technical Notes:**

```typescript
interface Jinja2Processor {
  // Определяет, является ли файл Jinja2 шаблоном
  isJinja2Template(content: string): boolean;

  // Рендерит Jinja2 → JSON с контекстом
  renderTemplate(
    filePath: string,
    content: string,
    context?: Record<string, any>
  ): {
    rendered: string;
    sourceMap: PositionMapping;
    dependencies: string[];
  };

  // Получает контекст из .json/.yaml файла или генерирует smart context
  getContext(filePath: string): Record<string, any>;
}
```

---

#### FR-2: Comment-Import Processing

**Priority:** CRITICAL
**User Story:** Как SDUI разработчик, я хочу использовать комментарии-импорты `// [Title](file:///path)`, чтобы модульно структурировать контракты с визуальной документацией.

**Acceptance Criteria:**

**Scenario 1: Markdown-Style Import Detection**
- Given строка содержит `// [Title](file:///absolute/path/to/file.json)`
- When валидатор парсит комментарии
- Then валидатор извлекает path из `(file:///.../file.json)`
- And валидирует существование файла
- And добавляет файл в dependency graph

**Scenario 2: Import Inline Expansion**
- Given комментарий-импорт указывает на валидный JSON файл
- When валидатор обрабатывает импорт
- Then валидатор читает содержимое импортированного файла
- And встраивает JSON на место комментария
- And сохраняет source mapping для error reporting

**Scenario 3: Nested Imports Resolution**
- Given импортированный файл сам содержит импорты
- When валидатор обрабатывает nested imports
- Then валидатор рекурсивно резолвит все зависимости
- And детектирует циклические зависимости
- And выдает ошибку при circular dependency

**Scenario 4: Invalid Import Handling**
- Given комментарий-импорт указывает на несуществующий файл
- When валидатор проверяет импорт
- Then валидатор выдает WARNING с путем к несуществующему файлу
- And продолжает валидацию остального контракта

**Error Handling:**
- File not found → WARNING, skip import
- Circular dependency → ERROR, abort validation
- Invalid JSON in imported file → ERROR with file path

**Technical Notes:**

```typescript
interface ImportProcessor {
  // Регулярное выражение для детекции импортов
  IMPORT_PATTERN: RegExp; // \/\/ \[(.*?)\]\((file:\/\/\/.*?\.json)\)/g

  // Парсинг всех импортов в файле
  parseImports(content: string): ImportDeclaration[];

  // Резолв импорта с чтением файла
  resolveImport(importPath: string, parentPath: string): {
    content: string;
    dependencies: string[];
  };

  // Детекция циклических зависимостей
  detectCircularDependencies(graph: DependencyGraph): string[] | null;

  // Встраивание импортов в основной файл
  expandImports(
    content: string,
    imports: Map<string, string>
  ): {
    expanded: string;
    sourceMap: PositionMapping;
  };
}

interface ImportDeclaration {
  title: string;        // "Стопка монет"
  path: string;         // "file:///Users/.../Coins.json"
  lineNumber: number;   // Строка с комментарием
  replacement: string;  // JSON content для встраивания
}
```

---

#### FR-3: Position Tracking для Mixed Format

**Priority:** HIGH
**User Story:** Как SDUI разработчик, я хочу получать точные номера строк ошибок в оригинальном .j2.json файле, чтобы быстро исправлять проблемы.

**Acceptance Criteria:**

**Scenario 1: Source Mapping для Jinja2**
- Given Jinja2 template рендерится в JSON
- When валидатор строит position map
- Then валидатор сохраняет mapping `{rendered_line → original_line}`
- And используйет original_line в error links

**Scenario 2: Multi-Level Source Maps**
- Given файл содержит Jinja2 + imports
- When происходит ошибка в импортированном файле
- Then валидатор сообщает path к импортированному файлу + строку в нем
- And в основном файле указывает строку с комментарием-импортом

**Scenario 3: Fallback для Unmapped Positions**
- Given position не может быть смаплена на оригинальный файл
- When валидатор формирует error link
- Then валидатор использует fallback стратегию: closest parent → L1
- And добавляет warning `⚠️ Position approximate`

**Technical Notes:**

```typescript
interface PositionMapping {
  // Mapping: rendered position → original position
  toOriginal(renderedLine: number, renderedCol: number): PositionInfo;

  // Mapping: original position → rendered position
  toRendered(originalLine: number, originalCol: number): PositionInfo;

  // Информация об источнике (main file vs imported file)
  getSource(position: PositionInfo): {
    filePath: string;      // Абсолютный путь к файлу-источнику
    lineInSource: number;  // Строка в файле-источнике
    type: 'main' | 'import' | 'jinja';
  };
}

interface EnhancedPositionMap extends PositionMap {
  // Оригинальный position map (из v2.2.0)
  base: PositionMap;

  // Source maps для трансформаций
  jinja2SourceMap?: SourceMap;     // Jinja2 → JSON
  importSourceMaps?: Map<string, SourceMap>;  // Imports expansions

  // Unified поиск с fallback
  findLineNumber(path: string, pointer: string): {
    line: number;
    file: string;
    confidence: 'exact' | 'parent' | 'approximate';
  };
}
```

---

#### FR-4: Backward Compatibility с Pure JSON

**Priority:** CRITICAL
**User Story:** Как SDUI разработчик, я хочу, чтобы v2.3.0 работал с существующими .json файлами, чтобы не сломать текущий workflow.

**Acceptance Criteria:**

**Scenario 1: Pure JSON Fast Path**
- Given файл имеет расширение `.json` (не `.j2.json`)
- And файл не содержит Jinja2 синтаксиса
- When валидатор обрабатывает файл
- Then валидатор использует fast path (прямой JSON.parse)
- And НЕ вызывает Jinja2 processor
- And производительность идентична v2.2.0

**Scenario 2: Auto-Detection Jinja2 в .json Files**
- Given файл `.json` содержит `{{ ... }}` или `{% ... %}`
- When валидатор детектирует Jinja2 синтаксис
- Then валидатор выдает INFO: "Detected Jinja2, consider renaming to .j2.json"
- And обрабатывает файл через Jinja2 pipeline

**Scenario 3: CLI Flags Compatibility**
- Given v2.2.0 вызывается как `node validator.js <file>`
- When используется v2.3.0 с тем же синтаксисом
- Then валидатор работает идентично
- And все существующие VSCode tasks.json работают без изменений

**Constraints:**
- 0% регрессия производительности для pure JSON
- Все тесты v2.2.0 проходят на v2.3.0

---

#### FR-5: Smart Context Generation

**Priority:** MEDIUM
**User Story:** Как SDUI разработчик, я хочу, чтобы валидатор автоматически генерировал контекст для Jinja2 переменных, чтобы не создавать отдельные .json/.yaml файлы для тестовых данных.

**Acceptance Criteria:**

**Scenario 1: Auto-Context из Template Variables**
- Given Jinja2 template содержит `{{ user.name }}`
- And нет явного context файла
- When валидатор рендерит template
- Then валидатор генерирует smart context: `{"user": {"name": "TestUser"}}`
- And использует SafeDebugUndefined для undefined переменных

**Scenario 2: Explicit Context File**
- Given рядом с `contract.j2.json` есть `contract.context.json`
- When валидатор обрабатывает файл
- Then валидатор загружает context из `contract.context.json`
- And мерджит с auto-generated context

**Scenario 3: CLI Context Override**
- Given валидатор вызывается с `--context /path/to/context.json`
- When валидатор рендерит template
- Then валидатор использует provided context
- And игнорирует auto-generated context

**Technical Notes:**

```typescript
interface ContextProvider {
  // Загрузка context из файла
  loadContextFile(templatePath: string): Record<string, any> | null;

  // Генерация smart context из template
  generateSmartContext(templateContent: string): Record<string, any>;

  // Мердж контекстов (explicit > auto-generated)
  mergeContexts(...contexts: Record<string, any>[]): Record<string, any>;
}
```

---

### Non-Functional Requirements

#### NFR-1: Performance

**Target Metrics:**

| Operation | Target | Constraint |
|-----------|--------|------------|
| Pure JSON validation | < 200ms (95th %ile) | Не хуже v2.2.0 |
| .j2.json validation (< 50KB) | < 500ms (95th %ile) | +300ms overhead допустим |
| Jinja2 rendering | < 100ms | Для 50KB template |
| Import resolution | < 50ms per import | Max 20 imports per file |
| Position map build | < 20ms | Для 50KB file |

**Performance Requirements:**

**PR-1.1: Jinja2 Rendering Performance**
- Jinja2 engine ДОЛЖЕН кешировать compiled templates
- Cache invalidation при изменении файла или зависимостей
- Max memory overhead: +50MB для cache

**PR-1.2: Import Resolution Performance**
- Import files ДОЛЖНЫ кешироваться
- Parallel resolution для independent imports
- Timeout 5s для полного resolution graph

**PR-1.3: Position Mapping Performance**
- Source maps ДОЛЖНЫ строиться инкрементально
- O(1) lookup для position translation
- Memory: O(n) где n = количество строк

**Constraints:**
- Валидация 239KB файла: < 1s total
- Memory footprint: < 200MB для 100 файлов в cache

---

#### NFR-2: Reliability

**Availability:** 99.9% success rate для валидных контрактов

**Error Handling Requirements:**

**ER-1: Graceful Degradation**
- Jinja2 rendering error → WARNING, показать template AS-IS
- Import file missing → WARNING, skip import, продолжить валидацию
- Circular dependency → ERROR, abort с диагностикой цикла
- JSON parse error → ERROR с точной позицией (даже в rendered content)

**ER-2: Error Recovery**
- Partial validation при ошибках импорта
- Rollback на pure JSON mode при Jinja2 failure
- Detailed diagnostics для всех ошибок

**ER-3: Data Validation**
- Проверка всех file paths на существование ДО чтения
- Валидация JSON syntax ПОСЛЕ Jinja2 rendering
- Sandbox для Jinja2 execution (no filesystem write, no exec)

---

#### NFR-3: Maintainability

**Code Quality:**
- TypeScript strict mode enabled
- 100% type coverage для public API
- JSDoc для всех exported функций
- Zero ESLint warnings

**Testing Coverage:**
- Unit tests: > 80% coverage
- Integration tests: все critical paths
- Regression tests: все v2.2.0 тесты проходят

**Documentation:**
- README с примерами .j2.json usage
- API documentation для новых интерфейсов
- Migration guide v2.2.0 → v2.3.0

---

#### NFR-4: Compatibility

**Backward Compatibility:**
- v2.3.0 ДОЛЖЕН работать как drop-in replacement для v2.2.0
- Все существующие .json файлы валидируются без изменений
- CLI интерфейс полностью совместим

**Forward Compatibility:**
- Extensible architecture для будущих форматов
- Plugin system для custom processors
- Versioned configuration

**Platform Support:**
- Node.js >= 18.0.0
- VSCode >= 1.80.0
- macOS, Linux, Windows

**Dependencies:**
- Jinja2: через Python bridge или JS порт (nunjucks?)
- Existing MCP validator: alfa-sdui-mcp v1.x.x
- TypeScript >= 5.0.0

---

#### NFR-5: Security

**Security Requirements:**

**SEC-1: Path Traversal Prevention**
- Все file paths ДОЛЖНЫ резолвиться относительно PROJECT_ROOT
- Запрет на `../` escaping из PROJECT_ROOT
- Whitelist допустимых директорий для imports

**SEC-2: Jinja2 Sandbox**
- Запрет опасных Jinja2 функций (eval, exec, open)
- Ограничение доступа к filesystem (read-only)
- Timeout 5s для Jinja2 rendering

**SEC-3: Input Validation**
- Sanitization всех user-provided paths
- Валидация context data перед Jinja2 rendering
- Protection от XXE attacks в JSON parsing

---

### Architecture Requirements

#### AR-1: Modular Pipeline Architecture

**Architecture Pattern:** Pipeline с этапами обработки

```typescript
// Высокоуровневая архитектура
class ValidationPipeline {
  stages: ValidationStage[] = [
    new FileLoaderStage(),
    new FormatDetectionStage(),
    new Jinja2ProcessingStage(),   // NEW
    new ImportResolutionStage(),   // NEW
    new JSONParsingStage(),
    new PositionMappingStage(),    // ENHANCED
    new SDUIValidationStage(),
    new ErrorFormattingStage()
  ];

  async execute(filePath: string): Promise<ValidationReport> {
    let context = { filePath, content: null };

    for (const stage of this.stages) {
      context = await stage.process(context);
      if (context.shouldAbort) break;
    }

    return context.report;
  }
}
```

**Stage Responsibilities:**

1. **FileLoaderStage**: Чтение файла, определение encoding
2. **FormatDetectionStage**: Детекция .json vs .j2.json, pure JSON vs mixed
3. **Jinja2ProcessingStage** (NEW): Рендеринг Jinja2 templates
4. **ImportResolutionStage** (NEW): Резолв и встраивание импортов
5. **JSONParsingStage**: Парсинг финального JSON
6. **PositionMappingStage**: Построение enhanced position map
7. **SDUIValidationStage**: Валидация через alfa-sdui-mcp
8. **ErrorFormattingStage**: Форматирование вывода

**Benefits:**
- Каждый stage изолирован и тестируется независимо
- Легко добавить новые stages (например, YAML support)
- Debugging через stage-by-stage execution

---

#### AR-2: Source Map Architecture

**Source Map Hierarchy:**

```typescript
// Многослойная система source maps
interface SourceMapLayer {
  type: 'jinja2' | 'import' | 'base';
  sourceFile: string;
  targetFile: string;
  mappings: PositionMapping;
}

class LayeredSourceMap {
  layers: SourceMapLayer[] = [];

  // Добавление нового слоя трансформации
  addLayer(layer: SourceMapLayer): void;

  // Резолв финальной позиции через все слои
  resolvePosition(finalLine: number, finalCol: number): {
    sourceFile: string;
    sourceLine: number;
    sourceCol: number;
    transformationChain: string[];  // ['jinja2', 'import', 'base']
  };

  // Обратный резолв (source → final)
  reverseResolve(sourceFile: string, sourceLine: number): {
    finalLine: number;
    finalCol: number;
  };
}
```

**Example Transformation Chain:**

```
Original .j2.json (L42)
  ↓ Jinja2 rendering
Intermediate JSON (L38)
  ↓ Import expansion
Final JSON (L156)
  ↓ Validation error at L156
Resolved back to .j2.json L42
```

---

#### AR-3: Cache Strategy

**Multi-Level Caching:**

```typescript
interface CacheLayer {
  // L1: In-memory cache для текущей сессии
  memoryCache: Map<string, CachedEntry>;

  // L2: Persistent cache на диске (опционально)
  diskCache?: FileSystemCache;

  // Cache invalidation
  invalidate(filePath: string, reason: InvalidationReason): void;

  // Dependency tracking для cascading invalidation
  dependencyGraph: DependencyGraph;
}

interface CachedEntry {
  filePath: string;
  mtime: number;               // Для invalidation по timestamp
  contentHash: string;         // Для invalidation по содержимому

  // Кешированные результаты
  jinja2Rendered?: string;
  importsResolved?: Map<string, string>;
  positionMap?: EnhancedPositionMap;
  validationReport?: ValidationReport;

  // Metadata
  dependencies: string[];      // Файлы, от которых зависит этот
  dependents: string[];        // Файлы, которые зависят от этого
}
```

**Cache Invalidation Strategy:**

1. **On File Change:** Invalidate entry + all dependents
2. **On Dependency Change:** Cascading invalidation вверх по графу
3. **On Memory Pressure:** LRU eviction
4. **On Version Change:** Clear all cache при обновлении validator

---

#### AR-4: Integration с Jinja Hot Reload

**Shared Components:**

Вместо дублирования логики, интегрировать с `jinja_hot_reload_v3.7.0.py`:

```typescript
// Bridge к Python Jinja processor
class PythonJinjaBridge {
  pythonScript = '/Users/username/Scripts/Python/utils/jinja_hot_reload_v3.7.0.py';

  async renderTemplate(
    templatePath: string,
    context?: Record<string, any>
  ): Promise<{
    rendered: string;
    fixes: AutoFixReport[];  // Из SmartJSONFixer
    dependencies: string[];
  }> {
    // Вызов Python script через child_process
    const result = await execPython([
      this.pythonScript,
      '--render-only',
      '--template', templatePath,
      '--context', JSON.stringify(context),
      '--output-format', 'json'
    ]);

    return JSON.parse(result.stdout);
  }
}

// Альтернатива: Pure TypeScript Jinja (nunjucks)
class NunjucksJinjaProcessor {
  env: nunjucks.Environment;

  constructor(searchPaths: string[]) {
    this.env = nunjucks.configure(searchPaths, {
      autoescape: false,
      trimBlocks: true,
      lstripBlocks: true
    });

    // Регистрация custom filters из jinja_hot_reload
    this.registerCustomFilters();
  }

  renderTemplate(content: string, context: any): string {
    return this.env.renderString(content, context);
  }
}
```

**Decision:** Использовать Nunjucks для чистоты TypeScript stack, но обеспечить feature parity с Python Jinja filters.

---

#### AR-5: Error Reporting Architecture

**Enhanced Error Format:**

```typescript
interface ValidationError {
  // Базовые поля (из v2.2.0)
  path: string;              // JSON path
  message: string;
  pointer: string;           // JSON Pointer

  // Новые поля для v2.3.0
  sourceLocation: {
    file: string;            // Абсолютный путь к файлу-источнику
    line: number;            // Строка в оригинальном файле
    column: number;
    excerpt: string;         // 3 строки контекста
  };

  transformationChain?: {
    original: PositionInfo;  // Позиция в .j2.json
    jinja2: PositionInfo;    // Позиция после Jinja2 rendering
    import: PositionInfo;    // Позиция после import expansion
    final: PositionInfo;     // Позиция в финальном JSON
  };

  confidence: 'exact' | 'parent' | 'approximate';

  // Кликабельная ссылка
  link: string;              // "file:///path#L42:15"
}
```

**Error Context Extraction:**

```typescript
interface ErrorContextExtractor {
  // Извлечение 3 строк контекста вокруг ошибки
  extractContext(
    filePath: string,
    line: number,
    linesAround: number = 1
  ): {
    before: string[];
    errorLine: string;
    after: string[];
    lineNumbers: number[];
  };

  // Форматирование с подсветкой синтаксиса
  formatWithHighlight(context: ErrorContext): string;
}
```

---

### Testing Requirements

#### TR-1: Unit Testing

**Test Coverage Requirements:**

| Component | Coverage Target | Priority |
|-----------|----------------|----------|
| Jinja2Processor | > 90% | Critical |
| ImportProcessor | > 90% | Critical |
| PositionMapping | > 85% | High |
| FormatDetection | > 80% | High |
| ValidationPipeline | > 80% | High |
| CacheLayer | > 75% | Medium |
| ErrorFormatting | > 70% | Medium |

**Unit Test Cases:**

**UT-1.1: Jinja2 Detection**
```typescript
describe('FormatDetectionStage', () => {
  it('should detect pure Jinja2 template', () => {
    const content = '{# Template comment #}\n{{ variable }}';
    expect(detector.isJinja2(content)).toBe(true);
  });

  it('should detect mixed Jinja+JSON', () => {
    const content = '{"key": {{ value }}}';
    expect(detector.isJinja2(content)).toBe(true);
  });

  it('should NOT detect pure JSON as Jinja2', () => {
    const content = '{"key": "value"}';
    expect(detector.isJinja2(content)).toBe(false);
  });
});
```

**UT-1.2: Import Parsing**
```typescript
describe('ImportProcessor', () => {
  it('should parse markdown-style import', () => {
    const line = '// [Title](file:///path/to/file.json)';
    const imports = processor.parseImports(line);
    expect(imports).toHaveLength(1);
    expect(imports[0].title).toBe('Title');
    expect(imports[0].path).toBe('file:///path/to/file.json');
  });

  it('should detect circular dependency', () => {
    const graph = new DependencyGraph();
    graph.addEdge('a.json', 'b.json');
    graph.addEdge('b.json', 'c.json');
    graph.addEdge('c.json', 'a.json');

    expect(processor.detectCircularDependencies(graph)).toEqual([
      'a.json', 'b.json', 'c.json', 'a.json'
    ]);
  });
});
```

**UT-1.3: Position Mapping**
```typescript
describe('LayeredSourceMap', () => {
  it('should resolve position through Jinja2 layer', () => {
    const sourceMap = new LayeredSourceMap();
    sourceMap.addLayer({
      type: 'jinja2',
      mappings: { /* ... */ }
    });

    const resolved = sourceMap.resolvePosition(10, 5);
    expect(resolved.sourceFile).toBe('original.j2.json');
    expect(resolved.sourceLine).toBe(8);
  });
});
```

---

#### TR-2: Integration Testing

**Integration Test Scenarios:**

**IT-2.1: End-to-End .j2.json Validation**
```typescript
describe('ValidationPipeline E2E', () => {
  it('should validate .j2.json with imports', async () => {
    const testFile = '/path/to/test.j2.json';
    const result = await validateFile(testFile);

    expect(result.valid).toBe(true);
    expect(result.errors).toHaveLength(0);
    expect(result.processedImports).toBeGreaterThan(0);
  });
});
```

**IT-2.2: Integration с alfa-sdui-mcp**
```typescript
describe('MCP Integration', () => {
  it('should use MCP validator after Jinja2 processing', async () => {
    const result = await validateFile('test.j2.json');
    expect(result.webCompatibility).toBeGreaterThanOrEqual(0);
    expect(result.versions).toBeDefined();
  });
});
```

---

#### TR-3: Regression Testing

**Regression Test Requirements:**

**RT-3.1: v2.2.0 Compatibility**
- Все тесты из v2.2.0 ДОЛЖНЫ проходить на v2.3.0
- Используйте snapshot testing для стабильности output format

**RT-3.2: Performance Regression**
- Benchmark suite для pure JSON (не должен замедлиться)
- Performance tests для .j2.json (baseline для будущих версий)

**RT-3.3: Existing Contracts**
```typescript
describe('Real World Contracts Regression', () => {
  const existingContracts = [
    '/path/to/payroll/main_screen.json',
    '/path/to/dashboard/layout.json',
    // ... top 50 most used contracts
  ];

  existingContracts.forEach(contract => {
    it(`should validate ${contract} without regression`, async () => {
      const result = await validateFile(contract);
      expect(result.valid).toBe(true);
    });
  });
});
```

---

#### TR-4: Error Scenario Testing

**Error Test Cases:**

**ET-4.1: Jinja2 Errors**
```typescript
describe('Jinja2 Error Handling', () => {
  it('should handle undefined variable gracefully', async () => {
    const content = '{"key": {{ undefined_var }}}';
    const result = await validateFile(writeTemp(content));

    expect(result.warnings).toContainEqual(
      expect.objectContaining({
        message: expect.stringContaining('undefined_var')
      })
    );
  });
});
```

**ET-4.2: Import Errors**
```typescript
describe('Import Error Handling', () => {
  it('should warn on missing import file', async () => {
    const content = '// [Missing](file:///nonexistent.json)\n{}';
    const result = await validateFile(writeTemp(content));

    expect(result.warnings).toContainEqual(
      expect.objectContaining({
        message: expect.stringContaining('not found')
      })
    );
  });

  it('should detect circular dependency', async () => {
    // Setup: a.json imports b.json, b.json imports a.json
    const result = await validateFile('a.json');

    expect(result.errors).toContainEqual(
      expect.objectContaining({
        message: expect.stringContaining('Circular dependency')
      })
    );
  });
});
```

**ET-4.3: Position Mapping Edge Cases**
```typescript
describe('Position Mapping Edge Cases', () => {
  it('should handle minified JSON', async () => {
    const minified = '{"key":"value","nested":{"array":[1,2,3]}}';
    const result = await validateFile(writeTemp(minified));

    // All errors should point to L1
    result.errors.forEach(error => {
      expect(error.sourceLocation.line).toBe(1);
    });
  });

  it('should map position after import expansion', async () => {
    // Test that error in imported file points to correct file+line
  });
});
```

---

#### TR-5: Test Fixtures

**Test Fixtures Structure:**

```
tests/fixtures/v2.3.0/
├── pure-json/
│   ├── valid-contract.json
│   ├── invalid-type.json
│   └── missing-field.json
├── pure-jinja2/
│   ├── simple-template.j2.json
│   ├── with-includes.j2.json
│   └── undefined-vars.j2.json
├── mixed-format/
│   ├── jinja-in-json.j2.json
│   ├── comments-imports.j2.json
│   └── nested-imports.j2.json
├── error-cases/
│   ├── circular-import-a.j2.json
│   ├── circular-import-b.j2.json
│   ├── missing-import.j2.json
│   └── invalid-jinja-syntax.j2.json
└── performance/
    ├── large-50kb.j2.json
    ├── many-imports-20x.j2.json
    └── deep-nesting.j2.json
```

**Fixture Requirements:**
- Каждый fixture должен иметь `.expected.json` с ожидаемым результатом
- Performance fixtures должны иметь `.benchmark.json` с target metrics

---

## Success Metrics

### Key Performance Indicators (KPIs)

| Metric | Baseline (v2.2.0) | Target (v2.3.0) | Measurement Method |
|--------|-------------------|-----------------|-------------------|
| **Functionality** | | | |
| .j2.json validation support | 0% | 100% | Test suite pass rate |
| Import resolution success rate | N/A | > 95% | Real-world contracts |
| Position mapping accuracy | 90% | > 85% | Manual verification |
| **Performance** | | | |
| Pure JSON validation time | 180ms (95th) | < 200ms (95th) | Benchmark suite |
| .j2.json validation time | N/A | < 500ms (95th) | Benchmark suite |
| Memory footprint | 80MB | < 150MB | Process monitoring |
| **Quality** | | | |
| False positive rate | 2% | < 3% | User reports |
| False negative rate | 0.5% | < 1% | Audit |
| Crash rate | 0.1% | < 0.2% | Error tracking |

### User Satisfaction Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Developer adoption rate | > 80% within 2 weeks | VSCode extension analytics |
| Time to fix errors | -30% vs manual flow | User survey |
| User satisfaction (NPS) | > 40 | Post-release survey |
| Documentation clarity | > 4.0/5.0 | Feedback form |

### Business Impact Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Reduction in production bugs | -25% | Bug tracker analysis |
| Development velocity | +15% | Sprint velocity tracking |
| Support tickets (validator issues) | < 5/month | Support system |

---

## Scope & Timeline

### In Scope (v2.3.0)

**Phase 1: Core Jinja2 Support (Week 1-2)**
- ✅ Jinja2 template detection
- ✅ Nunjucks integration с custom filters
- ✅ Smart context generation
- ✅ Basic position mapping для Jinja2

**Phase 2: Import System (Week 3-4)**
- ✅ Comment-import parsing
- ✅ Import resolution и expansion
- ✅ Circular dependency detection
- ✅ Multi-level source maps

**Phase 3: Integration & Testing (Week 5-6)**
- ✅ Integration с alfa-sdui-mcp
- ✅ Enhanced error reporting
- ✅ Performance optimization
- ✅ Comprehensive test suite

**Phase 4: Documentation & Release (Week 7)**
- ✅ README update
- ✅ Migration guide
- ✅ API documentation
- ✅ Release v2.3.0

### Out of Scope (Future Versions)

**Deferred to v2.4.0:**
- ❌ YAML support для context files
- ❌ Visual Studio integration (non-VSCode)
- ❌ Real-time collaborative validation
- ❌ AI-powered auto-fix suggestions

**Deferred to v3.0.0:**
- ❌ TypeScript contract generation
- ❌ GraphQL-style contract querying
- ❌ Cloud-based validation service

### Timeline & Milestones

| Milestone | Date | Deliverable |
|-----------|------|-------------|
| **M1: Requirements Sign-off** | 2025-10-12 | Этот PRD утвержден stakeholders |
| **M2: Prototype Demo** | 2025-10-19 | Working demo Jinja2 + imports |
| **M3: Alpha Release** | 2025-10-26 | Internal testing build |
| **M4: Beta Release** | 2025-11-02 | Limited rollout (10 developers) |
| **M5: GA Release** | 2025-11-09 | Public release v2.3.0 |

---

## Risks & Mitigation

### Technical Risks

| Risk | Impact | Probability | Mitigation Strategy |
|------|--------|-------------|---------------------|
| **R1: Nunjucks incompatibility с Python Jinja2** | High | Medium | Создать feature parity test suite; fallback на Python bridge если нужно |
| **R2: Performance degradation для pure JSON** | High | Low | Strict performance tests в CI; fast path для pure JSON |
| **R3: Position mapping неточность** | Medium | Medium | Extensive testing; confidence levels в output; fallback strategy |
| **R4: Circular dependency в real contracts** | Medium | High | Clear error messages; auto-fix suggestions; documentation |
| **R5: Integration breaking changes в alfa-sdui-mcp** | High | Low | Version pinning; integration tests; semver strict |

### Operational Risks

| Risk | Impact | Probability | Mitigation Strategy |
|------|--------|-------------|---------------------|
| **R6: Adoption resistance (developers prefer old flow)** | Medium | Medium | Early stakeholder demos; migration guide; side-by-side comparison |
| **R7: Documentation insufficient** | Medium | Medium | User testing of docs; video tutorials; FAQ section |
| **R8: Breaking changes в existing workflows** | High | Low | Comprehensive regression testing; backward compatibility guarantee |

### Schedule Risks

| Risk | Impact | Probability | Mitigation Strategy |
|------|--------|-------------|---------------------|
| **R9: Scope creep** | High | Medium | Strict scope management; defer nice-to-haves to v2.4.0 |
| **R10: Dependencies delay (nunjucks issues)** | Medium | Low | Early spike on nunjucks integration; backup plan (Python bridge) |
| **R11: Testing coverage insufficient** | Medium | Medium | Start testing from Week 1; continuous integration |

---

## Assumptions

### Technical Assumptions

**A1: Jinja2 Syntax Compatibility**
- ПРЕДПОЛАГАЕТСЯ: Nunjucks syntax 95%+ совместим с Python Jinja2
- ВАЛИДАЦИЯ: Feature parity testing против jinja_hot_reload_v3.7.0.py

**A2: Import Format Stability**
- ПРЕДПОЛАГАЕТСЯ: Формат `// [Title](file:///path)` не изменится
- ВАЛИДАЦИЯ: Alignment с SDUI team на formат импортов

**A3: File System Access**
- ПРЕДПОЛАГАЕТСЯ: Validator имеет read access ко всем импортированным файлам
- ВАЛИДАЦИЯ: Permission checks перед import resolution

**A4: alfa-sdui-mcp Stability**
- ПРЕДПОЛАГАЕТСЯ: MCP validator API стабилен
- ВАЛИДАЦИЯ: Integration tests с pinned версией

### Organizational Assumptions

**A5: Stakeholder Availability**
- ПРЕДПОЛАГАЕТСЯ: Tech Lead доступен для weekly reviews
- ВАЛИДАЦИЯ: Scheduled calendar invites

**A6: Development Resources**
- ПРЕДПОЛАГАЕТСЯ: 1 developer full-time на 7 недель
- ВАЛИДАЦИЯ: Resource allocation confirmed

**A7: Testing Environment**
- ПРЕДПОЛАГАЕТСЯ: Access к real-world .j2.json contracts для testing
- ВАЛИДАЦИЯ: Setup test data repository

---

## Open Questions

### Questions Requiring Resolution

**Q1: Jinja2 Engine Choice**
- ❓ Использовать Nunjucks (TypeScript) или Python bridge к jinja_hot_reload?
- **Impact:** Architecture, performance, maintainability
- **Decision Needed By:** 2025-10-12 (M1)
- **Proposed Answer:** Nunjucks для чистоты stack, но обеспечить 100% feature parity

**Q2: Import Syntax Extensions**
- ❓ Нужна ли поддержка дополнительных форматов импорта (например, `{% import_json 'file.json' %}`)?
- **Impact:** Scope, complexity
- **Decision Needed By:** 2025-10-12 (M1)
- **Proposed Answer:** Только markdown-style в v2.3.0, остальное в v2.4.0

**Q3: Context File Format**
- ❓ Поддерживать только JSON для context или также YAML?
- **Impact:** Dependencies, testing scope
- **Decision Needed By:** 2025-10-15
- **Proposed Answer:** Только JSON в v2.3.0, YAML в v2.4.0

**Q4: Error Severity Levels**
- ❓ Как классифицировать ошибки Jinja2 (ERROR vs WARNING)?
- **Impact:** User experience, validation strictness
- **Decision Needed By:** 2025-10-19 (M2)
- **Proposed Answer:** Undefined variables = WARNING, syntax errors = ERROR

**Q5: Cache Persistence**
- ❓ Нужен ли persistent disk cache или только in-memory?
- **Impact:** Performance, complexity
- **Decision Needed By:** 2025-10-26 (M3)
- **Proposed Answer:** In-memory для v2.3.0, disk cache в v2.4.0 если нужно

**Q6: VSCode Extension**
- ❓ Упаковать validator в отдельный VSCode extension или оставить как external tool?
- **Impact:** Distribution, installation experience
- **Decision Needed By:** 2025-11-02 (M4)
- **Proposed Answer:** External tool в v2.3.0, extension в v3.0.0

---

## Appendix A: Technical Design Diagrams

### A.1: Validation Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                       VALIDATION PIPELINE                        │
└─────────────────────────────────────────────────────────────────┘

Input: /path/to/contract.j2.json
   │
   ▼
┌─────────────────────┐
│ FileLoaderStage     │ → Read file content
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ FormatDetection     │ → Detect: .j2.json? Jinja2 syntax?
└──────────┬──────────┘
           │
           ├─ Pure JSON ──────────────────┐ (Fast path)
           │                              │
           ├─ .j2.json ───────────┐       │
           │                      ▼       ▼
           │           ┌──────────────────────┐
           │           │ Jinja2Processing     │
           │           │ - Render template    │
           │           │ - Build source map   │
           │           └──────────┬───────────┘
           │                      │
           ▼                      ▼
┌──────────────────────────────────────┐
│ ImportResolutionStage                │
│ - Parse // [Title](file:///)         │
│ - Resolve dependencies               │
│ - Expand imports                     │
│ - Detect circular deps               │
└──────────┬───────────────────────────┘
           │
           ▼
┌─────────────────────┐
│ JSONParsingStage    │ → JSON.parse(finalContent)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ PositionMapping     │ → Build enhanced position map
└──────────┬──────────┘    (with source map layers)
           │
           ▼
┌─────────────────────┐
│ SDUIValidation      │ → alfa-sdui-mcp validator
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ ErrorFormatting     │ → Format output with links
└──────────┬──────────┘
           │
           ▼
Output: ValidationReport with clickable links
```

### A.2: Source Map Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                      SOURCE MAP LAYERS                           │
└─────────────────────────────────────────────────────────────────┘

Layer 3: Final JSON (after all transformations)
┌──────────────────────────────────────┐
│ 156: "type": "StackView",            │ ◄─── Error here
│ 157: "content": {                    │
│ 158:   "children": [...]             │
└──────────────────────────────────────┘
              ▲
              │ Import Source Map
              │
Layer 2: After import expansion
┌──────────────────────────────────────┐
│  38: "type": "StackView",            │
│  39: "content": {                    │
└──────────────────────────────────────┘
              ▲
              │ Jinja2 Source Map
              │
Layer 1: After Jinja2 rendering
┌──────────────────────────────────────┐
│  35: "type": "StackView",            │
│  36: "content": {                    │
└──────────────────────────────────────┘
              ▲
              │ Original Position
              │
Layer 0: Original .j2.json
┌──────────────────────────────────────┐
│  42: "type": "{{ component_type }}", │ ◄─── Report error here
│  43: "content": {                    │
└──────────────────────────────────────┘

Resolution Chain: L156 → L38 → L35 → L42
```

### A.3: Dependency Graph Example

```
┌─────────────────────────────────────────────────────────────────┐
│                      DEPENDENCY GRAPH                            │
└─────────────────────────────────────────────────────────────────┘

main_screen.j2.json
   │
   ├─ imports ──► Coins.json
   │                 (no dependencies)
   │
   ├─ imports ──► Header.json
   │                 │
   │                 └─ imports ──► Logo.json
   │
   └─ imports ──► Footer.json
                     │
                     ├─ imports ──► Links.json
                     └─ imports ──► Copyright.json

Validation Order (bottom-up):
1. Logo.json, Coins.json
2. Header.json, Links.json, Copyright.json
3. Footer.json
4. main_screen.j2.json

Invalidation Cascade (top-down):
- If Logo.json changes → invalidate Header.json → main_screen.j2.json
```

---

## Appendix B: Example Workflows

### B.1: Developer Workflow с v2.3.0

**Scenario:** Разработчик редактирует модульный контракт

```bash
# 1. Открыть VSCode
code /path/to/payroll/main_screen.j2.json

# 2. Редактировать файл
# Добавить новый компонент с импортом:
# // [New Section](file:///path/to/new-section.json)

# 3. Сохранить (Cmd+S)
# → VSCode автоматически запускает validator
# → Validator обрабатывает Jinja2
# → Validator резолвит импорты
# → Validator показывает результат в OUTPUT panel

# 4. Если есть ошибки:
# → Кликнуть на ссылку "file:///path#L42:5"
# → VSCode открывает файл на нужной строке
# → Исправить ошибку

# 5. Сохранить снова → Validator re-runs → ✅ Success
```

### B.2: CI/CD Integration

**Scenario:** Автоматическая валидация в GitHub Actions

```yaml
# .github/workflows/validate-contracts.yml
name: Validate SDUI Contracts

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install validator
        run: npm install -g vscode-validate-on-save@2.3.0

      - name: Validate all contracts
        run: |
          find . -name "*.json" -o -name "*.j2.json" | \
          xargs -I {} node /path/to/vscode-validate-on-save_v2.3.0.js {}

      - name: Upload validation report
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: validation-errors
          path: validation-report.json
```

---

## Appendix C: Migration Guide (v2.2.0 → v2.3.0)

### Breaking Changes

**NONE** - v2.3.0 полностью обратно совместима с v2.2.0

### New Features Available

1. **Jinja2 Template Support**
   - Rename `.json` → `.j2.json` для включения Jinja2 processing
   - Или оставить `.json` - auto-detection сработает

2. **Comment-Import System**
   ```json
   {
     // [Reusable Component](file:///path/to/component.json)
     "rootElement": { ... }
   }
   ```

3. **Smart Context Generation**
   - Автоматическая генерация контекста для undefined переменных
   - Или создать `contract.context.json` для explicit контекста

### Migration Steps

**Step 1:** Update validator binary
```bash
npm install vscode-validate-on-save@2.3.0
# OR
curl -o validator.js https://releases/vscode-validate-on-save_v2.3.0.js
```

**Step 2:** (Optional) Rename files для Jinja2
```bash
# Если файл использует Jinja2 синтаксис
mv contract.json contract.j2.json
```

**Step 3:** Update VSCode tasks.json (if needed)
```json
{
  "tasks": [{
    "label": "Validate SDUI",
    "command": "node",
    "args": [
      "/path/to/vscode-validate-on-save_v2.3.0.js",
      "${file}"
    ]
  }]
}
```

**Step 4:** Test validation
```bash
node vscode-validate-on-save_v2.3.0.js your-contract.j2.json
```

**Step 5:** Enjoy enhanced validation! 🎉

---

## Appendix D: FAQ

**Q: Нужно ли переименовывать все `.json` → `.j2.json`?**
A: Нет. Validator автоматически детектирует Jinja2 синтаксис. Переименование опционально для явности.

**Q: Что если мой файл содержит строку `{{ ... }}` но это НЕ Jinja2?**
A: Используйте escaping: `\{{ ... \}}` или оставьте `.json` расширение и validator не будет обрабатывать Jinja2.

**Q: Поддерживаются ли все фильтры из jinja_hot_reload_v3.7.0.py?**
A: Да, v2.3.0 обеспечивает feature parity с custom filters: `now`, `isoformat`, `formatCurrency`, `formatDate`, `tojson`, `daysUntil`.

**Q: Как работает кеширование импортов?**
A: Validator кеширует импортированные файлы и инвалидирует cache при изменении файла (по mtime).

**Q: Можно ли использовать относительные пути в импортах?**
A: Нет, все импорты должны использовать абсолютные `file:///` URLs для безопасности.

**Q: Что делать при circular dependency?**
A: Validator выдаст ERROR с цепочкой файлов в цикле. Рефакторите структуру для устранения цикла.

**Q: Влияет ли v2.3.0 на производительность pure JSON валидации?**
A: Нет, для pure JSON используется fast path без overhead.

---

## Document Approval

| Stakeholder | Role | Status | Date | Signature |
|-------------|------|--------|------|-----------|
| Tech Lead | Approver | ⏳ Pending | - | - |
| SDUI Team Lead | Reviewer | ⏳ Pending | - | - |
| QA Lead | Reviewer | ⏳ Pending | - | - |
| Product Owner | Approver | ⏳ Pending | - | - |

---

## Changelog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1 | 2025-10-05 | Requirements Analysis | Initial draft |
| 1.0 | TBD | - | Approved version after stakeholder review |

---

**END OF DOCUMENT**
