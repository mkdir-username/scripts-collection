# Parser Modules v1.0.0

Модульная система парсеров для обработки JSON, Jinja2/Java шаблонов, импортов и переменных.

## Архитектура

### Общий интерфейс IParser

Все парсеры реализуют единый интерфейс `IParser<TInput, TOutput, TConfig>`:

```typescript
interface IParser<TInput, TOutput, TConfig extends ParserConfig> {
  parse(input: TInput, options?: ParseOptions): Promise<ParseResult<TOutput>>;
  parseSync?(input: TInput, options?: ParseOptions): ParseResult<TOutput>;
  validate(input: TInput): Promise<boolean>;
  getConfig(): Readonly<TConfig>;
  updateConfig(config: Partial<TConfig>): void;
}
```

### Типизированные ошибки

Все ошибки парсинга типизированы через enum `ParseErrorType`:

```typescript
enum ParseErrorType {
  SYNTAX_ERROR = 'syntax_error',
  CIRCULAR_IMPORT = 'circular_import',
  FILE_NOT_FOUND = 'file_not_found',
  INVALID_TEMPLATE = 'invalid_template',
  INVALID_JSON = 'invalid_json',
  UNRESOLVED_VARIABLE = 'unresolved_variable',
  IMPORT_ERROR = 'import_error',
  UNKNOWN = 'unknown',
}
```

### Exception классы

Иерархия исключений:

- `ParserException` - базовый класс
  - `SyntaxException` - ошибки синтаксиса
  - `ImportException` - ошибки импорта
    - `CircularImportException` - циклические импорты
    - `FileNotFoundException` - файл не найден

## Модули

### 1. JsonParser

Парсер JSON с отслеживанием позиций и построением position map.

#### Особенности

- **Position Map**: O(n) построение карты позиций для быстрого поиска
- **Nested Cache**: кэширование вложенных путей для оптимизации
- **Parent Tracking**: отслеживание родительских путей
- **Array Support**: полная поддержка массивов любой вложенности

#### Использование

```typescript
import { JsonParser } from './parsers/json-parser_v1.0.0.js';

const parser = new JsonParser({
  strict: true,
  allowComments: false,
  reviver: (key, value) => value,
});

const result = await parser.parse('/path/to/file.json');

if (result.success) {
  const { json, positionMap } = result.data!;

  // Поиск позиции по пути
  const position = parser.findPosition(positionMap, 'component.type');
  console.log(`Line: ${position.line}, Column: ${position.column}`);
}
```

#### Position Map API

```typescript
interface PositionMap {
  byPointer: Map<string, PositionInfo>;    // JSON Pointer -> Position
  byPath: Map<string, PositionInfo>;       // Property path -> Position
  nestedCache: Map<string, PositionInfo[]>; // Nested paths cache
  totalLines: number;
  buildTimeMs: number;
}

interface PositionInfo {
  line: number;
  column: number;
  offset: number;
  length?: number;    // Длина токена
  parent?: string;    // Родительский путь
}
```

#### Примеры

```typescript
// Базовый парсинг
const result = await parser.parse('contract.json');

// С кастомным reviver
const dateParser = new JsonParser({
  reviver: (key, value) => {
    if (key.endsWith('Date')) return new Date(value);
    return value;
  }
});

// Синхронный парсинг
const syncResult = parser.parseSync('contract.json');

// Быстрая валидация
const isValid = await parser.validate('contract.json');
```

### 2. JinjaParser

Парсер Jinja2/Java шаблонов с поддержкой импортов и переменных.

#### Особенности

- **Import Resolution**: резолвинг `// [Description](file://path)` импортов
- **Variable Replacement**: замена `{{ variable }}` с выводом типов
- **Control Structures**: обработка `{% if %}`/`{% for %}` конструкций
- **Source Mapping**: построение карты трансформаций
- **Type Inference**: автоматический вывод типов переменных

#### Использование

