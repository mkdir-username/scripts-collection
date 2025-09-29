#!/bin/bash

# Путь к корневой директории
ROOT="/Users/username/Documents/front-middle-schema"

# Путь к Python-скрипту
PY_SCRIPT="/Users/username/Scripts/sdui_web_validator_v6.3.0.py"

# Переходим в корневую директорию
cd "$ROOT" || { echo "Ошибка: Не удалось перейти в директорию $ROOT"; exit 1; }

# Цикл по компонентам
for component in SDUI/components/*/ ; do
    if [[ -d "$component" ]]; then
        # Цикл по версиям v1 и v2
        for ver in v{1,2}; do
            samples_dir="$component$ver/samples"
            if [[ -d "$samples_dir" ]]; then
                # Цикл по JSON-файлам в samples
                for file in "$samples_dir"/*.json; do
                    if [[ -f "$file" ]]; then
                        # Формируем относительный путь от корня
                        arg="${file#$ROOT/}"
                        echo "Запуск для файла: $arg"
                        python3 "$PY_SCRIPT" "$arg"
                    fi
                done
            fi
        done
    fi
done

echo "Обработка завершена."