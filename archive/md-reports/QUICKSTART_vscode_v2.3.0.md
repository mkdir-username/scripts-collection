# VSCode Validator v2.3.0 - Quickstart Guide

**Быстрый старт** для работы с валидатором SDUI контрактов с поддержкой Jinja2/Java шаблонов.

---

## Установка

### 1. Компиляция (если нужно)

```bash
cd /Users/username/Scripts
npx tsc vscode-validate-on-save_v2.3.0.ts --target ES2020 --module ESNext --moduleResolution node
```

### 2. Проверка

```bash
node vscode-validate-on-save_v2.3.0.js --help
```

---

## Базовое использование

### Валидация JSON файла

```bash
node vscode-validate-on-save_v2.3.0.js path/to/contract.json
```

**Вывод:**

```
✅ CONTRACT VALID
🌐 Web Compatibility ..... 100.0%
📦 Components ............ 15 total (v1: 12, v2: 3)
```

### Валидация Jinja2/Java шаблона

```bash
node vscode-validate-on-save_v2.3.0.js path/to/contract.j2.java
```

**Вывод:**

```
🔧 Jinja2 Template Processing...
   • Imports resolved: 2
   • Variables replaced: 5
✅ CONTRACT VALID
```

---

## Работа с шаблонами

### Синтаксис импортов

```java
// [Описание модуля](file://путь/к/модулю.json)
```

**Примеры:**

```java
// [Common Styles](file://./modules/styles.json)
// [Header Component](file:///Users/username/contracts/header.json)
// [Footer](file://../shared/footer.json)
```

### Синтаксис переменных

```java
{
  "title": "{{ pageTitle }}",
  "count": {{ itemCount }},
  "isVisible": {{ showContent }}
}
```

**Автовывод типов:**

- `isVisible`, `hasData` → `false`
- `itemCount`, `size` → `0`
- `items`, `list` → `[]`
- `config`, `data` → `{}`
- Остальное → `""`

### Пример полного шаблона

```java
// contract.j2.java
{
  "type": "ScreenView",
  // [Header Module](file://./modules/header.json)
  "title": "{{ screenTitle }}",
  "components": [
    {
      "type": "ListView",
      "items": {{ listItems }},
      "isScrollable": {{ enableScroll }}
    },
    // [Footer Module](file://./modules/footer.json)
  ]
}
```

**Модуль header.json:**

```json
{
  "type": "HeaderView",
  "title": "Header",
  "showBackButton": true
}
```

**Результат после парсинга:**

```json
{
  "type": "ScreenView",
  {
    "type": "HeaderView",
    "title": "Header",
    "showBackButton": true
  },
  "title": "",
  "components": [
    {
      "type": "ListView",
      "items": [],
      "isScrollable": false
    },
    {
      "type": "FooterView",
      "links": []
    }
  ]
}
```

---

## Интеграция с VSCode

### Настройка Run on Save

**1. Установите расширение:**

```bash
code --install-extension emeraldwalk.RunOnSave
```

**2. Откройте Settings (JSON):**

`Cmd+Shift+P` → "Preferences: Open User Settings (JSON)"

**3. Добавьте конфигурацию:**

```json
{
  "emeraldwalk.runonsave": {
    "commands": [
      {
        "match": ".*\\.(json|j2\\.java)$",
        "cmd": "node /Users/username/Scripts/vscode-validate-on-save_v2.3.0.js ${file}"
      }
    ]
  }
}
```

### Настройка Tasks

**1. Создайте `.vscode/tasks.json`:**

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Validate SDUI Contract",
      "type": "shell",
      "command": "node",
      "args": [
        "/Users/username/Scripts/vscode-validate-on-save_v2.3.0.js",
        "${file}"
      ],
      "group": {
        "kind": "test",
        "isDefault": true
      },
      "presentation": {
        "reveal": "always",
        "panel": "dedicated"
      },
      "problemMatcher": []
    }
  ]
}
```

**2. Запуск через палитру:**

`Cmd+Shift+P` → "Tasks: Run Task" → "Validate SDUI Contract"

**3. Горячая клавиша:**

`Cmd+Shift+B` (если `isDefault: true`)

---

## Обработка ошибок

### Ошибка парсинга JSON

```
❌ PARSE ERROR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Unexpected token } in JSON at position 234
```

**Решение:** Проверьте синтаксис JSON (запятые, скобки)

### Ошибка импорта модуля

```
🔧 Jinja2 Template Processing...
   ⚠️  Jinja Parse Errors:
     - Импортируемый файл не найден: /path/to/module.json at line 5
