# План реорганизации Scripts

Дата: 2025-10-02
Статус: Утверждено к выполнению

## 🎯 Цели

1. Соответствие naming convention
2. Очистка временных файлов
3. Правильная структура директорий
4. Сохранение всех зависимостей

## ⚠️ КРИТИЧНО: НЕ ТРОГАТЬ

### Файлы с зависимостями
- ✋ `validation-formatters_v1.0.0.js` - используется vscode-validate-on-save
- ✋ Все Python/ симлинки (23 шт) - удобный доступ к модулям
- ✋ Пути в скриптах - не изменять (hardcoded)
- ✋ `/Users/username/Documents/front-middle-schema` - внешняя зависимость

## ✅ ЭТАП 1: Cleanup (безопасно)

### 1.1 Удаление __pycache__
```bash
rm -rf Python/__pycache__/
rm -rf Python/utils/__pycache__/
```
Эффект: 668 KB, файлы автоматически пересоздаются

### 1.2 Удаление workspace агентов
```bash
rm -rf Python/utils/workspace/agent_*_20251001/
```
Эффект: 752 KB, завершённые задачи от 1 октября

### 1.3 Удаление временных workspace
```bash
rm -rf workspace/impl_format_output_20251001/
rm -rf workspace/test_formatters_20251001/
```
Эффект: ~43 KB, дубликаты старых версий

### 1.4 Удаление старого README
```bash
rm README.md  # Старая версия, есть README_v2.1.0.md
```

## ✅ ЭТАП 2: Перемещение файлов

### 2.1 Python файлы из корня → Python/
```bash
mv sdui_web_validator_vscode_v1.0.0.py Python/sdui/
mv sdui_web_validator_v7.0.0.py Python/sdui/
mv update_json_schema_v1.0.0.py Python/utils/
mv generate_settings_rules_v1.0.0.py Python/utils/
```

### 2.2 Документация из корня → docs/
```bash
mkdir -p docs/guides/
mv IMPLEMENTATION_SUMMARY_v1.0.0.md docs/
mv QUICKSTART_SafeDebugUndefined_v1.0.0.md docs/guides/
mv SETUP_CHECKLIST_v1.0.0.md docs/guides/
```

### 2.3 Тестовая документация → docs/testing/
```bash
mkdir -p docs/testing/
mv tests/TEST_ACCEPTANCE_CRITERIA_v1.0.0.md docs/testing/
mv tests/TEST_CASES_SPECIFICATION_v1.0.0.md docs/testing/
mv tests/TEST_SUMMARY_v1.0.0.md docs/testing/
```

### 2.4 Тесты из workspace → tests/unit/
```bash
mkdir -p tests/unit/jinja_hot_reload/
mv Python/utils/workspace/agent_filesystemloader_20251001/test_filesystemloader_v1.0.0.py tests/unit/jinja_hot_reload/
mv Python/utils/workspace/agent_logging_20251001/test_enhanced_logger_v1.0.0.py tests/unit/jinja_hot_reload/
mv Python/utils/workspace/agent_filters_20251001/test_custom_filters_v1.0.0.py tests/unit/jinja_hot_reload/
mv Python/utils/workspace/agent_import_parser_20251001/test_import_parser_v1.0.0.py tests/unit/jinja_hot_reload/
mv Python/utils/workspace/agent_auto_rerender_20251001/test_auto_rerender_v1.0.0.py tests/unit/jinja_hot_reload/
mv Python/utils/workspace/agent_visualizer_20251001/test_tree_visualizer_v1.0.0.py tests/unit/jinja_hot_reload/
mv Python/utils/workspace/agent_include_parser_20251001/test_include_parser_v1.0.0.py tests/unit/jinja_hot_reload/
mv Python/utils/workspace/agent_dependency_tracker_20251001/test_dependency_tracker_v1.0.0.py tests/unit/jinja_hot_reload/
```

## ✅ ЭТАП 3: Исправления

### 3.1 Исправить сломанный импорт
```bash
# Создать symlink для jinja_hot_reload_daemon.py
cd Python/utils/
ln -s jinja_hot_reload_v2.0.0.py jinja_hot_reload_v2_0_0.py
```

### 3.2 Обновить .gitignore
```bash
cat >> .gitignore << 'EOF'

# Python
__pycache__/
*.py[cod]
*$py.class
Python/venv/
workspace/
node_modules/
EOF
```

## 📊 Результат

### До реорганизации
- Корень: 25 файлов
- Python/: 4 файла в корне + симлинки
- workspace/: 2 временные папки
- Размер cleanup: ~1.5 MB

### После реорганизации
- ✅ Корень: только версионированные скрипты
- ✅ Python/: чистая структура пакетов
- ✅ docs/: вся документация структурирована
- ✅ tests/: все тесты организованы
- ✅ Освобождено: ~1.5 MB

## ⚠️ Тестирование

После реорганизации проверить:
1. vscode-validate-on-save_v2.1.0.ts (импорт validation-formatters)
2. jinja_hot_reload_v3.6.0.py (пути не изменились)
3. Python импорты (если используются относительные пути)

## 🔒 Безопасность

- ✅ Все зависимости сохранены
- ✅ Hardcoded пути не изменены
- ✅ Симлинки не тронуты
- ✅ Внешние зависимости не затронуты
- ✅ Критические скрипты не перемещены
