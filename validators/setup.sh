#!/bin/bash

# Скрипт установки SDUI валидаторов
# Автоматическая настройка окружения и зависимостей

set -e

echo "🚀 Установка SDUI валидаторов..."
echo

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не установлен. Установите Python 3.8+ и повторите попытку."
    exit 1
fi

echo "✅ Python найден: $(python3 --version)"

# Создание виртуального окружения
if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активация виртуального окружения
echo "🔄 Активация виртуального окружения..."
source venv/bin/activate

# Установка зависимостей
echo "📚 Установка зависимостей..."
pip install --upgrade pip
pip install -r requirements.txt

# Создание символической ссылки для быстрого доступа
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Добавление в PATH (опционально)
echo
echo "💡 Для удобства использования добавьте следующие строки в ~/.bashrc или ~/.zshrc:"
echo
echo "# SDUI Validators"
echo "export PATH=\"\$PATH:$SCRIPT_DIR\""
echo "source $SCRIPT_DIR/aliases.sh"
echo

# Тестирование установки
echo "🧪 Проверка установки..."
python3 validate.py --list

echo
echo "✅ Установка завершена!"
echo
echo "📖 Использование:"
echo "  python validate.py contract.json              # Проверка последней версией"
echo "  python validate.py --version v1.2.0 file.json # Использовать конкретную версию"
echo "  python validate.py --type visual file.json    # Визуальный валидатор"
echo "  python validate.py --list                     # Список доступных валидаторов"
echo
echo "🔗 Символические ссылки:"
echo "  В проекте front-middle-schema:"
echo "  sdui_web_validator_latest.py -> v2.0.0/sdui_web_validator_v2.0.0_advanced_lines.py"
echo