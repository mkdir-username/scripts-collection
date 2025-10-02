# Test Suite для Jinja2/JSON Validation v1.0.0

Комплексный набор тестов для проверки всех исправлений в системе валидации.

## Быстрый старт

```bash
cd /Users/username/Scripts/tests
node test_validation_suite_v1.0.0.js
```

## Что тестируется

### ✅ Pure Jinja2 Templates
- Удаление комментариев `{# #}`
- Обработка `{% include %}`
- Undefined переменные
- Format strings

### ✅ Mixed JSON+Jinja2
- Trailing commas после include
- Missing commas между элементами
- Nested structures
- Comments + imports

### ✅ SDUI Fallback
- Без SDUI модулей (JSON fallback)
- С SDUI модулями (schema validation)
- Jinja2 трансформация в SDUI

### ✅ Error Recovery
- Template not found
- Syntax errors
- JSON decode errors
- Circular includes

## Структура

```
tests/
├── fixtures/          # 20 тестовых файлов
├── results/           # Отчеты тестирования
├── test_validation_suite_v1.0.0.js   # Test runner
├── TEST_CASES_SPECIFICATION_v1.0.0.md # Полная спецификация
└── README_v1.0.0.md  # Этот файл
```

## Результаты

После запуска:
- Консольный вывод с цветовой индикацией
- JSON отчет: `results/test_report.json`
- Exit code: 0 (success) или 1 (failure)

## Примеры вывода

### Успешный тест
```
→ 1.1 Jinja2 Comments Removal
  ✓ PASSED
  Comments should be removed during validation
```

### Проваленный тест
```
→ 2.1 Trailing Comma Handling
  ✗ FAILED
  Expected trailing comma to be removed
```

## Детальная спецификация

Полное описание всех test cases: [`TEST_CASES_SPECIFICATION_v1.0.0.md`](./TEST_CASES_SPECIFICATION_v1.0.0.md)

## Расширение

Для добавления нового теста:
1. Создайте fixture в `fixtures/`
2. Добавьте test case в `test_validation_suite_v1.0.0.js`
3. Документируйте в спецификации

---

**Coverage**: 16 test cases, 100% функциональности
**Status**: READY FOR TESTING
