#!/usr/bin/env python3
"""
План миграции и организации валидаторов
Автоматизированный скрипт для организации Python валидаторов
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Конфигурация путей
SOURCE_DIR = Path("/Users/username/Documents/front-middle-schema")
TARGET_DIR = Path("/Users/username/Scripts/validators")

# Карта миграции файлов
MIGRATION_MAP = {
    # Актуальная версия v2.0.0
    "v2.0.0": {
        "sdui_web_validator_v2.0.0_advanced_lines.py": "sdui_web_validator.py",
    },

    # Стабильные версии v1.0.0
    "v1.0.0": {
        "simple_validator.py": "simple_validator.py",
        "simple_validator_fixed.py": "simple_validator_fixed.py",
        "byzantine_validator.py": "byzantine_validator.py",
    },

    # Специализированные валидаторы
    "specialized": {
        "sdui_visual_validator.py": "visual_validator.py",
        "agent_terminal_validator.py": "terminal_validator.py",
        "sdui_contract_validator.py": "contract_validator.py",
        "sdui_web_validator_improved.py": "web_validator_improved.py",
        "sdui_web_validator_new.py": "web_validator_new.py",
        "sdui_web_validator_with_lines.py": "web_validator_with_lines.py",
    },

    # Утилиты
    "utils": {
        "sdui_index_cache.py": "sdui_index_cache.py",
        "check_validator_compatibility.py": "compatibility_checker.py",
        "test_validators.py": "test_runner.py",
    },

    # Архивные версии
    "archive/v1.0.0": {
        "validators/archive/sdui_web_validator_v1.0.0.py": "sdui_web_validator.py",
    },
    "archive/v1.1.0": {
        "validators/archive/sdui_web_validator_v1.1.0.py": "sdui_web_validator.py",
    },
    "archive/v1.2.0": {
        "validators/archive/sdui_web_validator_v1.2.0_with_lines.py": "sdui_web_validator_with_lines.py",
        "validators/archive/sdui_web_validator_improved.py": "sdui_web_validator_improved.py",
    },
}

def create_directory_structure():
    """Создает структуру директорий"""
    directories = [
        "v2.0.0",
        "v1.0.0",
        "specialized",
        "utils",
        "archive/v1.0.0",
        "archive/v1.1.0",
        "archive/v1.2.0",
        "tests",
        "docs",
    ]

    for dir_path in directories:
        full_path = TARGET_DIR / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Создана директория: {full_path}")

def copy_validators():
    """Копирует валидаторы в целевые директории"""
    copied_files = []
    failed_files = []

    for target_subdir, files_map in MIGRATION_MAP.items():
        target_path = TARGET_DIR / target_subdir

        for source_file, target_file in files_map.items():
            source_path = SOURCE_DIR / source_file
            destination = target_path / target_file

            if source_path.exists():
                try:
                    shutil.copy2(source_path, destination)
                    copied_files.append((source_file, str(destination.relative_to(TARGET_DIR))))
                    print(f"✓ Скопирован: {source_file} → {target_subdir}/{target_file}")
                except Exception as e:
                    failed_files.append((source_file, str(e)))
                    print(f"✗ Ошибка копирования {source_file}: {e}")
            else:
                failed_files.append((source_file, "Файл не найден"))
                print(f"⚠ Не найден: {source_file}")

    return copied_files, failed_files

def create_requirements_txt():
    """Создает файл requirements.txt"""
    requirements_content = """# Основные зависимости для SDUI валидаторов
# Сгенерировано: {date}

# Обязательные зависимости
requests>=2.28.0        # Для visual_validator.py

# Опциональные зависимости для разработки
pytest>=7.0.0          # Для запуска тестов
black>=22.0.0          # Форматирование кода
pylint>=2.15.0         # Линтинг
mypy>=0.991            # Статическая типизация

# Дополнительные утилиты
colorama>=0.4.6        # Цветной вывод в консоль
tabulate>=0.9.0        # Форматированные таблицы
click>=8.1.0           # CLI интерфейс
""".format(date=datetime.now().strftime("%Y-%m-%d"))

    requirements_path = TARGET_DIR / "requirements.txt"
    requirements_path.write_text(requirements_content)
    print(f"✓ Создан файл requirements.txt")

def create_main_readme():
    """Создает основной README.md"""
    readme_content = """# SDUI Validators Collection

Организованная коллекция валидаторов для SDUI контрактов.

## Структура проекта

```
validators/
├── v2.0.0/              # Актуальная версия (продакшен)
├── v1.0.0/              # Стабильная версия
├── specialized/         # Специализированные валидаторы
├── utils/               # Вспомогательные модули
├── archive/             # Архивные версии
└── tests/               # Тесты
```

## Быстрый старт

### Установка зависимостей

```bash
pip install -r requirements.txt
```

### Использование основного валидатора

```bash
# Валидация контракта с v2.0.0
python v2.0.0/sdui_web_validator.py contract.json

# Простая валидация
python v1.0.0/simple_validator.py contract.json

# Byzantine валидация
python v1.0.0/byzantine_validator.py contract.json /path/to/sdui
```

## Версии валидаторов

### v2.0.0 (Актуальная)
- **sdui_web_validator.py** - Продвинутая валидация с точными номерами строк
- Поддержка всех WEB компонентов
- Детальные сообщения об ошибках

### v1.0.0 (Стабильная)
- **simple_validator.py** - Базовая валидация без зависимостей
- **byzantine_validator.py** - Byzantine Fault-Tolerant проверки

### Специализированные
- **visual_validator.py** - Визуальная валидация (требует requests)
- **terminal_validator.py** - Проверка через эндпоинты
- **contract_validator.py** - Валидация контрактов

