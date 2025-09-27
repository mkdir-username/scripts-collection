#!/bin/bash
# Скрипт для проверки всех SDUI samples на совместимость с веб-платформой
# Version: 1.0.0
# Created: 2025-01-27
# Description: Validates all SDUI sample files for web platform compatibility

# Определяем базовые пути
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="/Users/username/Documents/front-middle-schema"

# Цветные выводы
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}🔍 SDUI Web Compatibility Sample Validator${NC}"
echo -e "${BLUE}==========================================${NC}"

# Переходим в директорию проекта
cd "$PROJECT_ROOT" || exit 1

# Подсчитываем общее количество файлов
TOTAL=$(find SDUI -type f -path "*/samples/*.json" 2>/dev/null | wc -l | tr -d ' ')
echo -e "Found ${YELLOW}$TOTAL${NC} sample files to check\n"

# Счетчики
CHECKED=0
ERRORS=0
WARNINGS=0
FAILED_FILES=()

# Временный файл для сохранения ошибок
ERROR_LOG="/tmp/sdui_samples_errors_$(date +%Y%m%d_%H%M%S).log"
> "$ERROR_LOG"

echo -e "${BLUE}Checking samples...${NC}"
echo -e "──────────────────────────────────────────\n"

# Определяем путь к валидатору
VALIDATOR_PATH=""
if [ -f "$PROJECT_ROOT/tools/python/v1.0.0/sdui_web_validator_new_v1.0.0.py" ]; then
    VALIDATOR_PATH="$PROJECT_ROOT/tools/python/v1.0.0/sdui_web_validator_new_v1.0.0.py"
elif [ -f "$PROJECT_ROOT/sdui_web_validator_new.py" ]; then
    VALIDATOR_PATH="$PROJECT_ROOT/sdui_web_validator_new.py"
else
    echo -e "${RED}❌ Error: Web validator not found!${NC}"
    echo "Please ensure the validator is available at:"
    echo "  - $PROJECT_ROOT/tools/python/v1.0.0/sdui_web_validator_new_v1.0.0.py"
    echo "  - or $PROJECT_ROOT/sdui_web_validator_new.py"
    exit 1
fi

# Проверяем каждый файл
while IFS= read -r file; do
    CHECKED=$((CHECKED + 1))

    # Прогресс
    if [ $((CHECKED % 50)) -eq 0 ] || [ $CHECKED -eq $TOTAL ]; then
        echo -ne "\r${BLUE}Progress:${NC} $CHECKED/$TOTAL files checked"
    fi

    # Запускаем валидацию, перенаправляя вывод во временный файл
    OUTPUT=$(python3 "$VALIDATOR_PATH" "$file" 2>&1)
    EXIT_CODE=$?

    # Проверяем результат
    if echo "$OUTPUT" | grep -q "❌ Contract has compatibility issues"; then
        ERRORS=$((ERRORS + 1))
        FAILED_FILES+=("$file")

        # Извлекаем информацию об ошибках
        echo -e "\n\n${RED}❌ $file${NC}" >> "$ERROR_LOG"
        echo "$OUTPUT" | grep -E "❌ Component|❌ Field" >> "$ERROR_LOG"
    elif echo "$OUTPUT" | grep -q "⚠️"; then
        WARNINGS=$((WARNINGS + 1))
    fi
done < <(find SDUI -type f -path "*/samples/*.json" 2>/dev/null)

echo -e "\n\n${BLUE}──────────────────────────────────────────${NC}"
echo -e "${BLUE}📊 Summary Report${NC}"
echo -e "${BLUE}──────────────────────────────────────────${NC}\n"

echo -e "Total files checked: ${YELLOW}$CHECKED${NC}"
echo -e "Files with errors:   ${RED}$ERRORS${NC}"
echo -e "Files with warnings: ${YELLOW}$WARNINGS${NC}"
echo -e "Files passed:        ${GREEN}$((CHECKED - ERRORS - WARNINGS))${NC}"

if [ ${#FAILED_FILES[@]} -gt 0 ]; then
    echo -e "\n${RED}🚫 Files with Web Platform Incompatibilities:${NC}"
    echo -e "──────────────────────────────────────────"

    # Группируем по компонентам
    declare -A COMPONENT_FILES

    for file in "${FAILED_FILES[@]}"; do
        # Извлекаем имя компонента из пути
        component=$(echo "$file" | sed -E 's/.*\/([^\/]+)\/v[0-9]+\/samples\/.*/\1/')

        if [ -z "${COMPONENT_FILES[$component]}" ]; then
            COMPONENT_FILES[$component]="$file"
        else
            COMPONENT_FILES[$component]="${COMPONENT_FILES[$component]}|$file"
        fi
    done

    # Выводим сгруппированный список
    for component in "${!COMPONENT_FILES[@]}"; do
        echo -e "\n${YELLOW}$component:${NC}"
        IFS='|' read -ra FILES <<< "${COMPONENT_FILES[$component]}"
        count=0
        for file in "${FILES[@]}"; do
            count=$((count + 1))
            if [ $count -le 3 ]; then
                echo "  • $(basename "$file")"
            fi
        done
        if [ ${#FILES[@]} -gt 3 ]; then
            echo "  ... and $((${#FILES[@]} - 3)) more files"
        fi
    done

    echo -e "\n${YELLOW}Full error log saved to:${NC} $ERROR_LOG"
fi

echo -e "\n${BLUE}──────────────────────────────────────────${NC}"

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ All samples are compatible with web platform!${NC}"
    exit 0
else
    echo -e "${RED}❌ Found $ERRORS files with web platform incompatibilities${NC}"
    echo -e "${YELLOW}💡 Tip:${NC} Check components with 'releaseVersion.web: notReleased'"
    exit 1
fi