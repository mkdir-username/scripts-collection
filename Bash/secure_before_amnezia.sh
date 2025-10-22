#!/bin/bash

#==============================================================================
# БЕЗОПАСНАЯ НАСТРОЙКА VPS ДЛЯ AMNEZIA VPN (XRAY REALITY)
# Версия: 2.0 (исправлены все конфликты)
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

# Функция для отображения предупреждения
print_warning() {
    echo -e "${YELLOW}${BOLD}"
    echo "╔══════════════════════════════════════════════════════════════════════╗"
    printf "║ %-68s ║\n" "$1"
    echo "╚══════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Проверка root
if [[ $EUID -ne 0 ]]; then
   print_box "ОШИБКА: Скрипт должен быть запущен от root" "$RED"
   echo -e "${YELLOW}Используйте: sudo bash $0${NC}\n"
   exit 1
fi

clear
print_box "БЕЗОПАСНАЯ НАСТРОЙКА VPS ДЛЯ AMNEZIA VPN v2.0" "$GREEN"
echo ""
echo -e "${CYAN}Этот скрипт подготовит VPS для установки AmneziaVPN${NC}"
echo -e "${CYAN}с учётом всех конфликтов Docker, UFW и безопасности${NC}"
echo ""
read -p "Нажмите Enter для начала настройки..."

#==============================================================================
# ШАГ 1: ПРОВЕРКА SSH-КЛЮЧА (КРИТИЧЕСКИЙ)
#==============================================================================

print_step "[1/11] КРИТИЧЕСКИЙ ШАГ: Проверка SSH-ключа"

SSH_KEY_EXISTS=false

# Проверяем наличие authorized_keys
if [ -f ~/.ssh/authorized_keys ] && [ -s ~/.ssh/authorized_keys ]; then
    KEY_COUNT=$(grep -c "^ssh-" ~/.ssh/authorized_keys 2>/dev/null || echo "0")
    if [ "$KEY_COUNT" -gt 0 ]; then
        SSH_KEY_EXISTS=true
        echo -e "${GREEN}✓ Обнаружено SSH-ключей: $KEY_COUNT${NC}"
        echo ""
        echo -e "${YELLOW}Содержимое ~/.ssh/authorized_keys:${NC}"
        echo -e "${CYAN}─────────────────────────────────────────────────────────────────${NC}"
        cat ~/.ssh/authorized_keys | head -n 3
        if [ "$KEY_COUNT" -gt 3 ]; then
            echo -e "${CYAN}... (показаны первые 3 ключа)${NC}"
        fi
        echo -e "${CYAN}─────────────────────────────────────────────────────────────────${NC}"
        echo ""
    fi
fi

# Если ключей нет - показываем диалоговое окно
if [ "$SSH_KEY_EXISTS" = false ]; then
    echo -e "${RED}${BOLD}"
    echo "╔══════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                      ║"
    echo "║                    ⚠️  ВНИМАНИЕ: SSH-КЛЮЧ НЕ НАЙДЕН!                ║"
    echo "║                                                                      ║"
    echo "║  Без SSH-ключа вы ПОТЕРЯЕТЕ доступ к серверу после выполнения       ║"
    echo "║  этого скрипта (будет отключена парольная аутентификация)           ║"
    echo "║                                                                      ║"
    echo "╚══════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    echo -e "${YELLOW}${BOLD}Выберите действие:${NC}"
    echo ""
    echo -e "${GREEN}1)${NC} Добавить SSH-ключ сейчас (РЕКОМЕНДУЕТСЯ)"
    echo -e "${YELLOW}2)${NC} У меня уже есть ключ, но он не отображается"
    echo -e "${RED}3)${NC} Пропустить (ОПАСНО! Возможна потеря доступа)"
    echo -e "${BLUE}4)${NC} Выход из скрипта"
    echo ""

    while true; do
        read -p "Ваш выбор [1-4]: " choice
        case $choice in
            1)
                echo ""
                print_step "Добавление SSH-ключа"

                mkdir -p ~/.ssh
                chmod 700 ~/.ssh

                echo -e "${CYAN}Где находится ваш SSH-ключ?${NC}"
                echo ""
                echo -e "${GREEN}1)${NC} Вставить ключ прямо сейчас"
                echo -e "${YELLOW}2)${NC} Ключ на моем компьютере (покажу команду)"
                echo ""
                read -p "Выбор [1-2]: " key_choice

                if [ "$key_choice" = "1" ]; then
                    echo ""
                    echo -e "${YELLOW}${BOLD}Инструкция:${NC}"
                    echo "1. На ВАШЕМ КОМПЬЮТЕРЕ: cat ~/.ssh/id_rsa.pub"
                    echo "2. Скопируйте ВЕСЬ вывод (начинается с ssh-rsa или ssh-ed25519)"
                    echo "3. Вставьте ниже и нажмите Enter, затем Ctrl+D"
                    echo ""
                    echo -e "${GREEN}Вставьте ваш публичный SSH-ключ:${NC}"
                    echo -e "${CYAN}─────────────────────────────────────────────────────────────────${NC}"

                    ssh_key_input=$(cat)

                    if echo "$ssh_key_input" | grep -qE "^(ssh-rsa|ssh-ed25519|ecdsa-sha2-nistp256|ssh-dss)"; then
                        echo "$ssh_key_input" >> ~/.ssh/authorized_keys
                        chmod 600 ~/.ssh/authorized_keys
                        echo ""
                        echo -e "${GREEN}✓ SSH-ключ успешно добавлен!${NC}"
                        SSH_KEY_EXISTS=true
                    else
                        echo ""
                        echo -e "${RED}✗ Ошибка: неверный формат ключа!${NC}"
                        exit 1
                    fi

                elif [ "$key_choice" = "2" ]; then
                    CURRENT_IP=$(hostname -I | awk '{print $1}')
                    echo ""
                    echo -e "${YELLOW}${BOLD}На ВАШЕМ КОМПЬЮТЕРЕ выполните:${NC}"
                    echo -e "${GREEN}ssh-copy-id root@$CURRENT_IP${NC}"
                    echo ""
                    read -p "Нажмите Enter после выполнения..."

                    if [ -f ~/.ssh/authorized_keys ] && [ -s ~/.ssh/authorized_keys ]; then
                        echo -e "${GREEN}✓ SSH-ключ обнаружен!${NC}"
                        SSH_KEY_EXISTS=true
                    else
                        echo -e "${RED}✗ Ключ не найден. Выход${NC}"
                        exit 1
                    fi
                fi
                break
                ;;
            2)
                echo ""
                echo -e "${YELLOW}Проверка других пользователей...${NC}"
                for user_home in /home/*; do
                    if [ -f "$user_home/.ssh/authorized_keys" ]; then
                        username=$(basename "$user_home")
                        key_count=$(grep -c "^ssh-" "$user_home/.ssh/authorized_keys" 2>/dev/null || echo "0")
                        echo -e "${GREEN}✓ $username${NC} - ключей: $key_count"
                    fi
                done
                SSH_KEY_EXISTS=true
                break
                ;;
            3)
                echo ""
                print_warning "ПОСЛЕДНЕЕ ПРЕДУПРЕЖДЕНИЕ"
                read -p "Введите 'YES' для продолжения БЕЗ ключа: " confirm
                if [ "$confirm" = "YES" ]; then
                    echo -e "${RED}Продолжаем БЕЗ SSH-ключа (на ваш риск)${NC}"
                    break
                else
                    exit 0
                fi
                ;;
            4)
                exit 0
                ;;
        esac
    done
fi

echo ""
read -p "Нажмите Enter для продолжения..."

#==============================================================================
# ШАГ 2: ОБНОВЛЕНИЕ СИСТЕМЫ
#==============================================================================

print_step "[2/11] Обновление системы"
apt update && apt upgrade -y
echo -e "${GREEN}✓ Система обновлена${NC}"

#==============================================================================
# ШАГ 3: НАСТРОЙКА SSH
#==============================================================================

NEW_SSH_PORT=2222
CURRENT_SSH_PORT=$(grep "^Port " /etc/ssh/sshd_config | awk '{print $2}')
if [ -z "$CURRENT_SSH_PORT" ]; then
    CURRENT_SSH_PORT=22
fi

print_step "[3/11] Настройка SSH (текущий порт: $CURRENT_SSH_PORT)"

# Бэкап конфигурации
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup.$(date +%Y%m%d_%H%M%S)

# Изменение порта SSH
if ! grep -q "^Port " /etc/ssh/sshd_config; then
    echo "Port $NEW_SSH_PORT" >> /etc/ssh/sshd_config
else
    sed -i "s/^Port .*/Port $NEW_SSH_PORT/" /etc/ssh/sshd_config
    sed -i "s/^#Port .*/Port $NEW_SSH_PORT/" /etc/ssh/sshd_config
