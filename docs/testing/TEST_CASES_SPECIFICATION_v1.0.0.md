# Test Cases Specification v1.0.0

Комплексный набор тестовых сценариев для проверки всех исправлений в системе валидации Jinja2/JSON.

---

## 📋 Оглавление

1. [Pure Jinja2 Templates](#1-pure-jinja2-templates)
2. [Mixed JSON+Jinja2](#2-mixed-jsonjinja2)
3. [SDUI Fallback](#3-sdui-fallback)
4. [Error Recovery](#4-error-recovery)
5. [Запуск тестов](#запуск-тестов)

---

## 1. Pure Jinja2 Templates

### 1.1 Jinja2 Comments Removal

**Цель**: Проверить корректное удаление Jinja2 комментариев `{# #}`

**Входные данные**:
```json
{# This is a Jinja2 comment that should be removed #}
{
  "type": "ButtonView",
  {# Another comment inside object #}
  "title": {
    "defaultValue": "Click Me"
  }
}
```

**Ожидаемый результат**:
- Все комментарии `{# ... #}` удалены перед валидацией
- Результат является валидным JSON после рендеринга
- Структура данных сохранена

**Критерий успеха**:
```javascript
// После обработки Jinja2:
{
  "type": "ButtonView",
  "title": {
    "defaultValue": "Click Me"
  }
}
```

**Fixture**: `/tests/fixtures/pure_jinja2_with_comments.json`

---

### 1.2 Jinja2 Include Directive

**Цель**: Проверить обработку директивы `{% include %}`

**Входные данные**:
```json
{
  "type": "LayoutElement",
  "children": [
    {% include 'button_component.json' %},
    {
      "type": "TextView",
      "text": "{{ user_name }}"
    }
  ]
}
```

**button_component.json**:
```json
{
  "type": "ButtonView",
  "title": {
    "defaultValue": "Included Button"
  }
}
```

**Ожидаемый результат**:
- Include директива заменена содержимым файла
- Автоматически добавлена запятая между элементами массива
- Итоговый JSON валиден

**Критерий успеха**:
```javascript
// После рендеринга:
{
  "type": "LayoutElement",
  "children": [
    {
      "type": "ButtonView",
      "title": {
        "defaultValue": "Included Button"
      }
    },
    {
      "type": "TextView",
      "text": "John Doe"
    }
  ]
}
```

**Fixture**: `/tests/fixtures/jinja2_with_include.json`

---

### 1.3 Undefined Variables Handling

**Цель**: Проверить обработку undefined переменных с и без фильтров

**Входные данные**:
```json
{
  "type": "TextView",
  "text": "Hello {{ undefined_variable }}",
  "subtitle": "{{ another_undefined | default('N/A') }}",
  "metadata": {
    "timestamp": "{{ current_time }}",
    "user": "{{ user_id | default('anonymous') }}"
  }
}
```

**Ожидаемый результат**:
- Переменные с `| default()` заменяются на значения по умолчанию
- Переменные без фильтра вызывают предупреждение, но не ломают валидацию
- JSON остается валидным

**Критерий успеха**:
```javascript
// С пустым контекстом:
{
  "type": "TextView",
  "text": "Hello ",
  "subtitle": "N/A",
  "metadata": {
    "timestamp": "",
    "user": "anonymous"
  }
}
```

**Fixture**: `/tests/fixtures/jinja2_undefined_vars.json`

---

### 1.4 Format Strings in Templates

**Цель**: Проверить поддержку Python format strings в Jinja2

**Входные данные**:
```json
{
  "type": "TextView",
  "text": "User: {{ user.name | upper }}",
  "formatted": "{{ '{:,.2f}'.format(price) }}",
  "pythonic": "{{ f'Total: {total:.2f}' }}",
  "nested": {
    "pattern": "{{ 'ID: {}'.format(item_id) }}"
  }
}
```

**Контекст**:
```python
{
  "user": {"name": "john"},
  "price": 1234.567,
  "total": 99.99,
  "item_id": 42
}
```

**Ожидаемый результат**:
- `.format()` работает корректно
- F-strings (если поддерживаются) обрабатываются
- Фильтры Jinja2 применяются

**Критерий успеха**:
```javascript
{
  "type": "TextView",
  "text": "User: JOHN",
  "formatted": "1,234.57",
  "pythonic": "Total: 99.99",
  "nested": {
    "pattern": "ID: 42"
  }
}
```

**Fixture**: `/tests/fixtures/jinja2_format_strings.json`

---

## 2. Mixed JSON+Jinja2

### 2.1 Trailing Comma Handling

**Цель**: Проверить обнаружение и исправление trailing commas после include

**Входные данные**:
```json
{
  "type": "LayoutElement",
  "children": [
    {% include 'button.json' %},
    {
      "type": "TextView",
      "text": "{{ message }}"
    },
  ]
}
```

**Проблема**: Лишняя запятая после последнего элемента массива

**Ожидаемый результат**:
- Trailing comma обнаружена
- При рендеринге запятая корректно обработана
- Итоговый JSON валиден

**Критерий успеха**:
```javascript
// После обработки:
{
  "type": "LayoutElement",
  "children": [
    {...},  // content from button.json
    {
      "type": "TextView",
      "text": "Hello"
    }
  ]  // NO trailing comma
}
```

**Fixture**: `/tests/fixtures/mixed_trailing_comma.json`

---

### 2.2 Missing Comma Detection

**Цель**: Проверить обнаружение отсутствующих запятых между элементами

**Входные данные**:
```json
{
  "type": "StackView",
  "children": [
    {
      "type": "ButtonView",
      "title": {"defaultValue": "Button 1"}
    }
    {% include 'separator.json' %}
    {
      "type": "ButtonView",
      "title": {"defaultValue": "Button 2"}
    }
  ]
}
```

**Проблема**: Отсутствуют запятые между `}` и `{%`, а также после `%}` и `{`

**Ожидаемый результат**:
- Missing commas обнаружены
- Автоматически добавлены запятые
- JSON валиден после рендеринга

**Критерий успеха**:
```javascript
// После обработки:
{
  "type": "StackView",
  "children": [
    {
      "type": "ButtonView",
      "title": {"defaultValue": "Button 1"}
    },  // ADDED COMMA
    {
      "type": "Divider",
      "height": 1
    },  // ADDED COMMA
    {
      "type": "ButtonView",
      "title": {"defaultValue": "Button 2"}
    }
  ]
}
```

**Fixture**: `/tests/fixtures/mixed_missing_comma.json`

---

### 2.3 Nested Structures with Jinja2

**Цель**: Проверить обработку вложенных структур с Jinja2

**Входные данные**:
```json
{
  "type": "LayoutElement",
  "data": {
    "user": {
      "name": "{{ user.name }}",
      "profile": {% include 'profile.json' %},
      "settings": {
        "theme": "{{ theme | default('light') }}",
        "notifications": [
          {% for notif in notifications %}
          {
            "type": "{{ notif.type }}",
            "enabled": {{ notif.enabled | lower }}
          }{% if not loop.last %},{% endif %}
          {% endfor %}
        ]
      }
    }
  }
}
```

**Ожидаемый результат**:
- Вложенные include обработаны
- For loops работают корректно
- Условные запятые расставлены правильно
- Глубокая вложенность сохранена

**Критерий успеха**:
```javascript
// С контекстом:
{
  "user": {"name": "Alice"},
  "theme": "dark",
  "notifications": [
    {"type": "email", "enabled": true},
    {"type": "push", "enabled": false}
  ]
}

// Результат:
{
  "type": "LayoutElement",
  "data": {
    "user": {
      "name": "Alice",
      "profile": {...},  // from profile.json
      "settings": {
        "theme": "dark",
        "notifications": [
          {
            "type": "email",
            "enabled": "true"
          },
          {
            "type": "push",
            "enabled": "false"
          }
        ]
      }
    }
  }
}
```

**Fixture**: `/tests/fixtures/mixed_nested_structures.json`

---

### 2.4 Comments with Imports

**Цель**: Проверить совместную работу комментариев и include

**Входные данные**:
```json
{# Import base layout #}
{% include 'base_layout.json' %}

{# Override specific properties #}
{
  "customizations": {
    {# Dynamic title #}
    "title": "{{ page_title }}",
    {# Include footer #}
    "footer": {% include 'footer.json' %}
  }
}
```

**Ожидаемый результат**:
- Комментарии удалены
- Include обработаны
- Структура объединена корректно
- Запятые расставлены правильно

**Критерий успеха**:
```javascript
// Результат:
{
  "type": "Screen",
  "header": {
    "type": "HeaderView",
    "title": "Default Title"
  },
  "body": {
    "type": "LayoutElement"
  },
  "customizations": {
    "title": "My Page",
    "footer": {
      "type": "FooterView",
      "text": "Copyright 2025"
    }
  }
}
```

**Fixture**: `/tests/fixtures/mixed_comment_imports.json`

---

## 3. SDUI Fallback

### 3.1 SDUI Without Modules

**Цель**: Проверить fallback на JSON валидацию при отсутствии SDUI модулей

**Входные данные**:
```json
{
  "type": "ButtonView",
  "releaseVersion": {
    "web": "released",
    "android": "released",
    "ios": "released"
  },
  "title": {
    "defaultValue": "Submit",
    "highlightedValue": "Submit!"
  },
  "backgroundColor": {
    "defaultValue": "#007AFF"
  }
}
```

**Ожидаемый результат**:
- Файл распознан как чистый JSON (без Jinja2)
- SDUI модули не загружены
- Fallback на обычную JSON валидацию
- Структура соответствует SDUI schema

**Критерий успеха**:
```javascript
// Валидация проходит как обычный JSON
// Предупреждение: "SDUI modules not available, using JSON validation"
// Результат: VALID
```

**Fixture**: `/tests/fixtures/sdui_without_modules.json`

---

### 3.2 SDUI With Modules

**Цель**: Проверить работу с SDUI модулями при их наличии

**Входные данные**:
```json
{
  "type": "ButtonView",
  "releaseVersion": {
    "web": "released"
  },
  "title": {
    "defaultValue": "Click Here"
  },
  "action": {
    "type": "HttpAction",
    "url": "/api/submit",
    "method": "POST"
  },
  "style": {
    "$ref": "#/components/styles/primaryButton"
  }
}
```

**Ожидаемый результат**:
- SDUI модули загружены
- `$ref` разрешены
- Schema validation выполнена
- ReleaseVersion проверен

**Критерий успеха**:
```javascript
// SDUI validation active
// $ref resolved to actual style object
// Schema compliance: PASS
// Platform check: web = "released" ✓
```

**Fixture**: `/tests/fixtures/sdui_with_modules.json`

---

### 3.3 SDUI Transformation

**Цель**: Проверить трансформацию Jinja2 в SDUI контексте

**Входные данные**:
```json
{
  "type": "LayoutElement",
  "releaseVersion": {
    "web": "released"
  },
  "children": [
    {
      "type": "TextView",
      "text": {
        "defaultValue": "Welcome {{ user_name }}"
      },
      "textColor": {
        "defaultValue": "#000000",
        "highlightedValue": "#FF0000"
      }
    }
  ]
}
```

**Ожидаемый результат**:
- Обнаружен Jinja2 внутри SDUI
- Выполнен Jinja2 rendering
- Результат валидирован по SDUI schema
- StateAware паттерны сохранены

**Критерий успеха**:
```javascript
// После рендеринга с контекстом {user_name: "Alice"}:
{
  "type": "LayoutElement",
  "releaseVersion": {
    "web": "released"
  },
  "children": [
    {
      "type": "TextView",
      "text": {
        "defaultValue": "Welcome Alice"
      },
      "textColor": {
        "defaultValue": "#000000",
        "highlightedValue": "#FF0000"
      }
    }
  ]
}
// ✓ SDUI schema valid
// ✓ StateAware patterns preserved
```

**Fixture**: `/tests/fixtures/sdui_transformation.json`

---

## 4. Error Recovery

### 4.1 Template Not Found Error

**Цель**: Проверить обработку ошибки отсутствующего шаблона

**Входные данные**:
```json
{
  "type": "LayoutElement",
  "children": [
    {% include 'non_existent_template.json' %},
    {
      "type": "TextView",
      "text": "This should still work"
    }
  ]
}
```

**Ожидаемый результат**:
- Ошибка: `TemplateNotFound: non_existent_template.json`
- Валидация прервана
- Четкое сообщение об ошибке
- Указана строка с ошибкой

**Критерий успеха**:
```javascript
// Error output:
{
  "valid": false,
  "errors": [
    {
      "type": "TemplateNotFound",
      "message": "Template 'non_existent_template.json' not found",
      "line": 3,
      "suggestion": "Check file path and ensure template exists"
    }
  ]
}
```

**Fixture**: `/tests/fixtures/error_template_not_found.json`

---

### 4.2 Jinja2 Syntax Error

**Цель**: Проверить обработку синтаксических ошибок Jinja2

**Входные данные**:
```json
{
  "type": "ButtonView",
  "title": {
    "defaultValue": "{{ unclosed_tag "
  },
  "action": {
    "type": "{{ action_type }"
  }
}
```

**Ожидаемый результат**:
- Ошибка: `TemplateSyntaxError: unexpected end of template`
- Указана позиция незакрытого тега
- Валидация прервана

**Критерий успеха**:
```javascript
// Error output:
{
  "valid": false,
  "errors": [
    {
      "type": "TemplateSyntaxError",
      "message": "unexpected end of template, expected '}}' or '}}'",
      "line": 4,
      "column": 31,
      "suggestion": "Close the Jinja2 expression with '}}'"
    }
  ]
}
```

**Fixture**: `/tests/fixtures/error_syntax_error.json`

---

### 4.3 JSON Decode Error

**Цель**: Проверить обработку невалидного JSON после рендеринга

**Входные данные**:
```json
{
  "type": "TextView",
  "text": "Valid text",
  "invalidField": {{ this_is_not_valid_json }},
  "nested": {
    "broken": {{ undefined }}
  }
}
```

**Контекст**: `{}` (пустой)

**Ожидаемый результат**:
- Jinja2 рендеринг завершается
- JSON.parse() падает
- Четкое сообщение об ошибке
- Указана позиция невалидного JSON

**Критерий успеха**:
```javascript
// После рендеринга:
{
  "type": "TextView",
  "text": "Valid text",
  "invalidField": ,  // INVALID!
  "nested": {
    "broken":
  }
}

// Error:
{
  "valid": false,
  "errors": [
    {
      "type": "JSONDecodeError",
      "message": "Unexpected token ',' at position 67",
      "line": 4,
      "suggestion": "Check Jinja2 variables render to valid JSON values"
    }
  ]
}
```

**Fixture**: `/tests/fixtures/error_json_decode.json`

---

### 4.4 Circular Include Detection

**Цель**: Проверить обнаружение циклических включений

**Входные данные**:

**error_circular_include.json**:
```json
{
  "type": "LayoutElement",
  "children": [
    {% include 'error_circular_include_2.json' %}
  ]
}
```

**error_circular_include_2.json**:
```json
{
  "type": "TextView",
  "nested": {% include 'error_circular_include.json' %}
}
```

**Ожидаемый результат**:
- Обнаружен циклический include
- Ошибка: `RecursionError` или `Circular include detected`
- Валидация прервана
- Указан путь циркуляции

**Критерий успеха**:
```javascript
// Error:
{
  "valid": false,
  "errors": [
    {
      "type": "CircularIncludeError",
      "message": "Circular include detected",
      "path": [
        "error_circular_include.json",
        "error_circular_include_2.json",
        "error_circular_include.json"
      ],
      "suggestion": "Remove circular dependency between templates"
    }
  ]
}
```

**Fixture**: `/tests/fixtures/error_circular_include.json`

---

## Запуск тестов

### Быстрый запуск

```bash
cd /Users/username/Scripts/tests
node test_validation_suite_v1.0.0.js
```

### Ожидаемый вывод

```
═══════════════════════════════════════════════
  TEST CATEGORY 1: Pure Jinja2 Templates
═══════════════════════════════════════════════

→ 1.1 Jinja2 Comments Removal
  ✓ PASSED
  Comments should be removed during validation

→ 1.2 Jinja2 Include Directive
  ✓ PASSED
  Include directive found (will be processed by Jinja2)

...

═══════════════════════════════════════════════
  TEST EXECUTION SUMMARY
═══════════════════════════════════════════════

Total Tests:  16
Passed:       16
Failed:       0
Skipped:      0

Success Rate: 100.0%

Report saved to: /Users/username/Scripts/tests/results/test_report.json
```

### Интерпретация результатов

| Статус | Описание |
|--------|----------|
| ✓ PASSED | Тест прошел успешно, функционал работает как ожидалось |
| ✗ FAILED | Тест не прошел, обнаружена проблема в реализации |
| ⊘ SKIPPED | Тест пропущен (зависимость не выполнена) |

### Просмотр отчета

```bash
cat /Users/username/Scripts/tests/results/test_report.json
```

Пример отчета:
```json
{
  "timestamp": "2025-10-02T14:30:00.000Z",
  "summary": {
    "total": 16,
    "passed": 16,
    "failed": 0,
    "skipped": 0,
    "successRate": "100.0%"
  },
  "errors": []
}
```

---

## Структура тестовых файлов

```
tests/
├── fixtures/                          # Тестовые данные
│   ├── pure_jinja2_with_comments.json
│   ├── jinja2_with_include.json
│   ├── button_component.json
│   ├── jinja2_undefined_vars.json
│   ├── jinja2_format_strings.json
│   ├── mixed_trailing_comma.json
│   ├── mixed_missing_comma.json
│   ├── separator.json
│   ├── mixed_nested_structures.json
│   ├── profile.json
│   ├── mixed_comment_imports.json
│   ├── base_layout.json
│   ├── footer.json
│   ├── sdui_without_modules.json
│   ├── sdui_with_modules.json
│   ├── sdui_transformation.json
│   ├── error_template_not_found.json
│   ├── error_syntax_error.json
│   ├── error_json_decode.json
│   ├── error_circular_include.json
│   └── error_circular_include_2.json
├── cases/                             # Описания test cases (опционально)
├── results/                           # Результаты тестирования
│   └── test_report.json
├── test_validation_suite_v1.0.0.js   # Основной test runner
└── TEST_CASES_SPECIFICATION_v1.0.0.md # Эта спецификация
```

---

## Критерии качества

### Покрытие функционала

- ✅ Pure Jinja2: 4/4 cases
- ✅ Mixed JSON+Jinja2: 4/4 cases
- ✅ SDUI Fallback: 3/3 cases
- ✅ Error Recovery: 4/4 cases

**Итого: 16 test cases, 100% покрытие**

### Критические сценарии

1. **Комментарии + Include** (2.4) - самый сложный case
2. **Circular Include** (4.4) - критичная безопасность
3. **SDUI Transformation** (3.3) - основной use case

### Метрики успешности

- Success Rate ≥ 95% - система стабильна
- Success Rate 80-95% - требуются доработки
- Success Rate < 80% - критические проблемы

---

## Расширение тестов

### Добавление нового test case

1. Создать fixture в `/tests/fixtures/`
2. Добавить test в `test_validation_suite_v1.0.0.js`
3. Документировать в этом файле
4. Запустить полный test suite

### Шаблон нового теста

```javascript
runTest('X.Y Test Name', () => {
  const input = fs.readFileSync(
    path.join(__dirname, 'fixtures/test_fixture.json'),
    'utf8'
  );

  // Ваша логика проверки
  const condition = checkSomething(input);

  return {
    success: condition,
    message: condition ? 'Passed message' : 'Failed message'
  };
});
```

---

**Версия**: 1.0.0
**Дата**: 2025-10-02
**Статус**: READY FOR TESTING
