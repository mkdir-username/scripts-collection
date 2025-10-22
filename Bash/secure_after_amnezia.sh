#!/bin/bash

#==============================================================================
# БЕЗОПАСНАЯ НАСТРОЙКА VPS ПОСЛЕ УСТАНОВКИ AMNEZIA VPN
# Версия: 2.1 (для уже работающего VPN)
#==============================================================================

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

# Функция для отображения рамки
print_box() {
    local text="$1"
    local color="$2"
    echo -e "${color}"
    echo "╔══════════════════════════════════════════════════════════════════════╗"
    printf "║ %-68s ║\n" "$text"
    echo "╚══════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Функция для отображения шага
print_step() {
    echo -e "\n${CYAN}${BOLD}▶ $1${NC}"
    echo -e "${CYAN}$(printf '─%.0s' {1..70})${NC}\n"
}

# Проверка root
if [[ $EUID -ne 0 ]]; then
   print_box "ОШИБКА: Скрипт должен быть запущен от root" "$RED"
   echo -e "${YELLOW}Используйте: sudo bash $0${NC}\n"
   exit 1
fi

clear
print_box "НАСТРОЙКА БЕЗОПАСНОСТИ (ПОСЛЕ УСТАНОВКИ AMNEZIA VPN)" "$GREEN"
echo ""
echo -e "${CYAN}Этот скрипт настроит безопасность на сервере${NC}"
echo -e "${CYAN}с уже работающим AmneziaVPN (XRAY Reality)${NC}"
echo ""
echo -e "${YELLOW}Текущая ситуация:${NC}"
echo -e "  • AmneziaVPN с Reality: ${GREEN}Установлен${NC}"
echo -e "  • SSH-ключ: ${YELLOW}Есть на локальной машине, не добавлен на сервер${NC}"
echo -e "  • Безопасность: ${RED}Не настроена${NC}"
echo ""
read -p "Нажмите Enter для начала настройки..."

#==============================================================================
# ШАГ 0: ПРОВЕРКА AMNEZIAVPN И DOCKER
#==============================================================================

print_step "[0/11] Проверка установленных компонентов"

# Проверка Docker
if command -v docker &> /dev/null; then
    echo -e "  Docker: ${GREEN}✓ Установлен${NC}"
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
    echo -e "  Версия: ${CYAN}$DOCKER_VERSION${NC}"
else
    echo -e "  Docker: ${RED}✗ Не найден${NC}"
    echo -e "${YELLOW}Возможно AmneziaVPN не установлен. Продолжить? (y/n)${NC}"
    read -p "> " continue_choice
    if [[ ! "$continue_choice" =~ ^([yY])$ ]]; then
        exit 0
    fi
fi

# Проверка запущенных контейнеров
if command -v docker &> /dev/null; then
    CONTAINERS=$(docker ps --format "{{.Names}}" 2>/dev/null)
    if [ -n "$CONTAINERS" ]; then
        echo ""
        echo -e "${YELLOW}Запущенные Docker контейнеры:${NC}"
        docker ps --format "  • {{.Names}} ({{.Image}}) - Ports: {{.Ports}}"
    fi
fi

# Проверка используемых портов
echo ""
echo -e "${YELLOW}Проверка используемых портов...${NC}"
USED_PORTS=$(ss -tulpn | grep LISTEN | grep -E ':(22|80|443|2222)' || true)
if [ -n "$USED_PORTS" ]; then
    echo -e "${CYAN}Занятые порты (22, 80, 443, 2222):${NC}"
    echo "$USED_PORTS" | awk '{print "  " $5}' | cut -d: -f2 | sort -u
fi

echo ""
read -p "Проверка завершена. Продолжить настройку? (y/n): " continue_setup
if [[ ! "$continue_setup" =~ ^([yY])$ ]]; then
    exit 0
fi

#==============================================================================
# ШАГ 1: ДОБАВЛЕНИЕ SSH-КЛЮЧА С ЛОКАЛЬНОЙ МАШИНЫ
#==============================================================================

print_step "[1/11] КРИТИЧЕСКИЙ ШАГ: Добавление SSH-ключа"

SSH_KEY_EXISTS=false

# Проверяем наличие authorized_keys
if [ -f ~/.ssh/authorized_keys ] && [ -s ~/.ssh/authorized_keys ]; then
    KEY_COUNT=$(grep -c "^ssh-" ~/.ssh/authorized_keys 2>/dev/null || echo "0")
    if [ "$KEY_COUNT" -gt 0 ]; then
        SSH_KEY_EXISTS=true
        echo -e "${GREEN}✓ Обнаружено SSH-ключей: $KEY_COUNT${NC}"
        echo ""
        echo -e "${YELLOW}Текущие ключи в ~/.ssh/authorized_keys:${NC}"
        echo -e "${CYAN}─────────────────────────────────────────────────────────────────${NC}"
        cat ~/.ssh/authorized_keys | head -n 3
        if [ "$KEY_COUNT" -gt 3 ]; then
            echo -e "${CYAN}... (показаны первые 3)${NC}"
        fi
        echo -e "${CYAN}─────────────────────────────────────────────────────────────────${NC}"
        echo ""

        read -p "Добавить ещё один SSH-ключ? (y/n): " add_more
        if [[ ! "$add_more" =~ ^([yY])$ ]]; then
            SSH_KEY_EXISTS=true
        else
            SSH_KEY_EXISTS=false
        fi
    fi
fi

# Если нужно добавить ключ
if [ "$SSH_KEY_EXISTS" = false ]; then
    echo -e "${YELLOW}${BOLD}Выберите способ добавления SSH-ключа:${NC}"
    echo ""
    echo -e "${GREEN}1)${NC} Скопировать ключ с локальной машины (ssh-copy-id)"
    echo -e "${YELLOW}2)${NC} Вставить ключ вручную (скопировать содержимое .pub файла)"
    echo -e "${BLUE}3)${NC} Пропустить (ОПАСНО - доступ по паролю будет отключен!)"
    echo ""

    while true; do
        read -p "Ваш выбор [1-3]: " key_method
        case $key_method in
            1)
                CURRENT_IP=$(hostname -I | awk '{print $1}')
                CURRENT_PORT=$(grep "^Port " /etc/ssh/sshd_config | awk '{print $2}')
                if [ -z "$CURRENT_PORT" ]; then
                    CURRENT_PORT=22
                fi

                echo ""
                echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
                echo -e "${CYAN}${BOLD}  ИНСТРУКЦИЯ: Копирование SSH-ключа с локальной машины${NC}"
                echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
                echo ""
                echo -e "${YELLOW}1. НЕ ЗАКРЫВАЙТЕ это окно терминала!${NC}"
                echo ""
                echo -e "${YELLOW}2. Откройте НОВЫЙ терминал на ВАШЕМ КОМПЬЮТЕРЕ${NC}"
                echo ""
                echo -e "${YELLOW}3. Выполните команду:${NC}"
                echo ""
                echo -e "${GREEN}${BOLD}ssh-copy-id -p $CURRENT_PORT root@$CURRENT_IP${NC}"
                echo ""
                echo -e "${YELLOW}4. Введите пароль от сервера (последний раз)${NC}"
                echo ""
                echo -e "${YELLOW}5. После успешного копирования вернитесь сюда${NC}"
                echo ""
                echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
                echo ""
                echo -e "${RED}Если ssh-copy-id не найден, используйте:${NC}"
                echo -e "${GREEN}cat ~/.ssh/id_rsa.pub | ssh -p $CURRENT_PORT root@$CURRENT_IP 'mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys'${NC}"
                echo ""

                read -p "Нажмите Enter после выполнения команды..."

                # Проверяем добавился ли ключ
                sleep 1
                if [ -f ~/.ssh/authorized_keys ] && [ -s ~/.ssh/authorized_keys ]; then
                    NEW_KEY_COUNT=$(grep -c "^ssh-" ~/.ssh/authorized_keys 2>/dev/null || echo "0")
                    if [ "$NEW_KEY_COUNT" -gt "$KEY_COUNT" ] || [ "$NEW_KEY_COUNT" -gt 0 ]; then
                        echo -e "${GREEN}✓ SSH-ключ успешно добавлен!${NC}"
                        echo ""
                        echo -e "${YELLOW}Последний добавленный ключ:${NC}"
                        echo -e "${CYAN}─────────────────────────────────────────────────────────────────${NC}"
                        tail -n 1 ~/.ssh/authorized_keys
                        echo -e "${CYAN}─────────────────────────────────────────────────────────────────${NC}"
                        SSH_KEY_EXISTS=true
                        break
                    else
                        echo -e "${RED}✗ Ключ не обнаружен. Попробуйте снова или выберите способ 2${NC}"
                    fi
                else
                    echo -e "${RED}✗ Файл authorized_keys не найден${NC}"
                fi
                ;;
            2)
                echo ""
                mkdir -p ~/.ssh
                chmod 700 ~/.ssh

                echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
                echo -e "${CYAN}${BOLD}  ИНСТРУКЦИЯ: Ручное добавление SSH-ключа${NC}"
                echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
                echo ""
                echo -e "${YELLOW}1. На ВАШЕМ КОМПЬЮТЕРЕ выполните:${NC}"
                echo ""
                echo -e "${GREEN}cat ~/.ssh/id_rsa.pub${NC}"
                echo -e "${CYAN}   или${NC}"
                echo -e "${GREEN}cat ~/.ssh/id_ed25519.pub${NC}"
                echo ""
                echo -e "${YELLOW}2. Скопируйте ВЕСЬ вывод (начинается с ssh-rsa или ssh-ed25519)${NC}"
                echo ""
                echo -e "${YELLOW}3. Вставьте ниже и нажмите Enter, затем Ctrl+D${NC}"
                echo ""
                echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
                echo ""
                echo -e "${GREEN}Вставьте публичный SSH-ключ:${NC}"
                echo -e "${CYAN}─────────────────────────────────────────────────────────────────${NC}"

                ssh_key_input=$(cat)

                if echo "$ssh_key_input" | grep -qE "^(ssh-rsa|ssh-ed25519|ecdsa-sha2-nistp256|ssh-dss)"; then
                    echo "$ssh_key_input" >> ~/.ssh/authorized_keys
                    chmod 600 ~/.ssh/authorized_keys
                    echo ""
                    echo -e "${GREEN}✓ SSH-ключ успешно добавлен!${NC}"
                    echo ""
                    echo -e "${YELLOW}Добавленный ключ:${NC}"
                    echo -e "${CYAN}─────────────────────────────────────────────────────────────────${NC}"
                    tail -n 1 ~/.ssh/authorized_keys
                    echo -e "${CYAN}─────────────────────────────────────────────────────────────────${NC}"
                    SSH_KEY_EXISTS=true
                    break
                else
                    echo ""
                    echo -e "${RED}✗ Ошибка: неверный формат ключа!${NC}"
                    echo -e "${YELLOW}Ключ должен начинаться с: ssh-rsa, ssh-ed25519, ecdsa-sha2-nistp256${NC}"
                    exit 1
                fi
                ;;
            3)
                echo ""
                echo -e "${RED}${BOLD}╔════════════════════════════════════════════════════════════╗${NC}"
                echo -e "${RED}${BOLD}║  ⚠️  КРИТИЧЕСКОЕ ПРЕДУПРЕЖДЕНИЕ                            ║${NC}"
                echo -e "${RED}${BOLD}║                                                            ║${NC}"
                echo -e "${RED}${BOLD}║  Скрипт отключит парольную аутентификацию!                 ║${NC}"
                echo -e "${RED}${BOLD}║  Без SSH-ключа вы ПОТЕРЯЕТЕ доступ к серверу!             ║${NC}"
                echo -e "${RED}${BOLD}╚════════════════════════════════════════════════════════════╝${NC}"
                echo ""
                read -p "Я понимаю риск (введите YES заглавными): " final_confirm
                if [ "$final_confirm" = "YES" ]; then
                    echo -e "${RED}Продолжаем БЕЗ SSH-ключа (на ваш страх и риск)${NC}"
                    break
                else
                    echo -e "${YELLOW}Отменено. Добавьте SSH-ключ.${NC}"
                    continue
                fi
                ;;
            *)
                echo -e "${RED}Неверный выбор${NC}"
                ;;
        esac
    done