fi

# ВАЖНО: Используем prohibit-password для AmneziaVPN
echo ""
echo -e "${YELLOW}Настройка доступа root для AmneziaVPN:${NC}"
echo -e "${CYAN}Root вход будет разрешен ТОЛЬКО по SSH-ключу (без пароля)${NC}"
echo -e "${CYAN}Это необходимо для автоустановки AmneziaVPN${NC}"
echo ""

if ! grep -q "^PermitRootLogin " /etc/ssh/sshd_config; then
    echo "PermitRootLogin prohibit-password" >> /etc/ssh/sshd_config
else
    sed -i "s/^PermitRootLogin .*/PermitRootLogin prohibit-password/" /etc/ssh/sshd_config
    sed -i "s/^#PermitRootLogin .*/PermitRootLogin prohibit-password/" /etc/ssh/sshd_config
fi

# Отключение парольной аутентификации
if ! grep -q "^PasswordAuthentication " /etc/ssh/sshd_config; then
    echo "PasswordAuthentication no" >> /etc/ssh/sshd_config
else
    sed -i "s/^PasswordAuthentication .*/PasswordAuthentication no/" /etc/ssh/sshd_config
    sed -i "s/^#PasswordAuthentication .*/PasswordAuthentication no/" /etc/ssh/sshd_config
