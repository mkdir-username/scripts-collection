# Comprehensive Test Suite для SDUI Validator v2.3.0

Полное покрытие тестами валидатора SDUI контрактов с поддержкой Jinja2 шаблонов.

## Структура тестов

### Unit Tests (jinja_parser_v1.0.0.ts)

**1. Import Parsing**
- ✅ Парсинг импортов из комментариев `// [...](file://path)`
- ✅ Обработка абсолютных путей
- ✅ Обработка относительных путей
- ✅ Детекция циклических импортов
- ✅ Обработка отсутствующих импортов
- ✅ Ограничение глубины импортов

**2. Module Resolution**
- ✅ Резолвинг .json модулей
- ✅ Резолвинг .j2.java модулей
- ✅ Резолвинг вложенных импортов

**3. Jinja Variable Processing**
- ✅ Замена переменных на значения по умолчанию
- ✅ Вывод значений на основе имен переменных
- ✅ Обработка вложенных переменных (obj.field)

**4. Source Map Building**
- ✅ Построение source map для маппинга позиций
- ✅ Корректный маппинг строк и колонок

**5. Error Handling**
- ✅ Обработка некорректного JSON синтаксиса
- ✅ Обработка отсутствующих файлов
- ✅ Сбор статистики парсинга

**6. Utility Functions**
- ✅ isJinjaTemplate - определение Jinja файлов
- ✅ normalizeImportPath - нормализация путей

### Integration Tests (jinja_aware_validator_v1.0.0.ts)

**1. Web Compatibility Validation**
- ✅ Валидация WEB-совместимых компонентов
- ✅ Детекция WEB-несовместимых компонентов

**2. Required Fields Validation**
- ✅ Детекция отсутствующих обязательных полей
- ✅ Пропуск компонентов с корректными полями

**3. Recursive Import Validation**
- ✅ Рекурсивная валидация импортов
- ✅ Обработка ошибок в импортах
- ✅ Обработка отсутствующих импортов

**4. Position Tracking для .j2.java**
- ✅ Маппинг ошибок на исходные позиции
- ✅ Корректный маппинг после обработки Jinja

**5. Backward Compatibility с .json**
- ✅ Валидация обычных .json файлов
- ✅ Обработка .json без Jinja логики

**6. Validation Reporting**
- ✅ Генерация детального отчета
- ✅ Экспорт результата в JSON

### Real-World Examples

**1. Real Project File: main_screen.j2.java**
- ✅ Парсинг реального файла с импортами
- ✅ Валидация с WEB compatibility
- ✅ Обработка state и data bindings

**2. Valid Basic Jinja File**
- ✅ Парсинг базового Jinja файла с Java кодом

### Performance Tests

- ✅ Парсинг большого файла (1000 компонентов) за < 500ms
- ✅ Обработка множественных импортов (50 модулей) за < 1s

### Edge Cases

- ✅ Пустой файл
- ✅ Файл только с комментариями
- ✅ Экранированные символы в Jinja переменных
- ✅ Unicode символы
- ✅ Очень длинные строки (10000 символов)

## Установка зависимостей

```bash
cd /Users/username/Scripts/validators/v3.0.0

# Установка Jest и зависимостей
npm install --save-dev \
  jest \
  @jest/globals \
  ts-jest \
  @types/jest \
  jest-junit
```

## Запуск тестов

### Все тесты

```bash
npm test -- test_validator_v2.3.0.ts
```

### Конкретная группа тестов

```bash
# Unit тесты JinjaParser
npm test -- test_validator_v2.3.0.ts -t "JinjaParser Unit Tests"

# Integration тесты JinjaAwareValidator
npm test -- test_validator_v2.3.0.ts -t "JinjaAwareValidator Integration Tests"

# Реальные примеры
npm test -- test_validator_v2.3.0.ts -t "Real-World Examples"

# Performance тесты
npm test -- test_validator_v2.3.0.ts -t "Performance Tests"

# Edge cases
npm test -- test_validator_v2.3.0.ts -t "Edge Cases"
```

### Конкретный тест

```bash
# Тест парсинга импортов
npm test -- test_validator_v2.3.0.ts -t "должен парсить импорты из комментариев"

# Тест циклических зависимостей
npm test -- test_validator_v2.3.0.ts -t "должен детектировать циклические импорты"
```

### С покрытием кода

```bash
npm test -- test_validator_v2.3.0.ts --coverage
```

### Watch mode (авто-перезапуск при изменениях)

