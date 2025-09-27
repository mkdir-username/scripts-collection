# SDUI Web Validators

Организованная коллекция валидаторов для проверки SDUI контрактов на совместимость с веб-платформой.

## Структура директорий

```
validators/
├── v2.0.0/                 # Последняя стабильная версия
│   └── sdui_web_validator_v2.0.0_advanced_lines.py
├── v1.x.x/                 # Предыдущие версии
│   ├── sdui_web_validator_v1.0.0.py
│   ├── sdui_web_validator_v1.1.0.py
│   ├── sdui_web_validator_v1.2.0_with_lines.py
│   └── sdui_web_validator_improved.py
├── specialized/            # Специализированные валидаторы
│   ├── byzantine_validator.py
│   ├── sdui_visual_validator.py
│   ├── agent_validate_cli.py
│   ├── agent_terminal_validator.py
│   ├── sdui_contract_validator.py
│   └── validation_pipeline.py
├── basic/                  # Простые валидаторы
│   ├── simple_validator.py
│   ├── simple_validator_fixed.py
│   ├── validate_contract.py
│   ├── validate_root_element.py
│   └── check_validator_compatibility.py
├── archive/                # Архивные версии
│   ├── sdui_web_validator_new.py
│   ├── sdui_web_validator_with_lines.py
│   ├── sdui_web_validator.py
│   └── sdui_web_validator_improved.py
└── test_validators.py      # Тесты для валидаторов
```

## Использование

### Последняя версия (v2.0.0)
```bash
python /Users/username/Scripts/validators/v2.0.0/sdui_web_validator_v2.0.0_advanced_lines.py contract.json
```

### Специализированные валидаторы
```bash
# Byzantine валидатор для сложных проверок
python /Users/username/Scripts/validators/specialized/byzantine_validator.py contract.json

# Визуальный валидатор с графическим выводом
python /Users/username/Scripts/validators/specialized/sdui_visual_validator.py contract.json

# CLI валидатор с интерактивным режимом
python /Users/username/Scripts/validators/specialized/agent_validate_cli.py contract.json
```

### Простые валидаторы
```bash
# Базовая проверка
python /Users/username/Scripts/validators/basic/simple_validator.py contract.json

# Проверка корневых элементов
python /Users/username/Scripts/validators/basic/validate_root_element.py contract.json
```

## Обратная совместимость

Для обратной совместимости в проекте front-middle-schema созданы символические ссылки:
- sdui_web_validator_latest.py → указывает на v2.0.0

## Версионирование

- **v2.0.0** - Продвинутая версия с детальными номерами строк и улучшенной визуализацией
- **v1.2.0** - Добавлена поддержка номеров строк
- **v1.1.0** - Улучшенная обработка ошибок
- **v1.0.0** - Первая стабильная версия

## Зависимости

```bash
pip install jsonschema
```

## Тестирование

```bash
python test_validators.py
```
