#!/bin/bash
##############################################################################
# VSCode Validator v2.3.1 - Installation Script
#
# Устанавливает и настраивает валидатор для использования с VSCode
#
# Usage:
#   bash install_v2.3.1.sh
#   bash install_v2.3.1.sh --skip-deps  # Пропустить установку зависимостей
#   bash install_v2.3.1.sh --compile-only  # Только компиляция
#
# Author: DevOps Engineer
# Date: 2025-10-07
# Version: 2.3.1
##############################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Конфигурация
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="${PROJECT_ROOT:-/Users/username/Documents/FMS_GIT}"
VALIDATOR_VERSION="2.3.1"
VALIDATOR_TS="${SCRIPT_DIR}/vscode-validate-on-save_v${VALIDATOR_VERSION}.ts"
VALIDATOR_JS="${SCRIPT_DIR}/vscode-validate-on-save_v${VALIDATOR_VERSION}.js"
VSCODE_SETTINGS="${PROJECT_ROOT}/.vscode/settings.json"

# Флаги
SKIP_DEPS=false
COMPILE_ONLY=false

# Парсинг аргументов
while [[ $# -gt 0 ]]; do
  case $1 in
    --skip-deps)
      SKIP_DEPS=true
      shift
      ;;
    --compile-only)
      COMPILE_ONLY=true
      shift
      ;;
    --help|-h)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "OPTIONS:"
      echo "  --skip-deps      Skip npm dependencies installation"
      echo "  --compile-only   Only compile TypeScript, skip other steps"
      echo "  --help, -h       Show this help message"
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      exit 1
      ;;
  esac
done

##############################################################################
# Функции
##############################################################################

print_header() {
  echo ""
  echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${CYAN}  $1${NC}"
  echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo ""
}

print_step() {
  echo -e "${BLUE}▶${NC} $1"
}

print_success() {
  echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
  echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
  echo -e "${RED}✗${NC} $1"
}

check_prerequisites() {
  print_step "Checking prerequisites..."

  # Check Node.js
  if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed"
    echo "Please install Node.js 14+ from https://nodejs.org/"
    exit 1
  fi

  local node_version=$(node --version | sed 's/v//')
  local major_version=$(echo "$node_version" | cut -d. -f1)

  if [ "$major_version" -lt 14 ]; then
    print_error "Node.js version $node_version is too old"
    echo "Required: Node.js 14+, found: $node_version"
    exit 1
  fi

  print_success "Node.js $node_version"

  # Check npm
  if ! command -v npm &> /dev/null; then
    print_error "npm is not installed"
    exit 1
  fi

  local npm_version=$(npm --version)
  print_success "npm $npm_version"

  # Check TypeScript
  if ! command -v tsc &> /dev/null; then
    print_warning "TypeScript compiler not found globally"
    print_step "Will use local TypeScript from node_modules"
  else
    local tsc_version=$(tsc --version | awk '{print $2}')
    print_success "TypeScript $tsc_version"
  fi

  echo ""
}

install_dependencies() {
  if [ "$SKIP_DEPS" = true ]; then
    print_warning "Skipping dependencies installation (--skip-deps)"
    return
  fi

  print_step "Installing npm dependencies..."

  cd "$SCRIPT_DIR"

  # Проверяем наличие package.json
  if [ ! -f "package.json" ]; then
    print_error "package.json not found in $SCRIPT_DIR"
    exit 1
  fi

  # Устанавливаем зависимости
  if npm install --silent; then
    print_success "Dependencies installed"
  else
    print_error "Failed to install dependencies"
    exit 1
  fi

  echo ""
}

compile_typescript() {
  print_step "Compiling TypeScript..."

  cd "$SCRIPT_DIR"

  # Проверяем наличие исходного файла
  if [ ! -f "$VALIDATOR_TS" ]; then
    print_error "Source file not found: $VALIDATOR_TS"
    exit 1
  fi

  # Компиляция через локальный tsc
  if [ -f "node_modules/.bin/tsc" ]; then
    if ./node_modules/.bin/tsc --project tsconfig.json; then
      print_success "TypeScript compiled successfully"
    else
      print_error "TypeScript compilation failed"
      exit 1
    fi
  else
    print_error "TypeScript compiler not found in node_modules"
    print_step "Run: npm install"
    exit 1
  fi

  # Проверяем создание JS файла
  if [ -f "$VALIDATOR_JS" ]; then
    print_success "Generated: $(basename "$VALIDATOR_JS")"

    # Делаем файл исполняемым
    chmod +x "$VALIDATOR_JS"
    print_success "Made executable"
  else
    print_error "Compiled JS file not found: $VALIDATOR_JS"
    exit 1
  fi

  echo ""
}

