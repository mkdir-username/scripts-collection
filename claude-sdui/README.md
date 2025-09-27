# SDUI Scripts Collection

Коллекция скриптов для работы с SDUI (Server Driven UI) схемами в проекте Front-Middle-Schema.

## 📁 Структура

```
claude-sdui/
├── README.md                    # Эта документация
├── sdui_validator.py           # Валидатор JSON схем
├── sdui_refs_manager.py        # Менеджер $ref ссылок
├── generate_vscode_schemas.py  # Генератор конфигурации VS Code
├── validate_contract.py        # Валидатор контрактов
└── vscode_schemas_config.json  # Готовая конфигурация схем
```

## 🚀 Быстрый старт

### Установка зависимостей
```bash
pip install jsonschema
```

## 📚 Описание скриптов

### 1. sdui_validator.py
**Назначение:** Валидация JSON файлов против их схем с поддержкой file:/// URI.

**Использование:**
```bash
# Базовая валидация
python ~/Scripts/claude-sdui/sdui_validator.py /path/to/SDUI

# С подробным выводом
python ~/Scripts/claude-sdui/sdui_validator.py /path/to/SDUI -v

# Сохранить результаты
python ~/Scripts/claude-sdui/sdui_validator.py /path/to/SDUI -o report.json

# Только sample файлы
python ~/Scripts/claude-sdui/sdui_validator.py /path/to/SDUI --samples-only
```

**Возможности:**
- Автоматическое обнаружение схем для файлов
- Поддержка file:/// URI ссылок
- Детальная отчётность об ошибках
- Кеширование схем для производительности

---

### 2. sdui_refs_manager.py
**Назначение:** Управление $ref ссылками в JSON схемах (конвертация между относительными и абсолютными путями).

**Использование:**
```bash
# Конвертировать в абсолютные пути (file:///)
python ~/Scripts/claude-sdui/sdui_refs_manager.py /path/to/SDUI --to-absolute

# Конвертировать в относительные пути
python ~/Scripts/claude-sdui/sdui_refs_manager.py /path/to/SDUI --to-relative

# Проверить все ссылки
python ~/Scripts/claude-sdui/sdui_refs_manager.py /path/to/SDUI --check

# Dry run (без изменений)
python ~/Scripts/claude-sdui/sdui_refs_manager.py /path/to/SDUI --to-absolute --dry-run
```

**Возможности:**
- Конвертация между форматами путей
- Добавление .json расширений
- Проверка существования файлов
- Безопасный режим с dry-run

---

### 3. generate_vscode_schemas.py
**Назначение:** Генерация конфигурации JSON схем для VS Code settings.json.

### 3.1. generate_deep_vscode_schemas.py ⭐ NEW
**Назначение:** Генерация конфигурации с ГЛУБОКОЙ валидацией всей иерархии схем.

**Особенности:**
- Анализирует ВСЕ зависимости схем рекурсивно
- Регистрирует 420+ схем (вместо 231 в базовой версии)
- Поддерживает полную иерархию вложенных типов
- Правильно обрабатывает атомарные типы (Shape, Size, Color и т.д.)
- Исправляет проблемы с автокомплитом на глубоких уровнях вложенности

**Использование:**
```bash
# Генерация глубокой конфигурации
python ~/Scripts/claude-sdui/generate_deep_vscode_schemas.py /path/to/SDUI -v

# Применение конфигурации
python ~/Scripts/claude-sdui/update_vscode_settings.py
```

### 3.2. update_vscode_settings.py ⭐ NEW
**Назначение:** Автоматическое обновление VS Code settings.json с новой конфигурацией.

**Использование:**
```bash
# Генерировать конфигурацию для SDUI
python ~/Scripts/claude-sdui/generate_vscode_schemas.py /path/to/SDUI

# Сохранить в файл
python ~/Scripts/claude-sdui/generate_vscode_schemas.py /path/to/SDUI -o schemas.json

# С дополнительными паттернами
python ~/Scripts/claude-sdui/generate_vscode_schemas.py /path/to/SDUI --include-tests
```

