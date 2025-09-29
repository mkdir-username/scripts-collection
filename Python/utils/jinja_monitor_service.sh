#!/bin/bash

# Jinja Hot Reload Monitor Service Manager
# Скрипт для управления службой мониторинга Jinja шаблонов

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Конфигурация
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_SCRIPT="${SCRIPT_DIR}/jinja_hot_reload_v2.0.0.py"
DAEMON_SCRIPT="${SCRIPT_DIR}/jinja_hot_reload_daemon.py"
BASE_PATH="/Users/username/Documents/front-middle-schema/.JSON"
PID_FILE="/tmp/jinja_hot_reload.pid"
LOG_FILE="/tmp/jinja_hot_reload.log"
PYTHON_CMD="python3"

# Функция для вывода заголовка
print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}    Jinja Hot Reload Monitor Service v2.0.0    ${NC}"
    echo -e "${BLUE}================================================${NC}"
}

# Функция проверки зависимостей
check_dependencies() {
    echo -e "${YELLOW}Проверка зависимостей...${NC}"

    # Проверка Python
    if ! command -v $PYTHON_CMD &> /dev/null; then
        echo -e "${RED}❌ Python3 не установлен${NC}"
        exit 1
    fi

    # Проверка модулей Python
    missing_modules=""

    $PYTHON_CMD -c "import jinja2" 2>/dev/null || missing_modules="$missing_modules jinja2"
    $PYTHON_CMD -c "import watchdog" 2>/dev/null || missing_modules="$missing_modules watchdog"

    if [ ! -z "$missing_modules" ]; then
        echo -e "${RED}❌ Отсутствуют модули Python:${missing_modules}${NC}"
        echo -e "${YELLOW}Установите их командой: pip install${missing_modules}${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ Все зависимости установлены${NC}"
}

# Функция запуска в обычном режиме
start_normal() {
    echo -e "${GREEN}Запуск в обычном режиме (foreground)...${NC}"
    $PYTHON_CMD "$PYTHON_SCRIPT"
}

# Функция запуска в фоновом режиме
start_background() {
    echo -e "${GREEN}Запуск в фоновом режиме...${NC}"

    # Проверяем, не запущен ли уже
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${YELLOW}⚠️ Сервис уже запущен (PID: $PID)${NC}"
            return 1
        else
            rm -f "$PID_FILE"
        fi
    fi

    # Запускаем в фоне
    nohup $PYTHON_CMD "$PYTHON_SCRIPT" > "$LOG_FILE" 2>&1 &
    PID=$!
    echo $PID > "$PID_FILE"

    sleep 2

    # Проверяем, запустился ли процесс
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Сервис запущен в фоне (PID: $PID)${NC}"
        echo -e "${BLUE}Логи: $LOG_FILE${NC}"
    else
        echo -e "${RED}❌ Ошибка запуска сервиса${NC}"
        rm -f "$PID_FILE"
        return 1
    fi
}

# Функция остановки сервиса
stop_service() {
    echo -e "${YELLOW}Остановка сервиса...${NC}"

    if [ ! -f "$PID_FILE" ]; then
        echo -e "${YELLOW}Сервис не запущен${NC}"
        return 0
    fi

    PID=$(cat "$PID_FILE")

    if ps -p $PID > /dev/null 2>&1; then
        kill -TERM $PID

        # Ждём завершения процесса
        for i in {1..10}; do
            if ! ps -p $PID > /dev/null 2>&1; then
                break
            fi
            sleep 1
        done

        # Если процесс не завершился, убиваем принудительно
        if ps -p $PID > /dev/null 2>&1; then
            kill -9 $PID
        fi

        echo -e "${GREEN}✅ Сервис остановлен${NC}"
    else
        echo -e "${YELLOW}Процесс не найден${NC}"
    fi

    rm -f "$PID_FILE"
}

# Функция проверки статуса
check_status() {
    echo -e "${BLUE}Проверка статуса...${NC}"

    if [ ! -f "$PID_FILE" ]; then
        echo -e "${RED}❌ Сервис не запущен${NC}"
        return 1
    fi

    PID=$(cat "$PID_FILE")

    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Сервис работает (PID: $PID)${NC}"

        # Показываем информацию о процессе
        echo -e "\n${BLUE}Информация о процессе:${NC}"
        ps -f -p $PID

        # Показываем последние строки лога
        if [ -f "$LOG_FILE" ]; then
            echo -e "\n${BLUE}Последние записи в логе:${NC}"
            tail -n 10 "$LOG_FILE"
        fi

        # Показываем статистику файлов
        echo -e "\n${BLUE}Статистика файлов:${NC}"
        JJ_COUNT=$(find "$BASE_PATH" -name "[JJ_*.json" 2>/dev/null | wc -l)
        FULL_COUNT=$(find "$BASE_PATH" -name "[FULL_*.json" 2>/dev/null | wc -l)
        DATA_COUNT=$(find "$BASE_PATH" -name "[data]*.json" 2>/dev/null | wc -l)

        echo -e "  [JJ_] файлов:   $JJ_COUNT"
        echo -e "  [FULL_] файлов: $FULL_COUNT"
        echo -e "  [data] файлов:  $DATA_COUNT"

        return 0
    else
        echo -e "${RED}❌ Сервис не работает (процесс не найден)${NC}"
        rm -f "$PID_FILE"
        return 1
    fi
}

