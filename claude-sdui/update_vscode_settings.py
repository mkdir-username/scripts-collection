#!/usr/bin/env python3
"""
Обновление VS Code settings.json с новой конфигурацией схем
"""

import json
import sys
from pathlib import Path
import shutil
from datetime import datetime


def update_vscode_settings(settings_path: Path, new_schemas_path: Path):
    """Обновляет settings.json с новыми схемами"""

    # Читаем текущие настройки
    print(f"📖 Читаю текущие настройки из: {settings_path}")
    with open(settings_path, 'r', encoding='utf-8') as f:
        settings = json.load(f)

    # Читаем новые схемы
    print(f"📖 Читаю новые схемы из: {new_schemas_path}")
    with open(new_schemas_path, 'r', encoding='utf-8') as f:
        new_config = json.load(f)

    # Создаём резервную копию
    backup_path = settings_path.parent / f"settings.json.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"💾 Создаю резервную копию: {backup_path}")
    shutil.copy2(settings_path, backup_path)

    # Обновляем схемы
    old_schemas_count = len(settings.get("json.schemas", []))
    settings["json.schemas"] = new_config["json.schemas"]
    new_schemas_count = len(settings["json.schemas"])

    # Сохраняем обновлённые настройки
    print(f"💾 Сохраняю обновлённые настройки...")
    with open(settings_path, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Готово!")
    print(f"  - Было схем: {old_schemas_count}")
    print(f"  - Стало схем: {new_schemas_count}")
    print(f"  - Резервная копия: {backup_path}")


if __name__ == "__main__":
    settings_path = Path("/Users/username/Library/Application Support/Code/User/profiles/20457074/settings.json")
    new_schemas_path = Path("/Users/username/Scripts/claude-sdui/vscode_deep_schemas_config.json")

    if not settings_path.exists():
        print(f"❌ Файл настроек не найден: {settings_path}")
        sys.exit(1)

    if not new_schemas_path.exists():
        print(f"❌ Файл с новыми схемами не найден: {new_schemas_path}")
        sys.exit(1)

    update_vscode_settings(settings_path, new_schemas_path)
    print("\n💡 Перезагрузите VS Code для применения изменений")