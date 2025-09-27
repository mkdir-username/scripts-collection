# SDUI Scripts - Краткая справка

## 🚀 Основные команды

### Валидация
```bash
# Быстрая проверка
python ~/Scripts/claude-sdui/sdui_validator.py /path/to/SDUI

# Только samples
python ~/Scripts/claude-sdui/sdui_validator.py /path/to/SDUI --samples-only

# С отчётом
python ~/Scripts/claude-sdui/sdui_validator.py /path/to/SDUI -o report.json -v
```

### Управление $ref
```bash
# В абсолютные пути (для VS Code)
python ~/Scripts/claude-sdui/sdui_refs_manager.py /path/to/SDUI --to-absolute

# В относительные (для Git)
python ~/Scripts/claude-sdui/sdui_refs_manager.py /path/to/SDUI --to-relative

# Проверить ссылки
python ~/Scripts/claude-sdui/sdui_refs_manager.py /path/to/SDUI --check
```

### VS Code настройка
```bash
# Генерировать схемы (базовые - 231 схема)
python ~/Scripts/claude-sdui/generate_vscode_schemas.py /path/to/SDUI

# ⭐ Генерировать ГЛУБОКИЕ схемы (420+ схем)
python ~/Scripts/claude-sdui/generate_deep_vscode_schemas.py /path/to/SDUI -v

# ⭐ Автоматически применить к VS Code
python ~/Scripts/claude-sdui/update_vscode_settings.py
```

### Валидация контракта
```bash
# Один файл
python ~/Scripts/claude-sdui/validate_contract.py contract.json

# Папка с контрактами
python ~/Scripts/claude-sdui/validate_contract.py /path/to/contracts/
```

## 📁 Пути по умолчанию

- **SDUI проект:** `~/Documents/front-middle-schema/SDUI`
- **VS Code settings:** `~/Library/Application Support/Code/User/profiles/*/settings.json`
- **Скрипты:** `~/Scripts/claude-sdui/`

## ⚡ Однострочники

```bash
# Полная проверка проекта
cd ~/Documents/front-middle-schema && python ~/Scripts/claude-sdui/sdui_validator.py SDUI -v

# ⭐ Обновить VS Code конфиг с ГЛУБОКОЙ валидацией
python ~/Scripts/claude-sdui/generate_deep_vscode_schemas.py ~/Documents/front-middle-schema/SDUI -v && python ~/Scripts/claude-sdui/update_vscode_settings.py

# Конвертировать все refs в абсолютные
python ~/Scripts/claude-sdui/sdui_refs_manager.py ~/Documents/front-middle-schema/SDUI --to-absolute

# Найти сломанные ссылки
python ~/Scripts/claude-sdui/sdui_refs_manager.py ~/Documents/front-middle-schema/SDUI --check | grep "NOT FOUND"
```

## 🔥 Горячие клавиши VS Code

- `Ctrl+Space` - автокомплит
- `Ctrl+Shift+M` - панель проблем
- `Ctrl+K Ctrl+I` - показать подсказку
- `F12` - перейти к определению

## 💡 Полезные флаги

| Флаг | Описание |
|------|----------|
| `-v, --verbose` | Подробный вывод |
| `-o, --output` | Сохранить в файл |
| `--dry-run` | Без изменений |
| `--samples-only` | Только примеры |
| `--check` | Только проверка |

---
*~/Scripts/claude-sdui/ • 2024*