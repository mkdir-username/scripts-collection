# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Обзор проекта

Коллекция утилит для разработки и валидации SDUI (Server-Driven UI) контрактов. Основные компоненты:

- **VSCode Validators** - валидация JSON контрактов с интеграцией в VSCode
- **Jinja Hot Reload** - система горячей перезагрузки Jinja2 шаблонов
- **Schema Generators** - генераторы JSON Schema для VSCode
- **Python/JS Utilities** - вспомогательные скрипты для обработки контрактов

## Архитектура

### Структура директорий

```
/Users/username/Scripts/
├── Python/
│   ├── utils/          # Python утилиты (Jinja processors, generators)
│   └── venv/           # Python виртуальное окружение
├── docs/               # Техническая документация
├── tests/              # Тесты и бенчмарки
│   └── fixtures/       # Тестовые данные
├── workspace/          # Временные рабочие директории
└── *.{js,ts,py}        # Версионированные скрипты в корне
```

### Система версионирования

**ОБЯЗАТЕЛЬНЫЙ формат:** `{name}_v{major}.{minor}.{patch}.{ext}`

Примеры:

- ✅ `vscode-validate-on-save_v2.1.0.ts`
- ✅ `jinja_hot_reload_v3.4.0.py`
- ❌ `validator_new.js` (неправильно)
- ❌ `test.py` (неправильно)

### Ключевые компоненты

#### 1. VSCode Validator (vscode-validate-on-save_v2.x.x.ts)

**Назначение:** Валидация SDUI контрактов при сохранении в VSCode

**Ключевые возможности:**

- Position tracking - точное отслеживание позиций в JSON для ссылок на ошибки
- Прогресс-бары и визуальный вывод с box drawing characters
- Интеграция с alfa-sdui-mcp валидатором
- Кликабельные ссылки на ошибки в формате `file:///path#L42`

**Архитектура position tracking:**

```typescript
buildPositionMap(jsonText, parsedData) → PositionMap {
  byPointer: Map<string, PositionInfo>,  // JSON Pointer index
  byPath: Map<string, PositionInfo>      // Property path index
}
```

- Алгоритм: O(n) однопроходный анализ текста
- Fallback стратегия: pointer → path → parent → L1
- Overhead: ~15ms для 239KB файла (3% от общего времени)

**Расположение MCP валидатора:**

```
/Users/username/Documents/FMS_GIT/alfa-sdui-mcp
```

#### 2. Jinja Hot Reload (jinja_hot_reload_v3.x.x.py)

**Назначение:** Горячая перезагрузка Jinja2 шаблонов с отслеживанием зависимостей

**Модули (v3.4.0):**

- FileSystemLoader для загрузки из файловой системы
- Include/Import support с отслеживанием зависимостей
- Auto re-rendering при изменении файлов в цепочке
- Custom filters: `now()`, `isoformat`, `formatCurrency`, `formatDate`, `tojson`, `daysUntil`
- Dependency graph visualization
- Template caching с инвалидацией
- Error recovery с graceful degradation
- Performance monitoring

**Особенность v3.4.0:** Автоопределение чистых Jinja2 шаблонов (начинаются с `{# комментария #}`)

#### 3. Schema Generators

- `generate_vscode_schema_v2.x.x.js` - генерация JSON Schema для VSCode
- `generate_settings_schemas_v1.0.0.js` - генерация схем настроек
- `generate_settings_rules_v1.0.0.py` - генерация правил валидации

## Команды

### Компиляция TypeScript

```bash
npx tsc {filename}.ts --target ES2020 --module ESNext --moduleResolution node
```

### Валидация контрактов

```bash
# CLI
node vscode-validate-on-save_v2.1.0.js path/to/contract.json

# VSCode integration
# Настроить через .vscode/tasks.json + Run on Save extension
```

### Jinja Hot Reload

```bash
python3 Python/utils/jinja_hot_reload_v3.4.0.py [template_file] [context_file]
```

### Бенчмарки

```bash
# TypeScript бенчмарки
tsx tests/position-tracking-benchmark_v1.0.0.ts
```

## Интеграция с VSCode

### tasks.json для валидации

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Validate SDUI Contract",
      "type": "shell",
      "command": "node",
      "args": [
        "/Users/username/Scripts/vscode-validate-on-save_v2.1.0.js",
        "${file}"
      ]
    }
  ]
}
```

### settings.json для auto-validation

```json
{
  "emeraldwalk.runonsave": {
    "commands": [
      {
        "match": ".*\\.json$",
        "cmd": "node /Users/username/Scripts/vscode-validate-on-save_v2.1.0.js ${file}"
      }
    ]
  }
}
```

## Зависимости

### Node.js/TypeScript

- Node.js >= 18.0.0
- TypeScript >= 5.0.0
- `jsonc-parser` для работы с JSON

### Python

- Python >= 3.12
- Jinja2 для шаблонов
- watchdog для отслеживания файлов
- requests для HTTP запросов

### Внешние системы

- **alfa-sdui-mcp** - валидатор SDUI контрактов (расположен в `/Users/username/Documents/FMS_GIT/alfa-sdui-mcp`)

## Важные особенности

### Position Tracking в валидаторе

При валидации контрактов используется оптимизированный position tracking:

1. **buildPositionMap()** строит карту позиций за один проход O(n)
2. **findLineNumber()** ищет позицию с 4-уровневым fallback
3. Ссылки на ошибки содержат реальные номера строк, а не #L1

**Ограничения:** Минифицированный JSON (одна строка) → все ссылки на L1

### Jinja2 Template Processing

Система поддерживает:

- Pure Jinja2 templates (начинаются с `{# ... #}`)
- Mixed Jinja+JSON templates
- Автоопределение типа по первой строке
- Рендеринг Jinja ПЕРЕД парсингом JSON
- Каскадное обновление parent-child зависимостей

### Работа с git

История коммитов показывает:

- Активная разработка валидаторов
- Итерации Jinja Hot Reload (v3.0.0 → v3.4.0)
- Периодическая чистка репозитория

## Производительность

### Benchmark метрики (position tracking)

| Размер файла | buildPositionMap() | Overhead |
| ------------ | ------------------ | -------- |
| 50 KB        | ~3ms               | 2%       |
| 239 KB       | ~15ms              | 3%       |
| 500 KB       | ~35ms              | 4%       |
| 1 MB         | ~75ms              | 5%       |

**Целевой показатель:** < 100ms для 239KB (достигнут с запасом)

## Troubleshooting

### Position map unavailable

```
⚠️  Line resolution: single-line JSON, using #L1 for all paths
```

**Решение:** Отформатировать JSON с отступами (Cmd+K Cmd+F в VSCode)

### Cannot find module (MCP)

**Решение:** Проверить путь к alfa-sdui-mcp в переменной `MCP_ROOT`

### TypeScript compilation errors

```bash
npx tsc {file}.ts --target ES2020 --module ESNext --moduleResolution node --esModuleInterop --skipLibCheck
```
