#!/bin/bash

# Скрипт для установки недостающих зависимостей на сервере
# Использование: bash scripts/install_dependencies.sh

SERVER_IP="85.198.84.197"
SERVER_USER="root"
SERVER_PASSWORD="QV%LQ&dzXi9&"
PROJECT_DIR="/opt/iget"

SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=10"

echo "📦 Установка недостающих зависимостей на сервере $SERVER_IP"
echo ""

# Определяем способ SSH подключения
if command -v sshpass > /dev/null 2>&1; then
    SSH_CMD="sshpass -p '$SERVER_PASSWORD' ssh"
    echo "🔑 Используется sshpass для аутентификации"
elif [ -n "$SSH_PASSWORD" ]; then
    SSH_CMD="sshpass -p '$SSH_PASSWORD' ssh"
    echo "🔑 Используется пароль из переменной SSH_PASSWORD"
else
    echo "⚠️  sshpass не найден. Будет использован интерактивный ввод пароля."
    SSH_CMD="ssh"
fi

# Установка зависимостей
echo "🐍 Установка зависимостей Python..."
if command -v sshpass > /dev/null 2>&1; then
    sshpass -p "$SERVER_PASSWORD" ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
        cd /opt/iget
        source venv/bin/activate
        
        echo "📦 Установка недостающих пакетов..."
        pip install --upgrade pip
        pip install psutil jinja2 python-multipart pyrogram tgcrypto pydantic pypdf python-docx
        
        echo "✅ Зависимости установлены"
ENDSSH
else
    ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
        cd /opt/iget
        source venv/bin/activate
        
        echo "📦 Установка недостающих пакетов..."
        pip install --upgrade pip
        pip install psutil jinja2 python-multipart pyrogram tgcrypto pydantic pypdf python-docx
        
        echo "✅ Зависимости установлены"
ENDSSH
fi

echo ""
echo "🔄 Перезапуск сервиса..."
if command -v sshpass > /dev/null 2>&1; then
    sshpass -p "$SERVER_PASSWORD" ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" "systemctl restart iget"
else
    ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" "systemctl restart iget"
fi

sleep 3

echo ""
echo "✅ Проверка статуса..."
if command -v sshpass > /dev/null 2>&1; then
    sshpass -p "$SERVER_PASSWORD" ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" "systemctl status iget --no-pager -l | head -20"
else
    ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" "systemctl status iget --no-pager -l | head -20"
fi

echo ""
echo "✅ Готово! Проверьте логи выше на наличие ошибок."
