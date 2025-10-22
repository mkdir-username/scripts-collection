#!/bin/bash
# Скрипт-обертка для валидатора SDUI с очисткой вывода
# Version: 1.0.0
# Created: 2025-01-27
# Description: Wrapper for SDUI validator with terminal clearing

# Определяем базовые пути
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="/Users/username/Documents/FMS_GIT"

# Очищаем терминал перед новым запуском
clear

# Добавляем цветной заголовок
echo -e "\033[1;36m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m"
echo -e "\033[1;36m🔍 Validating: $(basename "$1")\033[0m"
echo -e "\033[1;36m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m"

# Запускаем основные проверки
echo -e "\n\033[1;33mStep 1: JSON Syntax Check\033[0m"
if python3 -m json.tool "$1" > /dev/null 2>&1; then
    echo -e "\033[0;32m✓ JSON syntax is valid\033[0m"

    echo -e "\n\033[1;33mStep 3: Web Platform Compatibility Check\033[0m"

    # Используем обновленный путь к Python валидатору
    VALIDATOR_PATH="/Users/username/Scripts/validators/v2.0.0/sdui_web_validator_v2.0.0_advanced_lines.py"
    if [ -f "$VALIDATOR_PATH" ]; then
        python3 "$VALIDATOR_PATH" "$1"
    elif [ -f "$PROJECT_ROOT/sdui_web_validator_v2.0.0_advanced_lines.py" ]; then
        # Резервный путь для обратной совместимости
        python3 "$PROJECT_ROOT/sdui_web_validator_v2.0.0_advanced_lines.py" "$1"
    else
        echo -e "\033[0;31m✗ Validator script not found!\033[0m"
        exit 1
    fi

    # Добавляем финальную проверку
    if [ $? -eq 0 ]; then
        echo -e "\n\033[0;32m✓ All checks passed successfully!\033[0m"
    else
        echo -e "\n\033[0;31m✗ Found web-incompatible components!\033[0m"
    fi
else
    echo -e "\033[0;31m✗ JSON syntax is invalid!\033[0m"
    python3 -m json.tool "$1" 2>&1 | head -20
    exit 1
fi