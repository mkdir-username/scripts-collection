#!/bin/bash
# Скрипт для валидации SDUI контрактов при сохранении в VSCode
# Version: 1.0.0
# Created: 2025-01-27
# Description: Validates SDUI contracts on save in VSCode

# Определяем базовые пути
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="/Users/username/Documents/front-middle-schema"

FILE="$1"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Validating: $(basename "$FILE")"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. Проверка синтаксиса JSON
echo -e "\n${YELLOW}Step 1: JSON Syntax Check${NC}"
if python3 -m json.tool "$FILE" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ JSON syntax is valid${NC}"
else
    echo -e "${RED}✗ JSON syntax error!${NC}"
    python3 -m json.tool "$FILE"
    exit 1
fi

# 2. Проверка схемы через AJV (если файл в SDUI/)
if [[ "$FILE" == *"/SDUI/"* ]]; then
    echo -e "\n${YELLOW}Step 2: Schema Validation (AJV)${NC}"

    # Переходим в директорию проекта для AJV
    pushd "$PROJECT_ROOT" > /dev/null

    if command -v npx &> /dev/null && [ -f "node_modules/ajv-cli/ajv" ]; then
        if npx ajv validate -s metaschema/schema/strict_unversioned.json -d "$FILE" --errors=text 2>/dev/null; then
            echo -e "${GREEN}✓ Schema validation passed${NC}"
        else
            echo -e "${RED}✗ Schema validation failed!${NC}"
            npx ajv validate -s metaschema/schema/strict_unversioned.json -d "$FILE" --errors=text
        fi
    else
        echo "⚠️  AJV not installed, skipping schema validation"
    fi

    popd > /dev/null
fi

# 3. Проверка releaseVersion.web для контрактов
BASE_NAME=$(basename "$FILE")
IS_CONTRACT=false

# Проверяем по пути
if [[ "$FILE" == *".JSON/"* ]] || [[ "$FILE" == *"/samples/"* ]] || [[ "$FILE" == *"/examples/"* ]]; then
    IS_CONTRACT=true
fi

# Проверяем по имени файла
if [[ "$BASE_NAME" == *"[FULL_NN]"* ]] || [[ "$BASE_NAME" == *"_main-screen"* ]] || [[ "$BASE_NAME" == *"_contract"* ]]; then
    IS_CONTRACT=true
fi

# Исключаем известные схемы
if [[ "$FILE" == *"/v1/"*".json" ]] || [[ "$FILE" == *"/v2/"*".json" ]] || [[ "$FILE" == *"/v3/"*".json" ]]; then
    if [[ "$FILE" != *"/samples/"* ]] && [[ "$FILE" != *"/examples/"* ]]; then
        IS_CONTRACT=false
    fi
fi

if [ "$IS_CONTRACT" = true ]; then
    echo -e "\n${YELLOW}Step 3: Web Platform Compatibility Check${NC}"

    # Определяем путь к валидатору
    VALIDATOR_PATH=""

    # Проверяем в версионированной директории
    if [ -f "$PROJECT_ROOT/tools/python/v1.0.0/sdui_web_validator_new_v1.0.0.py" ]; then
        VALIDATOR_PATH="$PROJECT_ROOT/tools/python/v1.0.0/sdui_web_validator_new_v1.0.0.py"
    elif [ -f "$PROJECT_ROOT/sdui_web_validator_new.py" ]; then
        # Резервный путь для обратной совместимости
        VALIDATOR_PATH="$PROJECT_ROOT/sdui_web_validator_new.py"
    fi

    # Проверяем существование валидатора
    if [ -z "$VALIDATOR_PATH" ] || [ ! -f "$VALIDATOR_PATH" ]; then
        echo -e "${RED}❌ Error: Validator not found${NC}"
        exit 1
    fi

    # Запускаем валидатор и сохраняем результат
    python3 "$VALIDATOR_PATH" "$FILE"
    VALIDATION_RESULT=$?

    # Проверяем результат валидации
    if [ $VALIDATION_RESULT -eq 0 ]; then
        echo -e "${GREEN}✓ All components are web-compatible${NC}"
    else
        echo -e "${RED}✗ Found web-incompatible components!${NC}"
        exit 1
    fi
else
    echo -e "\n${YELLOW}Step 3: Web Platform Compatibility Check${NC}"
    echo "ℹ️  Skipping - this is a schema file, not a contract"
fi

# 4. Проверка на notReleased в схемах
if [[ "$FILE" == *"/SDUI/"* ]]; then
    echo -e "\n${YELLOW}Step 4: Check for 'notReleased' fields${NC}"

    # Ищем контракт валидатор в правильном месте
    CONTRACT_VALIDATOR=""

    if [ -f "$PROJECT_ROOT/tools/python/v1.0.0/sdui_contract_validator_v1.0.0.py" ]; then
        CONTRACT_VALIDATOR="$PROJECT_ROOT/tools/python/v1.0.0/sdui_contract_validator_v1.0.0.py"
    elif [ -f "$PROJECT_ROOT/sdui_contract_validator.py" ]; then
        CONTRACT_VALIDATOR="$PROJECT_ROOT/sdui_contract_validator.py"
    fi

    if [ -n "$CONTRACT_VALIDATOR" ] && [ -f "$CONTRACT_VALIDATOR" ]; then
        if python3 "$CONTRACT_VALIDATOR" "$FILE" 2>/dev/null; then
            echo -e "${GREEN}✓ No 'notReleased' issues found${NC}"
        else
            echo -e "${YELLOW}⚠️  Found 'notReleased' fields${NC}"
        fi
    else
        echo "⚠️  Contract validator not found, skipping check"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ Validation complete!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"