fi

# Проверка конфигурации
if ! sshd -t; then
    echo -e "${RED}✗ Ошибка в конфигурации SSH!${NC}"
    cp /etc/ssh/sshd_config.backup.* /etc/ssh/sshd_config
    exit 1
fi

echo -e "${GREEN}✓ SSH настроен (root доступ по ключу разрешен для AmneziaVPN)${NC}"

#==============================================================================
# ШАГ 4: УСТАНОВКА И НАСТРОЙКА UFW
#==============================================================================

print_step "[4/11] Установка UFW firewall"
apt install ufw -y

# Открываем новый SSH-порт ПЕРЕД включением firewall
ufw allow $NEW_SSH_PORT/tcp comment 'SSH'

# Порты для XRAY Reality (VLESS)
ufw allow 443/tcp comment 'XRAY Reality (VLESS)'
ufw allow 80/tcp comment 'HTTP (optional for certbot)'

# Политики по умолчанию
ufw default deny incoming
ufw default allow outgoing

echo -e "${GREEN}✓ UFW настроен (порты: $NEW_SSH_PORT, 443, 80)${NC}"

#==============================================================================
# ШАГ 5: ИНТЕГРАЦИЯ UFW + DOCKER (КРИТИЧНО!)
#==============================================================================

print_step "[5/11] Интеграция UFW с Docker (защита от обхода)"

echo -e "${YELLOW}Применяем исправление для Docker bypass...${NC}"

# Проверяем существует ли файл
if [ ! -f /etc/ufw/after.rules ]; then
    echo -e "${RED}Ошибка: /etc/ufw/after.rules не найден${NC}"
    exit 1
fi

# Добавляем правила в конец файла (если их еще нет)
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

# Разрешить DNS ответы
-A DOCKER-USER -p udp -m udp --sport 53 --dport 1024:65535 -j RETURN

# Блокировать новые TCP соединения извне к Docker контейнерам
-A DOCKER-USER -p tcp -m tcp --tcp-flags FIN,SYN,RST,ACK SYN -d 192.168.0.0/16 -j DROP
-A DOCKER-USER -p tcp -m tcp --tcp-flags FIN,SYN,RST,ACK SYN -d 10.0.0.0/8 -j DROP
-A DOCKER-USER -p tcp -m tcp --tcp-flags FIN,SYN,RST,ACK SYN -d 172.16.0.0/12 -j DROP

# Блокировать UDP на низкие порты извне к Docker контейнерам
-A DOCKER-USER -p udp -m udp --dport 0:32767 -d 192.168.0.0/16 -j DROP
-A DOCKER-USER -p udp -m udp --dport 0:32767 -d 10.0.0.0/8 -j DROP
-A DOCKER-USER -p udp -m udp --dport 0:32767 -d 172.16.0.0/12 -j DROP

