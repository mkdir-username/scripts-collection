"""
JSON Fix Logger v1.0.0
Система детального логирования автоматических исправлений JSON файлов.

Author: Claude Code
Date: 2025-10-05
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum


class FixType(Enum):
    """Типы автоматических исправлений"""
    MISSING_COMMA_AFTER_BRACE = "missing_comma_after_brace"
    MISSING_COMMA_AFTER_BRACKET = "missing_comma_after_bracket"
    MISSING_COMMA_AFTER_VALUE = "missing_comma_after_value"
    TRAILING_COMMA = "trailing_comma"
    INVALID_ESCAPE = "invalid_escape"
    UNCLOSED_STRING = "unclosed_string"
    UNCLOSED_BRACE = "unclosed_brace"
    UNCLOSED_BRACKET = "unclosed_bracket"
    EXTRA_COMMA = "extra_comma"
    INVALID_VALUE = "invalid_value"
    ENCODING_ISSUE = "encoding_issue"
    OTHER = "other"


@dataclass
class FixRecord:
    """Запись об одном исправлении"""
    fix_type: str
    line: int
    before: str
    after: str
    context: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь"""
        return asdict(self)


class Colors:
    """ANSI цветовые коды для терминала"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"


class JSONFixLogger:
    """
    Класс для детального логирования автоматических исправлений JSON файлов.

    Поддерживает:
    - Цветной вывод в консоль
    - Экспорт отчетов в JSON и Markdown
    - История всех исправлений
    - Интеграция с Python logging
    """

    def __init__(
        self,
        filepath: Optional[str] = None,
        use_colors: bool = True,
        log_level: int = logging.INFO
    ):
        """
        Инициализация логгера.

        Args:
            filepath: Путь к JSON файлу, который исправляется
            use_colors: Использовать ли цветной вывод
            log_level: Уровень логирования
        """
        self.filepath = filepath
        self.use_colors = use_colors
        self.fixes: List[FixRecord] = []
        self.start_time = datetime.now()

        # Настройка Python logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)

        # Если нет обработчиков, добавляем консольный
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(log_level)
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _colorize(self, text: str, color: str) -> str:
        """
        Добавляет цветовой код к тексту.

        Args:
            text: Текст для раскрашивания
            color: ANSI цветовой код

        Returns:
            Раскрашенный текст или исходный, если цвета отключены
        """
        if self.use_colors:
            return f"{color}{text}{Colors.RESET}"
        return text

    def log_fix(
        self,
        fix_type: str,
        line_number: int,
        before: str,
        after: str,
        context: str = ""
    ) -> None:
        """
        Логирование одного исправления.

        Args:
            fix_type: Тип исправления (из FixType enum или строка)
            line_number: Номер строки с исправлением
            before: Значение до исправления
            after: Значение после исправления
            context: Дополнительный контекст исправления
        """
        # Нормализация типа исправления
        if isinstance(fix_type, FixType):
            fix_type = fix_type.value

        # Создание записи
        fix_record = FixRecord(
            fix_type=fix_type,
            line=line_number,
            before=before,
            after=after,
            context=context
        )
        self.fixes.append(fix_record)

        # Форматирование для консоли
        fix_num = len(self.fixes)
        emoji_fix = "🔧"
        emoji_line = "📍"
        emoji_before = "❌"
        emoji_after = "✅"
        emoji_context = "📄"

        fix_type_display = fix_type.replace('_', ' ').title()

        log_message = (
            f"{emoji_fix} {self._colorize('AUTO-FIX #' + str(fix_num), Colors.BOLD + Colors.CYAN)}: "
            f"{self._colorize(fix_type_display, Colors.YELLOW)}\n"
            f"   {emoji_line} {self._colorize('Строка', Colors.BLUE)} {line_number}\n"
            f"   {emoji_before} {self._colorize('ДО:', Colors.RED)}   {before}\n"
            f"   {emoji_after} {self._colorize('ПОСЛЕ:', Colors.GREEN)} {after}"
        )

        if context:
            log_message += f"\n   {emoji_context} {self._colorize('Контекст:', Colors.MAGENTA)} {context}"

        self.logger.info(log_message)

    def get_summary(self) -> Dict[str, Any]:
        """
        Получение сводки всех исправлений.

        Returns:
            Словарь со статистикой исправлений
        """
        # Подсчет по типам
        fix_types_count: Dict[str, int] = {}
        for fix in self.fixes:
            fix_types_count[fix.fix_type] = fix_types_count.get(fix.fix_type, 0) + 1

        return {
            "total_fixes": len(self.fixes),
            "file": self.filepath,
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "fixes_by_type": fix_types_count,
            "all_fixes": [fix.to_dict() for fix in self.fixes]
        }

    def print_summary(self) -> None:
        """Вывод сводки в консоль с форматированием"""
        summary = self.get_summary()

        print("\n" + "=" * 60)
        print(self._colorize("📊 СВОДКА ИСПРАВЛЕНИЙ", Colors.BOLD + Colors.CYAN))
        print("=" * 60)

        if self.filepath:
            print(f"{self._colorize('Файл:', Colors.BOLD)} {self.filepath}")

        print(f"{self._colorize('Всего исправлений:', Colors.BOLD)} {summary['total_fixes']}")

        if summary['fixes_by_type']:
            print(f"\n{self._colorize('По типам:', Colors.BOLD)}")
            for fix_type, count in sorted(
                summary['fixes_by_type'].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                fix_type_display = fix_type.replace('_', ' ').title()
                print(f"  • {fix_type_display}: {self._colorize(str(count), Colors.GREEN)}")

        print("=" * 60 + "\n")

    def export_to_json(self, filepath: str) -> None:
        """
        Экспорт отчета в JSON файл.

        Args:
            filepath: Путь для сохранения JSON отчета
        """
        summary = self.get_summary()

        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        self.logger.info(
            f"📄 Отчет в JSON сохранен: {self._colorize(str(output_path), Colors.GREEN)}"
        )

    def export_to_markdown(self, filepath: str) -> None:
        """
        Экспорт отчета в Markdown файл.

        Args:
            filepath: Путь для сохранения Markdown отчета
        """
        summary = self.get_summary()
        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Формирование Markdown
        md_lines = [
            "# Отчет об автоматических исправлениях",
            "",
        ]

        if self.filepath:
            md_lines.append(f"**Файл:** `{self.filepath}`  ")

        md_lines.extend([
            f"**Дата начала:** {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}  ",
            f"**Дата окончания:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
            f"**Всего исправлений:** {summary['total_fixes']}",
            "",
        ])

        # Статистика по типам
        if summary['fixes_by_type']:
            md_lines.extend([
                "## Статистика по типам исправлений",
                "",
                "| Тип исправления | Количество |",
                "|-----------------|------------|",
            ])

            for fix_type, count in sorted(
                summary['fixes_by_type'].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                fix_type_display = fix_type.replace('_', ' ').title()
                md_lines.append(f"| {fix_type_display} | {count} |")

            md_lines.append("")

        # Детали исправлений
        if self.fixes:
            md_lines.extend([
                "## Детали исправлений",
                "",
            ])

            for idx, fix in enumerate(self.fixes, 1):
                fix_type_display = fix.fix_type.replace('_', ' ').title()
                md_lines.extend([
                    f"### Исправление #{idx}: {fix_type_display}",
                    "",
                    f"- **Строка:** {fix.line}",
                    f"- **До:** `{fix.before}`",
                    f"- **После:** `{fix.after}`",
                ])

                if fix.context:
                    md_lines.append(f"- **Контекст:** {fix.context}")

                md_lines.append("")

        # Сохранение файла
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md_lines))

        self.logger.info(
            f"📝 Отчет в Markdown сохранен: {self._colorize(str(output_path), Colors.GREEN)}"
        )

    def clear(self) -> None:
        """Очистка истории исправлений"""
        self.fixes.clear()
        self.start_time = datetime.now()
        self.logger.info("🧹 История исправлений очищена")


# Пример использования
if __name__ == "__main__":
    # Создание экземпляра логгера
    logger = JSONFixLogger(
        filepath="/path/to/sample.json",
        use_colors=True
    )

    # Логирование исправлений
    logger.log_fix(
        fix_type=FixType.MISSING_COMMA_AFTER_BRACE,
        line_number=140,
        before="}",
        after="},",
        context="rootElement завершается на строке 139"
    )

    logger.log_fix(
        fix_type=FixType.TRAILING_COMMA,
        line_number=256,
        before='"value": "test",',
        after='"value": "test"',
        context="Последний элемент в объекте"
    )

    logger.log_fix(
        fix_type=FixType.INVALID_ESCAPE,
        line_number=89,
        before=r'"path": "C:\Users\test"',
        after=r'"path": "C:\\Users\\test"',
        context="Экранирование обратных слешей"
    )

    # Вывод сводки
    logger.print_summary()

    # Экспорт отчетов
    logger.export_to_json("/Users/username/Scripts/Python/reports/fix_report.json")
    logger.export_to_markdown("/Users/username/Scripts/Python/reports/fix_report.md")

    # Получение сводки программно
    summary = logger.get_summary()
    print(f"\nПрограммный доступ к сводке:")
    print(f"Всего исправлений: {summary['total_fixes']}")
    print(f"Типы: {list(summary['fixes_by_type'].keys())}")
