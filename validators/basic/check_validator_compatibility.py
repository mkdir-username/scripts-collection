#!/usr/bin/env python3
"""
Скрипт проверки совместимости валидаторов SDUI
Проверяет доступность всех версий валидаторов и их импорт
"""

import os
import sys
import importlib.util
from pathlib import Path

def check_file_exists(filepath):
    """Проверяет существование файла"""
    return os.path.isfile(filepath)

def check_module_import(filepath):
    """Проверяет возможность импорта модуля"""
    try:
        spec = importlib.util.spec_from_file_location("validator", filepath)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return True, "OK"
    except Exception as e:
        return False, str(e)
    return False, "Unknown error"

def main():
    """Основная функция проверки"""
    base_dir = Path(__file__).parent

    # Список валидаторов для проверки
    validators = [
        # Основная версия
        ("sdui_web_validator_v2.0.0_advanced_lines.py", "v2.0.0 (Основная версия)"),

        # Файлы обратной совместимости
        ("sdui_web_validator.py", "v1.0.0 (Совместимость)"),
        ("sdui_web_validator_new.py", "v1.1.0 (Совместимость)"),
        ("sdui_web_validator_improved.py", "Improved (Совместимость)"),
        ("sdui_web_validator_with_lines.py", "v1.2.0 (Совместимость)"),

        # Архивные версии
        ("validators/archive/sdui_web_validator_v1.0.0.py", "v1.0.0 (Архив)"),
        ("validators/archive/sdui_web_validator_v1.1.0.py", "v1.1.0 (Архив)"),
        ("validators/archive/sdui_web_validator_improved.py", "Improved (Архив)"),
        ("validators/archive/sdui_web_validator_v1.2.0_with_lines.py", "v1.2.0 (Архив)"),
    ]

    print("=" * 70)
    print("ПРОВЕРКА СОВМЕСТИМОСТИ ВАЛИДАТОРОВ SDUI")
    print("=" * 70)

    all_ok = True

    # Проверка файлов
    print("\n📁 Проверка наличия файлов:")
    print("-" * 70)

    for filename, description in validators:
        filepath = base_dir / filename
        exists = check_file_exists(filepath)
        status = "✅" if exists else "❌"
        all_ok = all_ok and exists

        print(f"{status} {filename}")
        print(f"   {description}")
        if not exists:
            print(f"   ⚠️  Файл отсутствует!")
        print()

    # Проверка импорта модулей
    print("\n🔧 Проверка импорта модулей:")
    print("-" * 70)

    for filename, description in validators:
        filepath = base_dir / filename
        if check_file_exists(filepath):
            success, message = check_module_import(filepath)
            status = "✅" if success else "⚠️"

            print(f"{status} {filename}")
            if not success:
                print(f"   Ошибка импорта: {message[:100]}...")
                all_ok = False
        print()

    # Проверка скриптов
    print("\n📜 Проверка скриптов:")
    print("-" * 70)

    scripts = [
        ("run_validator_with_clear.sh", "sdui_web_validator_v2.0.0_advanced_lines.py"),
        (".vscode/tasks.json", "sdui_web_validator_v2.0.0_advanced_lines.py"),
    ]

    for script, expected_validator in scripts:
        script_path = base_dir / script
        if script_path.exists():
            content = script_path.read_text()
            if expected_validator in content:
                print(f"✅ {script} использует {expected_validator}")
            else:
                print(f"⚠️  {script} не использует ожидаемый валидатор")
                all_ok = False
        else:
            print(f"❌ {script} не найден")
            all_ok = False

    # Итоговый статус
    print("\n" + "=" * 70)
    if all_ok:
        print("✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ УСПЕШНО!")
        print("Система валидаторов полностью совместима.")
    else:
        print("⚠️  ОБНАРУЖЕНЫ ПРОБЛЕМЫ!")
        print("Проверьте указанные выше предупреждения.")
    print("=" * 70)

    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())