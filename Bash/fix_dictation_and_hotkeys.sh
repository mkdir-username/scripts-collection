#!/bin/bash

# Скрипт для исправления проблем с диктовкой (F5) и горячими клавишами Raycast
# Автор: Claude
# Дата создания: 2025-08-26

echo "🔧 Начинаю исправление проблем с диктовкой и горячими клавишами..."

# 1. Перезапуск процессов диктовки
echo "📝 Перезапускаю службы диктовки..."
killall DictationIM 2>/dev/null
killall com.apple.speech.speechsynthesisd 2>/dev/null
killall com.apple.speech.synthesisserver 2>/dev/null
killall SpeechRecognitionCore 2>/dev/null
killall speechrecognitiond 2>/dev/null

# 2. Перезапуск служб распознавания речи и ввода
echo "🎤 Перезапускаю службы распознавания речи..."
killall corespeechd 2>/dev/null
killall localspeechrecognition 2>/dev/null
killall keyboardservicesd 2>/dev/null
killall inputanalyticsd 2>/dev/null
killall com.apple.siri.embeddedspeech 2>/dev/null

# 3. Перезапуск Dock (управляет многими системными функциями)
echo "🖥️ Перезапускаю Dock..."
killall Dock

# 4. Перезапуск служб текстового ввода
echo "⌨️ Перезапускаю службы текстового ввода..."
killall TextInputMenuAgent 2>/dev/null
killall TextInputSwitcher 2>/dev/null

# 5. Очистка кэша служб речи и доступности
echo "🗑️ Очищаю кэш служб..."
rm -rf ~/Library/Caches/com.apple.speech* 2>/dev/null
rm -rf ~/Library/Caches/com.apple.accessibility* 2>/dev/null

# 6. Перезапуск Raycast с очисткой кэша
echo "🚀 Перезапускаю Raycast..."
killall Raycast 2>/dev/null
rm -rf ~/Library/Caches/com.raycast.macos 2>/dev/null
sleep 2

# 7. Сброс настроек горячих клавиш (опционально - закомментировано)
# echo "🔄 Сбрасываю настройки горячих клавиш..."
# defaults delete -g NSUserKeyEquivalents 2>/dev/null
# defaults delete com.apple.symbolichotkeys 2>/dev/null

# 8. Перезапуск службы настроек
echo "⚙️ Перезапускаю службу настроек..."
killall cfprefsd

# 9. Запуск Raycast
echo "▶️ Запускаю Raycast..."
open -a Raycast

echo ""
echo "✅ Готово! Проверьте:"
echo "   • F5 для диктовки"
echo "   • Option+3 в Raycast для скриншота"
echo ""
echo "Если проблемы остались, попробуйте перезагрузить Mac."