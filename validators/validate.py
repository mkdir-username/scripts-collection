#!/usr/bin/env python3
"""
Главный скрипт для запуска валидаторов SDUI.
Автоматически выбирает подходящий валидатор в зависимости от параметров.
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path

VALIDATORS = {
    'latest': 'v2.0.0/sdui_web_validator_v2.0.0_advanced_lines.py',
    'v2.0.0': 'v2.0.0/sdui_web_validator_v2.0.0_advanced_lines.py',
    'v1.2.0': 'v1.x.x/sdui_web_validator_v1.2.0_with_lines.py',
    'v1.1.0': 'v1.x.x/sdui_web_validator_v1.1.0.py',
    'v1.0.0': 'v1.x.x/sdui_web_validator_v1.0.0.py',
    'byzantine': 'specialized/byzantine_validator.py',
    'visual': 'specialized/sdui_visual_validator.py',
    'cli': 'specialized/agent_validate_cli.py',
    'terminal': 'specialized/agent_terminal_validator.py',
    'contract': 'specialized/sdui_contract_validator.py',
    'pipeline': 'specialized/validation_pipeline.py',
    'simple': 'basic/simple_validator.py',
    'root': 'basic/validate_root_element.py',
}

def main():
    parser = argparse.ArgumentParser(
        description='SDUI валидатор - проверка контрактов на совместимость с веб-платформой',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python validate.py contract.json                    # Использовать последнюю версию
  python validate.py --version v1.2.0 contract.json   # Использовать конкретную версию
  python validate.py --type visual contract.json      # Использовать визуальный валидатор
  python validate.py --list                           # Показать доступные валидаторы
        """
    )

    parser.add_argument('file', nargs='?', help='JSON файл контракта для валидации')
    parser.add_argument(
        '--version', '-v',
        choices=list(VALIDATORS.keys()),
        default='latest',
        help='Версия валидатора (по умолчанию: latest)'
    )
    parser.add_argument(
        '--type', '-t',
        choices=['byzantine', 'visual', 'cli', 'terminal', 'simple'],
        help='Тип специализированного валидатора'
    )
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='Показать доступные валидаторы'
    )

    args = parser.parse_args()

    if args.list:
        print("\n📋 Доступные валидаторы:\n")
        print("  Версии:")
        for key in ['latest', 'v2.0.0', 'v1.2.0', 'v1.1.0', 'v1.0.0']:
            print(f"    {key:<10} - {VALIDATORS[key]}")
        print("\n  Специализированные:")
        for key in ['byzantine', 'visual', 'cli', 'terminal', 'contract', 'pipeline']:
            print(f"    {key:<10} - {VALIDATORS[key]}")
        print("\n  Простые:")
        for key in ['simple', 'root']:
            print(f"    {key:<10} - {VALIDATORS[key]}")
        print()
        return

    if not args.file:
        parser.error("Необходимо указать файл для валидации (или используйте --list)")

    # Определяем какой валидатор использовать
    if args.type:
        validator_key = args.type
    else:
        validator_key = args.version

    validator_path = Path(__file__).parent / VALIDATORS[validator_key]

    if not validator_path.exists():
        print(f"❌ Ошибка: валидатор не найден: {validator_path}")
        sys.exit(1)

    # Запускаем валидатор
    print(f"🚀 Запуск валидатора: {validator_key}")
    print(f"📄 Файл: {args.file}")
    print(f"🔧 Путь: {validator_path}")
    print("=" * 80)
    print()

    try:
        result = subprocess.run(
            [sys.executable, str(validator_path), args.file],
            capture_output=False,
            text=True
        )
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n\n⚠️ Валидация прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Ошибка запуска валидатора: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()