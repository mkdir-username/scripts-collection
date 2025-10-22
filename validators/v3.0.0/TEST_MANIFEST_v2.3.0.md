# Test Manifest для SDUI Validator v2.3.0

## Обзор

Comprehensive test suite для валидации SDUI контрактов с поддержкой Jinja2 шаблонов.

**Версия:** 2.3.0
**Дата создания:** 2025-10-05
**Автор:** Claude Code (Agent Testing)

## Структура файлов

```
validators/v3.0.0/
├── test_validator_v2.3.0.ts          # Основной файл с тестами
├── test_fixtures_v2.3.0.ts           # Тестовые фикстуры
├── jest.config.test_v2.3.0.js        # Jest конфигурация
├── run_tests_v2.3.0.sh               # Quick start скрипт
├── README_test_v2.3.0.md             # Документация
└── TEST_MANIFEST_v2.3.0.md           # Этот файл
```

## Покрытие тестами

### Unit Tests: jinja_parser_v1.0.0.ts (6 блоков)

#### 1. Import Parsing (6 тестов)
- ✅ Парсинг импортов из комментариев `// [...](file://path)`
- ✅ Обработка абсолютных путей
- ✅ Обработка относительных путей
- ✅ Детекция циклических импортов
- ✅ Обработка отсутствующих импортов
- ✅ Ограничение глубины импортов

#### 2. Module Resolution (3 теста)
- ✅ Резолвинг .json модулей
- ✅ Резолвинг .j2.java модулей
- ✅ Резолвинг вложенных импортов

#### 3. Jinja Variable Processing (3 теста)
- ✅ Замена переменных на значения по умолчанию
- ✅ Вывод значений на основе имен переменных
- ✅ Обработка вложенных переменных (obj.field)

#### 4. Source Map Building (2 теста)
- ✅ Построение source map для маппинга позиций
- ✅ Корректный маппинг строк и колонок

#### 5. Error Handling (3 теста)
- ✅ Обработка некорректного JSON синтаксиса
- ✅ Обработка отсутствующих файлов
- ✅ Сбор статистики парсинга

#### 6. Utility Functions (2 теста)
- ✅ isJinjaTemplate - определение Jinja файлов
- ✅ normalizeImportPath - нормализация путей

**Итого Unit Tests: 19 тестов**

---

### Integration Tests: jinja_aware_validator_v1.0.0.ts (6 блоков)

#### 1. Web Compatibility Validation (2 теста)
- ✅ Валидация WEB-совместимых компонентов
- ✅ Детекция WEB-несовместимых компонентов

#### 2. Required Fields Validation (2 теста)
- ✅ Детекция отсутствующих обязательных полей
- ✅ Пропуск компонентов с корректными полями

#### 3. Recursive Import Validation (3 теста)
- ✅ Рекурсивная валидация импортов
- ✅ Обработка ошибок в импортах
- ✅ Обработка отсутствующих импортов

#### 4. Position Tracking для .j2.java (2 теста)
- ✅ Маппинг ошибок на исходные позиции
- ✅ Корректный маппинг после обработки Jinja

#### 5. Backward Compatibility с .json (2 теста)
- ✅ Валидация обычных .json файлов
- ✅ Обработка .json без Jinja логики

#### 6. Validation Reporting (2 теста)
- ✅ Генерация детального отчета
- ✅ Экспорт результата в JSON

**Итого Integration Tests: 13 тестов**

---

### Real-World Examples (2 блока)

#### 1. Real Project File: main_screen.j2.java (3 теста)
- ✅ Парсинг реального файла с импортами
- ✅ Валидация с WEB compatibility
- ✅ Обработка state и data bindings

#### 2. Valid Basic Jinja File (1 тест)
- ✅ Парсинг базового Jinja файла с Java кодом

**Итого Real-World Tests: 4 теста**

---

### Performance Tests (2 теста)

- ✅ Парсинг большого файла (1000 компонентов) за < 500ms
- ✅ Обработка множественных импортов (50 модулей) за < 1s

**Итого Performance Tests: 2 теста**

