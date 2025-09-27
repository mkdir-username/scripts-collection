# Универсальный конвертер $ref в абсолютные пути

## Скрипты

### 1. `sdui_refs_to_absolute.py` - Основной конвертер
Преобразует ВСЕ относительные `$ref` ссылки в абсолютные `file:///` пути во всём проекте front-middle-schema.

### 2. `universal_refs_converter.py` - То же самое (копия)

## Использование

### Быстрый старт
```bash
# Конвертировать все ref'ы в проекте
cd ~/Documents/front-middle-schema
python3 ~/Scripts/Python/sdui_refs_to_absolute.py .

# Режим предпросмотра (без изменений)
python3 ~/Scripts/Python/sdui_refs_to_absolute.py . --dry-run

# Подробный вывод
python3 ~/Scripts/Python/sdui_refs_to_absolute.py . -v
```

### Обработка конкретной директории
```bash
# Только SDUI
python3 ~/Scripts/Python/sdui_refs_to_absolute.py . -d SDUI

# Только widgets
python3 ~/Scripts/Python/sdui_refs_to_absolute.py . -d widgets
```

## Что делает скрипт

1. **Сканирует все JSON файлы** в:
   - SDUI/
   - widgets/
   - multistep/
   - valuefields/
   - dependentfields/
   - analytics/
   - metaschema/
   - и других директориях

2. **Преобразует ссылки**:
   - Относительные пути → `file:///абсолютный/путь`
   - Сохраняет внутренние ссылки (#/definitions/...)
   - Не трогает HTTP/HTTPS ссылки
   - Проверяет существование файлов

3. **Безопасность**:
   - Создаёт резервные копии перед изменением
   - Режим dry-run для предпросмотра
   - Подробная статистика изменений

## Результаты последнего запуска

- **Обработано файлов:** 2398
- **Модифицировано файлов:** 371
- **Конвертировано ссылок:** 1092

## Примеры преобразований

### До:
```json
{
  "$ref": "../../../analytics/models/Parameter"
}
```

### После:
```json
{
  "$ref": "file:////Users/username/Documents/front-middle-schema/analytics/models/Parameter.json"
}
```

## Флаги

- `--dry-run` - Только показать изменения, не применять
- `-v, --verbose` - Подробный вывод каждого преобразования
- `-d, --directory` - Обработать только указанную директорию

## Когда использовать

- После клонирования репозитория
- При проблемах с валидацией схем
- Для совместимости с VS Code JSON Schema валидацией
- При переносе проекта на другую машину