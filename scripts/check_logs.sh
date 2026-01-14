#!/bin/bash

# Скрипт для проверки логов и диагностики проблем
# Использование: bash scripts/check_logs.sh

SERVER_IP="85.198.84.197"
SERVER_USER="root"
SERVER_PASSWORD="QV%LQ&dzXi9&"

SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=10"

echo "📋 Проверка логов и диагностика проблем..."
echo ""

if command -v sshpass > /dev/null 2>&1; then
    echo "=== Последние 50 строк логов ==="
    sshpass -p "$SERVER_PASSWORD" ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" "journalctl -u iget -n 50 --no-pager"
    
    echo ""
    echo "=== Проверка установленных пакетов ==="
    sshpass -p "$SERVER_PASSWORD" ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
        cd /opt/iget
        source venv/bin/activate
        echo "Python: $(which python)"
        echo "Python version: $(python --version)"
        echo ""
        echo "Проверка ключевых пакетов:"
        python -c "import pyrogram; print('✅ pyrogram:', pyrogram.__version__)" 2>&1 || echo "❌ pyrogram не установлен"
        python -c "import psutil; print('✅ psutil:', psutil.__version__)" 2>&1 || echo "❌ psutil не установлен"
        python -c "import fastapi; print('✅ fastapi:', fastapi.__version__)" 2>&1 || echo "❌ fastapi не установлен"
        python -c "import pydantic; print('✅ pydantic:', pydantic.__version__)" 2>&1 || echo "❌ pydantic не установлен"
        python -c "import uvicorn; print('✅ uvicorn:', uvicorn.__version__)" 2>&1 || echo "❌ uvicorn не установлен"
ENDSSH
    
    echo ""
    echo "=== Попытка запуска вручную для диагностики ==="
    sshpass -p "$SERVER_PASSWORD" ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
        cd /opt/iget
        source venv/bin/activate
        echo "Попытка импорта основных модулей..."
        python -c "from iget.run import main; print('✅ Импорт успешен')" 2>&1 | head -20
ENDSSH
else
    echo "=== Последние 50 строк логов ==="
    ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" "journalctl -u iget -n 50 --no-pager"
    
    echo ""
    echo "=== Проверка установленных пакетов ==="
    ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
        cd /opt/iget
        source venv/bin/activate
        echo "Python: $(which python)"
        echo "Python version: $(python --version)"
        echo ""
        echo "Проверка ключевых пакетов:"
        python -c "import pyrogram; print('✅ pyrogram:', pyrogram.__version__)" 2>&1 || echo "❌ pyrogram не установлен"
        python -c "import psutil; print('✅ psutil:', psutil.__version__)" 2>&1 || echo "❌ psutil не установлен"
        python -c "import fastapi; print('✅ fastapi:', fastapi.__version__)" 2>&1 || echo "❌ fastapi не установлен"
        python -c "import pydantic; print('✅ pydantic:', pydantic.__version__)" 2>&1 || echo "❌ pydantic не установлен"
        python -c "import uvicorn; print('✅ uvicorn:', uvicorn.__version__)" 2>&1 || echo "❌ uvicorn не установлен"
ENDSSH
    
    echo ""
    echo "=== Попытка запуска вручную для диагностики ==="
    ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
        cd /opt/iget
        source venv/bin/activate
        echo "Попытка импорта основных модулей..."
        python -c "from iget.run import main; print('✅ Импорт успешен')" 2>&1 | head -20
ENDSSH
fi

echo ""
echo "✅ Диагностика завершена"
