# Анализ Python валидаторов в проекте front-middle-schema

## Обнаруженные валидаторы

### 1. Основные валидаторы в корне проекта

| Файл | Версия | Зависимости | Статус | Назначение |
|------|--------|-------------|---------|------------|
| `sdui_web_validator_v2.0.0_advanced_lines.py` | v2.0.0 | json, sys, os, re, Path, typing | Актуальный | Продвинутая валидация с точным определением номеров строк |
| `sdui_web_validator.py` | - | json, os, Path, typing, hashlib, datetime, re, defaultdict, **sdui_index_cache** | Требует зависимость | Основной валидатор WEB платформы с кэшированием |
| `sdui_web_validator_new.py` | - | json, sys, os, Path, typing | Автономный | Новая версия валидатора |
| `sdui_web_validator_improved.py` | - | json, typing, Path, datetime | Автономный | Улучшенная версия |
| `sdui_web_validator_with_lines.py` | - | json, sys, os, re, Path, typing | Автономный | Валидатор с поддержкой номеров строк |
| `byzantine_validator.py` | - | json, os, typing, Enum, defaultdict, re, datetime | Автономный | Byzantine Fault-Tolerant валидатор |
| `agent_terminal_validator.py` | - | json, sys, os, subprocess, Path, urllib, time | Автономный | Валидатор с проверкой через эндпоинты |
| `sdui_visual_validator.py` | - | json, os, time, **requests**, Path, typing, datetime, base64, hashlib, **sdui_web_validator_improved** | Требует зависимости | Визуальный валидатор с проверкой рендеринга |
| `simple_validator.py` | - | json, sys, os, Path | Автономный | Простой валидатор без зависимостей |
| `simple_validator_fixed.py` | - | json, sys, os, Path | Автономный | Исправленная версия простого валидатора |
| `sdui_contract_validator.py` | - | json, subprocess, sys, Path | Автономный | Контрактный валидатор |
| `test_validators.py` | - | json, sys, Path | Тестовый | Тесты для валидаторов |
| `check_validator_compatibility.py` | - | os, sys, importlib.util, Path | Утилита | Проверка совместимости валидаторов |

### 2. Архивные версии в /validators/archive/

| Файл | Версия | Зависимости | Статус |
|------|--------|-------------|---------|
| `sdui_web_validator_v1.0.0.py` | v1.0.0 | json, os, Path, typing, hashlib, datetime, re, defaultdict, **sdui_index_cache** | Архив |
| `sdui_web_validator_v1.1.0.py` | v1.1.0 | json, sys, os, Path, typing | Архив |
| `sdui_web_validator_v1.2.0_with_lines.py` | v1.2.0 | json, sys, os, re, Path, typing | Архив |
| `sdui_web_validator_improved.py` | - | json, typing, Path, datetime | Архив |

### 3. Встроенные валидаторы в подпроектах

| Файл | Расположение | Статус |
|------|--------------|---------|
| `validator.py` | superclaide-framework/setup/core/ | Часть фреймворка |
| `validator_wrapper.py` | SDUI/sdui-mcp-framework/modules/ | MCP обёртка |

## Внешние зависимости

### Обязательные Python модули
- **Встроенные**: json, sys, os, re, subprocess, time, base64, hashlib, datetime, urllib, enum
- **Python стандартные**: pathlib (Path), typing, collections (defaultdict), importlib.util

### Внешние зависимости
- **requests** - требуется для `sdui_visual_validator.py`
- **sdui_index_cache.py** - локальный модуль (25KB, найден в проекте)
- **sdui_web_validator_improved** - зависимость для visual validator

## Классификация по функциональности

### 1. Базовые валидаторы (без внешних зависимостей)
- `simple_validator.py` - минимальная функциональность
- `simple_validator_fixed.py` - исправленная версия

