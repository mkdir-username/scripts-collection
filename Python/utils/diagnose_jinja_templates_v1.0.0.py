#!/usr/bin/env python3
"""
Диагностический скрипт для Pure Jinja2 Templates v1.0.0

Проверяет:
- FileSystemLoader конфигурацию
- Наличие import/include зависимостей
- Разрешение путей к шаблонам
- Рендеринг с test data
"""

import sys
import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound, TemplateSyntaxError

def diagnose_template(template_path: Path):
    """Диагностика Pure Jinja2 шаблона"""

    print("=" * 80)
    print(f"🔍 ДИАГНОСТИКА: {template_path.name}")
    print("=" * 80)

    # 1. Проверка существования
    if not template_path.exists():
        print(f"❌ Файл не найден: {template_path}")
        return False

    print(f"✅ Файл существует: {template_path}")

    # 2. Чтение контента
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()

    print(f"✅ Размер: {len(content)} байт")

    # 3. Проверка import/include директив
    import re
    import_pattern = r"\{%\s*import\s+['\"]([^'\"]+)['\"]\s+"
    include_pattern = r"\{%\s*include\s+['\"]([^'\"]+)['\"]\s*%\}"

    imports = re.findall(import_pattern, content)
    includes = re.findall(include_pattern, content)

    print(f"\n📦 ЗАВИСИМОСТИ:")
    print(f"   Import директив: {len(imports)}")
    for imp in imports:
        print(f"      - {imp}")
    print(f"   Include директив: {len(includes)}")
    for inc in includes:
        print(f"      - {inc}")

    # 4. Построение search paths
    search_paths = [
        str(template_path.parent),  # Директория шаблона
        str(template_path.parent.parent),  # Родительская директория
    ]

    print(f"\n📂 SEARCH PATHS:")
    for i, path in enumerate(search_paths, 1):
        print(f"   {i}. {path}")

    # 5. Проверка разрешения зависимостей
    print(f"\n🔗 ПРОВЕРКА РАЗРЕШЕНИЯ ЗАВИСИМОСТЕЙ:")

    all_deps = set(imports + includes)
    missing_deps = []

    for dep in all_deps:
        found = False
        for search_path in search_paths:
            dep_path = Path(search_path) / dep
            if dep_path.exists():
                print(f"   ✅ {dep} → {dep_path}")
                found = True
                break

        if not found:
            print(f"   ❌ {dep} → НЕ НАЙДЕН")
            missing_deps.append(dep)

    if missing_deps:
        print(f"\n❌ ОТСУТСТВУЮЩИЕ ЗАВИСИМОСТИ: {len(missing_deps)}")
        return False

    # 6. Тест рендеринга
    print(f"\n🚀 ТЕСТ РЕНДЕРИНГА:")

    try:
        env = Environment(loader=FileSystemLoader(search_paths))

        # Добавляем кастомные фильтры
        def format_currency(val):
            return f"₽ {val:,.2f}".replace(',', ' ').replace('.', ',')

        def format_date(val):
            return str(val)

        env.filters['formatCurrency'] = format_currency
        env.filters['formatDate'] = format_date
        env.filters['isoformat'] = str

        # Добавляем функции
        from datetime import datetime
        env.globals['now'] = datetime.now

        # Test data
        test_data = {
            "images": {
                "coins_stack": "https://example.com/coins.png",
                "calendar_icon": "https://example.com/calendar.png",
                "video_poster": "https://example.com/video.jpg"
            },
            "salary": {
                "current": 125000,
                "average": 120000,
                "change": 4.2,
                "accrued": 145000,
                "deducted": 20000,
                "payout": 125000,
                "paymentDate": "2025-10-15"
            },
            "privileges": [
                {"id": "1", "title": "ДМС", "description": "Медицинское страхование"},
                {"id": "2", "title": "Спорт", "description": "Фитнес абонемент"}
            ],
            "actions": {
                "salaryDetails": "https://app.com/salary/details",
                "allPrivileges": "https://app.com/privileges"
            },
            "video": {
                "posterUrl": "https://example.com/poster.jpg",
                "url": "https://example.com/video.mp4",
                "title": "О зарплате",
                "subtitle": "Узнайте больше"
            }
        }

        # Пробуем загрузить шаблон
        template_name = template_path.name
        template = env.get_template(template_name)

        print(f"   ✅ Шаблон загружен: {template_name}")

        # Пробуем рендерить
        rendered = template.render(data=test_data)

        print(f"   ✅ Рендеринг успешен!")
        print(f"   📏 Размер результата: {len(rendered)} байт")

        # Проверяем валидность JSON
        try:
            json_obj = json.loads(rendered)
            print(f"   ✅ JSON валиден!")
            print(f"   📊 Ключей верхнего уровня: {len(json_obj)}")
            return True

        except json.JSONDecodeError as e:
            print(f"   ❌ JSON невалиден: {e}")
            print(f"   📝 Первые 500 символов:")
            print(rendered[:500])
            return False

    except TemplateNotFound as e:
        print(f"   ❌ Шаблон не найден: {e.name}")
        print(f"   💡 Проверьте search paths")
        return False

    except TemplateSyntaxError as e:
        print(f"   ❌ Синтаксическая ошибка: {e.message}")
        print(f"   📍 Строка {e.lineno}")
        return False

    except Exception as e:
        print(f"   ❌ Ошибка: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python diagnose_jinja_templates_v1.0.0.py <template_path>")
        sys.exit(1)

    template_path = Path(sys.argv[1])
    success = diagnose_template(template_path)

    print("\n" + "=" * 80)
    if success:
        print("✅ ДИАГНОСТИКА УСПЕШНА")
        print("=" * 80)
        sys.exit(0)
    else:
        print("❌ ДИАГНОСТИКА ПРОВАЛЕНА")
        print("=" * 80)
        sys.exit(1)


if __name__ == '__main__':
    main()