```typescript
import { JinjaParser } from './parsers/jinja-parser_v1.0.0.js';

const parser = new JinjaParser({
  basePath: '/project/root',
  maxImportDepth: 10,
  buildSourceMap: true,
  variableDefaults: new Map([
    ['customVar', 'custom value']
  ]),
});

const result = await parser.parse('/path/to/template.j2.java');

if (result.success) {
  const { extractedJson, imports, sourceMap, stats } = result.data!;

  console.log(`Imports: ${stats.importCount}`);
  console.log(`Variables: ${stats.variableCount}`);
  console.log(`Controls: ${stats.controlCount}`);
}
```

#### Type Inference Rules

```typescript
// Boolean: is*, has*, *enabled, show*, hide*
{{ isEnabled }}      // -> false
{{ hasData }}        // -> false
{{ showModal }}      // -> false

// Number: *count, *size, *length, *index, *id
{{ itemCount }}      // -> 0
{{ totalSize }}      // -> 0

// Array: *list, *items, *array, *elements
{{ itemList }}       // -> []
{{ dataArray }}      // -> []

// Object: *data, *config, *options, *settings
{{ appConfig }}      // -> {}
{{ userSettings }}   // -> {}

// Null: *null, none, empty
{{ nullValue }}      // -> null

// String: по умолчанию
{{ anyOther }}       // -> ""
```

#### Import Pattern

```jinja
// [Description](file://path/to/file.json)
// [Header Component](file://./components/header.json)
// [Base Config](file:///absolute/path/config.json)
```

### 3. ImportResolver

Резолвер импортов с обнаружением циклических зависимостей.

#### Особенности

- **Dependency Graph**: построение графа зависимостей
- **Circular Detection**: обнаружение циклических зависимостей
- **Caching**: кэширование резолвнутых импортов
- **Multiple Patterns**: поддержка разных форматов импорта
- **Depth Limiting**: ограничение глубины рекурсии

#### Использование

```typescript
import { ImportResolver } from './parsers/import-resolver_v1.0.0.js';

const resolver = new ImportResolver({
  basePath: '/project/root',
  maxDepth: 10,
  allowCircular: false,
  cacheImports: true,
  extensions: ['.json', '.j2.java'],
});

const result = await resolver.parse('/path/to/file.json');

if (result.success) {
  const { imports, dependencyGraph, circularDependencies } = result.data!;

  // Анализ зависимостей
  console.log(`Total imports: ${imports.length}`);
  console.log(`Circular deps: ${circularDependencies.length}`);

  // Граф зависимостей
  for (const [path, node] of dependencyGraph.nodes) {
    console.log(`${path} imports: ${node.imports.length}`);
  }
}
```

#### Dependency Graph API

```typescript
interface DependencyGraph {
  nodes: Map<string, DependencyNode>;
  edges: DependencyEdge[];
}

interface DependencyNode {
  path: string;
  depth: number;
  imports: string[];      // Что импортирует этот узел
  importedBy: string[];   // Кем импортируется этот узел
}

interface CircularDependency {
  cycle: string[];        // Полный цикл: A -> B -> C -> A
  startNode: string;
  endNode: string;
}
```

#### Supported Import Patterns

```typescript
// File protocol
// [Description](file://path/to/file.json)

// Relative import
import "./relative/path.json"

// Require syntax
require("./module.json")
```

### 4. VariableReplacer

Replacer переменных с выводом типов и кастомными стратегиями.

#### Особенности

- **Type Inference**: автоматический вывод типов
- **Custom Defaults**: кастомные значения по умолчанию
- **Custom Strategies**: пользовательские стратегии вывода
- **Statistics**: детальная статистика замен
- **Escaping**: экранирование специальных символов

#### Использование

```typescript
import { VariableReplacer } from './parsers/variable-replacer_v1.0.0.js';

const replacer = new VariableReplacer({
  defaultInferenceEnabled: true,
  customDefaults: new Map([
    ['appName', 'MyApp'],
    ['apiKey', 'secret-key']
  ]),
  allowUndefined: false,
  escapeOutput: true,
});

const result = await replacer.parse('{"name": {{ appName }}}');

if (result.success) {
  const { content, replacements, stats } = result.data!;

  console.log(`Processed: ${content}`);
  console.log(`Total replacements: ${stats.totalReplacements}`);
  console.log(`Inferred: ${stats.inferredReplacements}`);
  console.log(`Custom: ${stats.customReplacements}`);
}
```

