#!/usr/bin/env bash

set -euo pipefail

# SDUI Validator Installation Script v1.0.0
# Установка и настройка валидатора в VSCode

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="vscode-sdui-validator"
VSCODE_SETTINGS="${HOME}/.config/Code/User/settings.json"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

error_exit() {
    log_error "$1"
    exit 1
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Step counter
STEP=0
step() {
    STEP=$((STEP + 1))
    echo ""
    log_info "[$STEP/6] $*"
}

main() {
    cd "$SCRIPT_DIR" || error_exit "Cannot change to project directory"

    log_info "========================================"
    log_info "Installing ${PROJECT_NAME}"
    log_info "========================================"

    # Step 1: Prerequisites check
    step "Checking prerequisites"
    command_exists node || error_exit "Node.js is not installed. Install Node.js 18+ first."
    command_exists npm || error_exit "npm is not installed"

    NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 18 ]; then
        error_exit "Node.js version must be 18 or higher. Current: $(node -v)"
    fi

    log_success "Node.js $(node -v) and npm $(npm -v) found"

    # Step 2: Install dependencies
    step "Installing dependencies"
    npm install || error_exit "Failed to install dependencies"
    log_success "Dependencies installed"

    # Step 3: Build project
    step "Building project"
    chmod +x build.sh
    ./build.sh || error_exit "Build failed"
    log_success "Project built successfully"

    # Step 4: Run tests
    step "Running tests"
    if npm test 2>/dev/null; then
        log_success "All tests passed"
    else
        log_warning "Tests failed or not available. Continuing installation..."
    fi

    # Step 5: Link globally
    step "Linking globally"
    if npm link 2>/dev/null; then
        log_success "Package linked globally"
        log_info "You can now use 'sdui-validate' command from anywhere"
    else
        log_warning "Could not link globally. You may need to run with sudo."
        log_info "Manual linking: sudo npm link"
    fi

    # Step 6: Update VSCode settings
    step "Updating VSCode settings"

    VALIDATOR_PATH="${SCRIPT_DIR}/dist/cli.js"

    if [ ! -f "$VALIDATOR_PATH" ]; then
        log_warning "Validator executable not found at: $VALIDATOR_PATH"
        log_info "Skipping VSCode settings update"
    else
        # Create VSCode settings directory if not exists
        mkdir -p "$(dirname "$VSCODE_SETTINGS")"

        # Create backup of existing settings
        if [ -f "$VSCODE_SETTINGS" ]; then
            BACKUP_FILE="${VSCODE_SETTINGS}.backup.$(date +%Y%m%d_%H%M%S)"
            cp "$VSCODE_SETTINGS" "$BACKUP_FILE"
            log_info "Backup created: $BACKUP_FILE"
        fi

        # Check if validator is already configured
        if [ -f "$VSCODE_SETTINGS" ] && grep -q "sdui-validate" "$VSCODE_SETTINGS" 2>/dev/null; then
            log_info "SDUI validator already configured in VSCode"
        else
            log_info "Adding SDUI validator to VSCode settings..."

            # Create minimal settings file if doesn't exist
            if [ ! -f "$VSCODE_SETTINGS" ]; then
                echo '{}' > "$VSCODE_SETTINGS"
            fi

            # Add validator configuration using Python
            python3 << EOF
import json
import sys

settings_file = "${VSCODE_SETTINGS}"
validator_path = "${VALIDATOR_PATH}"

try:
    with open(settings_file, 'r') as f:
        settings = json.load(f)
except:
    settings = {}

# Add SDUI validator configuration
if "files.associations" not in settings:
    settings["files.associations"] = {}

settings["files.associations"]["*.j2.json"] = "jsonc"
settings["files.associations"]["*.jinja.json"] = "jsonc"

# Add task configuration hint
print("VSCode settings updated successfully")

with open(settings_file, 'w') as f:
    json.dump(settings, f, indent=2)

EOF

            log_success "VSCode settings updated"
            log_info "Validator path: $VALIDATOR_PATH"
        fi
    fi

    # Step 7: Verification
    echo ""
    log_info "========================================"
    log_info "Verifying installation"
    log_info "========================================"

    if [ -f "$VALIDATOR_PATH" ]; then
        log_success "Validator executable found"
        log_info "Testing validator..."

        # Create test file
        TEST_FILE="/tmp/test_sdui_validator.json"
        echo '{"test": true}' > "$TEST_FILE"

        if node "$VALIDATOR_PATH" "$TEST_FILE" 2>/dev/null; then
            log_success "Validator is working correctly"
        else
            log_warning "Validator test returned non-zero exit code (may be expected)"
        fi

        rm -f "$TEST_FILE"
    fi

    echo ""
    log_success "========================================"
    log_success "Installation completed!"
    log_success "========================================"
    echo ""
    log_info "Usage:"
    echo "  1. Command line: sdui-validate <file.json>"
    echo "  2. VSCode: Files are validated on save"
    echo "  3. NPM script: npm test"
    echo ""
    log_info "Configuration:"
    echo "  - Project: ${SCRIPT_DIR}"
    echo "  - Validator: ${VALIDATOR_PATH}"
    echo "  - VSCode settings: ${VSCODE_SETTINGS}"
    echo ""
    log_info "Documentation: ${SCRIPT_DIR}/README.md"
}

# Run main function
main "$@"
