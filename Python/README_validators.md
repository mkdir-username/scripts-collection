# Валидаторы и конвертеры JSON Schema $ref

## Основные скрипты

### 1. `validate_all_refs.py` - Валидатор всех ссылок
Проверяет корректность ВСЕХ `$ref` ссылок в JSON схемах без открытия целевых файлов.

**Возможности:**
- Проверка существования файлов по ссылкам
- Валидация формата file:/// путей
- Обнаружение отсутствующих расширений .json
- Поиск битых ссылок
- Автоматическое исправление (флаг --fix)

**Использование:**
```bash
# Проверка всего проекта
cd ~/Documents/front-middle-schema
python3 ~/Scripts/Python/validate_all_refs.py .

# Только проверка (без изменений)
python3 ~/Scripts/Python/validate_all_refs.py .

# Автоисправление где возможно
python3 ~/Scripts/Python/validate_all_refs.py . --fix

# Проверка конкретной директории
python3 ~/Scripts/Python/validate_all_refs.py . -d SDUI

# Проверка одного файла
python3 ~/Scripts/Python/validate_all_refs.py . -f path/to/file.json

# Подробный вывод
python3 ~/Scripts/Python/validate_all_refs.py . -v
```

### 2. `sdui_refs_to_absolute.py` - Конвертер в абсолютные пути
Преобразует ВСЕ относительные `$ref` в абсолютные `file:///` пути.

**Использование:**
```bash
# Конвертировать все ref'ы
python3 ~/Scripts/Python/sdui_refs_to_absolute.py .

# Режим предпросмотра
python3 ~/Scripts/Python/sdui_refs_to_absolute.py . --dry-run

# Только конкретная директория
python3 ~/Scripts/Python/sdui_refs_to_absolute.py . -d widgets
```

### 3. `fix_extra_slash.py` - Исправление лишних слэшей
Исправляет `file:////` на правильные `file:///`.

### 4. `fix_all_refs.py` - Добавление .json расширений
Добавляет отсутствующие `.json` расширения в ссылках.

## Типичные проблемы и решения

### Проблема: "File not found"
**Причина:** Файл по ссылке не существует
**Решение:**
1. Проверить правильность пути
2. Создать отсутствующий файл
3. Или исправить ссылку на правильную

### Проблема: "Invalid format (4 slashes)"
**Причина:** `file:////` вместо `file:///`
**Решение:** Запустить `fix_extra_slash.py`

### Проблема: "Missing .json extension"
**Причина:** Ссылка без расширения `.json`
**Решение:** Запустить `fix_all_refs.py`

### Проблема: "Relative path should be absolute"
**Причина:** Использование относительных путей `../`
**Решение:** Запустить `sdui_refs_to_absolute.py`

## Рекомендуемый порядок использования

1. **Сначала конвертировать в абсолютные пути:**
   ```bash
   python3 ~/Scripts/Python/sdui_refs_to_absolute.py .
   ```

2. **Проверить валидность всех ссылок:**
   ```bash
   python3 ~/Scripts/Python/validate_all_refs.py .
   ```

3. **Если есть проблемы, автоисправить:**
   ```bash
   python3 ~/Scripts/Python/validate_all_refs.py . --fix
   ```

4. **Финальная проверка:**
   ```bash
   python3 ~/Scripts/Python/validate_all_refs.py .
   ```

## Статистика последней проверки

- ✅ Валидных ссылок: 2588
- ❌ Проблемных: 52
  - Относительные пути в метасхемах: 52 (намеренно)

## Важные замечания

1. **Метасхемы** используют относительные пути намеренно (./type/...) - это нормально
2. **Валидатор НЕ открывает** целевые файлы - только проверяет их существование
3. **Автоисправление** работает для форматных ошибок, но не создаёт отсутствующие файлы