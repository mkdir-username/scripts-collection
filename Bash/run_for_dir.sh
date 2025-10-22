#!/bin/bash

# Путь к директории с файлами
DRAFT_DIR="/Users/username/Documents/FMS_GIT/_JSON/draft"

# Путь к Python-скрипту
PY_SCRIPT="/Users/username/Scripts/validators/v3.0.0/sdui_web_validator_v3.0.0_simple.py"

# Путь к родительской директории (для cd)
PARENT_DIR="/Users/username/Documents/FMS_GIT/_JSON"

# Переходим в родительскую директорию
cd "$PARENT_DIR" || { echo "Ошибка: Не удалось перейти в директорию $PARENT_DIR"; exit 1; }

# Цикл по всем файлам в папке draft (предполагаем .json файлы, но можно изменить на *)
for file in "$DRAFT_DIR"/*.json; do
    if [[ -f "$file" ]]; then
        # Извлекаем имя файла без пути
        filename=$(basename "$file")
        # Формируем аргумент как draft/filename (без ведущего слеша для относительного пути)
        arg="draft/$filename"
        echo "Запуск для файла: $arg"
        python3 "$PY_SCRIPT" "$arg"
    fi
done

echo "Обработка завершена."