## Зависимости

- Python 3.8+
- requests (для visual_validator)

## Документация

Подробная документация находится в директории `docs/`.

## Лицензия

Внутренний проект. Все права защищены.

---
Сгенерировано: {date}
""".format(date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    readme_path = TARGET_DIR / "README.md"
    readme_path.write_text(readme_content)
    print(f"✓ Создан файл README.md")

def create_unified_validator():
    """Создает единый валидатор с автоматическим выбором версии"""
    validator_content = '''#!/usr/bin/env python3
"""
Универсальный валидатор SDUI контрактов
Автоматически выбирает подходящий валидатор
"""

import sys
import json
from pathlib import Path

def validate(contract_path: str, mode: str = "auto"):
    """
    Запускает валидацию контракта

    Args:
        contract_path: Путь к JSON контракту
        mode: Режим валидации (auto, simple, advanced, byzantine, visual)
    """
    contract_path = Path(contract_path)

    if not contract_path.exists():
        print(f"❌ Файл не найден: {contract_path}")
        return False

    # Определяем тип валидации
    if mode == "auto":
        # Анализируем контракт для выбора валидатора
        try:
            with open(contract_path, 'r') as f:
                contract = json.load(f)

            # Выбираем валидатор на основе содержимого
            if 'releaseVersion' in contract and 'web' in contract.get('releaseVersion', {}):
                mode = "advanced"
            else:
                mode = "simple"
        except:
            mode = "simple"

    # Импортируем и запускаем соответствующий валидатор
    validators = {
        "simple": "v1.0.0/simple_validator",
        "advanced": "v2.0.0/sdui_web_validator",
        "byzantine": "v1.0.0/byzantine_validator",
        "visual": "specialized/visual_validator",
        "terminal": "specialized/terminal_validator"
    }

    validator_path = Path(__file__).parent / validators.get(mode, validators["simple"])

    # Динамический импорт и запуск
    import importlib.util
    spec = importlib.util.spec_from_file_location("validator", f"{validator_path}.py")
    validator_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator_module)

    # Запускаем валидацию
    if hasattr(validator_module, 'validate_contract'):
        return validator_module.validate_contract(str(contract_path))
    elif hasattr(validator_module, 'main'):
        sys.argv = ['validator', str(contract_path)]
        return validator_module.main()

    print(f"❌ Валидатор {mode} не поддерживает автоматический запуск")
    return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate.py <contract.json> [mode]")
        print("Modes: auto, simple, advanced, byzantine, visual, terminal")
        sys.exit(1)

    contract_path = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "auto"

    success = validate(contract_path, mode)
    sys.exit(0 if success else 1)
'''

    validator_path = TARGET_DIR / "validate.py"
    validator_path.write_text(validator_content)
    validator_path.chmod(0o755)  # Делаем исполняемым
    print(f"✓ Создан универсальный валидатор validate.py")

def create_migration_report(copied_files: List[Tuple[str, str]],
                           failed_files: List[Tuple[str, str]]):
    """Создает отчет о миграции"""
    report_content = f"""# Отчет о миграции валидаторов
Дата: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Статистика
- Успешно скопировано: {len(copied_files)} файлов
- Ошибок: {len(failed_files)} файлов
- Целевая директория: {TARGET_DIR}

## Скопированные файлы

| Исходный файл | Целевое расположение |
|---------------|---------------------|
"""

    for source, target in copied_files:
        report_content += f"| {source} | {target} |\n"

    if failed_files:
        report_content += "\n## Ошибки\n\n"
        report_content += "| Файл | Причина |\n"
        report_content += "|------|--------|\n"
        for file, reason in failed_files:
            report_content += f"| {file} | {reason} |\n"

    report_content += f"""

## Следующие шаги

1. Проверьте корректность миграции:
   ```bash
   cd {TARGET_DIR}
   python validate.py test_contract.json
   ```

2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

3. Запустите тесты:
   ```bash
   python utils/test_runner.py
   ```

## Рекомендации

- Обновите импорты в файлах при необходимости
- Проверьте работоспособность специализированных валидаторов
- Настройте CI/CD для автоматической валидации
"""

    report_path = TARGET_DIR / "migration_report.md"
    report_path.write_text(report_content)
    print(f"\n✓ Отчет о миграции сохранен в migration_report.md")

def main():
    """Основная функция миграции"""
    print("=" * 60)
    print("МИГРАЦИЯ ВАЛИДАТОРОВ SDUI")
    print("=" * 60)
    print(f"Источник: {SOURCE_DIR}")
    print(f"Назначение: {TARGET_DIR}")
    print("-" * 60)

    # Шаг 1: Создание структуры директорий
    print("\n📁 Создание структуры директорий...")
    create_directory_structure()

    # Шаг 2: Копирование файлов
    print("\n📋 Копирование валидаторов...")
    copied_files, failed_files = copy_validators()

    # Шаг 3: Создание вспомогательных файлов
    print("\n📝 Создание вспомогательных файлов...")
    create_requirements_txt()
    create_main_readme()
    create_unified_validator()

    # Шаг 4: Создание отчета
    print("\n📊 Создание отчета о миграции...")
    create_migration_report(copied_files, failed_files)

    # Итоговая статистика
    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТЫ МИГРАЦИИ")
    print("=" * 60)
    print(f"✅ Успешно скопировано: {len(copied_files)} файлов")
    if failed_files:
        print(f"⚠️ Ошибок: {len(failed_files)} файлов")
    print(f"📍 Расположение: {TARGET_DIR}")
    print("-" * 60)
    print("Миграция завершена!")

    return len(failed_files) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)