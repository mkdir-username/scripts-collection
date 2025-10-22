#!/bin/bash
# Скрипт управления символическими ссылками для валидаторов SDUI
# Version: 1.0.0
# Created: 2025-01-27
# Description: Manages symbolic links for SDUI validators migration

set -e

# Определяем базовые пути
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="/Users/username/Documents/FMS_GIT"
VALIDATORS_DIR="/Users/username/Scripts/validators"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

function print_header() {
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

function create_links() {
    print_header "Создание символических ссылок для миграции"

    cd "$PROJECT_ROOT" || exit 1

    # Сохраняем оригиналы, если они не символические ссылки
    for file in sdui_web_validator.py sdui_web_validator_new.py sdui_web_validator_improved.py sdui_web_validator_with_lines.py; do
        if [ -f "$file" ] && [ ! -L "$file" ]; then
            echo -e "${YELLOW}Сохраняем оригинал: $file -> ${file}.backup${NC}"
            cp "$file" "${file}.backup"
        fi
    done

    # Удаляем старые файлы/ссылки
    rm -f sdui_web_validator.py
    rm -f sdui_web_validator_new.py
    rm -f sdui_web_validator_improved.py
    rm -f sdui_web_validator_with_lines.py

    # Определяем путь к целевому валидатору
    TARGET_VALIDATOR=""
    if [ -f "$VALIDATORS_DIR/v2.0.0/sdui_web_validator_v2.0.0_advanced_lines.py" ]; then
        TARGET_VALIDATOR="$VALIDATORS_DIR/v2.0.0/sdui_web_validator_v2.0.0_advanced_lines.py"
    elif [ -f "$PROJECT_ROOT/sdui_web_validator_v2.0.0_advanced_lines.py" ]; then
        TARGET_VALIDATOR="$PROJECT_ROOT/sdui_web_validator_v2.0.0_advanced_lines.py"
    else
        echo -e "${RED}❌ Валидатор v2.0.0 не найден!${NC}"
        exit 1
    fi

    # Создаем символические ссылки
    ln -s "$TARGET_VALIDATOR" sdui_web_validator.py
    ln -s "$TARGET_VALIDATOR" sdui_web_validator_new.py
    ln -s "$TARGET_VALIDATOR" sdui_web_validator_improved.py
    ln -s "$TARGET_VALIDATOR" sdui_web_validator_with_lines.py

    echo -e "${GREEN}✅ Символические ссылки созданы${NC}"
    echo "Все старые имена теперь указывают на v2.0.0"
}

function restore_copies() {
    print_header "Восстановление копий файлов"

    cd "$PROJECT_ROOT" || exit 1

    # Удаляем символические ссылки
    rm -f sdui_web_validator.py
    rm -f sdui_web_validator_new.py
    rm -f sdui_web_validator_improved.py
    rm -f sdui_web_validator_with_lines.py

    # Восстанавливаем из архива или резервных копий
    if [ -d "validators/archive" ]; then
        [ -f "validators/archive/sdui_web_validator_v1.0.0.py" ] && \
            cp "validators/archive/sdui_web_validator_v1.0.0.py" sdui_web_validator.py
        [ -f "validators/archive/sdui_web_validator_v1.1.0.py" ] && \
            cp "validators/archive/sdui_web_validator_v1.1.0.py" sdui_web_validator_new.py
        [ -f "validators/archive/sdui_web_validator_improved.py" ] && \
            cp "validators/archive/sdui_web_validator_improved.py" sdui_web_validator_improved.py
        [ -f "validators/archive/sdui_web_validator_v1.2.0_with_lines.py" ] && \
            cp "validators/archive/sdui_web_validator_v1.2.0_with_lines.py" sdui_web_validator_with_lines.py
    else
        # Восстанавливаем из backup файлов
        for file in sdui_web_validator.py sdui_web_validator_new.py sdui_web_validator_improved.py sdui_web_validator_with_lines.py; do
            if [ -f "${file}.backup" ]; then
                cp "${file}.backup" "$file"
                echo -e "${GREEN}✅ Восстановлен $file из backup${NC}"
            fi
        done
    fi

    echo -e "${GREEN}✅ Копии файлов восстановлены${NC}"
    echo "Каждый файл теперь является независимой копией своей версии"
}

function status() {
    print_header "Текущий статус файлов валидаторов"

    # Проверяем в проекте
    echo -e "\n${YELLOW}В директории проекта:${NC}"
    cd "$PROJECT_ROOT" 2>/dev/null || echo -e "${RED}Проект не найден${NC}"

    for file in sdui_web_validator.py sdui_web_validator_new.py sdui_web_validator_improved.py sdui_web_validator_with_lines.py sdui_web_validator_v2.0.0_advanced_lines.py; do
        if [ -L "$file" ]; then
            target=$(readlink "$file")
            echo -e "${YELLOW}🔗 $file -> $target (символическая ссылка)${NC}"
        elif [ -f "$file" ]; then
            echo -e "${GREEN}📄 $file (обычный файл)${NC}"
        else
            echo -e "${RED}❌ $file (не существует)${NC}"
        fi
    done

    # Проверяем в Scripts/validators
    if [ -d "$VALIDATORS_DIR" ]; then
        echo -e "\n${YELLOW}В директории валидаторов:${NC}"
        find "$VALIDATORS_DIR" -name "*.py" -type f | sort | while read -r file; do
            echo -e "${GREEN}📄 $(basename "$file")${NC}"
        done
    fi
}

function show_help() {
    echo "Использование: $0 [команда]"
    echo ""
    echo "Команды:"
    echo "  links    - Создать символические ссылки на v2.0.0"
    echo "  copies   - Восстановить независимые копии файлов"
    echo "  status   - Показать текущий статус файлов"
    echo "  help     - Показать эту справку"
    echo ""
    echo "По умолчанию показывается статус"
}

# Основная логика
case "${1:-status}" in
    links)
        create_links
        ;;
    copies)
        restore_copies
        ;;
    status)
        status
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}Неизвестная команда: $1${NC}"
        show_help
        exit 1
        ;;
esac