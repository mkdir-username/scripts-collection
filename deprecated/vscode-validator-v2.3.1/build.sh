#!/usr/bin/env bash

set -euo pipefail

# SDUI Validator Build Script v1.0.0
# Компиляция TypeScript проекта с проверками качества

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="vscode-sdui-validator"
MAX_BUNDLE_SIZE_MB=5

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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

# Step counter
STEP=0
step() {
    STEP=$((STEP + 1))
    echo ""
    log_info "[$STEP/8] $*"
}

# Error handler
error_exit() {
    log_error "$1"
    exit 1
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Main build process
main() {
    cd "$SCRIPT_DIR" || error_exit "Cannot change to project directory"

    log_info "========================================"
    log_info "Building ${PROJECT_NAME} v$(node -p "require('./package.json').version")"
    log_info "========================================"

    # Step 1: Check prerequisites
    step "Checking prerequisites"
    command_exists node || error_exit "Node.js is not installed"
    command_exists npm || error_exit "npm is not installed"
    log_success "Node.js $(node --version) and npm $(npm --version) found"

    # Step 2: Install dependencies
    step "Installing dependencies"
    if [ ! -d "node_modules" ]; then
        log_info "Installing npm packages..."
        npm install || error_exit "Failed to install dependencies"
    else
        log_info "Dependencies already installed, skipping..."
    fi

    # Step 3: Run linter
    step "Running ESLint"
    log_info "Checking code quality..."
    npm run lint || {
        log_warning "Linting failed, attempting auto-fix..."
        npm run lint:fix || log_warning "Some linting errors could not be auto-fixed"
    }

    # Step 4: Run type checking
    step "Running TypeScript type checker"
    npm run typecheck || error_exit "Type checking failed"
    log_success "No type errors found"

    # Step 5: Clean previous build
    step "Cleaning previous build"
    if [ -d "dist" ]; then
        log_info "Removing old dist/ directory..."
        rm -rf dist
    fi
    log_success "Build directory cleaned"

    # Step 6: Compile TypeScript
    step "Compiling TypeScript"
    npm run compile || error_exit "TypeScript compilation failed"
    log_success "TypeScript compiled successfully"

    # Step 7: Make CLI executable
    step "Making CLI executable"
    if [ -f "dist/cli.js" ]; then
        chmod +x dist/cli.js
        # Add shebang if not present
        if ! head -n 1 dist/cli.js | grep -q "^#!"; then
            log_info "Adding shebang to CLI..."
            echo "#!/usr/bin/env node" | cat - dist/cli.js > dist/cli.js.tmp
            mv dist/cli.js.tmp dist/cli.js
            chmod +x dist/cli.js
        fi
        log_success "CLI is executable"
    else
        log_warning "CLI file not found, skipping..."
    fi

    # Step 8: Check bundle size
    step "Checking bundle size"
    if [ -d "dist" ]; then
        BUNDLE_SIZE_BYTES=$(du -sb dist | cut -f1)
        BUNDLE_SIZE_MB=$(echo "scale=2; $BUNDLE_SIZE_BYTES / 1048576" | bc)

        log_info "Bundle size: ${BUNDLE_SIZE_MB} MB"

        if (( $(echo "$BUNDLE_SIZE_MB > $MAX_BUNDLE_SIZE_MB" | bc -l) )); then
            log_warning "Bundle size exceeds ${MAX_BUNDLE_SIZE_MB} MB"
        else
            log_success "Bundle size is acceptable"
        fi
    fi

    echo ""
    log_success "========================================"
    log_success "Build completed successfully!"
    log_success "========================================"
    echo ""
    log_info "Output directory: ${SCRIPT_DIR}/dist"
    log_info "CLI executable: ${SCRIPT_DIR}/dist/cli.js"
    echo ""
    log_info "Next steps:"
    echo "  - Run tests: npm test"
    echo "  - Install globally: npm link"
    echo "  - Use CLI: ./dist/cli.js <file.json>"
}

# Run main function
main "$@"
