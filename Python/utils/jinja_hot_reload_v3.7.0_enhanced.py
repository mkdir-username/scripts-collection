#!/usr/bin/env python3
"""
Jinja Hot Reload v3.7.0 Enhanced - Расширенная система автоисправления JSON
Интеллектуальное исправление синтаксических ошибок в JSON/Jinja2 шаблонах

Новые возможности v3.7.0:
1. Исправление пропущенных запятых после скобок/фигурных скобок
2. Обработка дублирующихся запятых
3. Автоматическое добавление кавычек к свойствам
4. Очистка некорректных комментариев JSON
5. Детальное логирование всех исправлений с контекстом

Автор: Claude Code
Дата: 2025-10-05
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging


class FixType(Enum):
    """Типы исправлений для категоризации."""
    MISSING_COMMA_AFTER_BRACE = "missing_comma_after_brace"
    MISSING_COMMA_AFTER_BRACKET = "missing_comma_after_bracket"
    DUPLICATE_COMMA = "duplicate_comma"
    MISSING_QUOTES = "missing_quotes"
    INVALID_COMMENT = "invalid_comment"
    TRAILING_COMMA = "trailing_comma"
    OBJECT_SEPARATOR = "object_separator"


@dataclass
class Fix:
    """Информация о примененном исправлении."""
    fix_type: FixType
    line_number: int
    context_before: str
    context_after: str
    description: str
    column: Optional[int] = None


class SmartJSONFixer:
    """
    Интеллектуальная система автоисправления JSON синтаксиса.

    Исправляет:
    - Пропущенные запятые после }/]
    - Дублирующиеся запятые
    - Свойства без кавычек
    - Некорректные комментарии
    - Trailing commas
    """

    def __init__(self, verbose: bool = True):
        """
        Инициализация фиксера.

        Args:
            verbose: Включить подробное логирование исправлений
        """
        self.fixes_applied: List[Fix] = []
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)

        # Статистика
        self.total_fixes = 0
        self.fixes_by_type: Dict[FixType, int] = {ft: 0 for ft in FixType}

    def fix_json(self, content: str) -> str:
        """
        Применяет все исправления к JSON контенту.

        Args:
            content: Исходный JSON контент

        Returns:
            Исправленный JSON контент
        """
        self.fixes_applied = []

        # Порядок исправлений важен!
        content = self._fix_invalid_comments(content)
        content = self._fix_missing_comma_after_brace(content)
        content = self._fix_missing_comma_after_bracket(content)
        content = self._fix_duplicate_commas(content)
        content = self._fix_missing_quotes(content)
        content = self._fix_trailing_commas(content)

        self.total_fixes = len(self.fixes_applied)

        if self.verbose and self.fixes_applied:
            self._log_fixes()

        return content

    def _fix_missing_comma_after_brace(self, content: str) -> str:
        """
        Исправляет пропущенные запятые после закрывающей фигурной скобки.

        Паттерны:
        - }\n"property" → },\n"property"
        - }\n{ → },\n{
        - } "property" → }, "property"

        Args:
            content: JSON контент

        Returns:
            Исправленный контент
        """
        lines = content.split('\n')
        result = []

        for i, line in enumerate(lines):
            line_num = i + 1
            stripped = line.strip()

            # Паттерн 1: } в конце строки, следующая начинается с " или {
            if stripped.endswith('}') and i + 1 < len(lines):
                next_line = lines[i + 1].strip()

                if next_line and (next_line.startswith('"') or next_line.startswith('{')):
                    # Проверяем, нет ли уже запятой
                    if not stripped.endswith(',}'):
                        context_before = line
                        line = line.rstrip('}') + '},'
                        context_after = line

                        self._add_fix(
                            FixType.MISSING_COMMA_AFTER_BRACE,
                            line_num,
                            context_before,
                            context_after,
                            f"Добавлена запятая после '}}' перед {next_line[:30]}..."
                        )

            # Паттерн 2: } "property" на одной строке
            if re.search(r'\}\s+"', line):
                context_before = line
                line = re.sub(r'\}(\s+)"', r'},\1"', line)
                context_after = line

                if context_before != context_after:
                    self._add_fix(
                        FixType.MISSING_COMMA_AFTER_BRACE,
                        line_num,
                        context_before,
                        context_after,
                        "Добавлена запятая между } и следующим свойством"
                    )

            # Паттерн 3: }{ на одной строке
            if '}{' in line and '},\n{' not in line:
                context_before = line
                line = line.replace('}{', '},\n{')
                context_after = line

                if context_before != context_after:
                    self._add_fix(
                        FixType.OBJECT_SEPARATOR,
                        line_num,
                        context_before,
                        context_after,
                        "Добавлена запятая и перенос строки между объектами"
                    )

            result.append(line)

        return '\n'.join(result)

    def _fix_missing_comma_after_bracket(self, content: str) -> str:
        """
        Исправляет пропущенные запятые после закрывающей квадратной скобки.

        Паттерны:
        - ]\n{ → ],\n{
        - ]\n" → ],\n"
        - ] { → ], {

        Args:
            content: JSON контент

        Returns:
            Исправленный контент
        """
        lines = content.split('\n')
        result = []

        for i, line in enumerate(lines):
            line_num = i + 1
            stripped = line.strip()

            # Паттерн 1: ] в конце строки, следующая начинается с { или "
            if stripped.endswith(']') and i + 1 < len(lines):
                next_line = lines[i + 1].strip()

                if next_line and (next_line.startswith('{') or next_line.startswith('"')):
                    # Проверяем, нет ли уже запятой
                    if not stripped.endswith(',]'):
                        context_before = line
                        line = line.rstrip(']') + '],'
                        context_after = line

                        self._add_fix(
                            FixType.MISSING_COMMA_AFTER_BRACKET,
                            line_num,
                            context_before,
                            context_after,
                            f"Добавлена запятая после ']' перед {next_line[:30]}..."
                        )

            # Паттерн 2: ] { или ] " на одной строке
            if re.search(r'\]\s+[{"]', line):
                context_before = line
                line = re.sub(r'\](\s+)([{"])', r'],\1\2', line)
                context_after = line

                if context_before != context_after:
                    self._add_fix(
                        FixType.MISSING_COMMA_AFTER_BRACKET,
                        line_num,
                        context_before,
                        context_after,
                        "Добавлена запятая после ']'"
                    )

            result.append(line)

        return '\n'.join(result)

    def _fix_duplicate_commas(self, content: str) -> str:
        """
        Исправляет дублирующиеся запятые.

        Паттерны:
        - ,, → ,
        - , , → ,
        - ,  , → ,

        Args:
            content: JSON контент

        Returns:
            Исправленный контент
        """
        lines = content.split('\n')
        result = []

        for i, line in enumerate(lines):
            line_num = i + 1
            context_before = line

            # Убираем множественные запятые с пробелами
            while re.search(r',\s*,', line):
                line = re.sub(r',\s*,', ',', line)

            if context_before != line:
                self._add_fix(
                    FixType.DUPLICATE_COMMA,
                    line_num,
                    context_before,
                    line,
                    "Удалены дублирующиеся запятые"
                )

            result.append(line)

        return '\n'.join(result)

    def _fix_missing_quotes(self, content: str) -> str:
        """
        Исправляет свойства JSON без кавычек.

        Паттерны:
        - propertyName: value → "propertyName": value
        - { id: 123 } → { "id": 123 }

        ВНИМАНИЕ: Не применяется внутри строковых значений!

        Args:
            content: JSON контент

        Returns:
            Исправленный контент
        """
        lines = content.split('\n')
        result = []

        # Безопасный паттерн: ключ без кавычек перед двоеточием
        # Избегаем изменений внутри строк
        pattern = re.compile(r'(\s+)([a-zA-Z_][a-zA-Z0-9_]*)\s*:')

        for i, line in enumerate(lines):
            line_num = i + 1

            # Пропускаем строки в комментариях
            if line.strip().startswith('//'):
                result.append(line)
                continue

            context_before = line

            # Ищем свойства без кавычек
            matches = pattern.finditer(line)
            replacements = []

            for match in matches:
                indent = match.group(1)
                prop_name = match.group(2)

                # Проверяем, что это не часть строки
                # Считаем кавычки до этой позиции
                before = line[:match.start()]
                quote_count = before.count('"') - before.count('\\"')

                # Если четное количество кавычек - мы вне строки
                if quote_count % 2 == 0:
                    replacements.append((match.group(0), f'{indent}"{prop_name}":'))

            # Применяем замены
            for old, new in replacements:
                line = line.replace(old, new, 1)

            if context_before != line:
                self._add_fix(
                    FixType.MISSING_QUOTES,
                    line_num,
                    context_before,
                    line,
                    f"Добавлены кавычки к свойству (-ам)"
                )

            result.append(line)

        return '\n'.join(result)

    def _fix_invalid_comments(self, content: str) -> str:
        """
        Исправляет или удаляет некорректные JSON комментарии.

        JSON стандарт не поддерживает комментарии.
        Этот метод:
        - Удаляет // комментарии
        - Удаляет /* */ блочные комментарии
        - Сохраняет строковые значения с // внутри

        Args:
            content: JSON контент

        Returns:
            Очищенный контент
        """
        lines = content.split('\n')
        result = []
        in_block_comment = False

        for i, line in enumerate(lines):
            line_num = i + 1
            context_before = line

            # Обработка блочных комментариев
            if '/*' in line:
                in_block_comment = True
                line = re.sub(r'/\*.*?\*/', '', line)  # Однострочный блочный комментарий

            if '*/' in line:
                in_block_comment = False
                line = re.sub(r'.*\*/', '', line)

            if in_block_comment:
                self._add_fix(
                    FixType.INVALID_COMMENT,
                    line_num,
                    context_before,
                    "",
                    "Удален блочный комментарий /* */"
                )
                continue

            # Обработка однострочных комментариев //
            # Проверяем, что это не часть строкового значения
            if '//' in line:
                # Считаем кавычки до //
                comment_pos = line.find('//')
                before_comment = line[:comment_pos]
                quote_count = before_comment.count('"') - before_comment.count('\\"')

                # Если четное количество кавычек - комментарий вне строки
                if quote_count % 2 == 0:
                    cleaned = line[:comment_pos].rstrip()

                    if cleaned != line.rstrip():
                        self._add_fix(
                            FixType.INVALID_COMMENT,
                            line_num,
                            context_before,
                            cleaned,
                            f"Удален комментарий: {line[comment_pos:].strip()[:40]}..."
                        )
                        line = cleaned

            result.append(line)

        return '\n'.join(result)

    def _fix_trailing_commas(self, content: str) -> str:
        """
        Удаляет trailing commas перед закрывающими скобками.

        Паттерны:
        - , } → }
        - , ] → ]
        - , \n} → \n}

        Args:
            content: JSON контент

        Returns:
            Исправленный контент
        """
        lines = content.split('\n')
        result = []

        for i, line in enumerate(lines):
            line_num = i + 1
            context_before = line

            # Trailing comma перед }
            if re.search(r',\s*\}', line):
                line = re.sub(r',(\s*\})', r'\1', line)

            # Trailing comma перед ]
            if re.search(r',\s*\]', line):
                line = re.sub(r',(\s*\])', r'\1', line)

            # Trailing comma в конце строки, если следующая - закрывающая скобка
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if line.rstrip().endswith(',') and next_line in ['}', ']', '},', '],']:
                    line = line.rstrip().rstrip(',')

            if context_before != line:
                self._add_fix(
                    FixType.TRAILING_COMMA,
                    line_num,
                    context_before,
                    line,
                    "Удалена trailing comma"
                )

            result.append(line)

        return '\n'.join(result)

    def _add_fix(
        self,
        fix_type: FixType,
        line_number: int,
        context_before: str,
        context_after: str,
        description: str,
        column: Optional[int] = None
    ) -> None:
        """
        Регистрирует примененное исправление.

        Args:
            fix_type: Тип исправления
            line_number: Номер строки
            context_before: Содержимое до исправления
            context_after: Содержимое после исправления
            description: Описание исправления
            column: Номер колонки (опционально)
        """
        fix = Fix(
            fix_type=fix_type,
            line_number=line_number,
            context_before=context_before.strip(),
            context_after=context_after.strip(),
            description=description,
            column=column
        )

        self.fixes_applied.append(fix)
        self.fixes_by_type[fix_type] += 1

    def _log_fixes(self) -> None:
        """Выводит подробный лог всех примененных исправлений."""
        print(f"\n{'='*80}")
        print(f"📝 ОТЧЕТ ОБ ИСПРАВЛЕНИЯХ JSON")
        print(f"{'='*80}")
        print(f"Всего исправлений: {self.total_fixes}\n")

        # Группируем по типам
        for fix_type in FixType:
            count = self.fixes_by_type[fix_type]
            if count > 0:
                print(f"\n{fix_type.value.upper().replace('_', ' ')}: {count}")
                print(f"{'-'*60}")

                for fix in self.fixes_applied:
                    if fix.fix_type == fix_type:
                        print(f"  Строка {fix.line_number}: {fix.description}")
                        print(f"    До:    {fix.context_before[:70]}")
                        print(f"    После: {fix.context_after[:70]}")
                        print()

        print(f"{'='*80}\n")

    def get_fixes_summary(self) -> Dict[str, Any]:
        """
        Возвращает сводку по исправлениям.

        Returns:
            Словарь со статистикой исправлений
        """
        return {
            'total_fixes': self.total_fixes,
            'fixes_by_type': {
                ft.value: count for ft, count in self.fixes_by_type.items()
            },
            'fixes': [
                {
                    'type': fix.fix_type.value,
                    'line': fix.line_number,
                    'description': fix.description,
                    'before': fix.context_before,
                    'after': fix.context_after
                }
                for fix in self.fixes_applied
            ]
        }

    def validate_json(self, content: str) -> Tuple[bool, Optional[str]]:
        """
        Проверяет валидность JSON после исправлений.

        Args:
            content: JSON контент

        Returns:
            Кортеж (is_valid, error_message)
        """
        try:
            json.loads(content)
            return True, None
        except json.JSONDecodeError as e:
            error_msg = f"JSON ошибка на строке {e.lineno}, колонка {e.colno}: {e.msg}"
            return False, error_msg


class EnhancedJSONProcessor:
    """
    Расширенный процессор JSON с автоисправлением.
    Интегрирует SmartJSONFixer в общий workflow.
    """

    def __init__(self, auto_fix: bool = True, verbose: bool = True):
        """
        Инициализация процессора.

        Args:
            auto_fix: Автоматически исправлять ошибки
            verbose: Подробное логирование
        """
        self.auto_fix = auto_fix
        self.fixer = SmartJSONFixer(verbose=verbose)
        self.processing_stats = {
            'files_processed': 0,
            'files_fixed': 0,
            'files_failed': 0
        }

    def process_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Обрабатывает JSON файл с автоисправлением.

        Args:
            file_path: Путь к JSON файлу

        Returns:
            Результат обработки
        """
        result = {
            'file': str(file_path),
            'status': 'pending',
            'fixes_applied': 0,
            'errors': []
        }

        try:
            # Читаем файл
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Пытаемся парсить как есть
            is_valid, error = self.fixer.validate_json(content)

            if is_valid:
                result['status'] = 'valid'
                result['message'] = 'JSON валиден без исправлений'
            elif self.auto_fix:
                # Применяем исправления
                fixed_content = self.fixer.fix_json(content)

                # Проверяем результат
                is_valid_after, error_after = self.fixer.validate_json(fixed_content)

                if is_valid_after:
                    result['status'] = 'fixed'
                    result['fixes_applied'] = self.fixer.total_fixes
                    result['fixes'] = self.fixer.get_fixes_summary()

                    # Сохраняем исправленный файл
                    backup_path = file_path.with_suffix('.json.backup')
                    file_path.rename(backup_path)

                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(fixed_content)

                    result['backup'] = str(backup_path)
                    result['message'] = f'Применено {self.fixer.total_fixes} исправлений'
                    self.processing_stats['files_fixed'] += 1
                else:
                    result['status'] = 'failed'
                    result['errors'].append(error_after)
                    result['fixes_applied'] = self.fixer.total_fixes
                    result['message'] = 'Не удалось исправить все ошибки'
                    self.processing_stats['files_failed'] += 1
            else:
                result['status'] = 'invalid'
                result['errors'].append(error)
                result['message'] = 'JSON невалиден, auto_fix отключен'
                self.processing_stats['files_failed'] += 1

            self.processing_stats['files_processed'] += 1

        except Exception as e:
            result['status'] = 'error'
            result['errors'].append(str(e))
            self.processing_stats['files_failed'] += 1

        return result

    def get_stats(self) -> Dict[str, int]:
        """Возвращает статистику обработки."""
        return self.processing_stats.copy()


def main():
    """Демонстрационная функция."""
    import argparse

    parser = argparse.ArgumentParser(
        description='SmartJSONFixer v3.7.0 - Интеллектуальное исправление JSON'
    )
    parser.add_argument(
        'file',
        type=Path,
        help='JSON файл для обработки'
    )
    parser.add_argument(
        '--no-auto-fix',
        action='store_true',
        help='Отключить автоисправление'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Минимальный вывод'
    )

    args = parser.parse_args()

    processor = EnhancedJSONProcessor(
        auto_fix=not args.no_auto_fix,
        verbose=not args.quiet
    )

    result = processor.process_file(args.file)

    print(f"\n{'='*80}")
    print(f"РЕЗУЛЬТАТ ОБРАБОТКИ: {result['file']}")
    print(f"{'='*80}")
    print(f"Статус: {result['status']}")
    print(f"Сообщение: {result['message']}")

    if result.get('fixes_applied', 0) > 0:
        print(f"\nПрименено исправлений: {result['fixes_applied']}")
        if result.get('backup'):
            print(f"Резервная копия: {result['backup']}")

    if result.get('errors'):
        print(f"\nОшибки:")
        for error in result['errors']:
            print(f"  - {error}")

    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
