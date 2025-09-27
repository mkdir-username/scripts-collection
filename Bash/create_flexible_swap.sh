#!/bin/bash

# Гибкая система swap для больших процессов
# Создает несколько файлов для безопасного тестирования

echo "=== Создание гибкой системы swap ==="

# Функция создания swap-файла
create_swap() {
    local size=$1
    local name=$2
    local file="/var/vm/swapfile_${name}"
    
    echo "Создание ${name}: ${size}ГБ..."
    sudo dd if=/dev/zero of=$file bs=1g count=$size
    sudo chmod 600 $file
    sudo chown root:wheel $file
    sudo mkswap $file
    echo "✅ ${name} готов: $file"
}

# Стратегия поэтапного увеличения
echo "Выберите размер swap:"
echo "1) 50 ГБ (безопасно)"
echo "2) 75 ГБ (умеренно)"  
echo "3) 100 ГБ (максимально)"
echo "4) Создать все поэтапно"

read -p "Выбор (1-4): " choice

case $choice in
    1) create_swap 50 "safe" ;;
    2) create_swap 75 "moderate" ;;
    3) create_swap 100 "maximum" ;;
    4) 
        create_swap 25 "test"
        create_swap 25 "extend1" 
        create_swap 25 "extend2"
        create_swap 25 "extend3"
        echo "Создано 4 файла по 25 ГБ = 100 ГБ total"
        ;;
esac

# Активация
echo "Для активации: sudo swapon /var/vm/swapfile_*"
echo "Для деактивации: sudo swapoff /var/vm/swapfile_*"