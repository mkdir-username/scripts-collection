#!/bin/bash

# version_manager_v2.0.0.sh
# Скрипт для управления версиями в Scripts директории
# Версия: 2.0.0
# Дата: 2025-09-27

set -e  # Остановка при ошибках

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Базовая директория
SCRIPTS_DIR="/Users/username/Scripts"

# Функция вывода сообщений
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Функция проверки версионного формата
validate_version() {
    local version=$1
    if [[ ! $version =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        log_error "Неверный формат версии: $version"
        log_info "Используйте формат: vX.Y.Z (например, v2.0.0)"
        return 1
    fi
    return 0
}

# Функция создания новой версии
create_version() {
    local category=$1
    local version=$2

    if [ -z "$category" ] || [ -z "$version" ]; then
        log_error "Использование: create_version <category> <version>"
        log_info "Категории: validators, tools, bash"
        return 1
    fi

    validate_version "$version" || return 1

    local version_dir="${SCRIPTS_DIR}/${category}/${version}"

    if [ -d "$version_dir" ]; then
        log_warn "Версия $version уже существует в $category"
        return 1
    fi

    mkdir -p "$version_dir"
    log_info "Создана новая версия: $version_dir"

    # Создание README для версии
    cat > "${version_dir}/README.md" << EOF
# ${category^} - ${version}

## Дата создания
$(date +"%Y-%m-%d")

## Изменения
- [Добавьте описание изменений]

## Файлы
- [Список файлов будет обновлен автоматически]
EOF

    log_info "Создан README.md для версии $version"
}

# Функция обновления символической ссылки current
update_current() {
    local category=$1
    local version=$2

    if [ -z "$category" ] || [ -z "$version" ]; then
        log_error "Использование: update_current <category> <version>"
        return 1
    fi

    validate_version "$version" || return 1

    local category_dir="${SCRIPTS_DIR}/${category}"
    local version_dir="${category_dir}/${version}"

    if [ ! -d "$version_dir" ]; then
        log_error "Версия $version не существует в $category"
        return 1
    fi

    cd "$category_dir"
    rm -f current
    ln -sf "$version" current

    log_info "Символическая ссылка 'current' обновлена на $version"
}

# Функция архивирования старой версии
archive_version() {
    local category=$1
    local version=$2
    local quarter=${3:-$(date +"%Y/Q%q")}  # Текущий квартал по умолчанию

    if [ -z "$category" ] || [ -z "$version" ]; then
        log_error "Использование: archive_version <category> <version> [quarter]"
        return 1
    fi

    local source_dir="${SCRIPTS_DIR}/${category}/${version}"
    local archive_dir="${SCRIPTS_DIR}/archive/${quarter}/${category}"

    if [ ! -d "$source_dir" ]; then
        log_error "Версия $version не существует в $category"
        return 1
    fi

    mkdir -p "$archive_dir"

    # Создание метаданных архива
    local meta_file="${archive_dir}/${version}.meta"
    cat > "$meta_file" << EOF
{
  "archived_date": "$(date +"%Y-%m-%d")",
  "source_category": "${category}",
  "version": "${version}",
  "reason": "Архивирование старой версии",
  "can_delete_after": "$(date -d '+2 years' +"%Y-%m-%d")"
}
EOF

    # Перемещение версии в архив
    mv "$source_dir" "$archive_dir/"
    log_info "Версия $version архивирована в $archive_dir"
}

# Функция листинга версий
list_versions() {
    local category=$1

    if [ -z "$category" ]; then
        log_info "Все версии:"
        for cat in validators tools bash; do
            echo -e "\n${GREEN}${cat^}:${NC}"
            ls -1 "${SCRIPTS_DIR}/${cat}" | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' || true
            current=$(readlink "${SCRIPTS_DIR}/${cat}/current" 2>/dev/null || echo "не установлена")
            echo -e "  ${YELLOW}current -> ${current}${NC}"
        done
    else
        echo -e "\n${GREEN}${category^}:${NC}"
        ls -1 "${SCRIPTS_DIR}/${category}" | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' || true
        current=$(readlink "${SCRIPTS_DIR}/${category}/current" 2>/dev/null || echo "не установлена")
        echo -e "  ${YELLOW}current -> ${current}${NC}"
    fi
}

# Главное меню
main() {
    case "${1:-help}" in
        create)
            create_version "$2" "$3"
            ;;
        update)
            update_current "$2" "$3"
            ;;
        archive)
            archive_version "$2" "$3" "$4"
            ;;
        list)
            list_versions "$2"
            ;;
        help|--help|-h)
            cat << EOF
Управление версиями Scripts

Использование: $(basename $0) <команда> [параметры]

Команды:
  create <category> <version>    - Создать новую версию
  update <category> <version>    - Обновить символическую ссылку current
  archive <category> <version>   - Архивировать версию
  list [category]                 - Показать все версии
  help                           - Показать эту справку

Категории:
  validators  - Валидаторы
  tools       - Python утилиты
  bash        - Bash скрипты

Примеры:
  $(basename $0) create tools v2.1.0
  $(basename $0) update tools v2.1.0
  $(basename $0) archive tools v1.0.0
  $(basename $0) list tools
EOF
            ;;
        *)
            log_error "Неизвестная команда: $1"
            echo "Используйте '$(basename $0) help' для справки"
            exit 1
            ;;
    esac
}

# Запуск главной функции
main "$@"