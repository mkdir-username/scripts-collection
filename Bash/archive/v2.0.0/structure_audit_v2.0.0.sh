#!/bin/bash

# structure_audit_v2.0.0.sh
# Скрипт аудита и проверки структуры Scripts директории
# Версия: 2.0.0
# Дата: 2025-09-27

set -e

SCRIPTS_DIR="/Users/username/Scripts"

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Аудит структуры Scripts ===${NC}\n"

# Проверка основных директорий
echo -e "${GREEN}[1/5] Проверка основных директорий:${NC}"
for dir in validators tools bash archive docs; do
    if [ -d "${SCRIPTS_DIR}/${dir}" ]; then
        echo -e "  ✓ ${dir}/"
    else
        echo -e "  ${RED}✗ ${dir}/ - отсутствует${NC}"
    fi
done

# Проверка символических ссылок current
echo -e "\n${GREEN}[2/5] Проверка символических ссылок 'current':${NC}"
for dir in validators tools bash; do
    if [ -L "${SCRIPTS_DIR}/${dir}/current" ]; then
        target=$(readlink "${SCRIPTS_DIR}/${dir}/current")
        echo -e "  ✓ ${dir}/current → ${target}"
    else
        echo -e "  ${YELLOW}⚠ ${dir}/current - не установлена${NC}"
    fi
done

# Проверка версионирования файлов
echo -e "\n${GREEN}[3/5] Проверка соответствия именования:${NC}"
violations=0
correct=0

# Функция проверки имени файла
check_filename() {
    local file=$1
    local basename=$(basename "$file")

    # Пропускаем директории и README файлы
    if [ -d "$file" ] || [[ "$basename" == "README"* ]] || [[ "$basename" == "requirements.txt" ]]; then
        return 0
    fi

    # Проверяем на запрещенные паттерны
    if [[ "$basename" =~ _new\.|_final\.|_temp\.|_old\.|^test\. ]]; then
        echo -e "  ${RED}✗ Нарушение: $file${NC}"
        ((violations++))
        return 1
    fi

    # Проверяем на правильное версионирование (если применимо)
    if [[ "$basename" =~ _v[0-9]+\.[0-9]+\.[0-9]+(\.|_) ]]; then
        ((correct++))
        return 0
    fi

    return 0
}

# Проверяем файлы в версионных директориях
for category in validators tools bash; do
    for version_dir in "${SCRIPTS_DIR}/${category}"/v*; do
        if [ -d "$version_dir" ]; then
            while IFS= read -r file; do
                check_filename "$file"
            done < <(find "$version_dir" -type f -maxdepth 1 2>/dev/null)
        fi
    done
done

echo -e "  Корректных файлов: ${correct}"
if [ $violations -gt 0 ]; then
    echo -e "  ${RED}Нарушений: ${violations}${NC}"
else
    echo -e "  ${GREEN}Нарушений не найдено${NC}"
fi

# Проверка структуры архива
echo -e "\n${GREEN}[4/5] Проверка структуры архива:${NC}"
for year in 2024 2025; do
    if [ -d "${SCRIPTS_DIR}/archive/${year}" ]; then
        echo -e "  ✓ archive/${year}/"
        for quarter in Q1 Q2 Q3 Q4; do
            if [ -d "${SCRIPTS_DIR}/archive/${year}/${quarter}" ]; then
                count=$(find "${SCRIPTS_DIR}/archive/${year}/${quarter}" -type f 2>/dev/null | wc -l)
                if [ $count -gt 0 ]; then
                    echo -e "    └─ ${quarter}: ${count} файлов"
                fi
            fi
        done
    fi
done

# Статистика
echo -e "\n${GREEN}[5/5] Статистика:${NC}"

# Подсчет файлов по категориям
for category in validators tools bash; do
    count=$(find "${SCRIPTS_DIR}/${category}" -type f -name "*.py" -o -name "*.sh" -o -name "*.js" 2>/dev/null | wc -l)
    echo -e "  ${category}: ${count} файлов"
done

# Проверка наличия requirements.txt
echo -e "\n${BLUE}Файлы requirements.txt:${NC}"
find "${SCRIPTS_DIR}" -name "requirements.txt" -type f | while read -r req; do
    echo -e "  • ${req#${SCRIPTS_DIR}/}"
done

# Итоговый отчет
echo -e "\n${BLUE}=== Итоговый отчет ===${NC}"

# Проверяем критичные проблемы
critical_issues=0

# Файлы в корне Scripts (не должно быть)
root_files=$(find "${SCRIPTS_DIR}" -maxdepth 1 -type f \
    ! -name "README.md" \
    ! -name ".gitignore" \
    ! -name "*.md" 2>/dev/null | wc -l)

if [ $root_files -gt 0 ]; then
    echo -e "${RED}⚠ Найдено ${root_files} файлов в корне Scripts/${NC}"
    ((critical_issues++))
fi

# Временные файлы
temp_files=$(find "${SCRIPTS_DIR}" -type f \( -name "*.tmp" -o -name "*.temp" -o -name "*~" \) 2>/dev/null | wc -l)
if [ $temp_files -gt 0 ]; then
    echo -e "${YELLOW}⚠ Найдено ${temp_files} временных файлов${NC}"
fi

if [ $critical_issues -eq 0 ] && [ $violations -eq 0 ]; then
    echo -e "${GREEN}✅ Структура соответствует всем правилам!${NC}"
else
    echo -e "${YELLOW}⚠ Обнаружены проблемы, требующие внимания${NC}"
    echo -e "\nРекомендации:"
    echo -e "  1. Переместите файлы из корня в соответствующие версионные директории"
    echo -e "  2. Переименуйте файлы с нарушениями именования"
    echo -e "  3. Удалите временные файлы"
    echo -e "  4. Обновите символические ссылки 'current'"
fi

echo -e "\n${BLUE}=== Аудит завершен ===${NC}"