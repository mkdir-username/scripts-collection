# Scripts Directory Cleanup Plan

## Текущее состояние (хаос)

### Проблемы
- 21 версия jinja_hot_reload в utils/
- Дубли скриптов в корне и Python/
- Множество MD отчётов от агентов
- Неструктурированные workspace/
- Старые venv и node_modules

## План структуры

```
Scripts/
├── active/                    # Активные скрипты (текущие версии)
│   ├── jinja_hot_reload.py   # Symlink на v3.6.0
│   ├── validate_sdui.py      # Последняя версия
│   └── README.md
│
├── Python/
│   ├── utils/
│   │   ├── jinja_hot_reload_v3.6.0.py  # CURRENT
│   │   ├── sdui_jinja_extensions.py
│   │   ├── sdui_to_jinja2_transformer.py
│   │   └── archive/
│   │       └── [старые версии v1-v3.5]
│   │
│   ├── sdui/
│   │   ├── validators/       # Только актуальные
│   │   └── archive/          # Старые версии
│   │
│   └── refs/                 # Refs конвертеры (актуальные)
│
├── Bash/
│   ├── current/              # Текущие версии
│   └── archive/              # Старые v1.0.0, v1.1.0
│
├── validators/
│   ├── v3.0.0/              # Последняя версия
│   └── archive/             # v1.x, v2.x
│
├── deprecated/              # Устаревшие проекты
│   ├── alfa-sdui-mcp/
│   ├── claude-agents_v2/
│   ├── claude-sdui/
│   ├── json-schema-mcp/
│   ├── vscode-validator-v2.3.1/
│   ├── xray-installer/
│   └── zen-mcp-server/
│
├── docs/                    # Актуальная документация
│   └── README.md
│
└── README.md               # Главная документация
```

## Действия

### 1. Архивирование старых версий jinja_hot_reload
- Оставить v3.6.0 как текущую
- v3.7.0 в archive (если не стабильная)
- v1-v3.5 в archive

### 2. Очистка корня
- Удалить старые computed_data_parser*.js
- Удалить старые vscode-validate-on-save*.ts/js
- Удалить MD отчёты агентов

### 3. Архивирование deprecated проектов
- alfa-sdui-mcp, claude-agents, etc в deprecated/

### 4. Создание active/ директории
- Symlinks на актуальные скрипты

### 5. Создание .cursorignore
- Исключить venv/, node_modules/, archive/, deprecated/