#### Custom Inference Strategies

```typescript
// Добавить кастомную стратегию
replacer.addInferenceStrategy({
  name: 'uuid-generator',
  pattern: /uuid$/i,
  inferValue: (name, context) => {
    return crypto.randomUUID();
  },
  priority: 200,  // Более высокий приоритет
});

// Добавить кастомное значение
replacer.setCustomDefault('apiKey', process.env.API_KEY);
```

#### Variable Analysis

```typescript
// Извлечь все переменные
const variables = replacer.extractVariables(content);
for (const v of variables) {
  console.log(`${v.name} at line ${v.position.line}`);
}

// Статистика по переменным
const stats = replacer.getVariableStats(content);
console.log(`Total: ${stats.total}`);
console.log(`Unique: ${stats.unique.length}`);
stats.byOccurrence.forEach((count, name) => {
  console.log(`${name}: ${count} occurrences`);
});
```

## Factory Functions

Упрощенное создание парсеров:

```typescript
import {
  createJsonParser,
  createJinjaParser,
  createImportResolver,
  createVariableReplacer,
} from './parsers/index_v1.0.0.js';

const jsonParser = createJsonParser({ strict: true });
const jinjaParser = createJinjaParser({ basePath: '/root' });
const importResolver = createImportResolver({ maxDepth: 5 });
const variableReplacer = createVariableReplacer({ escapeOutput: true });
```

## Parser Registry

Центральный реестр парсеров:

```typescript
import { ParserRegistry } from './parsers/index_v1.0.0.js';

// Получить парсер по имени
const jsonParser = ParserRegistry.get('json');

// Проверить существование
if (ParserRegistry.has('jinja')) {
  // ...
}

// Зарегистрировать кастомный парсер
ParserRegistry.register('custom', MyCustomParser);

// Получить все парсеры
const allParsers = ParserRegistry.getAll();
```

## Комбинированное использование

### Полный Pipeline

```typescript
import {
  JsonParser,
  JinjaParser,
  ImportResolver,
  VariableReplacer,
} from './parsers/index_v1.0.0.js';

async function processTemplate(filePath: string) {
  // 1. Резолвим импорты
  const importResolver = new ImportResolver({ basePath: '/root' });
  const importResult = await importResolver.parse(filePath);

  if (!importResult.success) {
    console.error('Import errors:', importResult.errors);
    return;
  }

  // 2. Парсим Jinja шаблон
  const jinjaParser = new JinjaParser({ basePath: '/root' });
  const jinjaResult = await jinjaParser.parse(filePath);

  if (!jinjaResult.success) {
    console.error('Jinja errors:', jinjaResult.errors);
    return;
  }

  // 3. Заменяем переменные
  const replacer = new VariableReplacer({
    customDefaults: new Map([['env', 'production']])
  });

  const content = JSON.stringify(jinjaResult.data!.extractedJson);
  const replaceResult = await replacer.parse(content);

  if (!replaceResult.success) {
    console.error('Variable errors:', replaceResult.errors);
    return;
  }

  // 4. Финальный парсинг JSON
  const jsonParser = new JsonParser();
  const jsonResult = await jsonParser.parseSync(
    replaceResult.data!.content
  );

  if (jsonResult.success) {
    console.log('Final JSON:', jsonResult.data!.json);

    // Position map для error reporting
    const position = jsonParser.findPosition(
      jsonResult.data!.positionMap,
      'component.type'
    );
    console.log(`Type field at line ${position?.line}`);
  }
}
```

### Обработка ошибок

