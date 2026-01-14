#!/bin/bash

# Скрипт автоматического обновления iGet на сервере
# Использование: bash update.sh

SERVER_IP="85.198.84.197"
SERVER_USER="root"
PROJECT_DIR="/opt/iget"
LOCAL_DIR="."

echo "🔄 Обновление iGet на сервере $SERVER_IP"
echo ""

# Проверка подключения
echo "📡 Проверка подключения к серверу..."
if ! ssh -o ConnectTimeout=5 "$SERVER_USER@$SERVER_IP" "echo 'Connected'" > /dev/null 2>&1; then
    echo "❌ Не удалось подключиться к серверу. Проверьте подключение и учетные данные."
    exit 1
fi
echo "✅ Подключение установлено"
echo ""

# Остановка сервиса
echo "⏸️  Остановка сервиса..."
ssh "$SERVER_USER@$SERVER_IP" "systemctl stop iget || true"
echo "✅ Сервис остановлен"
echo ""

# Копирование файлов
echo "📤 Загрузка обновленных файлов..."
cd "$LOCAL_DIR" && tar --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='*.log' \
    --exclude='data/*.session' \
    --exclude='data/*.db' \
    -czf - . | ssh "$SERVER_USER@$SERVER_IP" "cd $PROJECT_DIR && tar -xzf -"
echo "✅ Файлы загружены"
echo ""

# Обновление зависимостей и копирование iget
echo "📦 Обновление зависимостей Python и копирование iget..."
ssh "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
    cd /opt/iget
    source venv/bin/activate
    
    # Удаляем установленный пакет iget, чтобы использовать локальный код
    pip uninstall iget -y 2>/dev/null || true
    
    pip install --upgrade pip
    if [ -f "requirements_parsers.txt" ]; then
        pip install -r requirements_parsers.txt --upgrade
    fi
    pip install fastapi uvicorn aiohttp selenium webdriver-manager beautifulsoup4 --upgrade || true
ENDSSH

# Копирование iget из локального venv (если есть)
if [ -d "$LOCAL_DIR/venv/Lib/site-packages/iget" ]; then
    echo "📦 Копирование обновленного iget из локального venv..."
    ssh "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
        cd /opt/iget
        # Находим директорию site-packages и удаляем старую версию
        for site_pkg in venv/lib/python*/site-packages; do
            if [ -d "$site_pkg" ]; then
                rm -rf "$site_pkg/iget"* 2>/dev/null || true
            fi
        done
ENDSSH
    
    # Копируем iget на сервер
    cd "$LOCAL_DIR" && tar --exclude='__pycache__' --exclude='*.pyc' -czf - -C venv/Lib/site-packages iget iget*.dist-info 2>/dev/null | \
        ssh "$SERVER_USER@$SERVER_IP" "cd /opt/iget && for site_pkg in venv/lib/python*/site-packages; do [ -d \"\$site_pkg\" ] && cd \"\$site_pkg\" && tar -xzf - && break; done"

    echo "✅ iget скопирован из локального venv"
elif [ -d "$LOCAL_DIR/venv/lib/python"*/site-packages/iget ]; then
    echo "📦 Копирование обновленного iget из локального venv (Linux путь)..."
    IGET_PATH=$(find "$LOCAL_DIR/venv/lib" -type d -name "iget" -path "*/site-packages/*" | head -1)
    if [ -n "$IGET_PATH" ]; then
        SITE_PACKAGES_DIR=$(dirname "$IGET_PATH")
        ssh "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
            cd /opt/iget
            for site_pkg in venv/lib/python*/site-packages; do
                if [ -d "$site_pkg" ]; then
                    rm -rf "$site_pkg/iget"* 2>/dev/null || true
                fi
            done
ENDSSH
        
        cd "$LOCAL_DIR" && tar --exclude='__pycache__' --exclude='*.pyc' -czf - -C "$SITE_PACKAGES_DIR" iget iget*.dist-info 2>/dev/null | \
            ssh "$SERVER_USER@$SERVER_IP" "cd /opt/iget && for site_pkg in venv/lib/python*/site-packages; do [ -d \"\$site_pkg\" ] && cd \"\$site_pkg\" && tar -xzf - && break; done"
        
        echo "✅ iget скопирован из локального venv"
    fi
fi

echo "✅ Зависимости обновлены"
echo ""

# Перезапуск сервиса
echo "🚀 Перезапуск сервиса..."
ssh "$SERVER_USER@$SERVER_IP" "systemctl start iget"
sleep 3
ssh "$SERVER_USER@$SERVER_IP" "systemctl status iget --no-pager -l | head -20"
echo ""

# Проверка статуса
echo "✅ Проверка статуса..."
sleep 2
if ssh "$SERVER_USER@$SERVER_IP" "systemctl is-active --quiet iget"; then
    echo "✅ Проект успешно обновлен и запущен!"
    echo ""
    echo "🌐 Приложение доступно по адресам:"
    echo "   - http://85.198.84.197 (через Nginx)"
    echo "   - http://85.198.84.197:8000 (напрямую)"
    echo ""
    echo "📝 Полезные команды:"
    echo "   Просмотр логов: ssh $SERVER_USER@$SERVER_IP 'journalctl -u iget -f'"
    echo "   Статус: ssh $SERVER_USER@$SERVER_IP 'systemctl status iget'"
else
    echo "❌ Ошибка при запуске. Проверьте логи:"
    echo "   ssh $SERVER_USER@$SERVER_IP 'journalctl -u iget -n 50'"
    exit 1
fi
