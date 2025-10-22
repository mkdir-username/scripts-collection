#!/bin/bash

# Скрипт для быстрого тестирования CLI v2.3.1

set -e

echo "======================================"
echo "Testing vscode-validator v2.3.1 CLI"
echo "======================================"
echo ""

# Цвета
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверка наличия dist/cli.js
if [ ! -f "dist/cli.js" ]; then
  echo -e "${RED}Error: dist/cli.js not found${NC}"
  echo "Please run: npm run build"
  exit 1
fi

# Тест 1: Вывод версии
echo -e "${YELLOW}Test 1: Version${NC}"
node dist/cli.js --version
echo ""

# Тест 2: Вывод помощи
echo -e "${YELLOW}Test 2: Help${NC}"
node dist/cli.js --help
echo ""

# Тест 3: Валидация валидного файла
echo -e "${YELLOW}Test 3: Valid JSON${NC}"
if [ -f "examples/test-valid.json" ]; then
  node dist/cli.js examples/test-valid.json --verbose
else
  echo -e "${YELLOW}Skipped: examples/test-valid.json not found${NC}"
fi
echo ""

# Тест 4: Валидация невалидного файла
echo -e "${YELLOW}Test 4: Invalid JSON${NC}"
if [ -f "examples/test-invalid.json" ]; then
  node dist/cli.js examples/test-invalid.json --verbose || echo -e "${GREEN}Expected failure${NC}"
else
  echo -e "${YELLOW}Skipped: examples/test-invalid.json not found${NC}"
fi
echo ""

# Тест 5: Валидация Jinja файла
echo -e "${YELLOW}Test 5: Jinja JSON${NC}"
if [ -f "examples/test-jinja.jinja.json" ]; then
  node dist/cli.js examples/test-jinja.jinja.json --verbose --jinja-aware
else
  echo -e "${YELLOW}Skipped: examples/test-jinja.jinja.json not found${NC}"
fi
echo ""

# Тест 6: JSON вывод
echo -e "${YELLOW}Test 6: JSON Output${NC}"
if [ -f "examples/test-valid.json" ]; then
  node dist/cli.js examples/test-valid.json --output json
else
  echo -e "${YELLOW}Skipped: examples/test-valid.json not found${NC}"
fi
echo ""

echo -e "${GREEN}======================================"
echo "All tests completed!"
echo "======================================${NC}"
