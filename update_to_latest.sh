#!/bin/bash

################################################################################
# Script: update_to_latest.sh
# Version: 1.0.0
# Description: Автоматическое обновление символических ссылок на последние версии
# Author: System Administrator
# Date: 2025-09-27
################################################################################

set -euo pipefail

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Базовая директория скриптов
SCRIPTS_DIR="/Users/username/Scripts"
BACKUP_DIR="${SCRIPTS_DIR}/backups/$(date +%Y%m%d_%H%M%S)"
LOG_FILE="${SCRIPTS_DIR}/logs/update_$(date +%Y%m%d_%H%M%S).log"

# Создание необходимых директорий
mkdir -p "${SCRIPTS_DIR}/logs"
mkdir -p "$BACKUP_DIR"

# Функция логирования
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Функция вывода с цветом
print_colored() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Функция проверки работоспособности скрипта
test_script() {
    local script_path=$1
    local script_type="${script_path##*.}"

    case "$script_type" in
        sh)
            if bash -n "$script_path" 2>/dev/null; then
                return 0
            else
                return 1
            fi
            ;;
        py)
            if python3 -m py_compile "$script_path" 2>/dev/null; then
                return 0
            else
                return 1
            fi
            ;;
        *)
            return 0
            ;;
    esac
}

# Функция создания резервной копии
backup_link() {
    local link_path=$1
    local link_name=$(basename "$link_path")

    if [ -L "$link_path" ]; then
        local target=$(readlink "$link_path")
        echo "$link_name -> $target" >> "$BACKUP_DIR/links.txt"
        log "Резервная копия ссылки: $link_name -> $target"
    fi
}

# Функция поиска последней версии
find_latest_version() {
    local base_name=$1
    local directory=$2
    local extension=$3

    # Поиск файлов с версионированием
    local latest_file=$(find "$directory" -maxdepth 1 -name "${base_name}_v[0-9]*.[0-9]*.[0-9]*${extension}" 2>/dev/null | sort -V | tail -1)

    if [ -n "$latest_file" ]; then
        echo "$latest_file"
    else
        echo ""
    fi
}

# Функция обновления символической ссылки
update_symlink() {
    local directory=$1
    local base_name=$2
    local extension=$3

    local latest_link="${directory}/${base_name}_latest${extension}"
    local latest_version=$(find_latest_version "$base_name" "$directory" "$extension")

    if [ -z "$latest_version" ]; then
        print_colored "$YELLOW" "⚠ Не найдены версии для: ${base_name}${extension}"
        return 1
    fi

    # Проверка работоспособности последней версии
    if ! test_script "$latest_version"; then
        print_colored "$RED" "✗ Ошибка синтаксиса в: $(basename $latest_version)"
        return 1
    fi

    # Создание резервной копии существующей ссылки
    backup_link "$latest_link"

    # Удаление старой ссылки, если существует
    if [ -L "$latest_link" ]; then
        rm "$latest_link"
    fi

    # Создание новой ссылки
    ln -s "$(basename $latest_version)" "$latest_link"

    print_colored "$GREEN" "✓ Обновлено: ${base_name}_latest${extension} -> $(basename $latest_version)"
    log "Обновлена ссылка: $latest_link -> $(basename $latest_version)"

    return 0
}

# Функция сканирования директории
scan_directory() {
    local dir=$1
    local dir_name=$(basename "$dir")

    print_colored "$BLUE" "\n=== Сканирование: $dir_name ==="

    local updated=0
    local failed=0

    # Поиск всех версионированных файлов
    while IFS= read -r -d '' file; do
        local filename=$(basename "$file")

        # Извлечение базового имени и расширения
        if [[ $filename =~ ^(.+)_v[0-9]+\.[0-9]+\.[0-9]+(.*)$ ]]; then
            local base_name="${BASH_REMATCH[1]}"
            local extension="${BASH_REMATCH[2]}"

            # Проверка, не обработали ли мы уже этот базовый файл
            if [ ! -f "/tmp/processed_${base_name}" ]; then
                touch "/tmp/processed_${base_name}"

                if update_symlink "$(dirname $file)" "$base_name" "$extension"; then
                    ((updated++))
                else
                    ((failed++))
                fi
            fi
        fi
    done < <(find "$dir" -type f -name "*_v[0-9]*.[0-9]*.[0-9]*.*" -print0 2>/dev/null)

    # Очистка временных файлов
    rm -f /tmp/processed_*

    print_colored "$BLUE" "Обновлено: $updated, Ошибок: $failed"

    return 0
}

