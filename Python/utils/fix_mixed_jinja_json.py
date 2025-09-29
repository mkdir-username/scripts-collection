#!/usr/bin/env python3
"""
Фикс для обработки файлов со смешанным Jinja2/JSON синтаксисом
Преобразует Jinja2 блоки в валидные JSON строки для последующей обработки
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, Any, Tuple

def fix_mixed_syntax(content: str) -> Tuple[str, Dict[str, str]]:
    """
    Исправляет смешанный Jinja2/JSON синтаксис

    Returns:
        Tuple[str, Dict]: (исправленный контент, карта замен)
    """
    replacements = {}
    counter = 0

    # Паттерны для поиска Jinja2 конструкций
    patterns = [
        # {% if ... %} ... {% endif %}
        (r'\{%\s*if\s+.*?%\}.*?\{%\s*endif\s*%\}', 'JINJA_IF_BLOCK'),
        # {% for ... %} ... {% endfor %}
        (r'\{%\s*for\s+.*?%\}.*?\{%\s*endfor\s*%\}', 'JINJA_FOR_BLOCK'),
        # Одиночные {% ... %}
        (r'\{%[^}]*%\}', 'JINJA_TAG'),
    ]

    fixed = content

    # Заменяем Jinja2 блоки на временные плейсхолдеры
    for pattern, block_type in patterns:
        matches = re.finditer(pattern, fixed, re.DOTALL)
        for match in reversed(list(matches)):
            counter += 1
            placeholder = f'"__JINJA_PLACEHOLDER_{block_type}_{counter}__"'
            replacements[placeholder.strip('"')] = match.group()
            fixed = fixed[:match.start()] + placeholder + fixed[match.end():]

    # Исправляем проблемы с запятыми
    # Добавляем запятые между объектами в массивах
    fixed = re.sub(r'\}\s*\n\s*\{', '},\n{', fixed)

    # Убираем лишние запятые перед закрывающими скобками
    fixed = re.sub(r',\s*([}\]])', r'\1', fixed)

    return fixed, replacements

def restore_jinja_blocks(content: str, replacements: Dict[str, str]) -> str:
    """Восстанавливает Jinja2 блоки после обработки"""
    result = content
    for placeholder, original in replacements.items():
        result = result.replace(f'"{placeholder}"', original)
    return result

def process_file(file_path: Path) -> bool:
    """
    Обрабатывает файл со смешанным синтаксисом

    Returns:
        bool: True если успешно, False если ошибка
    """
    print(f"🔧 Обработка: {file_path.name}")

    try:
        # Читаем оригинальный файл
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Создаем резервную копию
        backup_path = file_path.with_suffix('.json.backup')
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  📦 Резервная копия: {backup_path.name}")

        # Исправляем синтаксис
        fixed_content, replacements = fix_mixed_syntax(content)

        # Проверяем валидность JSON
        try:
            json_obj = json.loads(fixed_content)
            print(f"  ✅ JSON валиден после исправления")
        except json.JSONDecodeError as e:
            print(f"  ❌ JSON все еще невалиден: {e}")
            # Сохраняем промежуточный результат для отладки
            debug_path = file_path.with_name(f"{file_path.stem}_debug.json")
            with open(debug_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"  📝 Промежуточный результат: {debug_path.name}")
            return False

        # Создаем версию для обработки (с плейсхолдерами)
        processing_path = file_path.with_name(f"{file_path.stem}_processing.json")
        with open(processing_path, 'w', encoding='utf-8') as f:
            json.dump(json_obj, f, indent=2, ensure_ascii=False)
        print(f"  📄 Версия для обработки: {processing_path.name}")

        # Создаем финальную версию (с восстановленными Jinja блоками)
        final_json_str = json.dumps(json_obj, indent=2, ensure_ascii=False)
        final_content = restore_jinja_blocks(final_json_str, replacements)

        # Сохраняем исправленную версию
        fixed_path = file_path.with_name(f"{file_path.stem}_fixed.json")
        with open(fixed_path, 'w', encoding='utf-8') as f:
            f.write(final_content)
        print(f"  ✨ Исправленная версия: {fixed_path.name}")

        # Сохраняем карту замен
        map_path = file_path.with_name(f"{file_path.stem}_replacements.json")
        with open(map_path, 'w', encoding='utf-8') as f:
            json.dump(replacements, f, indent=2, ensure_ascii=False)
        print(f"  🗺️  Карта замен: {map_path.name}")

        print(f"  ✅ Успешно обработан!")
        return True

    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Главная функция"""
    if len(sys.argv) < 2:
        print("Использование: python fix_mixed_jinja_json.py <путь_к_файлу>")
        print("Пример: python fix_mixed_jinja_json.py [JJ_NN]_main-screen_v1.json")
        sys.exit(1)

    file_path = Path(sys.argv[1])

    if not file_path.exists():
        print(f"❌ Файл не найден: {file_path}")
        sys.exit(1)

    if not file_path.suffix == '.json':
        print(f"⚠️  Предупреждение: файл не имеет расширения .json")

    print(f"\n🎯 Исправление смешанного Jinja2/JSON синтаксиса")
    print(f"📁 Файл: {file_path}")
    print("-" * 50)

    success = process_file(file_path)

    print("-" * 50)
    if success:
        print("✅ Обработка завершена успешно!")
        print(f"\n📌 Следующие шаги:")
        print(f"1. Используйте {file_path.stem}_processing.json для парсинга как JSON")
        print(f"2. Используйте {file_path.stem}_fixed.json для Jinja2 обработки")
        print(f"3. Карта замен сохранена в {file_path.stem}_replacements.json")
    else:
        print("❌ Обработка завершена с ошибками")
        print("\n💡 Рекомендации:")
        print("1. Проверьте _debug.json файл для анализа промежуточного результата")
        print("2. Возможно требуется ручное исправление синтаксиса")

    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()