fi

# Тестирование SSH-ключа
if [ "$SSH_KEY_EXISTS" = true ]; then
    echo ""
    echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}${BOLD}  КРИТИЧЕСКИ ВАЖНО: Проверка SSH-ключа${NC}"
    echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    CURRENT_IP=$(hostname -I | awk '{print $1}')
    CURRENT_PORT=$(grep "^Port " /etc/ssh/sshd_config | awk '{print $2}')
    if [ -z "$CURRENT_PORT" ]; then
        CURRENT_PORT=22
    fi

    echo -e "${YELLOW}ПЕРЕД продолжением ОБЯЗАТЕЛЬНО проверьте SSH-ключ!${NC}"
    echo ""
    echo -e "${YELLOW}1. Откройте НОВЫЙ терминал на вашем компьютере${NC}"
    echo -e "${YELLOW}2. Попробуйте подключиться по ключу:${NC}"
    echo ""
    echo -e "${GREEN}ssh -p $CURRENT_PORT root@$CURRENT_IP${NC}"
    echo ""
    echo -e "${YELLOW}3. Подключение должно пройти БЕЗ запроса пароля${NC}"
    echo -e "${YELLOW}4. НЕ ЗАКРЫВАЙТЕ старое соединение до проверки!${NC}"
    echo ""
    echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
    echo ""

    while true; do
        read -p "SSH-ключ работает (подключились без пароля)? (y/n): " key_works
        if [[ "$key_works" =~ ^([yY])$ ]]; then
            echo -e "${GREEN}✓ Отлично! SSH-ключ работает. Продолжаем.${NC}"
            break
        elif [[ "$key_works" =~ ^([nN])$ ]]; then
            echo ""
            echo -e "${RED}SSH-ключ не работает!${NC}"
            echo -e "${YELLOW}Возможные причины:${NC}"
            echo "  1. Ключ добавлен неправильно"
            echo "  2. Права на файлы ~/.ssh/* неверные"
            echo "  3. На локальной машине используется другой ключ"
            echo ""
            read -p "Попробовать исправить? (y=исправить/n=выход): " fix_choice
            if [[ "$fix_choice" =~ ^([yY])$ ]]; then
                echo ""
                echo -e "${YELLOW}Исправление прав доступа...${NC}"
                chmod 700 ~/.ssh
                chmod 600 ~/.ssh/authorized_keys
                echo -e "${GREEN}Права исправлены${NC}"
                echo ""
                echo -e "${YELLOW}Попробуйте подключиться снова${NC}"
                continue
            else
                echo -e "${RED}Выход. Добавьте SSH-ключ и запустите скрипт заново.${NC}"
                exit 1
            fi
        fi
    done
