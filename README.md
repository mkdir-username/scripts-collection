# Scripts & Utilities

> Коллекция утилит и скриптов для работы с SDUI

**Последнее обновление**: 22 октября 2025

---

## 📁 Структура

```
Scripts/
├── active/                 # ⭐ Актуальные скрипты (symlinks)
│   ├── jinja_hot_reload.py → Python/utils/jinja_hot_reload_v3.6.0.py
│   └── validate_sdui.py → validators/v3.0.0/sdui_web_validator_v3.0.0.py
│
├── Python/
│   ├── utils/             # Утилиты
│   │   ├── jinja_hot_reload_v3.6.0.py  # ⭐ ТЕКУЩАЯ
│   │   ├── sdui_jinja_extensions.py
│   │   ├── sdui_to_jinja2_transformer.py
│   │   └── archive/       # Старые версии v1-v3.5
│   │
│   ├── sdui/              # SDUI утилиты
│   │   └── archive/       # Старые версии
│   │
│   └── refs/              # Refs конвертеры
│
├── Bash/                  # Bash скрипты
│   └── archive/           # Старые версии
│
├── validators/            # Валидаторы
│   ├── v3.0.0/           # ⭐ ТЕКУЩАЯ версия
│   └── archive/           # v1.x, v2.x
│
├── deprecated/            # Устаревшие проекты
│   ├── alfa-sdui-mcp/
│   ├── claude-agents_v2/
│   ├── claude-sdui/
│   ├── json-schema-mcp/
│   ├── vscode-validator-v2.3.1/
│   ├── xray-installer/
│   └── zen-mcp-server/
│
├── archive/               # Архивы
│   ├── md-reports/        # MD отчёты от агентов
│   ├── old-scripts/       # Старые JS/TS скрипты
│   └── old-bash/          # Старые bash скрипты
│
├── docs/                  # Документация
│
├── .cursorignore          # Исключения для Cursor AI
└── README.md             # Этот файл
```

---

## ⭐ Активные скрипты (active/)

Используй скрипты из этой директории - они всегда указывают на актуальные версии:

### jinja_hot_reload.py
```bash
python ~/Scripts/active/jinja_hot_reload.py

# Или полный путь
python /Users/username/Scripts/active/jinja_hot_reload.py
```

**Назначение**: Парсинг Jinja2-JSON контрактов  
**Версия**: 3.6.0  
**Документация**: Внутри файла (docstring)

### validate_sdui.py
```bash
python ~/Scripts/active/validate_sdui.py <contract.json>
```

**Назначение**: Валидация SDUI контрактов  
**Версия**: 3.0.0

---

## 📦 Python Scripts

### Python/utils/

#### jinja_hot_reload_v3.6.0.py ⭐
**Текущая стабильная версия** парсера Jinja→JSON

**Использование**:
```bash
cd /Users/username/Documents/FMS_GIT/_JSON/WEB/feature/desktop/
python ~/Scripts/Python/utils/jinja_hot_reload_v3.6.0.py
```

**Особенности**:
- Hot reload (watch режим)
- Подстановка variables из [data]*.json
- Поддержка include/import
- Error recovery
- Performance monitoring

#### sdui_jinja_extensions.py
Кастомные Jinja2 фильтры для SDUI:
- `formatAmount()` - форматирование сумм
- `formatDate()` - форматирование дат
- И другие...

#### sdui_to_jinja2_transformer.py
Трансформация SDUI синтаксиса в Jinja2

#### archive/
Старые версии jinja_hot_reload (v1.0.0 - v3.5.0)

---

### Python/sdui/

SDUI специфичные скрипты:
- Валидаторы
- API утилиты
- Resolvers

**archive/**: Старые версии

---

### Python/refs/

Утилиты для работы с JSON $ref:
- `convert_to_absolute_refs_v1.0.0.py`
- `fix_broken_refs_v1.0.0.py`
- `sdui_refs_manager_v1.0.0.py`
- И другие...

---

## 🛡️ Validators

### validators/v3.0.0/ ⭐
**Текущая версия** валидаторов SDUI контрактов

**Файлы**:
- `sdui_web_validator_v3.0.0.py` - основной валидатор

**Использование**:
```bash
python ~/Scripts/validators/v3.0.0/sdui_web_validator_v3.0.0.py <contract.json>
```

### validators/archive/
Старые версии (v1.x, v2.x)

---

## 💻 Bash Scripts

### Bash/

Активные bash скрипты:
- `run_for_dir_fms.sh` - запуск для FMS директорий
- `smart-kill.sh` - умное завершение процессов
- `sdui_validator.sh` - bash обёртка валидатора
- И другие...

### Bash/archive/
Старые версии

---

## 🗑️ Deprecated Projects

### deprecated/

Устаревшие проекты, которые больше не используются:
- `alfa-sdui-mcp/` - старая MCP интеграция
- `claude-agents_v2/` - старые агенты
- `claude-sdui/` - старые SDUI утилиты
- `json-schema-mcp/` - старый MCP сервер
- `vscode-validator-v2.3.1/` - старый VSCode валидатор
- `xray-installer/` - установщик Xray
- `zen-mcp-server/` - старый MCP сервер

**Статус**: Сохранены для истории, не индексируются

---

## 📚 Archive

### archive/md-reports/
MD отчёты от AI агентов (CHANGELOG, MIGRATION, SUMMARY и т.д.)

### archive/old-scripts/
Старые JS/TS скрипты (computed_data_parser, vscode-validate-on-save и т.д.)

### archive/old-bash/
Старые bash скрипты (format-json-jinja, install и т.д.)

---

## 🚀 Быстрый доступ

### Парсинг Jinja контракта
```bash
cd /Users/username/Documents/FMS_GIT/_JSON/WEB/my-feature/desktop/
python ~/Scripts/active/jinja_hot_reload.py
```

### Валидация контракта
```bash
python ~/Scripts/active/validate_sdui.py ~/Documents/FMS_GIT/_JSON/WEB/my-feature/desktop/[FULL_PC]_my-feature_web.json
```

### Запуск валидатора для директории FMS
```bash
cd ~/Documents/FMS_GIT
bash ~/Scripts/Bash/run_for_dir_fms.sh
```

---

## 📝 Maintenance

### Добавление нового скрипта

1. Создай в соответствующей директории:
   - Python скрипты → `Python/utils/`
   - Bash скрипты → `Bash/`
   - Валидаторы → `validators/vX.X.X/`

2. Если скрипт критичен - добавь symlink:
   ```bash
   cd ~/Scripts/active
   ln -sf ../Python/utils/my_script.py my_script.py
   ```

### Архивация старой версии

```bash
cd ~/Scripts/Python/utils
mv old_script_v1.0.0.py archive/
```

### Обновление README

После значительных изменений обнови этот README

---

## 🔒 Git Ignore

Все вспомогательные файлы и архивы исключены из индексации через `.cursorignore`:
- `archive/`, `deprecated/`, `workspace/`
- `venv/`, `node_modules/`
- `*REPORT*.md`, `*SUMMARY*.md`

---

## 📊 Статистика

- **Активных скриптов**: 2 (в active/)
- **Архивировано версий**: ~50+
- **Deprecated проектов**: 7
- **Общий размер архивов**: ~500 MB

---

## 🔗 Связь с проектами

### FMS_GIT
→ Использует `jinja_hot_reload.py` для парсинга контрактов

### Validators
→ Используются в CI/CD для проверки контрактов

### SDUI проекты
→ Общие утилиты для всех SDUI проектов

---

**Организовано**: 22 октября 2025  
**Статус**: ✅ ЧИСТО И СТРУКТУРИРОВАНО