### 2. Продвинутые валидаторы
- `sdui_web_validator_v2.0.0_advanced_lines.py` - самый актуальный, с точными номерами строк
- `sdui_web_validator.py` - основной с кэшированием (требует sdui_index_cache)
- `sdui_web_validator_with_lines.py` - с поддержкой номеров строк

### 3. Специализированные валидаторы
- `byzantine_validator.py` - Byzantine Fault-Tolerant проверки
- `agent_terminal_validator.py` - интеграция с эндпоинтами
- `sdui_visual_validator.py` - визуальная валидация (требует requests)

### 4. Утилиты
- `check_validator_compatibility.py` - проверка совместимости
- `test_validators.py` - тестирование

## Рекомендации по организации

### Структура директории /Users/username/Scripts/validators/

```
validators/
├── v2.0.0/                          # Актуальная версия
│   ├── sdui_web_validator.py       # Основной валидатор v2.0.0
│   ├── line_mapper.py               # Модуль для работы с номерами строк
│   └── README.md                    # Документация
│
├── v1.0.0/                          # Стабильные версии
│   ├── simple_validator.py         # Простой валидатор
│   └── byzantine_validator.py      # Byzantine валидатор
│
├── specialized/                     # Специализированные
│   ├── visual_validator.py         # Визуальный валидатор
│   ├── terminal_validator.py       # Терминальный валидатор
│   └── contract_validator.py       # Контрактный валидатор
│
├── utils/                           # Вспомогательные модули
│   ├── sdui_index_cache.py        # Кэширование индексов
│   ├── compatibility_checker.py    # Проверка совместимости
│   └── test_runner.py              # Запуск тестов
│
├── archive/                         # Архивные версии
│   ├── v1.0.0/
│   ├── v1.1.0/
│   └── v1.2.0/
│
├── requirements.txt                 # Зависимости
├── setup.py                        # Установка
└── README.md                       # Главная документация
```

## Зависимости для requirements.txt

```txt
# Основные зависимости
requests>=2.28.0  # Для visual_validator

# Опциональные зависимости для разработки
pytest>=7.0.0
black>=22.0.0
pylint>=2.15.0
```

## План миграции

### Фаза 1: Подготовка (Немедленно)
1. ✅ Создать директорию `/Users/username/Scripts/validators/`
2. Скопировать `sdui_index_cache.py` в `utils/`
3. Создать структуру директорий

### Фаза 2: Организация основных валидаторов
1. Переместить `sdui_web_validator_v2.0.0_advanced_lines.py` → `v2.0.0/sdui_web_validator.py`
2. Выделить класс `AdvancedJSONLineMapper` в отдельный модуль `v2.0.0/line_mapper.py`
3. Обновить импорты

### Фаза 3: Организация специализированных валидаторов
1. Переместить специализированные валидаторы в `specialized/`
2. Унифицировать интерфейсы
3. Создать общий базовый класс

### Фаза 4: Архивация
1. Переместить старые версии в `archive/`
2. Создать индекс версий
3. Документировать изменения между версиями

### Фаза 5: Интеграция
1. Создать единую точку входа `validate.py`
2. Настроить автоматический выбор валидатора
3. Интегрировать с CI/CD

## Приоритеты

### Критические
1. Сохранить работоспособность `sdui_web_validator_v2.0.0_advanced_lines.py`
2. Обеспечить доступность `sdui_index_cache.py`

### Важные
1. Организовать версионирование
2. Создать документацию
3. Настроить тесты

### Желательные
1. Унифицировать API
2. Создать CLI интерфейс
3. Добавить логирование

## Статистика

- **Всего валидаторов**: 19 файлов
- **Активных**: 13
- **Архивных**: 4
- **Утилит**: 2
- **Требуют внешних зависимостей**: 2 (visual_validator, основной с кэшем)
- **Полностью автономных**: 11

## Следующие шаги

1. Создать базовую структуру директорий
2. Скопировать критические файлы
3. Обновить импорты и зависимости
4. Протестировать работоспособность
5. Создать документацию