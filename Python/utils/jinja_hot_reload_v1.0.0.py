#!/usr/bin/env python3
"""
Jinja2 Template Hot Reload Server
Автоматическая перезагрузка и рендеринг Jinja2 шаблонов при изменениях
"""

import os
import sys
import time
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

try:
    from jinja2 import Environment, FileSystemLoader, Template
    from jinja2.exceptions import TemplateError
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    print("Установите необходимые зависимости:")
    print("pip install jinja2 watchdog")
    sys.exit(1)


class JinjaHotReloader(FileSystemEventHandler):
    """Обработчик событий файловой системы для hot reload Jinja2 шаблонов"""

    def __init__(self, template_dir: str, output_dir: str = None,
                 context_file: str = None, auto_render: bool = True):
        """
        Инициализация hot reloader

        Args:
            template_dir: Директория с шаблонами
            output_dir: Директория для вывода рендеренных файлов
            context_file: JSON файл с контекстом для рендеринга
            auto_render: Автоматический рендеринг при изменениях
        """
        self.template_dir = Path(template_dir)
        self.output_dir = Path(output_dir) if output_dir else self.template_dir / 'rendered'
        self.context_file = Path(context_file) if context_file else None
        self.auto_render = auto_render

        # Создаем директорию вывода если не существует
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Настраиваем Jinja2 окружение
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            auto_reload=True,
            cache_size=0  # Отключаем кеш для hot reload
        )

        # Загружаем контекст
        self.context = self.load_context()

        print(f"🔥 Hot Reload сервер запущен")
        print(f"📁 Директория шаблонов: {self.template_dir}")
        print(f"📁 Директория вывода: {self.output_dir}")
        if self.context_file:
            print(f"📄 Файл контекста: {self.context_file}")

    def load_context(self) -> Dict[str, Any]:
        """Загрузка контекста из JSON файла"""
        if not self.context_file or not self.context_file.exists():
            return {}

        try:
            with open(self.context_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Ошибка загрузки контекста: {e}")
            return {}

    def render_template(self, template_path: Path) -> Optional[str]:
        """
        Рендеринг шаблона

        Args:
            template_path: Путь к файлу шаблона

        Returns:
            Рендеренный контент или None при ошибке
        """
        try:
            # Получаем относительный путь от директории шаблонов
            relative_path = template_path.relative_to(self.template_dir)

            # Загружаем и рендерим шаблон
            template = self.env.get_template(str(relative_path))

            # Добавляем метаданные в контекст
            render_context = {
                **self.context,
                'render_time': datetime.now().isoformat(),
                'template_name': str(relative_path),
            }

            rendered = template.render(render_context)

            # Сохраняем результат
            if self.auto_render:
                output_file = self.output_dir / relative_path.with_suffix('.html')
                output_file.parent.mkdir(parents=True, exist_ok=True)

                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(rendered)

                print(f"✅ Рендеринг: {relative_path} -> {output_file.name}")

            return rendered

        except TemplateError as e:
            print(f"❌ Ошибка шаблона {template_path.name}: {e}")
            return None
        except Exception as e:
            print(f"❌ Неожиданная ошибка: {e}")
            return None

    def on_modified(self, event):
        """Обработчик изменения файла"""
        if event.is_directory:
            return

        path = Path(event.src_path)

        # Перезагружаем контекст если изменился JSON
        if self.context_file and path == self.context_file:
            print(f"🔄 Перезагрузка контекста: {path.name}")
            self.context = self.load_context()
            # Перерендериваем все шаблоны
            self.render_all_templates()
            return

        # Рендерим измененный шаблон
        if path.suffix in ['.j2', '.jinja2', '.jinja', '.html.j2']:
            print(f"🔄 Изменен шаблон: {path.name}")
            self.render_template(path)

    def render_all_templates(self):
        """Рендеринг всех шаблонов в директории"""
        templates = list(self.template_dir.glob('**/*.j2')) + \
                   list(self.template_dir.glob('**/*.jinja2')) + \
                   list(self.template_dir.glob('**/*.jinja'))

        print(f"🚀 Рендеринг {len(templates)} шаблонов...")

        for template_path in templates:
            self.render_template(template_path)

        print("✨ Все шаблоны обработаны")

    def watch(self):
        """Запуск наблюдателя за изменениями файлов"""
        observer = Observer()

        # Наблюдаем за директорией шаблонов
        observer.schedule(self, str(self.template_dir), recursive=True)

        # Наблюдаем за файлом контекста
        if self.context_file and self.context_file.exists():
            observer.schedule(self, str(self.context_file.parent), recursive=False)

        observer.start()

        print("👀 Отслеживание изменений... (Ctrl+C для остановки)")

        try:
            # Первичный рендеринг всех шаблонов
            self.render_all_templates()

            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            print("\n🛑 Hot reload остановлен")

        observer.join()


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description='Jinja2 Hot Reload Server - автоматический рендеринг шаблонов',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  # Простой запуск в текущей директории
  %(prog)s

  # Указание директории с шаблонами
  %(prog)s templates/

  # С контекстом из JSON файла
  %(prog)s templates/ --context data.json

  # Вывод в другую директорию
  %(prog)s templates/ --output dist/

  # Однократный рендеринг без наблюдения
  %(prog)s templates/ --no-watch
"""
    )

    parser.add_argument(
        'template_dir',
        nargs='?',
        default='.',
        help='Директория с Jinja2 шаблонами (по умолчанию: текущая)'
    )

    parser.add_argument(
        '-o', '--output',
        help='Директория для вывода рендеренных файлов'
    )

    parser.add_argument(
        '-c', '--context',
        help='JSON файл с контекстом для рендеринга'
    )

    parser.add_argument(
        '--no-watch',
        action='store_true',
        help='Однократный рендеринг без отслеживания изменений'
    )

    parser.add_argument(
        '--no-auto-render',
        action='store_true',
        help='Не сохранять рендеренные файлы автоматически'
    )

    args = parser.parse_args()

    # Проверяем существование директории
    template_dir = Path(args.template_dir)
    if not template_dir.exists():
        print(f"❌ Директория не найдена: {template_dir}")
        sys.exit(1)

    # Создаем hot reloader
    reloader = JinjaHotReloader(
        template_dir=str(template_dir),
        output_dir=args.output,
        context_file=args.context,
        auto_render=not args.no_auto_render
    )

    # Запускаем
    if args.no_watch:
        # Однократный рендеринг
        reloader.render_all_templates()
    else:
        # Hot reload режим
        reloader.watch()


if __name__ == '__main__':
    main()