# Функция перезапуска
restart_service() {
    echo -e "${YELLOW}Перезапуск сервиса...${NC}"
    stop_service
    sleep 2
    start_background
}

# Функция просмотра логов
view_logs() {
    if [ ! -f "$LOG_FILE" ]; then
        echo -e "${YELLOW}Файл логов не найден${NC}"
        return 1
    fi

    echo -e "${BLUE}Просмотр логов (Ctrl+C для выхода)...${NC}"
    tail -f "$LOG_FILE"
}

# Функция очистки
cleanup() {
    echo -e "${YELLOW}Очистка временных файлов...${NC}"

    # Останавливаем сервис если запущен
    if [ -f "$PID_FILE" ]; then
        stop_service
    fi

    # Удаляем логи
    if [ -f "$LOG_FILE" ]; then
        rm -f "$LOG_FILE"
        echo -e "${GREEN}✅ Логи удалены${NC}"
    fi

    # Удаляем все [FULL_] файлы
    echo -e "${YELLOW}Удаление всех [FULL_] файлов...${NC}"
    FULL_FILES=$(find "$BASE_PATH" -name "[FULL_*.json" 2>/dev/null)
    if [ ! -z "$FULL_FILES" ]; then
        COUNT=$(echo "$FULL_FILES" | wc -l)
        echo "$FULL_FILES" | xargs rm -f
        echo -e "${GREEN}✅ Удалено $COUNT [FULL_] файлов${NC}"
    else
        echo -e "${YELLOW}[FULL_] файлы не найдены${NC}"
    fi
}

# Функция установки как системного сервиса (macOS)
install_service() {
    echo -e "${BLUE}Установка как системного сервиса (macOS)...${NC}"

    PLIST_FILE="$HOME/Library/LaunchAgents/com.jinjahotreload.monitor.plist"

    cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.jinjahotreload.monitor</string>

    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_CMD</string>
        <string>$PYTHON_SCRIPT</string>
    </array>

    <key>WorkingDirectory</key>
    <string>$HOME</string>

    <key>StandardOutPath</key>
    <string>$LOG_FILE</string>

    <key>StandardErrorPath</key>
    <string>$LOG_FILE</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
EOF

    # Загружаем сервис
    launchctl load "$PLIST_FILE"

    echo -e "${GREEN}✅ Сервис установлен и запущен${NC}"
    echo -e "${BLUE}Управление:${NC}"
    echo "  Остановить: launchctl stop com.jinjahotreload.monitor"
    echo "  Запустить:  launchctl start com.jinjahotreload.monitor"
    echo "  Удалить:    launchctl unload $PLIST_FILE"
}

# Функция помощи
show_help() {
    print_header
    echo ""
    echo "Использование: $0 [команда]"
    echo ""
    echo "Команды:"
    echo "  start       - Запустить мониторинг в обычном режиме"
    echo "  background  - Запустить в фоновом режиме"
    echo "  stop        - Остановить мониторинг"
    echo "  restart     - Перезапустить мониторинг"
    echo "  status      - Проверить статус"
    echo "  logs        - Просмотр логов в реальном времени"
    echo "  cleanup     - Очистка временных файлов и [FULL_] файлов"
    echo "  install     - Установить как системный сервис (macOS)"
    echo "  check       - Проверить зависимости"
    echo "  help        - Показать эту справку"
    echo ""
    echo "Примеры:"
    echo "  $0 start       # Запуск в консоли"
    echo "  $0 background  # Запуск в фоне"
    echo "  $0 status      # Проверка статуса"
    echo ""
}

# Главная логика
print_header

case "$1" in
    start)
        check_dependencies
        start_normal
        ;;
    background|bg)
        check_dependencies
        start_background
        ;;
    stop)
        stop_service
        ;;
    restart)
        check_dependencies
        restart_service
        ;;
    status)
        check_status
        ;;
    logs|log)
        view_logs
        ;;
    cleanup|clean)
        cleanup
        ;;
    install)
        check_dependencies
        install_service
        ;;
    check|deps)
        check_dependencies
        ;;
    help|--help|-h|"")
        show_help
        ;;
    *)
        echo -e "${RED}Неизвестная команда: $1${NC}"
        echo "Используйте '$0 help' для справки"
        exit 1
        ;;
esac

echo ""