---

### Edge Cases (5 тестов)

- ✅ Пустой файл
- ✅ Файл только с комментариями
- ✅ Экранированные символы в Jinja переменных
- ✅ Unicode символы
- ✅ Очень длинные строки (10000 символов)

**Итого Edge Case Tests: 5 тестов**

---

## Общая статистика

| Категория         | Количество тестов |
|-------------------|-------------------|
| Unit Tests        | 19                |
| Integration Tests | 13                |
| Real-World Tests  | 4                 |
| Performance Tests | 2                 |
| Edge Cases        | 5                 |
| **ВСЕГО**         | **43 теста**      |

## Coverage цели

| Метрика    | Целевой % | Текущий % |
|------------|-----------|-----------|
| Statements | 80%       | TBD       |
| Branches   | 75%       | TBD       |
| Functions  | 80%       | TBD       |
| Lines      | 80%       | TBD       |

## Тестовые фикстуры

### Валидные контракты (5 шт.)
- `VALID_SIMPLE_STACK` - Простой StackView
- `VALID_BUTTON` - ButtonView с обязательными полями
- `VALID_WITH_JINJA_VARS` - С Jinja переменными
- `VALID_WITH_IMPORTS` - С импортами
- `VALID_WITH_STATE` - С state и data bindings

### Невалидные контракты (6 шт.)
- `INVALID_MISSING_REQUIRED_FIELDS` - Отсутствующие поля
- `INVALID_UNKNOWN_COMPONENT` - Неизвестный компонент
- `INVALID_JSON_SYNTAX` - Некорректный JSON
- `INVALID_CIRCULAR_IMPORT_A/B` - Циклические импорты
- `INVALID_MISSING_IMPORT` - Отсутствующий импорт

### Edge Cases (7 шт.)
- `EDGE_EMPTY_OBJECT` - Пустой объект
- `EDGE_ONLY_COMMENTS` - Только комментарии
- `EDGE_DEEP_NESTING` - Глубокая вложенность (10 уровней)
- `EDGE_LONG_STRING` - Длинная строка (10000 символов)
- `EDGE_UNICODE` - Unicode символы
- `EDGE_ESCAPED_CHARS` - Экранированные символы
- `EDGE_LARGE_ARRAY` - Большой массив (1000 элементов)

### Реальные примеры (3 шт.)
- `REAL_MAIN_SCREEN` - Main Screen с импортами
- `REAL_JAVA_CLASS` - Java класс с Jinja
- `REAL_BUTTON_MODULE` - Модуль кнопки

### Модули для импортов (4 шт.)
- `MODULE_HEADER` - Header компонент
- `MODULE_FOOTER` - Footer компонент
- `MODULE_SPACER` - Spacer
- `MODULE_ICON_BUTTON` - Icon Button

## Быстрый старт

### 1. Установка зависимостей

```bash
cd /Users/username/Scripts/validators/v3.0.0
npm install --save-dev jest @jest/globals ts-jest @types/jest jest-junit
```

### 2. Запуск тестов

```bash
# Все тесты
./run_tests_v2.3.0.sh

# Только unit тесты
./run_tests_v2.3.0.sh unit

# С покрытием
./run_tests_v2.3.0.sh coverage

# Watch mode
./run_tests_v2.3.0.sh watch
```

### 3. Альтернативный запуск (через npm)

```bash
npx jest test_validator_v2.3.0.ts --config jest.config.test_v2.3.0.js
```

## Зависимости

### Runtime
- Node.js >= 18.0.0
- TypeScript >= 5.0.0

### Dev Dependencies
```json
{
  "jest": "^29.0.0",
  "@jest/globals": "^29.0.0",
  "ts-jest": "^29.0.0",
  "@types/jest": "^29.0.0",
  "jest-junit": "^16.0.0"
}
```

## Используемые реальные файлы

```
/Users/username/Documents/FMS_GIT/tests/validator_v3.0.0/
├── test_real_project_file_v1.0.0.j2.java       # Main screen с импортами
├── test_j2_java_valid_basic_v1.0.0.j2.java     # Java класс с Jinja
├── test_j2_java_valid_loops_v1.0.0.j2.java     # Тесты с циклами
└── test_j2_java_invalid_braces_v1.0.0.j2.java  # Невалидный синтаксис
```

