# Руководство по миграции

## Обзор миграции

Документ описывает перемещение скриптов из различных локаций в централизованную структуру `/Users/username/Scripts/`.

## Что было перенесено

### 1. Из домашней директории

#### Было:
```
/Users/username/
├── backup.sh
├── deploy.sh
├── test_script.py
└── utils/
    └── helper.sh
```

#### Стало:
```
/Users/username/Scripts/
├── Bash/
│   ├── backup/
│   │   └── backup_v1.0.0.sh
│   └── utils/
│       └── helper_v1.0.0.sh
└── Python/
    └── utils/
        └── test_script_v1.0.0.py
```

### 2. Из /usr/local/bin

#### Было:
```
/usr/local/bin/
├── my-tool
├── validate-json
└── process-data
```

#### Стало:
```
/Users/username/Scripts/
├── tools/
│   └── analyzers/
│       └── my_tool_v1.0.0.sh
└── validators/
    └── json/
        └── validate_json_v1.0.0.py
```

### 3. Из проектных директорий

#### Было:
```
/Users/username/projects/
├── project1/scripts/
│   └── deploy.sh
└── project2/tools/
    └── build.sh
```

#### Стало:
```
/Users/username/Scripts/
├── Bash/
│   └── automation/
│       ├── project1_deploy_v1.0.0.sh
│       └── project2_build_v1.0.0.sh
```

## Созданные символические ссылки

### Для обратной совместимости

```bash
# В /usr/local/bin
ln -s /Users/username/Scripts/validators/json/validate_json_v1.0.0.py /usr/local/bin/validate-json
ln -s /Users/username/Scripts/tools/analyzers/my_tool_v1.0.0.sh /usr/local/bin/my-tool

# В домашней директории
ln -s /Users/username/Scripts/Bash/backup/backup_v1.0.0.sh ~/backup.sh
ln -s /Users/username/Scripts/Bash/automation/deploy_v1.0.0.sh ~/deploy.sh
```

### Ссылки на последние версии

```bash
# В каждой категории
cd /Users/username/Scripts/validators/json/
ln -s validate_json_v1.5.0.py validate_json_latest.py

cd /Users/username/Scripts/Bash/backup/
ln -s backup_system_v1.0.0.sh backup_system_latest.sh
```

## Обновленные пути в конфигурациях

### .bashrc / .zshrc

#### Было:
```bash
export PATH="/Users/username/bin:$PATH"
alias backup="/Users/username/backup.sh"
alias deploy="/Users/username/deploy.sh"
```

#### Стало:
```bash
export PATH="/Users/username/Scripts/Bash/utils:$PATH"
export PATH="/Users/username/Scripts/Python/utils:$PATH"

# Алиасы на версионированные скрипты
alias backup="/Users/username/Scripts/Bash/backup/backup_system_latest.sh"
alias deploy="/Users/username/Scripts/Bash/automation/deploy_latest.sh"
alias validate="/Users/username/Scripts/validators/json/validate_json_latest.py"
```

### crontab

#### Было:
```cron
0 2 * * * /Users/username/backup.sh
0 */6 * * * /Users/username/monitor.sh
```

#### Стало:
```cron
0 2 * * * /Users/username/Scripts/Bash/backup/backup_system_latest.sh
0 */6 * * * /Users/username/Scripts/Bash/monitoring/monitor_services_latest.sh
```

### systemd службы

#### Было:
```ini
[Service]
ExecStart=/usr/local/bin/my-service
```

#### Стало:
```ini
[Service]
ExecStart=/Users/username/Scripts/tools/services/my_service_latest.sh
```

## Процесс миграции

### Шаг 1: Инвентаризация
```bash
# Найти все скрипты
find ~ -name "*.sh" -o -name "*.py" > scripts_inventory.txt

# Проверить /usr/local/bin
ls -la /usr/local/bin/ | grep -E "^-.*x" > local_bin_scripts.txt
```

### Шаг 2: Категоризация
```bash
# Создать структуру директорий
mkdir -p /Users/username/Scripts/{Bash,Python}/{automation,backup,monitoring,utils}
mkdir -p /Users/username/Scripts/{validators,tools}/{json,schema,generators,converters,analyzers}
mkdir -p /Users/username/Scripts/archive/{2024,2025}
```

### Шаг 3: Перемещение с версионированием
```bash
# Пример для bash скриптов
for script in *.sh; do
    name="${script%.sh}"
    cp "$script" "/Users/username/Scripts/Bash/utils/${name}_v1.0.0.sh"
    ln -s "${name}_v1.0.0.sh" "${name}_latest.sh"
done
```

