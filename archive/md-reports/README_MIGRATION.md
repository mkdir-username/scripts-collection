# МИГРАЦИЯ MCP И SDUI В ~/Scripts

## Что было перемещено

### 1. SDUI Схемы → ~/Scripts/sdui-data_v2/
```
~/Scripts/sdui-data_v2/
├── SDUI/        (694MB) - Все SDUI схемы
├── metaschema/  (132KB) - Метасхемы валидации
├── workspace/   (72MB)  - Рабочая область
└── .JSON/       (36MB)  - JSON данные
```

### 2. SDUI Скрипты → ~/Scripts/sdui-scripts_v2/
```
~/Scripts/sdui-scripts_v2/
├── sdui_optimized_bundler.js           - Оптимизированный бандлер с кэшем
├── generate_vscode_schema_v2.0.0.js    - Генератор VSCode схем (УЛУЧШЕННАЯ версия, +104 строки)
├── sdui_schema_bundler.js              - Профессиональный CLI бандлер
├── sdui_vscode_proper_schema.js        - Альтернативный генератор
├── sdui_vscode_direct_schema_config.js - Конфигуратор VSCode
├── sdui_vscode_schema_generator.js     - Упрощенный генератор
└── restore_vscode_settings.js          - Восстановление настроек VSCode
```

**6 из 7 скриптов УНИКАЛЬНЫ** - аналогов в старом ~/Scripts нет!

### 3. Claude Агенты → ~/Scripts/claude-agents_v2/
```
~/Scripts/claude-agents_v2/agents/
└── 11 агентов (sdui-*.md)
```

**ПРИМЕЧАНИЕ**: Агенты идентичны оригиналам из .claude/agents

### 4. Симлинки заменены реальными файлами
- ~/Scripts/tools/ - 3 файла (validation_pipeline, sdui_orchestrator, agent_feedback_system)
- ~/Scripts/validators/ - 5 файлов (web_validator, visual_validator, byzantine_validator и др.)

## Обновленная конфигурация

### ~/Scripts/.mcp.json v2.0.0
Новая версия .mcp.json с путями на ~/Scripts/sdui-data_v2:
- **alfa-sdui-mcp**: PROJECT_ROOT, SDUI_BASE_PATH, METASCHEMA_PATH
- **code-index**: PROJECT_PATH
- **json-patch**: DEFAULT_BASE_PATH
- **json-maker**: PROJECT_PATH, OUTPUT_PATH, TEMPLATES_PATH
- **zen**: PROJECT_ROOT, SDUI_BASE_PATH

### Использование
Теперь можно безопасно удалить /Users/username/Documents/front-middle-schema через git discard:
```bash
cd /Users/username/Documents/front-middle-schema
git reset --hard HEAD
```

Все MCP серверы и скрипты работают независимо от репозитория.

## Версионирование

Все новые папки используют постфикс **_v2**:
- **sdui-data_v2** - данные SDUI (802MB)
- **sdui-scripts_v2** - скрипты генерации (92KB)
- **claude-agents_v2** - агенты Claude (188KB)

**Старые инструменты в ~/Scripts сохранены без изменений:**
- generate_vscode_schema_v2.0.0.js (старая версия - 598 строк)
- generate_vscode_schema_v2.3.0.js
- generate_vscode_schema_simplified_v2.4.0.js
- vscode-validate-on-save_v2.*.js/ts
- Все остальные MCP серверы и инструменты

## Размер данных
- Всего перемещено: ~802MB
- SDUI схемы: 694MB
- Workspace: 72MB
- .JSON: 36MB
- metaschema: 132KB
- Скрипты: 92KB (7 файлов)
- Агенты: 188KB (11 файлов)

## Что нового в v2

### generate_vscode_schema_v2.0.0.js
- **+104 строки кода** (598 → 702)
- Современный стиль (single quotes)
- Улучшенное форматирование
- Дата: 4 октября 2025 (свежее на 4 дня)

### Уникальные скрипты (только в _v2)
1. `sdui_optimized_bundler.js` - батчевая обработка + кэш
2. `sdui_schema_bundler.js` - CLI с @apidevtools/json-schema-ref-parser
3. `restore_vscode_settings.js` - утилита восстановления
4. `sdui_vscode_direct_schema_config.js` - конфигуратор
5. `sdui_vscode_proper_schema.js` - альтернативная генерация
6. `sdui_vscode_schema_generator.js` - упрощенная генерация

## Дата миграции
2025-10-04

## Версия конфигурации
MCP Config: v2.0.0