fi

#==============================================================================
# ШАГ 2: ОБНОВЛЕНИЕ СИСТЕМЫ
#==============================================================================

print_step "[2/11] Обновление системы"
apt update && apt upgrade -y
echo -e "${GREEN}✓ Система обновлена${NC}"

#==============================================================================
# ШАГ 3: ПРОВЕРКА ПОРТОВ AMNEZIAVPN
#==============================================================================

print_step "[3/11] Определение портов AmneziaVPN"

echo -e "${YELLOW}Анализ портов Docker контейнеров...${NC}"

VPN_PORTS=""
if command -v docker &> /dev/null; then
    # Получаем порты из контейнеров
    CONTAINER_PORTS=$(docker ps --format "{{.Ports}}" 2>/dev/null | grep -oE '[0-9]+/tcp|[0-9]+/udp' | cut -d/ -f1 | sort -u)

    if [ -n "$CONTAINER_PORTS" ]; then
        echo -e "${GREEN}Обнаружены порты Docker контейнеров:${NC}"
        while IFS= read -r port; do
            echo -e "  • ${CYAN}$port${NC}"
        done <<< "$CONTAINER_PORTS"
        VPN_PORTS="$CONTAINER_PORTS"
    else
        echo -e "${YELLOW}Docker контейнеры не найдены или порты не опубликованы${NC}"
    fi
