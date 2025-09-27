#!/bin/bash
# Главный управляющий скрипт для SDUI валидаторов
# Version: 1.0.0
# Created: 2025-01-27

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION="v1.0.0"

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

show_help() {
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}   SDUI Validator Management Tool ${VERSION}    ${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Использование: $(basename $0) [команда] [аргументы]"
    echo ""
    echo "Команды валидации:"
    echo "  validate <file>     - Валидировать один файл"
    echo "  validate-all        - Валидировать все samples"
    echo "  clear <file>        - Валидация с очисткой экрана"
    echo ""
    echo "Команды управления:"
    echo "  links [cmd]         - Управление символическими ссылками"
    echo "  organize            - Организация bash скриптов"
    echo "  list                - Показать все доступные скрипты"
    echo "  status              - Статус системы валидации"
    echo "  help                - Показать эту справку"
    echo ""
    echo "Примеры:"
    echo "  $(basename $0) validate ./contract.json"
    echo "  $(basename $0) validate-all"
    echo "  $(basename $0) links status"
    echo "  $(basename $0) status"
}

list_scripts() {
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}Доступные скрипты валидации:${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}Основные валидаторы:${NC}"
    for script in "$SCRIPT_DIR/v1.0.0"/*validate*.sh; do
        if [ -f "$script" ]; then
            echo -e "  ${GREEN}• $(basename $script)${NC}"
        fi
    done
    echo ""
    echo -e "${YELLOW}Утилиты управления:${NC}"
    for script in "$SCRIPT_DIR/v1.0.0"/*manage*.sh "$SCRIPT_DIR/v1.0.0"/*organize*.sh; do
        if [ -f "$script" ]; then
            echo -e "  ${GREEN}• $(basename $script)${NC}"
        fi
    done
}

show_status() {
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}Статус системы SDUI валидации${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    # Проверяем наличие скриптов
    echo -e "${YELLOW}Bash скрипты:${NC}"
    local script_count=$(ls -1 "$SCRIPT_DIR/v1.0.0"/*.sh 2>/dev/null | wc -l | tr -d ' ')
    if [ "$script_count" -gt 0 ]; then
        echo -e "  ${GREEN}✓ Найдено скриптов: $script_count${NC}"
    else
        echo -e "  ${RED}✗ Скрипты не найдены${NC}"
    fi

    # Проверяем Python валидаторы
    echo -e "\n${YELLOW}Python валидаторы:${NC}"
    VALIDATORS_DIR="/Users/username/Scripts/validators"
    if [ -d "$VALIDATORS_DIR" ]; then
        local py_count=$(find "$VALIDATORS_DIR" -name "*.py" -type f | wc -l | tr -d ' ')
        echo -e "  ${GREEN}✓ Найдено валидаторов: $py_count${NC}"
    else
        echo -e "  ${YELLOW}⚠ Директория валидаторов не найдена${NC}"
    fi

    # Проверяем символические ссылки
    echo -e "\n${YELLOW}Обратная совместимость:${NC}"
    PROJECT_ROOT="/Users/username/Documents/front-middle-schema"
    if [ -L "$PROJECT_ROOT/validate_on_save.sh" ]; then
        echo -e "  ${GREEN}✓ Символические ссылки активны${NC}"
    else
        echo -e "  ${YELLOW}⚠ Символические ссылки не настроены${NC}"
    fi

    # Проверяем Python
    echo -e "\n${YELLOW}Зависимости:${NC}"
    if command -v python3 &> /dev/null; then
        local py_version=$(python3 --version | cut -d' ' -f2)
        echo -e "  ${GREEN}✓ Python: $py_version${NC}"
    else
        echo -e "  ${RED}✗ Python не найден${NC}"
    fi

    # Проверяем Node.js
    if command -v node &> /dev/null; then
        local node_version=$(node --version)
        echo -e "  ${GREEN}✓ Node.js: $node_version${NC}"
    else
        echo -e "  ${YELLOW}⚠ Node.js не установлен (опционально)${NC}"
    fi
}

# Обработка команд
COMMAND="${1:-help}"
shift || true

case "$COMMAND" in
    validate)
        if [ -z "$1" ]; then
            echo -e "${RED}Ошибка: не указан файл для валидации${NC}"
            echo "Использование: $(basename $0) validate <file>"
            exit 1
        fi
        exec "$SCRIPT_DIR/v1.0.0/validate_on_save_v1.0.0.sh" "$@"
        ;;
    validate-all)
        exec "$SCRIPT_DIR/v1.0.0/validate_all_samples_v1.0.0.sh" "$@"
        ;;
    clear)
        if [ -z "$1" ]; then
            echo -e "${RED}Ошибка: не указан файл для валидации${NC}"
            echo "Использование: $(basename $0) clear <file>"
            exit 1
        fi
        exec "$SCRIPT_DIR/v1.0.0/run_validator_with_clear_v1.0.0.sh" "$@"
        ;;
    links)
        exec "$SCRIPT_DIR/v1.0.0/manage_validator_links_v1.0.0.sh" "$@"
        ;;
    organize)
        exec "$SCRIPT_DIR/v1.0.0/organize_bash_scripts_v1.0.0.sh" "$@"
        ;;
    list)
        list_scripts
        ;;
    status)
        show_status
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}Неизвестная команда: $COMMAND${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac