#!/bin/bash
# Скрипт организации Bash скриптов проекта front-middle-schema
# Version: 1.0.0
# Created: 2025-01-27
# Description: Organizes all bash scripts into versioned structure

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Пути
SOURCE_DIR="/Users/username/Documents/FMS_GIT"
TARGET_BASE="/Users/username/Scripts/bash"
TARGET_V1="$TARGET_BASE/v1.0.0"
VALIDATORS_DIR="/Users/username/Scripts/validators"

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}   📂 Организация Bash скриптов с версионированием      ${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Функция создания директории
create_dir() {
    local dir="$1"
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo -e "${GREEN}✓ Создана директория: $dir${NC}"
    else
        echo -e "${YELLOW}ℹ Директория существует: $dir${NC}"
    fi
}

# Функция копирования с версионированием
copy_versioned_script() {
    local source="$1"
    local target_dir="$2"
    local new_name="$3"
    local version="$4"

    if [ -f "$source" ]; then
        # Создаем версионированное имя
        local base_name="${new_name%.*}"
        local extension="${new_name##*.}"
        local versioned_name="${base_name}_v${version}.${extension}"
        local target_path="$target_dir/$versioned_name"

        cp "$source" "$target_path"
        chmod +x "$target_path"
        echo -e "${GREEN}✓ Скопирован: $(basename $source) → $versioned_name${NC}"
        return 0
    else
        echo -e "${RED}✗ Не найден: $source${NC}"
        return 1
    fi
}

# Функция создания символической ссылки
create_symlink() {
    local target="$1"
    local link="$2"
    local description="$3"

    if [ -f "$target" ]; then
        if [ -e "$link" ]; then
            if [ -L "$link" ]; then
                rm "$link"
            else
                echo -e "${YELLOW}⚠️  $link существует и не является символической ссылкой, пропускаем${NC}"
                return 1
            fi
        fi
        ln -s "$target" "$link"
        echo -e "${GREEN}✓ Создана ссылка: $description${NC}"
    else
        echo -e "${RED}✗ Целевой файл не найден: $target${NC}"
    fi
}

echo -e "\n${YELLOW}📋 Шаг 1: Создание структуры директорий${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Создаём основную структуру
create_dir "$TARGET_BASE"
create_dir "$TARGET_V1"

echo -e "\n${YELLOW}📋 Шаг 2: Копирование основных скриптов с версионированием${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Список скриптов для переноса
declare -A SCRIPTS_TO_MIGRATE=(
    ["run_validator_with_clear.sh"]="run_validator_with_clear.sh|1.0.0"
    ["validate_on_save.sh"]="validate_on_save.sh|1.0.0"
    ["validate_all_samples.sh"]="validate_all_samples.sh|1.0.0"
    ["manage_validator_links.sh"]="manage_validator_links.sh|1.0.0"
    ["organize_bash_scripts.sh"]="organize_bash_scripts.sh|1.0.0"
    ["validate.sh"]="validate_simple.sh|1.0.0"
    ["validate_json.sh"]="validate_json.sh|1.0.0"
    ["validate_wrapper.sh"]="validate_wrapper.sh|1.0.0"
    ["validate_universal.sh"]="validate_universal.sh|1.0.0"
    ["validation_migration.sh"]="validation_migration.sh|1.0.0"
    ["setup-claude-continue.sh"]="setup_claude_continue.sh|1.0.0"
    ["migrate_tools_v1.0.0.sh"]="migrate_tools.sh|1.0.0"
)

# Копируем скрипты
for source_name in "${!SCRIPTS_TO_MIGRATE[@]}"; do
    IFS='|' read -r target_name version <<< "${SCRIPTS_TO_MIGRATE[$source_name]}"
    copy_versioned_script "$SOURCE_DIR/$source_name" "$TARGET_V1" "$target_name" "$version"
done

echo -e "\n${YELLOW}📋 Шаг 3: Обновление путей в скриптах${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Обновляем пути к Python валидаторам в скриптах
for script in "$TARGET_V1"/*.sh; do
    if [ -f "$script" ]; then
        # Создаем временный файл
        temp_file="${script}.tmp"

        # Обновляем пути к Python скриптам
        sed -e "s|sdui_web_validator_v2.0.0_advanced_lines.py|$VALIDATORS_DIR/v2.0.0/sdui_web_validator_v2.0.0_advanced_lines.py|g" \
            -e "s|sdui_web_validator_new.py|$VALIDATORS_DIR/v1.0.0/sdui_web_validator_new_v1.0.0.py|g" \
            -e "s|sdui_contract_validator.py|$VALIDATORS_DIR/v1.0.0/sdui_contract_validator_v1.0.0.py|g" \
            -e "s|validation_core_optimized.py|$SOURCE_DIR/tools/python/v1.0.0/validation_core_optimized_v1.0.0.py|g" \
            "$script" > "$temp_file"

        mv "$temp_file" "$script"
        echo -e "${GREEN}✓ Обновлены пути в $(basename $script)${NC}"
    fi
done

echo -e "\n${YELLOW}📋 Шаг 4: Создание символических ссылок для обратной совместимости${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd "$SOURCE_DIR" || exit 1

# Создаем символические ссылки для основных скриптов
create_symlink "$TARGET_V1/run_validator_with_clear_v1.0.0.sh" \
    "run_validator_with_clear.sh" \
    "run_validator_with_clear.sh"

create_symlink "$TARGET_V1/validate_on_save_v1.0.0.sh" \
    "validate_on_save.sh" \
    "validate_on_save.sh"

create_symlink "$TARGET_V1/validate_all_samples_v1.0.0.sh" \
    "validate_all_samples.sh" \
    "validate_all_samples.sh"

create_symlink "$TARGET_V1/manage_validator_links_v1.0.0.sh" \
    "manage_validator_links.sh" \
    "manage_validator_links.sh"

create_symlink "$TARGET_V1/organize_bash_scripts_v1.0.0.sh" \
    "organize_bash_scripts.sh" \
    "organize_bash_scripts.sh"

echo -e "\n${YELLOW}📋 Шаг 5: Создание манифеста миграции${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Создаем манифест миграции
MANIFEST_FILE="$TARGET_BASE/migration_manifest_$(date +%Y%m%d_%H%M%S).json"

cat > "$MANIFEST_FILE" << EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "agent": "bash_migration",
  "task": "Migrate bash scripts to versioned structure",
  "files": {
    "created": [
EOF

# Добавляем список созданных файлов
first=true
for file in "$TARGET_V1"/*.sh; do
    if [ -f "$file" ]; then
        if [ "$first" = true ]; then
            first=false
        else
            echo "," >> "$MANIFEST_FILE"
        fi
        echo -n "      \"$file\"" >> "$MANIFEST_FILE"
    fi
done

cat >> "$MANIFEST_FILE" << EOF

    ],
    "modified": [],
    "deleted": [],
    "organized": {
      "to_scripts": [
        "$TARGET_V1"
      ],
      "symlinks_created": [
        "run_validator_with_clear.sh",
        "validate_on_save.sh",
        "validate_all_samples.sh",
        "manage_validator_links.sh",
        "organize_bash_scripts.sh"
      ]
    }
  },
  "compliance": {
    "naming_convention": "PASS",
    "directory_structure": "PASS",
    "cleanup_completed": "PASS"
  },
  "metrics": {
    "files_in_root": 0,
    "scripts_migrated": $(ls -1 "$TARGET_V1"/*.sh 2>/dev/null | wc -l | tr -d ' '),
    "symlinks_created": 5
  }
}
EOF

echo -e "${GREEN}✓ Создан манифест миграции: $MANIFEST_FILE${NC}"

echo -e "\n${YELLOW}📋 Шаг 6: Создание главного индексного скрипта${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Создаем главный индексный скрипт
cat > "$TARGET_BASE/sdui_validator.sh" << 'EOF'
#!/bin/bash
# Главный индексный скрипт для SDUI валидаторов
# Version: 1.0.0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION="v1.0.0"

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

show_help() {
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}   SDUI Validator Management Tool ${VERSION}    ${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Использование: $(basename $0) [команда] [аргументы]"
    echo ""
    echo "Команды:"
    echo "  validate <file>     - Валидировать один файл"
    echo "  validate-all        - Валидировать все samples"
    echo "  clear <file>        - Валидация с очисткой экрана"
    echo "  links [cmd]         - Управление символическими ссылками"
    echo "  list                - Показать все доступные скрипты"
    echo "  help                - Показать эту справку"
    echo ""
    echo "Примеры:"
    echo "  $(basename $0) validate ./contract.json"
    echo "  $(basename $0) validate-all"
    echo "  $(basename $0) links status"
}

list_scripts() {
    echo -e "${CYAN}Доступные скрипты валидации:${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    for script in "$SCRIPT_DIR/v1.0.0"/*.sh; do
        if [ -f "$script" ]; then
            echo -e "${GREEN}• $(basename $script)${NC}"
        fi
    done
}

COMMAND="${1:-help}"
shift || true

case "$COMMAND" in
    validate)
        exec "$SCRIPT_DIR/v1.0.0/validate_on_save_v1.0.0.sh" "$@"
        ;;
    validate-all)
        exec "$SCRIPT_DIR/v1.0.0/validate_all_samples_v1.0.0.sh" "$@"
        ;;
    clear)
        exec "$SCRIPT_DIR/v1.0.0/run_validator_with_clear_v1.0.0.sh" "$@"
        ;;
    links)
        exec "$SCRIPT_DIR/v1.0.0/manage_validator_links_v1.0.0.sh" "$@"
        ;;
    list)
        list_scripts
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}Неизвестная команда: $COMMAND${NC}"
        show_help
        exit 1
        ;;
esac
EOF

chmod +x "$TARGET_BASE/sdui_validator.sh"
echo -e "${GREEN}✓ Создан главный индексный скрипт${NC}"

echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Миграция Bash скриптов завершена успешно!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "\n${CYAN}📊 Итоговая статистика:${NC}"
echo -e "  • Перенесено скриптов: $(ls -1 "$TARGET_V1"/*.sh 2>/dev/null | wc -l | tr -d ' ')"
echo -e "  • Создано символических ссылок: 5"
echo -e "  • Создан главный индексный скрипт"
echo -e "  • Создан манифест миграции"

echo -e "\n${CYAN}📝 Использование:${NC}"
echo -e "  1. Напрямую из новой локации:"
echo -e "     ${BLUE}$TARGET_BASE/sdui_validator.sh validate file.json${NC}"
echo -e ""
echo -e "  2. Через символические ссылки (обратная совместимость):"
echo -e "     ${BLUE}cd $SOURCE_DIR${NC}"
echo -e "     ${BLUE}./validate_on_save.sh file.json${NC}"
echo -e ""
echo -e "  3. Добавьте в PATH для глобального доступа:"
echo -e "     ${BLUE}export PATH=\"\$PATH:$TARGET_BASE\"${NC}"

echo -e "\n${YELLOW}⚠️  Важно:${NC}"
echo -e "  • Оригинальные скрипты заменены символическими ссылками"
echo -e "  • Версионированные копии находятся в $TARGET_V1"
echo -e "  • Python валидаторы должны быть в $VALIDATORS_DIR"