-A DOCKER-USER -j RETURN
COMMIT
# END UFW AND DOCKER
EOF
    echo -e "${GREEN}✓ Правила UFW+Docker добавлены${NC}"
else
    echo -e "${YELLOW}Правила UFW+Docker уже существуют${NC}"
fi

#==============================================================================
# ШАГ 6: ВКЛЮЧЕНИЕ UFW И ПЕРЕЗАПУСК SSH
#==============================================================================

print_step "[6/11] Включение firewall и перезапуск SSH"

# Включаем UFW без интерактивного подтверждения
echo -e "${YELLOW}Включение UFW...${NC}"
ufw --force enable
echo -e "${GREEN}✓ UFW активирован${NC}"

# Перезапускаем SSH
echo -e "${YELLOW}Перезапуск SSH...${NC}"
systemctl restart ssh

sleep 2
if ! systemctl is-active --quiet ssh; then
    echo -e "${RED}✗ SSH не запустился! Восстановление...${NC}"
    cp /etc/ssh/sshd_config.backup.* /etc/ssh/sshd_config
    systemctl restart ssh
    exit 1
fi

CURRENT_IP=$(hostname -I | awk '{print $1}')

echo -e "${GREEN}✓ SSH перезапущен на порту $NEW_SSH_PORT${NC}"
echo ""
echo -e "${YELLOW}${BOLD}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}${BOLD}║  ⚠️  НЕ ЗАКРЫВАЙТЕ это SSH-соединение до проверки нового!         ║${NC}"
echo -e "${YELLOW}${BOLD}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Откройте НОВЫЙ терминал и проверьте:${NC}"
echo ""
echo -e "${GREEN}ssh -p $NEW_SSH_PORT root@$CURRENT_IP${NC}"
echo ""

while true; do
    read -p "Новое SSH-соединение работает? (y/n): " confirm
    if [[ "$confirm" =~ ^([yY])$ ]]; then
        echo -e "${GREEN}✓ Отлично! Продолжаем...${NC}"
        break
    elif [[ "$confirm" =~ ^([nN])$ ]]; then
        echo -e "${RED}Восстановление конфигурации...${NC}"
        cp /etc/ssh/sshd_config.backup.* /etc/ssh/sshd_config
        systemctl restart ssh
        ufw delete allow $NEW_SSH_PORT/tcp
        ufw allow $CURRENT_SSH_PORT/tcp
        echo -e "${YELLOW}Восстановлено. Проверьте ошибку.${NC}"
        exit 1
    fi
done

#==============================================================================
# ШАГ 7: УСТАНОВКА FAIL2BAN (С УЧЕТОМ СМЕНЫ IP)
#==============================================================================

print_step "[7/11] Установка Fail2Ban (защита от брутфорса)"
apt install fail2ban -y

# Узнаем текущий IP пользователя
echo ""
echo -e "${YELLOW}Хотите добавить ваш текущий IP в белый список Fail2Ban?${NC}"
echo -e "${CYAN}(Ваш IP не будет блокироваться даже при неудачных попытках входа)${NC}"
echo ""
echo -e "Ваш текущий IP: ${GREEN}$SSH_CLIENT${NC}" | awk '{print $1}'
USER_IP=$(echo $SSH_CLIENT | awk '{print $1}')
echo ""
read -p "Добавить в белый список? (y/n): " whitelist_choice

IGNORE_IP="127.0.0.1/8 ::1"
if [[ "$whitelist_choice" =~ ^([yY])$ ]] && [ -n "$USER_IP" ]; then
    IGNORE_IP="127.0.0.1/8 ::1 $USER_IP"
    echo -e "${GREEN}✓ IP $USER_IP добавлен в белый список${NC}"
fi

# Конфигурация Fail2Ban с мягкими настройками
cat > /etc/fail2ban/jail.local <<EOF
[DEFAULT]
# Белый список IP (не блокируются)
ignoreip = $IGNORE_IP

# Увеличено время банов и уменьшено количество попыток
bantime = 1800        # 30 минут (вместо 1 часа)
findtime = 600        # 10 минут
maxretry = 10         # 10 попыток (вместо 5)

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

