#!/bin/bash

# Быстрый скрипт для установки зависимостей напрямую
# Использование: bash scripts/fix_dependencies.sh

SERVER_IP="85.198.84.197"
SERVER_USER="root"
SERVER_PASSWORD="QV%LQ&dzXi9&"

SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=10"

echo "🔧 Установка зависимостей на сервере..."
echo ""

# Установка зависимостей напрямую
if command -v sshpass > /dev/null 2>&1; then
    sshpass -p "$SERVER_PASSWORD" ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
        cd /opt/iget
        source venv/bin/activate
        
        echo "📦 Обновление pip..."
        pip install --upgrade pip
        
        echo "📦 Установка всех зависимостей..."
        pip install psutil jinja2 python-multipart
        pip install pyrogram tgcrypto
        pip install pydantic
        pip install pypdf python-docx
        pip install fastapi uvicorn
        pip install aiohttp selenium webdriver-manager beautifulsoup4
        
        echo "✅ Проверка установки pyrogram..."
        python -c "import pyrogram; print('pyrogram установлен:', pyrogram.__version__)" || echo "❌ Ошибка импорта pyrogram"
        
        echo "✅ Зависимости установлены"
ENDSSH
else
    ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
        cd /opt/iget
        source venv/bin/activate
        
        echo "📦 Обновление pip..."
        pip install --upgrade pip
        
        echo "📦 Установка всех зависимостей..."
        pip install psutil jinja2 python-multipart
        pip install pyrogram tgcrypto
        pip install pydantic
        pip install pypdf python-docx
        pip install fastapi uvicorn
        pip install aiohttp selenium webdriver-manager beautifulsoup4
        
        echo "✅ Проверка установки pyrogram..."
        python -c "import pyrogram; print('pyrogram установлен:', pyrogram.__version__)" || echo "❌ Ошибка импорта pyrogram"
        
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

sleep 5

echo ""
echo "✅ Проверка статуса..."
if command -v sshpass > /dev/null 2>&1; then
    sshpass -p "$SERVER_PASSWORD" ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" "systemctl status iget --no-pager -l | head -30"
else
    ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" "systemctl status iget --no-pager -l | head -30"
fi

echo ""
echo "✅ Готово!"