fi

# Для XRAY Reality обычно используется 443
if [ -z "$VPN_PORTS" ]; then
    echo -e "${YELLOW}Используем стандартные порты для XRAY Reality${NC}"
    VPN_PORTS="443"
fi

echo ""
echo -e "${CYAN}Порты для открытия в firewall: ${GREEN}$VPN_PORTS${NC}"
echo ""

#==============================================================================
# ШАГ 4: НАСТРОЙКА SSH
#==============================================================================

NEW_SSH_PORT=2222
CURRENT_SSH_PORT=$(grep "^Port " /etc/ssh/sshd_config | awk '{print $2}')
if [ -z "$CURRENT_SSH_PORT" ]; then
    CURRENT_SSH_PORT=22
fi

print_step "[4/11] Настройка SSH (текущий порт: $CURRENT_SSH_PORT)"

# Бэкап
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup.$(date +%Y%m%d_%H%M%S)

# Изменение порта
if ! grep -q "^Port " /etc/ssh/sshd_config; then
    echo "Port $NEW_SSH_PORT" >> /etc/ssh/sshd_config
else
    sed -i "s/^Port .*/Port $NEW_SSH_PORT/" /etc/ssh/sshd_config
    sed -i "s/^#Port .*/Port $NEW_SSH_PORT/" /etc/ssh/sshd_config