### Шаг 4: Создание символических ссылок
```bash
# Для каждого критичного скрипта
ln -s /Users/username/Scripts/Bash/backup/backup_v1.0.0.sh /usr/local/bin/backup

# Проверка ссылок
ls -la /usr/local/bin/ | grep " -> "
```

### Шаг 5: Обновление конфигураций
```bash
# Резервное копирование
cp ~/.bashrc ~/.bashrc.backup
cp ~/.zshrc ~/.zshrc.backup

# Обновление путей
sed -i 's|/Users/username/backup.sh|/Users/username/Scripts/Bash/backup/backup_latest.sh|g' ~/.bashrc
```

## Откат миграции

Если необходимо вернуться к старой структуре:

### 1. Восстановление из резервных копий
```bash
# Восстановить конфигурации
cp ~/.bashrc.backup ~/.bashrc
cp ~/.zshrc.backup ~/.zshrc
source ~/.bashrc

# Восстановить crontab
crontab crontab.backup
```

### 2. Восстановление файлов
```bash
# Из архива
tar -xzf scripts_backup_20250927.tar.gz -C /

# Или копирование обратно
cp /Users/username/Scripts/Bash/backup/backup_v1.0.0.sh ~/backup.sh
chmod +x ~/backup.sh
```

## Проверка после миграции

### Тесты работоспособности
```bash
#!/bin/bash
# test_migration.sh

echo "Проверка миграции скриптов..."

# Проверка символических ссылок
for link in /usr/local/bin/*; do
    if [ -L "$link" ]; then
        if [ ! -e "$link" ]; then
            echo "❌ Битая ссылка: $link"
        else
            echo "✅ Рабочая ссылка: $link -> $(readlink $link)"
        fi
    fi
done

# Проверка алиасов
alias | grep -E "(backup|deploy|validate)"

# Проверка PATH
echo $PATH | tr ':' '\n' | grep Scripts

# Проверка cron
crontab -l | grep Scripts
```

### Проверка версий
```bash
# Список всех версионированных файлов
find /Users/username/Scripts -name "*_v[0-9]*" -type f | sort

# Проверка latest ссылок
find /Users/username/Scripts -name "*_latest.*" -type l -exec readlink {} \;
```

## Известные проблемы и решения

### Проблема 1: Скрипты не находятся в PATH
**Решение:**
```bash
export PATH="/Users/username/Scripts/Bash/utils:$PATH"
export PATH="/Users/username/Scripts/Python/utils:$PATH"
```

### Проблема 2: Права выполнения
**Решение:**
```bash
find /Users/username/Scripts -name "*.sh" -exec chmod +x {} \;
find /Users/username/Scripts -name "*.py" -exec chmod +x {} \;
```

### Проблема 3: Относительные пути в скриптах
**Решение:**
```bash
# Обновить пути в скриптах
sed -i 's|\./config|/Users/username/Scripts/config|g' script.sh
```

### Проблема 4: Зависимости между скриптами
**Решение:**
Использовать абсолютные пути или переменные окружения:
```bash
SCRIPTS_DIR="/Users/username/Scripts"
source "$SCRIPTS_DIR/Bash/utils/common_functions_v1.0.0.sh"
```

## Рекомендации

### Постепенная миграция
1. Начните с некритичных скриптов
2. Тестируйте после каждого перемещения
3. Сохраняйте резервные копии
4. Документируйте изменения

### Поддержка двойных путей
На переходный период поддерживайте оба пути:
```bash
# В скрипте
SCRIPT_PATH="/Users/username/Scripts/Bash/utils/helper_v1.0.0.sh"
OLD_PATH="/Users/username/utils/helper.sh"

if [ -f "$SCRIPT_PATH" ]; then
    source "$SCRIPT_PATH"
elif [ -f "$OLD_PATH" ]; then
    source "$OLD_PATH"
else
    echo "Скрипт не найден!"
    exit 1
fi
```

### Автоматизация обновлений
Используйте скрипт `update_to_latest.sh` для автоматического обновления ссылок на новые версии.

## Контрольный список миграции

- [ ] Создана структура директорий
- [ ] Скрипты перемещены с версионированием
- [ ] Созданы символические ссылки для обратной совместимости
- [ ] Обновлены конфигурационные файлы (.bashrc, .zshrc)
- [ ] Обновлен crontab
- [ ] Обновлены systemd службы
- [ ] Протестирована работоспособность
- [ ] Создано резервное копирование
- [ ] Документированы изменения
- [ ] Удалены старые файлы (после проверки)

---
*Последнее обновление: 27 сентября 2025*
*Версия документа: 1.0.0*