update_vscode_settings() {
  if [ "$COMPILE_ONLY" = true ]; then
    print_warning "Skipping VSCode settings update (--compile-only)"
    return
  fi

  print_step "Updating VSCode settings..."

  # Проверяем наличие .vscode директории
  if [ ! -d "$(dirname "$VSCODE_SETTINGS")" ]; then
    print_step "Creating .vscode directory..."
    mkdir -p "$(dirname "$VSCODE_SETTINGS")"
  fi

  # Создаем резервную копию существующих настроек
  if [ -f "$VSCODE_SETTINGS" ]; then
    local backup_file="${VSCODE_SETTINGS}.backup_$(date +%Y%m%d_%H%M%S)"
    cp "$VSCODE_SETTINGS" "$backup_file"
    print_success "Backup created: $(basename "$backup_file")"
  fi

  # Обновляем настройки
  # Используем Python для обновления JSON (если доступен)
  if command -v python3 &> /dev/null; then
    python3 << EOF
import json
import os

settings_file = "$VSCODE_SETTINGS"
validator_js = "$VALIDATOR_JS"

# Читаем существующие настройки или создаем новые
if os.path.exists(settings_file):
    with open(settings_file, 'r') as f:
        settings = json.load(f)
else:
    settings = {}

# Обновляем настройки валидатора
if "runOnSave.commands" not in settings:
    settings["runOnSave.commands"] = []

# Удаляем старые версии валидатора
settings["runOnSave.commands"] = [
    cmd for cmd in settings["runOnSave.commands"]
    if "vscode-validate-on-save" not in cmd.get("command", "")
]

# Добавляем новую версию
settings["runOnSave.commands"].append({
    "match": "\\.(json|j2\\.java|jinja\\.json)$",
    "command": f"node {validator_js} \${file}",
    "runIn": "terminal"
})

# Сохраняем
with open(settings_file, 'w') as f:
    json.dump(settings, f, indent=2)

print("VSCode settings updated successfully")
EOF

    if [ $? -eq 0 ]; then
      print_success "VSCode settings updated"
    else
      print_error "Failed to update VSCode settings"
      exit 1
    fi
  else
    print_warning "Python3 not found, skipping automatic settings update"
    print_step "Please manually add to $VSCODE_SETTINGS:"
    echo ""
    echo '  "runOnSave.commands": ['
    echo '    {'
    echo '      "match": "\\.(json|j2\\.java|jinja\\.json)$",'
    echo "      \"command\": \"node $VALIDATOR_JS \${file}\","
    echo '      "runIn": "terminal"'
    echo '    }'
    echo '  ]'
  fi

  echo ""
}

verify_installation() {
  if [ "$COMPILE_ONLY" = true ]; then
    return
  fi

  print_step "Verifying installation..."

  # Проверка 1: JS файл существует и исполняем
  if [ -x "$VALIDATOR_JS" ]; then
    print_success "Validator executable: $(basename "$VALIDATOR_JS")"
  else
    print_error "Validator not executable"
    exit 1
  fi

  # Проверка 2: Запуск с --version
  local version_output=$(node "$VALIDATOR_JS" --version 2>&1 || true)
  if echo "$version_output" | grep -q "$VALIDATOR_VERSION"; then
    print_success "Version check passed: $VALIDATOR_VERSION"
  else
    print_warning "Version check failed, but file exists"
  fi

  # Проверка 3: VSCode settings
  if [ -f "$VSCODE_SETTINGS" ]; then
    if grep -q "vscode-validate-on-save_v${VALIDATOR_VERSION}" "$VSCODE_SETTINGS"; then
      print_success "VSCode settings configured"
    else
      print_warning "VSCode settings may need manual update"
    fi
  fi

  echo ""
}

print_summary() {
  print_header "Installation Complete"

  echo -e "${GREEN}✓${NC} Validator v${VALIDATOR_VERSION} installed successfully"
  echo ""
  echo -e "${CYAN}USAGE:${NC}"
  echo "  # Validate a file"
  echo "  node $VALIDATOR_JS path/to/file.json"
  echo ""
  echo "  # Validate with verbose output"
  echo "  node $VALIDATOR_JS --verbose path/to/file.json"
  echo ""
  echo "  # Validate Jinja2 template"
  echo "  node $VALIDATOR_JS path/to/template.j2.java"
  echo ""
  echo "  # Show help"
  echo "  node $VALIDATOR_JS --help"
  echo ""
  echo -e "${CYAN}NPM SCRIPTS:${NC}"
  echo "  npm run build          # Compile TypeScript"
  echo "  npm run build:watch    # Watch mode compilation"
  echo "  npm run validate       # Run validator"
  echo ""
  echo -e "${CYAN}FILES:${NC}"
  echo "  Source:   $(basename "$VALIDATOR_TS")"
  echo "  Compiled: $(basename "$VALIDATOR_JS")"
  echo "  Config:   tsconfig.json"
  echo "  Package:  package.json"
  echo ""

  if [ "$COMPILE_ONLY" = false ]; then
    echo -e "${CYAN}VSCODE INTEGRATION:${NC}"
    echo "  Validator will run automatically on save for:"
    echo "  - .json files"
    echo "  - .j2.java files"
    echo "  - .jinja.json files"
    echo ""
  fi

  echo -e "${YELLOW}NOTE:${NC}"
  echo "  Restart VSCode to apply settings changes"
  echo ""
}

##############################################################################
# Основной процесс установки
##############################################################################

main() {
  print_header "VSCode Validator v${VALIDATOR_VERSION} - Installation"

  echo "Installation directory: $SCRIPT_DIR"
  echo "Project root: $PROJECT_ROOT"
  echo ""

  check_prerequisites

  if [ "$COMPILE_ONLY" = false ]; then
    install_dependencies
  fi

  compile_typescript

  if [ "$COMPILE_ONLY" = false ]; then
    update_vscode_settings
    verify_installation
  fi

  print_summary
}

# Запуск
main