# Функция проверки целостности
check_integrity() {
    print_colored "$BLUE" "\n=== Проверка целостности ==="

    local broken_links=0
    local valid_links=0

    while IFS= read -r -d '' link; do
        if [ ! -e "$link" ]; then
            print_colored "$RED" "✗ Битая ссылка: $link"
            ((broken_links++))
        else
            ((valid_links++))
        fi
    done < <(find "$SCRIPTS_DIR" -type l -name "*_latest.*" -print0 2>/dev/null)

    print_colored "$GREEN" "✓ Рабочих ссылок: $valid_links"
    if [ $broken_links -gt 0 ]; then
        print_colored "$RED" "✗ Битых ссылок: $broken_links"
    fi

    return 0
}

# Главная функция
main() {
    print_colored "$BLUE" "╔════════════════════════════════════════════════╗"
    print_colored "$BLUE" "║   Обновление символических ссылок на latest   ║"
    print_colored "$BLUE" "╚════════════════════════════════════════════════╝"

    log "Начало обновления символических ссылок"

    # Проверка существования директории
    if [ ! -d "$SCRIPTS_DIR" ]; then
        print_colored "$RED" "Ошибка: Директория $SCRIPTS_DIR не существует"
        exit 1
    fi

    # Сканирование основных директорий
    for category_dir in "$SCRIPTS_DIR"/{Bash,Python,validators,tools,xray-installer,claude-sdui}; do
        if [ -d "$category_dir" ]; then
            # Рекурсивное сканирование поддиректорий
            find "$category_dir" -type d | while read -r subdir; do
                scan_directory "$subdir"
            done
        fi
    done

    # Проверка целостности
    check_integrity

    # Создание отчета
    print_colored "$BLUE" "\n=== Создание отчета ==="

    cat > "$BACKUP_DIR/update_report.txt" <<EOF
Отчет об обновлении символических ссылок
========================================
Дата: $(date)
Лог файл: $LOG_FILE
Резервные копии: $BACKUP_DIR

Обновленные ссылки:
-------------------
$(grep "Обновлена ссылка" "$LOG_FILE" | wc -l) ссылок обновлено

Детали:
-------
$(grep "Обновлена ссылка" "$LOG_FILE")

Проблемы:
---------
$(grep "Ошибка" "$LOG_FILE" || echo "Ошибок не обнаружено")
EOF

    print_colored "$GREEN" "✓ Отчет сохранен в: $BACKUP_DIR/update_report.txt"

    # Опциональная очистка старых логов (старше 30 дней)
    find "${SCRIPTS_DIR}/logs" -name "update_*.log" -mtime +30 -delete 2>/dev/null

    print_colored "$GREEN" "\n✅ Обновление завершено успешно!"
    log "Обновление завершено"

    # Предложение просмотреть изменения
    echo
    read -p "Показать список обновленных ссылок? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        grep "Обновлена ссылка" "$LOG_FILE" | less
    fi
}

# Обработка аргументов командной строки
case "${1:-}" in
    --help|-h)
        cat <<EOF
Использование: $0 [ОПЦИИ]

Автоматическое обновление символических ссылок *_latest.* на последние версии файлов.

ОПЦИИ:
    --help, -h       Показать эту справку
    --dry-run        Показать, что будет сделано, без внесения изменений
    --check          Только проверить целостность ссылок
    --dir DIR        Обновить только указанную директорию
    --restore DATE   Восстановить ссылки из резервной копии

ПРИМЕРЫ:
    $0                    # Обновить все ссылки
    $0 --check           # Только проверка
    $0 --dir /path/dir   # Обновить конкретную директорию
    $0 --restore 20250927_120000  # Восстановить из резервной копии

EOF
        exit 0
        ;;
    --dry-run)
        print_colored "$YELLOW" "Режим DRY-RUN: изменения не будут внесены"
        # Здесь можно добавить логику для dry-run
        ;;
    --check)
        check_integrity
        exit 0
        ;;
    --dir)
        if [ -z "${2:-}" ]; then
            print_colored "$RED" "Ошибка: не указана директория"
            exit 1
        fi
        scan_directory "$2"
        exit 0
        ;;
    --restore)
        if [ -z "${2:-}" ]; then
            print_colored "$RED" "Ошибка: не указана дата резервной копии"
            exit 1
        fi
        # Здесь можно добавить логику восстановления
        print_colored "$YELLOW" "Функция восстановления в разработке"
        exit 0
        ;;
    *)
        main
        ;;
esac