```

**Решение:** Проверьте путь к модулю и его существование

### Циклический импорт

```
   ⚠️  Jinja Parse Errors:
     - Обнаружен циклический импорт: /path/to/module.json at line 12
```

**Решение:** Удалите циклическую зависимость между модулями

### Ошибка валидации контракта

```
❌ ERRORS: 1 critical issue
┌─ ButtonView ─────────────────────────────────────────────────────────────┐
│ 1 issue                                                                   │
└───────────────────────────────────────────────────────────────────────────┘

  ❌ [1] Missing required field 'title'

      Path: components[0]
      JSON Pointer: /components/0
      -> /path/to/contract.j2.java:15:1
```

**Решение:** Добавьте обязательное поле `title` в компонент

---

## Примеры команд

### Валидация одного файла

```bash
node vscode-validate-on-save_v2.3.0.js ./contract.json
```

### Валидация всех JSON в директории

```bash
find ./contracts -name "*.json" -exec node vscode-validate-on-save_v2.3.0.js {} \;
```

### Валидация всех .j2.java

```bash
find ./contracts -name "*.j2.java" -exec node vscode-validate-on-save_v2.3.0.js {} \;
```

### Валидация с выводом в файл

```bash
node vscode-validate-on-save_v2.3.0.js contract.json > validation_report.txt 2>&1
```

### Batch валидация с кодом выхода

```bash
#!/bin/bash
SUCCESS=0
FAILED=0

for file in ./contracts/*.json; do
  if node vscode-validate-on-save_v2.3.0.js "$file"; then
    ((SUCCESS++))
  else
    ((FAILED++))
  fi
done

echo "✅ Success: $SUCCESS"
echo "❌ Failed: $FAILED"
```

---

## Производительность

### Оптимизация для больших файлов

**Проблема:** Валидация файла > 500KB занимает > 1s

**Решение:**

1. Разбейте контракт на модули через импорты
2. Используйте .j2.java для переиспользования компонентов
3. Кешируйте результаты валидации

**Пример:**

```java
// Вместо одного большого файла (800KB)
{
  "components": [
    // 200 компонентов...
  ]
}

// Разбейте на модули
{
  "components": [
    // [Profile Components](file://./modules/profile.json)  // 50 компонентов
    // [Settings Components](file://./modules/settings.json) // 50 компонентов
    // [Dashboard Components](file://./modules/dashboard.json) // 100 компонентов
  ]
}
```

**Результат:** Валидация ускоряется в 3-4 раза за счет параллельной обработки модулей.

---

## Troubleshooting

### "Cannot find module jinja_parser_v1.0.0.js"

**Причина:** Внешний Jinja парсер не скомпилирован

**Решение:**

```bash
cd /Users/username/Scripts/validators/v3.0.0
npx tsc jinja_parser_v1.0.0.ts --target ES2020 --module ESNext
```

Или используйте встроенный fallback (работает автоматически).

### "Position map unavailable"

**Причина:** JSON минифицирован (одна строка)

**Решение:** Отформатируйте JSON:

```bash
# VSCode
Cmd+K Cmd+F

# CLI
cat contract.json | jq . > contract_formatted.json
```

### Слишком медленная валидация

**Проверьте размер файла:**

```bash
ls -lh contract.json
```

**Если > 500KB:**

- Разбейте на модули
- Используйте incremental validation
- Добавьте кеширование

---

## FAQ

**Q: Можно ли использовать v2.3.0 вместо v2.2.0 без изменений?**

A: Да, 100% обратная совместимость для .json файлов.

**Q: Поддерживает ли валидатор полную логику Jinja2?**

A: Нет, поддерживаются только базовые конструкции. Для полной логики используйте Python Jinja2.

**Q: Как работает резолвинг относительных путей в импортах?**

A: Относительно директории, где находится файл с импортом.

**Q: Можно ли импортировать .j2.java файлы?**

A: Да, парсер рекурсивно обрабатывает импортированные .j2.java файлы.

**Q: Как избежать циклических импортов?**

A: Используйте односторонние зависимости: common → components → screens.

---

## Дополнительная документация

- **Release Notes:** `RELEASE_NOTES_vscode_v2.3.0.md`
- **Project Guide:** `CLAUDE.md`
- **Jinja Parser:** `/validators/v3.0.0/jinja_parser_README_v1.0.0.md`

---

## Поддержка

**Issues:** Создайте issue в репозитории Scripts
**Questions:** Обратитесь к Agent 03 (Implementation)

**Версия:** v2.3.0
**Дата:** 2025-10-05