```typescript
import { ParserException, ParseErrorType } from './parsers/types_v1.0.0.js';

try {
  const result = await parser.parse(filePath);

  if (!result.success) {
    // Группировка ошибок по типу
    const errorsByType = new Map<ParseErrorType, ParseError[]>();

    for (const error of result.errors) {
      if (!errorsByType.has(error.type)) {
        errorsByType.set(error.type, []);
      }
      errorsByType.get(error.type)!.push(error);
    }

    // Обработка по типам
    if (errorsByType.has(ParseErrorType.CIRCULAR_IMPORT)) {
      console.error('Circular imports detected!');
      // ...
    }

    if (errorsByType.has(ParseErrorType.FILE_NOT_FOUND)) {
      console.error('Missing files!');
      // ...
    }
  }
} catch (error) {
  if (error instanceof ParserException) {
    console.error(`Parse error: ${error.message}`);
    console.error(`Type: ${error.type}`);
    console.error(`Position: ${error.position?.line}:${error.position?.column}`);
  }
}
```

## Performance

### Бенчмарки

```typescript
// JSON Parser - большой файл (1000 компонентов)
const largeJson = { items: Array.from({ length: 1000 }, ...) };
// Parse time: ~50-100ms
// Position map build: ~20-50ms

// Jinja Parser - с импортами и переменными
// Import resolution: ~10-30ms per import
// Variable replacement: ~1-5ms per variable
// Total: ~100-200ms

// Import Resolver - глубина 10 уровней
// Dependency graph build: ~50-150ms
// Circular detection: ~20-50ms

// Variable Replacer - 100 переменных
// Type inference: ~10-30ms
// Replacement: ~20-50ms
```

### Оптимизации

```typescript
// 1. Кэширование импортов
const resolver = new ImportResolver({ cacheImports: true });

// 2. Отключение source map если не нужен
const parser = new JinjaParser({ buildSourceMap: false });

// 3. Batch processing
const files = ['file1.json', 'file2.json', ...];
const results = await Promise.all(
  files.map(f => parser.parse(f))
);

// 4. Переиспользование парсеров
const parser = new JsonParser();
for (const file of files) {
  await parser.parse(file);  // Переиспользуем конфигурацию
}
```

## Testing

Все парсеры покрыты unit-тестами:

```bash
# Запуск всех тестов парсеров
npm test -- tests/parsers/

# Отдельные тесты
npm test -- tests/parsers/json-parser_v1.0.0.test.ts
npm test -- tests/parsers/jinja-parser_v1.0.0.test.ts
npm test -- tests/parsers/import-resolver_v1.0.0.test.ts
npm test -- tests/parsers/variable-replacer_v1.0.0.test.ts
```

## TypeScript Integration

Полная поддержка TypeScript:

```typescript
// Строгая типизация результатов
const result: ParseResult<JsonParseResult> = await parser.parse(file);

// Type guards
if (result.success) {
  // result.data типизирован как JsonParseResult
  const json = result.data.json;
} else {
  // result.errors типизирован как ParseError[]
  for (const error of result.errors) {
    console.error(error.message);
  }
}

// Generic парсеры
class CustomParser implements IParser<string, MyResult, MyConfig> {
  async parse(input: string): Promise<ParseResult<MyResult>> {
    // ...
  }
}
```

## Version History

### v1.0.0 (2025-10-07)

- Начальная версия модульных парсеров
- Единый интерфейс IParser
- Типизированные ошибки и исключения
- Position Map для JSON парсера
- Type Inference для Jinja и Variable Replacer
- Dependency Graph для Import Resolver
- Полное покрытие тестами
- Factory functions и Parser Registry

## Roadmap

### v1.1.0

- [ ] Async Jinja Parser для больших файлов
- [ ] Streaming JSON Parser
- [ ] WebAssembly оптимизации
- [ ] Advanced source maps с column mapping
- [ ] Plugin system для кастомных парсеров

### v1.2.0

- [ ] Watch mode для hot reload
- [ ] Incremental parsing
- [ ] Parallel import resolution
- [ ] Schema validation integration
- [ ] CLI tools для каждого парсера

## License

MIT

## Contributors

- TypeScript Pro Agent - Initial implementation