## Временные файлы

Тесты создают временные файлы в:
```
/tmp/sdui-test-<timestamp>/
```

Автоматически удаляются в `afterEach` хуках.

## Отчеты

### Coverage отчет
```
validators/v3.0.0/coverage/
├── lcov-report/index.html    # HTML отчет
├── lcov.info                 # LCOV формат
└── coverage-summary.json     # JSON сводка
```

### JUnit отчет
```
validators/v3.0.0/test-results/junit.xml
```

## Метрики производительности

### Целевые показатели
- Парсинг 1000 компонентов: < 500ms
- 50 импортов: < 1000ms
- Source map построение (239KB): < 15ms

### Тестируемые размеры
- Малый файл: ~10KB (10 компонентов)
- Средний файл: ~100KB (100 компонентов)
- Большой файл: ~1MB (1000 компонентов)

## Best Practices

### Написание тестов
1. ✅ Группировать в `describe` блоки
2. ✅ Использовать понятные названия с `должен...`
3. ✅ Очищать временные файлы в `afterEach`
4. ✅ Проверять граничные случаи
5. ✅ Тестировать ошибки, не только успешные кейсы

### Именование
- **Тесты:** `должен <действие>`
- **Блоки:** `<Компонент> <Категория>`
- **Файлы:** `test_<component>_v<version>.ts`

### Структура теста
```typescript
describe('Component Name', () => {
  beforeEach(() => {
    // Setup
  });

  afterEach(() => {
    // Cleanup
  });

  it('должен делать что-то', () => {
    // Arrange
    const input = createInput();

    // Act
    const result = component.process(input);

    // Assert
    expect(result).toBe(expected);
  });
});
```

## CI/CD интеграция

### GitHub Actions (пример)
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
      - run: ./run_tests_v2.3.0.sh coverage
      - uses: codecov/codecov-action@v3
```

## Troubleshooting

### Jest не находит модули
```bash
# Проверить tsconfig.json
{
  "compilerOptions": {
    "module": "ESNext",
    "moduleResolution": "node"
  }
}
```

### Timeout ошибки
```typescript
// Увеличить timeout
it('долгий тест', async () => {
  // ...
}, 60000); // 60s
```

### Реальные файлы не найдены
```bash
# Проверить наличие
ls /Users/username/Documents/FMS_GIT/tests/validator_v3.0.0/
```

## Changelog

### v2.3.0 (2025-10-05)
- ✅ Создан comprehensive test suite
- ✅ 43 теста покрывают все компоненты
- ✅ Unit тесты для JinjaParser (19)
- ✅ Integration тесты для JinjaAwareValidator (13)
- ✅ Real-world примеры (4)
- ✅ Performance тесты (2)
- ✅ Edge cases (5)
- ✅ Тестовые фикстуры (25 шт.)
- ✅ Quick start скрипт
- ✅ Jest конфигурация
- ✅ Полная документация

## Roadmap

### v2.4.0 (планируется)
- [ ] Snapshot тестирование для отчетов
- [ ] Visual regression тесты (Playwright)
- [ ] Мутационное тестирование (Stryker)
- [ ] Тесты на безопасность (SAST)
- [ ] Бенчмарки с различными размерами файлов

### v2.5.0 (планируется)
- [ ] End-to-end тесты с VSCode extension
- [ ] Тесты интеграции с alfa-sdui-mcp
- [ ] Stress тесты (10000+ компонентов)
- [ ] Memory leak тесты
- [ ] Concurrent validation тесты

## Контакты

**Автор:** Claude Code (Agent Testing)
**Email:** noreply@anthropic.com
**Версия:** 2.3.0
**Дата:** 2025-10-05

---

**Примечание:** Этот test suite является частью системы валидации SDUI контрактов и обеспечивает comprehensive покрытие всех компонентов валидатора v2.3.0.
