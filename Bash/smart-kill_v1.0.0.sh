#!/bin/bash
# Smart Kill Utility v1.0.0
# Убивает все процессы по названию с подтверждением

set -euo pipefail

if [ $# -eq 0 ]; then
    echo "Usage: smart-kill <process_name> [-f|--force]"
    echo "  -f, --force    Kill without confirmation"
    exit 1
fi

PROCESS_NAME="$1"
FORCE=false

if [ $# -eq 2 ] && [[ "$2" == "-f" || "$2" == "--force" ]]; then
    FORCE=true
fi

# Находим все PID процессов
PIDS=$(pgrep -f "$PROCESS_NAME" 2>/dev/null || true)

if [ -z "$PIDS" ]; then
    echo "❌ Процессы '$PROCESS_NAME' не найдены"
    exit 0
fi

# Показываем информацию о процессах
echo "📋 Найдено процессов: $(echo "$PIDS" | wc -l | tr -d ' ')"
echo ""
ps -fp $PIDS 2>/dev/null || ps -p $PIDS

# Подтверждение
if [ "$FORCE" = false ]; then
    echo ""
    read -p "🔪 Убить эти процессы? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Отменено"
        exit 0
    fi
fi

# Убиваем процессы
echo "$PIDS" | xargs kill -9 2>/dev/null || true

echo "✅ Процессы убиты"

# Проверяем что всё убито
REMAINING=$(pgrep -f "$PROCESS_NAME" 2>/dev/null || true)
if [ -n "$REMAINING" ]; then
    echo "⚠️  Некоторые процессы остались:"
    ps -fp $REMAINING 2>/dev/null || ps -p $REMAINING
    exit 1
fi