fi

# Root только по ключу
if ! grep -q "^PermitRootLogin " /etc/ssh/sshd_config; then
    echo "PermitRootLogin prohibit-password" >> /etc/ssh/sshd_config
else
    sed -i "s/^PermitRootLogin .*/PermitRootLogin prohibit-password/" /etc/ssh/sshd_config
    sed -i "s/^#PermitRootLogin .*/PermitRootLogin prohibit-password/" /etc/ssh/sshd_config
fi

# Отключение паролей
if ! grep -q "^PasswordAuthentication " /etc/ssh/sshd_config; then
    echo "PasswordAuthentication no" >> /etc/ssh/sshd_config
else
    sed -i "s/^PasswordAuthentication .*/PasswordAuthentication no/" /etc/ssh/sshd_config
    sed -i "s/^#PasswordAuthentication .*/PasswordAuthentication no/" /etc/ssh/sshd_config
fi

# Проверка конфигурации
if ! sshd -t; then
    echo -e "${RED}✗ Ошибка конфигурации SSH!${NC}"
    cp /etc/ssh/sshd_config.backup.* /etc/ssh/sshd_config
    exit 1
fi

echo -e "${GREEN}✓ SSH настроен${NC}"

#==============================================================================
# ШАГ 5: УСТАНОВКА UFW
#==============================================================================

print_step "[5/11] Установка UFW firewall"

if ! command -v ufw &> /dev/null; then
    apt install ufw -y
fi

# Открываем новый SSH порт
ufw allow $NEW_SSH_PORT/tcp comment 'SSH'

# Открываем порты VPN
for port in $VPN_PORTS; do
    ufw allow $port/tcp comment 'AmneziaVPN'
    echo -e "  Открыт порт: ${GREEN}$port/tcp${NC}"
done

# HTTP для certbot (опционально)
ufw allow 80/tcp comment 'HTTP'

# Политики
ufw default deny incoming
ufw default allow outgoing

echo -e "${GREEN}✓ UFW настроен${NC}"

#==============================================================================
# ШАГ 6: ИНТЕГРАЦИЯ UFW + DOCKER (КРИТИЧНО!)
#==============================================================================

print_step "[6/11] Интеграция UFW с Docker"

echo -e "${YELLOW}Применяем защиту от Docker bypass UFW...${NC}"

if ! grep -q "BEGIN UFW AND DOCKER" /etc/ufw/after.rules; then
    cat >> /etc/ufw/after.rules << 'EOF'