**Результат:**
Создаёт массив json.schemas для VS Code с маппингами:
- Компоненты и их samples
- Атомы (версионные и нет)
- Лейауты
- Действия
- Функции по категориям
- Модели и общие схемы

**Применение:**
1. Запустить скрипт
2. Открыть VS Code settings.json
3. Найти или создать секцию `"json.schemas"`
4. Вставить сгенерированный массив

---

### 4. validate_contract.py
**Назначение:** Валидация SDUI контрактов на соответствие бизнес-правилам.

**Использование:**
```bash
# Валидировать контракт
python ~/Scripts/claude-sdui/validate_contract.py contract.json

# С проверкой против схемы
python ~/Scripts/claude-sdui/validate_contract.py contract.json --schema ButtonView.json

# Проверка всех контрактов в папке
python ~/Scripts/claude-sdui/validate_contract.py /path/to/contracts/
```

**Проверки:**
- Обязательные поля (type, releaseVersion)
- Версионная совместимость
- Корректность ссылок
- Бизнес-логика компонентов

---

## 🔧 Конфигурация VS Code

### Автоматическая настройка
```bash
# 1. Сгенерировать конфигурацию
python ~/Scripts/claude-sdui/generate_vscode_schemas.py ~/Documents/front-middle-schema/SDUI

# 2. Конфигурация сохранена в vscode_schemas_config.json

# 3. Открыть VS Code settings.json и вставить содержимое
```

### Ручная настройка
Использовать готовый файл `vscode_schemas_config.json` с 231 схемой.

## 📋 Типовые задачи

### Задача 1: Настроить валидацию в новом проекте
```bash
# 1. Конвертировать refs в абсолютные
python ~/Scripts/claude-sdui/sdui_refs_manager.py ./SDUI --to-absolute

# 2. Сгенерировать VS Code конфигурацию
python ~/Scripts/claude-sdui/generate_vscode_schemas.py ./SDUI -o .vscode/schemas.json

# 3. Проверить валидацию
python ~/Scripts/claude-sdui/sdui_validator.py ./SDUI --samples-only
```

### Задача 2: Проверить все sample файлы
```bash
python ~/Scripts/claude-sdui/sdui_validator.py ~/Documents/front-middle-schema/SDUI \
  --samples-only \
  -o validation_report.json \
  -v
```

### Задача 3: Миграция на относительные пути
```bash
# Для коммита в Git лучше использовать относительные пути
python ~/Scripts/claude-sdui/sdui_refs_manager.py ./SDUI --to-relative
```

## 🐛 Решение проблем

### Проблема: "Schema not found"
```bash
# Проверить все ссылки
python ~/Scripts/claude-sdui/sdui_refs_manager.py ./SDUI --check

# Добавить .json расширения
python ~/Scripts/claude-sdui/sdui_refs_manager.py ./SDUI --fix-extensions
```

### Проблема: VS Code не показывает автокомплит
1. Проверить `json.validate.enable: true` в settings.json
2. Перезагрузить VS Code
3. Убедиться что путь к схеме правильный

### Проблема: Циклические ссылки
```bash
# Найти циклические зависимости
python ~/Scripts/claude-sdui/sdui_validator.py ./SDUI --detect-cycles
```

## 📊 Статистика проекта

Текущая конфигурация покрывает:
- **54 компонента** (все версии)
- **19 атомов**
- **8 лейаутов**
- **58 функций**
- **231 схему** всего

## 🔗 Связанные ресурсы

- [VS Code JSON Schema Docs](https://code.visualstudio.com/docs/languages/json#_json-schemas-and-settings)
- [JSON Schema Specification](https://json-schema.org/)
- [SDUI Project Structure](../front-middle-schema/SDUI/README.md)

## 📝 Лицензия

Внутренний проект. Все права защищены.

---
*Создано Claude для работы с SDUI схемами*