```bash
npm test -- test_validator_v2.3.0.ts --watch
```

### Verbose вывод

```bash
npm test -- test_validator_v2.3.0.ts --verbose
```

## Coverage метрики

Целевые показатели покрытия:

| Метрика    | Целевой % | Текущий % |
|------------|-----------|-----------|
| Statements | 80%       | TBD       |
| Branches   | 75%       | TBD       |
| Functions  | 80%       | TBD       |
| Lines      | 80%       | TBD       |

## Отчеты

### HTML отчет покрытия

```bash
npm test -- test_validator_v2.3.0.ts --coverage
open coverage/lcov-report/index.html
```

### JUnit XML отчет

```bash
npm test -- test_validator_v2.3.0.ts
cat test-results/junit.xml
```

## Тестовые файлы

Тесты используют следующие реальные файлы:

```
/Users/username/Documents/FMS_GIT/tests/validator_v3.0.0/
├── test_real_project_file_v1.0.0.j2.java       # Реальный проект файл
├── test_j2_java_valid_basic_v1.0.0.j2.java     # Базовый Jinja файл
├── test_j2_java_valid_loops_v1.0.0.j2.java     # Тесты с циклами
└── test_j2_java_invalid_braces_v1.0.0.j2.java  # Невалидный синтаксис
```

## Временные файлы

Тесты создают временные файлы в:

```
/tmp/sdui-test-<timestamp>/
```

Автоматически удаляются после завершения тестов.

## Debugging

### Запуск с отладчиком Node

```bash
node --inspect-brk node_modules/.bin/jest test_validator_v2.3.0.ts
```

### Добавление breakpoints

```typescript
import { describe, it } from '@jest/globals';

it('должен парсить импорты', () => {
  debugger; // Добавьте breakpoint
  const result = parser.parse(filePath);
  expect(result.imports).toHaveLength(2);
});
```

### Вывод консоли в тестах

```typescript
it('должен вывести результат', () => {
  console.log('Debug info:', result);
  expect(result).toBeDefined();
});
```

## CI/CD интеграция

### GitHub Actions

```yaml
name: Validator Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm install
      - run: npm test -- test_validator_v2.3.0.ts --coverage
      - uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info
```

## Troubleshooting

### Jest не находит модули

```bash
# Убедитесь, что tsconfig.json настроен корректно
{
  "compilerOptions": {
    "module": "ESNext",
    "moduleResolution": "node",
    "esModuleInterop": true
  }
}
```

### Timeout ошибки

```typescript
// Увеличьте timeout для долгих тестов
it('долгий тест', async () => {
  // ...
}, 60000); // 60 секунд
```

### Файлы не найдены

```bash
# Проверьте абсолютные пути
ls /Users/username/Documents/FMS_GIT/tests/validator_v3.0.0/
```

## Вклад в тесты

При добавлении новых тестов:

1. **Группируйте тесты логически** в `describe` блоки
2. **Используйте понятные названия** тестов с `должен...`
3. **Добавляйте комментарии** для сложной логики
4. **Очищайте временные файлы** в `afterEach`
5. **Проверяйте граничные случаи** (пустые значения, null, undefined)
6. **Тестируйте ошибки** не только успешные кейсы

## Примеры использования

### Создание тестового файла

```typescript
import { createTestWorkspace, createTestJinjaFile } from './test_validator_v2.3.0.js';

const workspace = await createTestWorkspace();
const filePath = await createTestJinjaFile(
  workspace,
  'test.j2.java',
  '{ "type": "StackView" }'
);
```

### Парсинг с кастомными опциями

```typescript
const parser = new JinjaParser({
  basePath: workspace,
  maxImportDepth: 10,
  defaultValues: {
    userName: 'Alice',
    itemCount: 42,
  },
});

const result = parser.parse(filePath);
```

### Валидация с опциями

```typescript
const validator = new JinjaAwareValidator({ verbose: true });

const result = await validator.validate(filePath, {
  validateImports: true,
  checkWebCompatibility: true,
  checkRequiredFields: true,
  maxImportDepth: 5,
});
```

## Контакты

**Автор:** Claude Code (Agent Testing)
**Версия:** 2.3.0
**Дата:** 2025-10-05

---

**Примечание:** Эти тесты являются частью comprehensive test suite для SDUI валидаторов и обеспечивают полное покрытие функциональности парсинга Jinja2 шаблонов и валидации SDUI контрактов.