# BEGIN UFW AND DOCKER
*filter
:ufw-user-forward - [0:0]
:DOCKER-USER - [0:0]
-A DOCKER-USER -j ufw-user-forward

# Разрешить внутренние сети Docker
-A DOCKER-USER -j RETURN -s 10.0.0.0/8
-A DOCKER-USER -j RETURN -s 172.16.0.0/12
-A DOCKER-USER -j RETURN -s 192.168.0.0/16

# Разрешить DNS
-A DOCKER-USER -p udp -m udp --sport 53 --dport 1024:65535 -j RETURN

# Блокировать новые TCP соединения извне
-A DOCKER-USER -p tcp -m tcp --tcp-flags FIN,SYN,RST,ACK SYN -d 192.168.0.0/16 -j DROP
-A DOCKER-USER -p tcp -m tcp --tcp-flags FIN,SYN,RST,ACK SYN -d 10.0.0.0/8 -j DROP
-A DOCKER-USER -p tcp -m tcp --tcp-flags FIN,SYN,RST,ACK SYN -d 172.16.0.0/12 -j DROP

# Блокировать UDP на низкие порты
-A DOCKER-USER -p udp -m udp --dport 0:32767 -d 192.168.0.0/16 -j DROP
-A DOCKER-USER -p udp -m udp --dport 0:32767 -d 10.0.0.0/8 -j DROP
-A DOCKER-USER -p udp -m udp --dport 0:32767 -d 172.16.0.0/12 -j DROP

-A DOCKER-USER -j RETURN
COMMIT
# END UFW AND DOCKER
EOF
    echo -e "${GREEN}✓ Правила UFW+Docker добавлены${NC}"
else
    echo -e "${YELLOW}Правила уже существуют${NC}"
fi

#==============================================================================
# ШАГ 7: ВКЛЮЧЕНИЕ UFW И ПЕРЕЗАПУСК SSH
#==============================================================================

print_step "[7/11] Включение firewall и перезапуск SSH"

echo -e "${YELLOW}Включение UFW...${NC}"
ufw --force enable
echo -e "${GREEN}✓ UFW активирован${NC}"

echo -e "${YELLOW}Перезапуск SSH...${NC}"
systemctl restart ssh

sleep 2
if ! systemctl is-active --quiet ssh; then
    echo -e "${RED}✗ SSH не запустился!${NC}"
    cp /etc/ssh/sshd_config.backup.* /etc/ssh/sshd_config
    systemctl restart ssh
    exit 1
fi

CURRENT_IP=$(hostname -I | awk '{print $1}')

echo -e "${GREEN}✓ SSH перезапущен на порту $NEW_SSH_PORT${NC}"
echo ""
echo -e "${YELLOW}${BOLD}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}${BOLD}║  ⚠️  НЕ ЗАКРЫВАЙТЕ текущее соединение!                             ║${NC}"
echo -e "${YELLOW}${BOLD}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Откройте НОВЫЙ терминал и проверьте подключение:${NC}"
echo ""
echo -e "${GREEN}ssh -p $NEW_SSH_PORT root@$CURRENT_IP${NC}"
echo ""

while true; do
    read -p "Новое SSH-соединение работает? (y/n): " confirm
    if [[ "$confirm" =~ ^([yY])$ ]]; then
        echo -e "${GREEN}✓ Продолжаем${NC}"
        break
    elif [[ "$confirm" =~ ^([nN])$ ]]; then
        echo -e "${RED}Восстановление...${NC}"
        cp /etc/ssh/sshd_config.backup.* /etc/ssh/sshd_config
        systemctl restart ssh
        ufw delete allow $NEW_SSH_PORT/tcp
        ufw allow $CURRENT_SSH_PORT/tcp
        exit 1
    fi
done

#==============================================================================
# ШАГ 8: FAIL2BAN
#==============================================================================

print_step "[8/11] Установка Fail2Ban"

apt install fail2ban -y

USER_IP=$(echo $SSH_CLIENT | awk '{print $1}')
echo ""
echo -e "Ваш текущий IP: ${GREEN}$USER_IP${NC}"
read -p "Добавить в белый список? (y/n): " whitelist_choice