echo -e "${GREEN}✓ Fail2Ban настроен (мягкие параметры для частой смены IP)${NC}"
echo -e "${CYAN}  Maxretry: 10 попыток${NC}"
echo -e "${CYAN}  Bantime: 30 минут${NC}"
echo -e "${CYAN}  Белый список: $IGNORE_IP${NC}"

#==============================================================================
# ШАГ 8: ВКЛЮЧЕНИЕ TCP BBR
#==============================================================================

print_step "[8/11] Включение TCP BBR (ускорение VPN)"

if ! grep -q "net.core.default_qdisc" /etc/sysctl.conf; then
    echo "net.core.default_qdisc = fq" >> /etc/sysctl.conf
    echo "net.ipv4.tcp_congestion_control = bbr" >> /etc/sysctl.conf
    sysctl -p > /dev/null 2>&1
    echo -e "${GREEN}✓ TCP BBR включен${NC}"
else
    echo -e "${YELLOW}TCP BBR уже настроен${NC}"
fi

#==============================================================================
# ШАГ 9: АВТООБНОВЛЕНИЯ (БЕЗ ЯДРА)
#==============================================================================

print_step "[9/11] Настройка автообновлений (ядро исключено)"

apt install unattended-upgrades -y

# Создаем конфиг без автообновления ядра
cat > /etc/apt/apt.conf.d/50unattended-upgrades << 'EOF'
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
    "${distro_id}ESMApps:${distro_codename}-apps-security";
    "${distro_id}ESM:${distro_codename}-infra-security";
};

// НЕ обновлять ядро автоматически (может потребовать перезагрузку)
Unattended-Upgrade::Package-Blacklist {
    "linux-image-*";
    "linux-headers-*";
    "linux-modules-*";
};

// НЕ перезагружать автоматически
Unattended-Upgrade::Automatic-Reboot "false";

// Удалять неиспользуемые зависимости
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";
EOF

cat > /etc/apt/apt.conf.d/20auto-upgrades << 'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
APT::Periodic::Download-Upgradeable-Packages "1";
EOF

echo -e "${GREEN}✓ Автообновления настроены (ядро исключено из автообновлений)${NC}"

#==============================================================================
# ШАГ 10: ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ БЕЗОПАСНОСТИ
#==============================================================================

print_step "[10/11] Дополнительные настройки безопасности"

# Отключение IPv6 (опционально, для упрощения firewall)
echo ""
read -p "Отключить IPv6? (рекомендуется если не используете) (y/n): " ipv6_choice
if [[ "$ipv6_choice" =~ ^([yY])$ ]]; then
    cat >> /etc/sysctl.conf << 'EOF'
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1
net.ipv6.conf.lo.disable_ipv6 = 1
EOF
    sysctl -p > /dev/null 2>&1
    echo -e "${GREEN}✓ IPv6 отключен${NC}"
fi

# Защита от SYN flood
if ! grep -q "net.ipv4.tcp_syncookies" /etc/sysctl.conf; then
    echo "net.ipv4.tcp_syncookies = 1" >> /etc/sysctl.conf
    echo "net.ipv4.tcp_max_syn_backlog = 2048" >> /etc/sysctl.conf
    echo "net.ipv4.tcp_synack_retries = 2" >> /etc/sysctl.conf
    echo "net.ipv4.tcp_syn_retries = 5" >> /etc/sysctl.conf
    sysctl -p > /dev/null 2>&1
    echo -e "${GREEN}✓ Защита от SYN flood включена${NC}"
fi

#==============================================================================
# ШАГ 11: ФИНАЛЬНАЯ ПРОВЕРКА И ОТЧЕТ
#==============================================================================

print_step "[11/11] Финальная проверка системы"

# Проверка служб
echo -e "${CYAN}Проверка служб...${NC}"
systemctl is-active --quiet ssh && echo -e "  SSH: ${GREEN}Работает${NC}" || echo -e "  SSH: ${RED}Ошибка${NC}"
systemctl is-active --quiet ufw && echo -e "  UFW: ${GREEN}Работает${NC}" || echo -e "  UFW: ${RED}Ошибка${NC}"
systemctl is-active --quiet fail2ban && echo -e "  Fail2Ban: ${GREEN}Работает${NC}" || echo -e "  Fail2Ban: ${RED}Ошибка${NC}"

# Итоговый отчет
clear
echo -e "${GREEN}${BOLD}"
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                      ║"
echo "║                 ✓ НАСТРОЙКА УСПЕШНО ЗАВЕРШЕНА!                      ║"
echo "║                                                                      ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}\n"

echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}${BOLD}                      ИТОГОВЫЙ ОТЧЕТ                                  ${NC}"
echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════════════${NC}\n"

echo -e "${YELLOW}${BOLD}Изменения конфигурации:${NC}"
echo -e "  SSH порт:         ${RED}$CURRENT_SSH_PORT${NC} → ${GREEN}$NEW_SSH_PORT${NC}"
echo -e "  Root login:       ${GREEN}По SSH-ключу (prohibit-password)${NC}"
echo -e "  Пароли SSH:       ${GREEN}Отключены (только ключи)${NC}"
echo -e "  Firewall (UFW):   ${GREEN}Активен + Docker интеграция${NC}"
echo -e "  Fail2Ban:         ${GREEN}Активен (мягкие настройки)${NC}"
echo -e "  TCP BBR:          ${GREEN}Включен${NC}"
echo -e "  Автообновления:   ${GREEN}Включены (ядро исключено)${NC}\n"

echo -e "${YELLOW}${BOLD}Открытые порты:${NC}"
echo -e "  ${GREEN}$NEW_SSH_PORT/tcp${NC}  - SSH"
echo -e "  ${GREEN}443/tcp${NC}       - XRAY Reality (VLESS)"
echo -e "  ${GREEN}80/tcp${NC}        - HTTP (для certbot)\n"

echo -e "${YELLOW}${BOLD}Защита от Docker bypass:${NC}"
echo -e "  ${GREEN}✓${NC} UFW интегрирован с Docker"
echo -e "  ${GREEN}✓${NC} Публичный доступ к контейнерам блокирован"
echo -e "  ${GREEN}✓${NC} Внутренние сети Docker разрешены\n"

echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}${BOLD}                   СЛЕДУЮЩИЕ ШАГИ                                     ${NC}"
echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════════════${NC}\n"

echo -e "${GREEN}${BOLD}1. Для подключения используйте:${NC}"
echo -e "   ${CYAN}ssh -p $NEW_SSH_PORT root@$CURRENT_IP${NC}\n"

echo -e "${GREEN}${BOLD}2. Установите AmneziaVPN:${NC}"
echo -e "   • Скачайте клиент AmneziaVPN"
echo -e "   • Выберите: Self-hosted VPN"
echo -e "   • Введите данные подключения:"
echo -e "     IP: ${CYAN}$CURRENT_IP${NC}"
echo -e "     Port: ${CYAN}$NEW_SSH_PORT${NC}"
echo -e "     User: ${CYAN}root${NC}"
echo -e "     Auth: ${CYAN}SSH-ключ${NC}"
echo -e "   • Выберите протокол: ${CYAN}XRAY Reality (VLESS)${NC}"
echo -e "   • AmneziaVPN автоматически установит Docker и настроит VPN\n"

echo -e "${GREEN}${BOLD}3. После установки AmneziaVPN (опционально):${NC}"
echo -e "   Для дополнительной безопасности можете полностью запретить root:"
echo -e "   ${CYAN}sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config${NC}"
echo -e "   ${CYAN}systemctl restart ssh${NC}\n"

echo -e "${YELLOW}${BOLD}Полезные команды:${NC}"
echo -e "  Статус UFW:           ${CYAN}ufw status verbose${NC}"
echo -e "  Статус Fail2Ban:      ${CYAN}fail2ban-client status sshd${NC}"
echo -e "  Разблокировать IP:    ${CYAN}fail2ban-client set sshd unbanip IP${NC}"
echo -e "  Добавить IP в белый:  ${CYAN}nano /etc/fail2ban/jail.local${NC} (ignoreip)\n"

echo -e "${YELLOW}${BOLD}Бэкапы конфигураций:${NC}"
echo -e "  SSH: ${CYAN}/etc/ssh/sshd_config.backup.*${NC}\n"

echo -e "${GREEN}${BOLD}Можете безопасно закрыть старое SSH-соединение.${NC}\n"

echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════════════${NC}\n"

# Показать текущие правила UFW
echo -e "${YELLOW}Текущие правила UFW:${NC}"
ufw status numbered

echo ""
echo -e "${GREEN}Настройка завершена! Сервер готов к установке AmneziaVPN.${NC}"
echo ""
