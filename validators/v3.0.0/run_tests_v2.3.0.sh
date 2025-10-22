#!/usr/bin/env bash
# ============================================================================
# Quick Start Script для тестов валидатора v2.3.0
#
# Usage:
#   ./run_tests_v2.3.0.sh              # Все тесты
#   ./run_tests_v2.3.0.sh unit         # Только unit тесты
#   ./run_tests_v2.3.0.sh integration  # Только integration тесты
#   ./run_tests_v2.3.0.sh performance  # Только performance тесты
#   ./run_tests_v2.3.0.sh coverage     # С покрытием кода
#   ./run_tests_v2.3.0.sh watch        # Watch mode
#
# @version 1.0.0
# @date 2025-10-05
# ============================================================================

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Директория скрипта
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ============================================================================
# ФУНКЦИИ
# ============================================================================

print_header() {
  echo ""
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${BLUE}$1${NC}"
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo ""
}

print_success() {
  echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
  echo -e "${RED}❌ $1${NC}"
}

print_warning() {
  echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
  echo -e "${BLUE}ℹ️  $1${NC}"
}

# ============================================================================
# ПРОВЕРКА ОКРУЖЕНИЯ
# ============================================================================

check_environment() {
  print_header "Проверка окружения"

  # Проверка Node.js
  if ! command -v node &> /dev/null; then
    print_error "Node.js не установлен"
    exit 1
  fi
  print_success "Node.js: $(node --version)"

  # Проверка npm
  if ! command -v npm &> /dev/null; then
    print_error "npm не установлен"
    exit 1
  fi
  print_success "npm: $(npm --version)"

  # Проверка node_modules
  if [ ! -d "node_modules" ]; then
    print_warning "node_modules не найден, устанавливаю зависимости..."
    npm install
  else
    print_success "node_modules найден"
  fi

  # Проверка Jest
  if [ ! -f "node_modules/.bin/jest" ]; then
    print_warning "Jest не установлен, устанавливаю..."
    npm install --save-dev jest @jest/globals ts-jest @types/jest jest-junit
  else
    print_success "Jest установлен"
  fi
}

# ============================================================================
# ЗАПУСК ТЕСТОВ
# ============================================================================

run_all_tests() {
  print_header "Запуск всех тестов"
  npx jest test_validator_v2.3.0.ts --config jest.config.test_v2.3.0.js
}

run_unit_tests() {
  print_header "Запуск Unit тестов"
  npx jest test_validator_v2.3.0.ts --config jest.config.test_v2.3.0.js -t "Unit Tests"
}

run_integration_tests() {
  print_header "Запуск Integration тестов"
  npx jest test_validator_v2.3.0.ts --config jest.config.test_v2.3.0.js -t "Integration Tests"
}

run_performance_tests() {
  print_header "Запуск Performance тестов"
  npx jest test_validator_v2.3.0.ts --config jest.config.test_v2.3.0.js -t "Performance Tests"
}

run_edge_case_tests() {
  print_header "Запуск Edge Case тестов"
  npx jest test_validator_v2.3.0.ts --config jest.config.test_v2.3.0.js -t "Edge Cases"
}

run_real_world_tests() {
  print_header "Запуск Real-World тестов"
  npx jest test_validator_v2.3.0.ts --config jest.config.test_v2.3.0.js -t "Real-World Examples"
}

run_with_coverage() {
  print_header "Запуск тестов с покрытием кода"
  npx jest test_validator_v2.3.0.ts --config jest.config.test_v2.3.0.js --coverage

  if [ -f "coverage/lcov-report/index.html" ]; then
    print_success "Отчет покрытия создан: coverage/lcov-report/index.html"
    print_info "Открыть отчет: open coverage/lcov-report/index.html"
  fi
}

run_watch_mode() {
  print_header "Запуск в Watch режиме"
  print_info "Тесты будут перезапускаться при изменении файлов"
  print_info "Нажмите Ctrl+C для выхода"
  npx jest test_validator_v2.3.0.ts --config jest.config.test_v2.3.0.js --watch
}

run_verbose() {
  print_header "Запуск всех тестов (подробный вывод)"
  npx jest test_validator_v2.3.0.ts --config jest.config.test_v2.3.0.js --verbose
}

# ============================================================================
# ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

show_help() {
  cat << EOF
${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}
${BLUE}SDUI Validator v2.3.0 - Test Runner${NC}
${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}

${GREEN}Использование:${NC}
  ./run_tests_v2.3.0.sh [команда]

${GREEN}Команды:${NC}
  ${YELLOW}all${NC}           - Запустить все тесты (по умолчанию)
  ${YELLOW}unit${NC}          - Только unit тесты (JinjaParser)
  ${YELLOW}integration${NC}   - Только integration тесты (JinjaAwareValidator)
  ${YELLOW}performance${NC}   - Только performance тесты
  ${YELLOW}edge${NC}          - Только edge case тесты
  ${YELLOW}real${NC}          - Только real-world тесты
  ${YELLOW}coverage${NC}      - Запустить с покрытием кода
  ${YELLOW}watch${NC}         - Запустить в watch режиме
  ${YELLOW}verbose${NC}       - Подробный вывод
  ${YELLOW}help${NC}          - Показать эту справку

${GREEN}Примеры:${NC}
  ./run_tests_v2.3.0.sh
  ./run_tests_v2.3.0.sh unit
  ./run_tests_v2.3.0.sh coverage
  ./run_tests_v2.3.0.sh watch

${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}
EOF
}

show_summary() {
  print_header "Сводка тестов"

  if [ -f "test-results/junit.xml" ]; then
    # Парсинг JUnit XML для статистики
    local tests=$(grep -o 'tests="[^"]*"' test-results/junit.xml | head -1 | sed 's/tests="//;s/"//')
    local failures=$(grep -o 'failures="[^"]*"' test-results/junit.xml | head -1 | sed 's/failures="//;s/"//')
    local time=$(grep -o 'time="[^"]*"' test-results/junit.xml | head -1 | sed 's/time="//;s/"//')

    echo "Всего тестов: $tests"
    echo "Провалено: $failures"
    echo "Время: ${time}s"

    if [ "$failures" -eq 0 ]; then
      print_success "Все тесты пройдены!"
    else
      print_error "$failures тест(ов) провалено"
    fi
  fi

  if [ -f "coverage/coverage-summary.json" ]; then
    echo ""
    print_info "Coverage отчет доступен: coverage/lcov-report/index.html"
  fi
}

# ============================================================================
# ОСНОВНАЯ ЛОГИКА
# ============================================================================

main() {
  check_environment

  case "${1:-all}" in
    all)
      run_all_tests
      ;;
    unit)
      run_unit_tests
      ;;
    integration)
      run_integration_tests
      ;;
    performance)
      run_performance_tests
      ;;
    edge)
      run_edge_case_tests
      ;;
    real)
      run_real_world_tests
      ;;
    coverage)
      run_with_coverage
      ;;
    watch)
      run_watch_mode
      ;;
    verbose)
      run_verbose
      ;;
    help)
      show_help
      exit 0
      ;;
    *)
      print_error "Неизвестная команда: $1"
      echo ""
      show_help
      exit 1
      ;;
  esac

  local exit_code=$?

  echo ""
  if [ $exit_code -eq 0 ]; then
    print_success "Тесты завершены успешно"
  else
    print_error "Тесты завершены с ошибками"
  fi

  show_summary

  exit $exit_code
}

# ============================================================================
# ЗАПУСК
# ============================================================================

main "$@"
