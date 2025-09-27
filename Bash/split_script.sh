#!/bin/bash

# Скрипт для разбиения файла на части. Автоматически определяет имя и расширение
# файла, сохраняет чанки в директорию исходного файла и использует
# количество строк по умолчанию (500), если оно не задано.
#
# Требует: GNU coreutils (команда gsplit). Установить: 'brew install coreutils'
#
# Использование:
#   ./power_split.sh [путь_к_файлу]
#   ./power_split.sh [путь_к_файлу] [строк_в_чанке]

# --- 1. Проверка аргументов и утилит ---
if [[ "$#" -lt 1 ]] || [[ "$#" -gt 2 ]]; then
    echo "Ошибка: Неверное количество аргументов."
    echo "Использование: $0 [путь_к_файлу] [строк_в_чанке (по умолч. 500)]"
    exit 1
fi

if ! command -v gsplit &> /dev/null; then
    echo "Ошибка: Команда 'gsplit' не найдена."
    echo "Пожалуйста, установите GNU coreutils: 'brew install coreutils'"
    exit 1
fi

INPUT_FILE="$1"
# Устанавливаем количество строк: используем второй аргумент ($2),
# а если он пуст, то по умолчанию ставим 500.
LINES_PER_CHUNK="${2:-500}"

if [ ! -f "$INPUT_FILE" ]; then
    echo "Ошибка: Файл '$INPUT_FILE' не найден."
    exit 1
fi

# --- 2. Автоматическое определение путей и имен ---

# Определяем директорию исходного файла. Сюда будут сохраняться чанки.
OUTPUT_DIR=$(dirname -- "$INPUT_FILE")

# Извлекаем только имя файла из полного пути (например, "script.sh")
FILENAME=$(basename -- "$INPUT_FILE")

# Извлекаем расширение и имя без расширения
EXTENSION="${FILENAME##*.}"
BASENAME="${FILENAME%.*}"

# Проверяем, есть ли у файла расширение
if [ "$BASENAME" == "$FILENAME" ] && [ "$EXTENSION" == "$FILENAME" ]; then
    # У файла нет расширения (например, 'Dockerfile')
    OUTPUT_SUFFIX=""
else
    # У файла есть расширение (например, '.sh')
    OUTPUT_SUFFIX=".$EXTENSION"
fi

# Собираем полный путь для префикса новых файлов
OUTPUT_PREFIX="${OUTPUT_DIR}/${BASENAME}_chunk_"


# --- 3. Выполнение команды gsplit ---
echo "--- Параметры операции ---"
echo "Исходный файл:     $INPUT_FILE"
echo "Строк в чанке:      $LINES_PER_CHUNK"
echo "Директория вывода:  $OUTPUT_DIR"
echo "Префикс чанков:     ${BASENAME}_chunk_"
echo "--------------------------"
echo "Начинаю разбиение..."

gsplit -l "$LINES_PER_CHUNK" -d --additional-suffix="$OUTPUT_SUFFIX" "$INPUT_FILE" "$OUTPUT_PREFIX"

echo "Готово! Файлы сохранены в '$OUTPUT_DIR'."
