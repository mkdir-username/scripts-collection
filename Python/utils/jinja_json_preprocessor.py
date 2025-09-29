#!/usr/bin/env python3
"""
Препроцессор для файлов со смешанным Jinja2/JSON синтаксисом.
Преобразует файл в два варианта:
1. Чистый JSON для парсинга (с удалением Jinja2 блоков)
2. Jinja2 шаблон для рендеринга
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any

class JinjaJsonPreprocessor:
    """Препроцессор для смешанного Jinja2/JSON синтаксиса"""

    def __init__(self):
        self.jinja_blocks = []
        self.block_counter = 0

    def extract_jinja_blocks(self, content: str) -> str:
        """
        Извлекает Jinja2 блоки и заменяет их на плейсхолдеры
        """
        # Паттерны для Jinja2 конструкций
        patterns = [
            # {% if %} ... {% endif %} блоки (многострочные)
            (r'\{%\s*if\s+[^%]+%[^}]?\}.*?\{%\s*endif\s*%[^}]?\}', 'IF_BLOCK'),
            # {% for %} ... {% endfor %} блоки (многострочные)
            (r'\{%\s*for\s+[^%]+%[^}]?\}.*?\{%\s*endfor\s*%[^}]?\}', 'FOR_BLOCK'),
            # Одиночные {% %} теги
            (r'\{%[^}]*%[^}]?\}', 'SINGLE_TAG'),
        ]

        result = content
        self.jinja_blocks = []

        # Обрабатываем многострочные блоки
        for pattern, block_type in patterns:
            while True:
                match = re.search(pattern, result, re.DOTALL | re.MULTILINE)
                if not match:
                    break

                self.block_counter += 1
                block_id = f"__JINJA_{block_type}_{self.block_counter}__"

                # Сохраняем блок для восстановления
                self.jinja_blocks.append({
                    'id': block_id,
                    'content': match.group(),
                    'type': block_type,
                    'start': match.start(),
                    'end': match.end()
                })

                # Заменяем блок на null (валидное JSON значение)
                result = result[:match.start()] + 'null' + result[match.end():]

        return result

    def fix_json_structure(self, content: str) -> str:
        """
        Исправляет структурные проблемы JSON
        """
        # Удаляем лишние запятые перед null (от Jinja блоков)
        content = re.sub(r',\s*null\s*,', ',', content)
        content = re.sub(r',\s*null\s*\]', ']', content)
        content = re.sub(r',\s*null\s*\}', '}', content)

        # Удаляем null в массивах $children
        content = re.sub(r'\[\s*null\s*,', '[', content)
        content = re.sub(r',\s*null\s*\]', ']', content)
        content = re.sub(r'\[\s*null\s*\]', '[]', content)

        # Исправляем проблемы с закрывающими скобками после Jinja
        # Находим паттерны вида "% }" и убираем лишний }
        content = re.sub(r'%\s*\}\s*\n\s*\{', '%}\n{', content)

        # Убираем изолированные } после Jinja блоков
        lines = content.split('\n')
        fixed_lines = []
        skip_next = False

        for i, line in enumerate(lines):
            if skip_next:
                skip_next = False
                continue

            # Если строка содержит только } после строки с Jinja
            if i > 0 and line.strip() == '}' and 'null' in lines[i-1]:
                # Проверяем, не является ли это закрывающей скобкой JSON объекта
                if i + 1 < len(lines) and lines[i+1].strip().startswith('{'):
                    continue  # Пропускаем эту строку

            fixed_lines.append(line)

        return '\n'.join(fixed_lines)

    def create_template(self, original_content: str, json_content: str) -> str:
        """
        Создает Jinja2 шаблон на основе оригинального контента
        """
        template = original_content

        # Исправляем синтаксические ошибки в Jinja2 блоках
        # {% if ... % } -> {% if ... %}
        template = re.sub(r'\{%\s*([^%]+)\s*%\s*\}', r'{% \1 %}', template)

        # Исправляем условия
        template = re.sub(r'\{%\s*if\s+(\w+)\s*!=\s*null\s*%\}', r'{% if \1 is defined and \1 is not none %}', template)
        template = re.sub(r'\{%\s*if\s+(\w+\.\w+)\s*!=\s*null\s*%\}', r'{% if \1 is defined and \1 is not none %}', template)

        # Исправляем фильтры длины
        template = re.sub(r'(\w+)\|length', r'\1|length', template)

        # Исправляем циклы
        template = re.sub(r'\{%\s*for\s+(\w+)\s+in\s+([^%]+)\s*%\}', r'{% for \1 in \2 %}', template)

        # Исправляем endif и endfor
        template = re.sub(r'\{%\s*endif\s*%\s*\}', r'{% endif %}', template)
        template = re.sub(r'\{%\s*endfor\s*%\s*\}', r'{% endfor %}', template)

        return template

    def process_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Обрабатывает файл и создает несколько версий
        """
        print(f"📋 Обработка файла: {file_path.name}")

        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        # 1. Извлекаем Jinja блоки
        json_content = self.extract_jinja_blocks(original_content)

        # 2. Исправляем JSON структуру
        json_content = self.fix_json_structure(json_content)

        # 3. Пробуем парсить JSON
        try:
            json_obj = json.loads(json_content)
            json_valid = True
            print("  ✅ JSON успешно распарсен")
        except json.JSONDecodeError as e:
            json_valid = False
            json_obj = None
            print(f"  ⚠️  JSON ошибка: {e}")

        # 4. Создаем Jinja2 шаблон
        template_content = self.create_template(original_content, json_content)

        # 5. Сохраняем результаты
        results = {
            'original_file': file_path,
            'json_valid': json_valid,
            'jinja_blocks_count': len(self.jinja_blocks),
            'files_created': []
        }

        # Сохраняем чистый JSON (для парсинга)
        json_path = file_path.with_name(f"{file_path.stem}_clean.json")
        if json_valid:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_obj, f, indent=2, ensure_ascii=False)
            print(f"  📄 Чистый JSON: {json_path.name}")
            results['files_created'].append(json_path)

        # Сохраняем Jinja2 шаблон
        template_path = file_path.with_name(f"{file_path.stem}_template.j2")
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
        print(f"  📝 Jinja2 шаблон: {template_path.name}")
        results['files_created'].append(template_path)

        # Сохраняем информацию о блоках
        blocks_path = file_path.with_name(f"{file_path.stem}_blocks.json")
        with open(blocks_path, 'w', encoding='utf-8') as f:
            json.dump(self.jinja_blocks, f, indent=2, ensure_ascii=False)
        print(f"  🔖 Инфо о блоках: {blocks_path.name}")
        results['files_created'].append(blocks_path)

        return results

def main():
    """Главная функция"""
    if len(sys.argv) < 2:
        print("Использование: python jinja_json_preprocessor.py <файл.json>")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"❌ Файл не найден: {file_path}")
        sys.exit(1)

    preprocessor = JinjaJsonPreprocessor()
    results = preprocessor.process_file(file_path)

    print("\n✅ Обработка завершена!")
    print(f"  JSON валиден: {results['json_valid']}")
    print(f"  Jinja2 блоков: {results['jinja_blocks_count']}")
    print(f"  Созданные файлы:")
    for file in results['files_created']:
        print(f"    - {file.name}")

    if results['json_valid']:
        print("\n📌 Следующие шаги:")
        print(f"  1. Используйте {file_path.stem}_clean.json для обработки как JSON")
        print(f"  2. Используйте {file_path.stem}_template.j2 для Jinja2 рендеринга")
        print(f"  3. Запустите jinja_hot_reload_v3.0.0.py для автоматической обработки")
    else:
        print("\n⚠️  JSON невалиден, требуется ручная проверка")

if __name__ == '__main__':
    main()