IGNORE_IP="127.0.0.1/8 ::1"
if [[ "$whitelist_choice" =~ ^([yY])$ ]] && [ -n "$USER_IP" ]; then
    IGNORE_IP="127.0.0.1/8 ::1 $USER_IP"
fi

cat > /etc/fail2ban/jail.local <<EOF
[DEFAULT]
ignoreip = $IGNORE_IP
bantime = 1800
findtime = 600
maxretry = 10

[sshd]
enabled = true
port = $NEW_SSH_PORT
filter = sshd
logpath = /var/log/auth.log
maxretry = 10
bantime = 1800
findtime = 600
EOF

systemctl enable fail2ban
systemctl restart fail2ban

echo -e "${GREEN}✓ Fail2Ban настроен${NC}"

#==============================================================================
# ШАГ 9-11: ОСТАЛЬНЫЕ НАСТРОЙКИ
#==============================================================================

print_step "[9/11] TCP BBR"
if ! grep -q "net.core.default_qdisc" /etc/sysctl.conf; then
    echo "net.core.default_qdisc = fq" >> /etc/sysctl.conf
    echo "net.ipv4.tcp_congestion_control = bbr" >> /etc/sysctl.conf
    sysctl -p > /dev/null 2>&1
    echo -e "${GREEN}✓ BBR включен${NC}"
fi

print_step "[10/11] Автообновления (ядро исключено)"
apt install unattended-upgrades -y

cat > /etc/apt/apt.conf.d/50unattended-upgrades << 'EOF'
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
};
Unattended-Upgrade::Package-Blacklist {
    "linux-image-*";
    "linux-headers-*";
};
Unattended-Upgrade::Automatic-Reboot "false";
EOF

cat > /etc/apt/apt.conf.d/20auto-upgrades << 'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
EOF

echo -e "${GREEN}✓ Автообновления настроены${NC}"

print_step "[11/11] Дополнительная безопасность"

read -p "Отключить IPv6? (y/n): " ipv6_choice
if [[ "$ipv6_choice" =~ ^([yY])$ ]]; then
    cat >> /etc/sysctl.conf << 'EOF'
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1
EOF
    sysctl -p > /dev/null 2>&1
    echo -e "${GREEN}✓ IPv6 отключен${NC}"
fi

if ! grep -q "net.ipv4.tcp_syncookies" /etc/sysctl.conf; then
    echo "net.ipv4.tcp_syncookies = 1" >> /etc/sysctl.conf
    sysctl -p > /dev/null 2>&1
fi

#==============================================================================
# ФИНАЛЬНЫЙ ОТЧЕТ
#==============================================================================

clear
echo -e "${GREEN}${BOLD}"
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                      ║"
echo "║              ✓ НАСТРОЙКА БЕЗОПАСНОСТИ ЗАВЕРШЕНА!                    ║"
echo "║                                                                      ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}\n"

echo -e "${CYAN}${BOLD}Изменения:${NC}"
echo -e "  SSH порт: ${RED}$CURRENT_SSH_PORT${NC} → ${GREEN}$NEW_SSH_PORT${NC}"
echo -e "  Root: ${GREEN}Только SSH-ключ${NC}"
echo -e "  Пароли: ${GREEN}Отключены${NC}"
echo -e "  UFW: ${GREEN}Активен + Docker интеграция${NC}"
echo -e "  Fail2Ban: ${GREEN}Активен${NC}"
echo -e "  BBR: ${GREEN}Включен${NC}\n"

echo -e "${CYAN}${BOLD}Открытые порты:${NC}"
ufw status numbered

echo ""
echo -e "${YELLOW}${BOLD}Для подключения используйте:${NC}"
echo -e "${GREEN}ssh -p $NEW_SSH_PORT root@$CURRENT_IP${NC}\n"

echo -e "${YELLOW}${BOLD}Проверьте работу VPN:${NC}"
echo -e "Подключитесь к AmneziaVPN и убедитесь что VPN работает\n"

echo -e "${GREEN}Настройка завершена!${NC}\n"
