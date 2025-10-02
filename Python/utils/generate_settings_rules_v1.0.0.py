#!/usr/bin/env python3
"""
Генератор json.schemas правил для .vscode/settings.json
Извлекает все пути компонентов из LayoutElementContent.json
"""
import json
import re
from pathlib import Path

SDUI_ROOT = Path("/Users/username/Documents/front-middle-schema")
LAYOUT_CONTENT = SDUI_ROOT / "SDUI/common/LayoutElement/LayoutElementContent.json"

def extract_component_paths():
    """Извлекает все $ref пути из LayoutElementContent"""
    with open(LAYOUT_CONTENT, 'r', encoding='utf-8') as f:
        data = json.load(f)

    components = []

    if 'oneOf' in data:
        for item in data['oneOf']:
            if '$ref' in item and 'value' in item:
                ref_path = item['$ref']
                component_name = item['value']

                # Преобразуем file:// путь в относительный
                # file:///Users/username/Documents/front-middle-schema/SDUI/...
                # → ./SDUI/...
                relative_path = ref_path.replace(
                    'file:///Users/username/Documents/front-middle-schema/',
                    './'
                )

                components.append({
                    'name': component_name,
                    'path': relative_path
                })

    return components

def generate_schema_rules(components):
    """Генерирует правила для json.schemas"""
    rules = []

    for comp in components:
        rule = {
            "fileMatch": [
                f"**/{comp['name']}/**/*.json",
                f"**/{comp['name']}.json",
                f"**/*{comp['name']}*.json"
            ],
            "url": comp['path']
        }
        rules.append(rule)

    return rules

def main():
    print("🔍 Извлечение путей компонентов из LayoutElementContent.json...\n")

    components = extract_component_paths()
    print(f"✅ Найдено {len(components)} компонентов\n")

    schema_rules = generate_schema_rules(components)

    # Добавляем правило для контрактов (.JSON файлов с rootElement)
    # Оно должно быть последним, чтобы срабатывать только если другие не подошли
    schema_rules.append({
        "fileMatch": [".JSON/**/*.json"],
        "url": "./SDUI/common/LayoutElement/LayoutElementContent.json"
    })

    output = {
        "json.schemas": schema_rules
    }

    output_path = SDUI_ROOT / "Scripts/settings_schemas_rules.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
        f.write('\n')

    print(f"📝 Создано {len(schema_rules)} правил")
    print(f"💾 Сохранено: {output_path}")
    print("\n💡 Скопируйте массив json.schemas в .vscode/settings.json")

    # Выводим первые 3 примера
    print("\n📋 Примеры правил:")
    for rule in schema_rules[:3]:
        print(f"\n  {rule['fileMatch'][1]} → {rule['url']}")

if __name__ == "__main__":
    main()