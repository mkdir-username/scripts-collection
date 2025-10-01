#!/usr/bin/env python3
"""
Массовое обновление $schema во всех JSON файлах проекта
"""
import json
import os
import sys
from pathlib import Path

NEW_SCHEMA = "/Users/username/Scripts/sdui_vscode_schema_v2.3.0.json"

def update_schema_in_file(filepath):
    """Обновляет $schema в одном файле"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            data = json.loads(content)

        # Проверяем, есть ли $schema
        if '$schema' in data:
            old_schema = data['$schema']
            if old_schema == NEW_SCHEMA:
                return 'skip'

            data['$schema'] = NEW_SCHEMA

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write('\n')

            print(f"✅ {filepath}")
            return 'updated'
        else:
            # Для контрактов (с rootElement) добавляем $schema
            if 'rootElement' in data:
                data = {"$schema": NEW_SCHEMA, **data}
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    f.write('\n')
                print(f"➕ {filepath} (добавлен $schema)")
                return 'added'
            else:
                return 'skip'

    except json.JSONDecodeError as e:
        print(f"❌ Ошибка JSON в {filepath}: {e}")
        return 'error'
    except Exception as e:
        print(f"❌ Ошибка в {filepath}: {e}")
        return 'error'

def main():
    base_path = Path("/Users/username/Documents/front-middle-schema")

    # Ищем все JSON файлы в .JSON/
    json_files = list(base_path.glob(".JSON/**/*.json"))

    print(f"🔍 Найдено {len(json_files)} JSON файлов\n")

    stats = {'updated': 0, 'added': 0, 'skip': 0, 'error': 0}

    for filepath in json_files:
        result = update_schema_in_file(filepath)
        stats[result] += 1

    print(f"\n📊 СТАТИСТИКА:")
    print(f"   ✅ Обновлено: {stats['updated']}")
    print(f"   ➕ Добавлено: {stats['added']}")
    print(f"   ⏭️  Пропущено: {stats['skip']}")
    print(f"   ❌ Ошибок: {stats['error']}")

if __name__ == "__main__":
    main()