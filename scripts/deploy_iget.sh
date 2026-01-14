#!/bin/bash

# Скрипт полной замены job-stalker на iGet
# Использование: bash scripts/deploy_iget.sh

SERVER_IP="85.198.84.197"
SERVER_USER="root"
SERVER_PASSWORD="QV%LQ&dzXi9&"
OLD_PROJECT_DIR="/opt/job-stalker"
NEW_PROJECT_DIR="/opt/iget"
LOCAL_DIR="."

# Определяем способ SSH подключения
SSH_CMD="ssh"
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=10"

# Проверяем наличие sshpass
if command -v sshpass > /dev/null 2>&1; then
    SSH_CMD="sshpass -p '$SERVER_PASSWORD' ssh"
    echo "🔑 Используется sshpass для аутентификации"
elif [ -n "$SSH_PASSWORD" ]; then
    SSH_CMD="sshpass -p '$SSH_PASSWORD' ssh"
    echo "🔑 Используется пароль из переменной SSH_PASSWORD"
else
    echo "⚠️  sshpass не найден. Будет использован интерактивный ввод пароля."
    echo "   Для автоматизации установите sshpass: apt-get install sshpass (Linux) или brew install hudochenkov/sshpass/sshpass (Mac)"
    echo "   Или настройте SSH ключи для беспарольного доступа."
    echo ""
    SSH_CMD="ssh"
fi

# Функция для выполнения SSH команд
ssh_exec() {
    local cmd="$1"
    if command -v sshpass > /dev/null 2>&1; then
        sshpass -p "$SERVER_PASSWORD" ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" "$cmd"
    elif [ -n "$SSH_PASSWORD" ]; then
        sshpass -p "$SSH_PASSWORD" ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" "$cmd"
    else
        ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" "$cmd"
    fi
}

# Функция для выполнения SSH с heredoc
ssh_exec_heredoc() {
    local heredoc_content="$1"
    if command -v sshpass > /dev/null 2>&1; then
        sshpass -p "$SERVER_PASSWORD" ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" bash << 'ENDSSH'
            $heredoc_content
ENDSSH
    else
        ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" bash << 'ENDSSH'
            $heredoc_content
ENDSSH
    fi
}

echo "🔄 Замена job-stalker на iGet на сервере $SERVER_IP"
echo ""

# Проверка подключения
echo "📡 Проверка подключения к серверу..."
if ! ssh_exec "echo 'Connected'" > /dev/null 2>&1; then
    echo "❌ Не удалось подключиться к серверу."
    echo "   Проверьте:"
    echo "   1. Доступность сервера: ping $SERVER_IP"
    echo "   2. Правильность пароля: $SERVER_PASSWORD"
    echo "   3. Наличие sshpass для автоматической аутентификации"
    echo "   4. Или настройте SSH ключи для беспарольного доступа"
    exit 1
fi
echo "✅ Подключение установлено"
echo ""

# Остановка и удаление старого сервиса
echo "🗑️  Удаление старого job-stalker..."
if command -v sshpass > /dev/null 2>&1; then
    sshpass -p "$SERVER_PASSWORD" ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
        # Останавливаем старый сервис
        systemctl stop job-stalker 2>/dev/null || true
        systemctl disable job-stalker 2>/dev/null || true
        
        # Удаляем systemd сервис
        rm -f /etc/systemd/system/job-stalker.service
        systemctl daemon-reload
        
        # Делаем бэкап данных (если есть)
        if [ -d "/opt/job-stalker/data" ]; then
            echo "📦 Создание бэкапа данных..."
            mkdir -p /opt/backup
            tar -czf /opt/backup/job-stalker-data-backup-$(date +%Y%m%d_%H%M%S).tar.gz -C /opt/job-stalker data/ 2>/dev/null || true
            echo "✅ Бэкап создан в /opt/backup/"
        fi
        
        # Удаляем старую директорию
        if [ -d "/opt/job-stalker" ]; then
            rm -rf /opt/job-stalker
            echo "✅ Старая директория удалена"
        fi
ENDSSH
else
    ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
        # Останавливаем старый сервис
        systemctl stop job-stalker 2>/dev/null || true
        systemctl disable job-stalker 2>/dev/null || true
        
        # Удаляем systemd сервис
        rm -f /etc/systemd/system/job-stalker.service
        systemctl daemon-reload
        
        # Делаем бэкап данных (если есть)
        if [ -d "/opt/job-stalker/data" ]; then
            echo "📦 Создание бэкапа данных..."
            mkdir -p /opt/backup
            tar -czf /opt/backup/job-stalker-data-backup-$(date +%Y%m%d_%H%M%S).tar.gz -C /opt/job-stalker data/ 2>/dev/null || true
            echo "✅ Бэкап создан в /opt/backup/"
        fi
        
        # Удаляем старую директорию
        if [ -d "/opt/job-stalker" ]; then
            rm -rf /opt/job-stalker
            echo "✅ Старая директория удалена"
        fi
ENDSSH
fi
echo "✅ Старый job-stalker удален"
echo ""

# Создание новой директории
echo "📁 Создание новой директории для iGet..."
ssh_exec "mkdir -p $NEW_PROJECT_DIR && mkdir -p $NEW_PROJECT_DIR/data"
echo "✅ Директория создана"
echo ""

# Копирование файлов
echo "📤 Загрузка нового проекта iGet..."
if command -v sshpass > /dev/null 2>&1; then
    cd "$LOCAL_DIR" && tar --exclude='venv' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.git' \
        --exclude='*.log' \
        -czf - . | sshpass -p "$SERVER_PASSWORD" ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" "cd $NEW_PROJECT_DIR && tar -xzf -"
else
    cd "$LOCAL_DIR" && tar --exclude='venv' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.git' \
        --exclude='*.log' \
        -czf - . | ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" "cd $NEW_PROJECT_DIR && tar -xzf -"
fi
echo "✅ Файлы загружены"
echo ""

# Настройка Python окружения
echo "🐍 Настройка Python окружения..."
if command -v sshpass > /dev/null 2>&1; then
    sshpass -p "$SERVER_PASSWORD" ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
    cd /opt/iget
    
    # Создание виртуального окружения
    python3 -m venv venv
    source venv/bin/activate
    
    pip install --upgrade pip
    
    # Установка зависимостей
    if [ -f "requirements_parsers.txt" ]; then
        pip install -r requirements_parsers.txt
    fi
    # Основные зависимости для FastAPI и веб-сервера
    pip install fastapi uvicorn jinja2 python-multipart
    # Зависимости для парсеров
    pip install aiohttp selenium webdriver-manager beautifulsoup4
    # Telegram клиент
    pip install pyrogram tgcrypto
    # Модели данных
    pip install pydantic
    # Обработка файлов
    pip install pypdf python-docx
    # Системные утилиты
    pip install psutil
ENDSSH
else
    ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
    cd /opt/iget
    
    # Создание виртуального окружения
    python3 -m venv venv
    source venv/bin/activate
    
    pip install --upgrade pip
    
    # Установка зависимостей
    if [ -f "requirements_parsers.txt" ]; then
        pip install -r requirements_parsers.txt
    fi
    # Основные зависимости для FastAPI и веб-сервера
    pip install fastapi uvicorn jinja2 python-multipart
    # Зависимости для парсеров
    pip install aiohttp selenium webdriver-manager beautifulsoup4
    # Telegram клиент
    pip install pyrogram tgcrypto
    # Модели данных
    pip install pydantic
    # Обработка файлов
    pip install pypdf python-docx
    # Системные утилиты
    pip install psutil
ENDSSH
fi
echo "✅ Python окружение настроено"
echo ""

# Копирование iget из локального venv (если есть)
if [ -d "$LOCAL_DIR/venv/Lib/site-packages/iget" ]; then
    echo "📦 Копирование iget из локального venv..."
    if command -v sshpass > /dev/null 2>&1; then
        sshpass -p "$SERVER_PASSWORD" ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
            cd /opt/iget
            for site_pkg in venv/lib/python*/site-packages; do
                if [ -d "$site_pkg" ]; then
                    rm -rf "$site_pkg/iget"* 2>/dev/null || true
                fi
            done
ENDSSH
        
        cd "$LOCAL_DIR" && tar --exclude='__pycache__' --exclude='*.pyc' -czf - -C venv/Lib/site-packages iget iget*.dist-info 2>/dev/null | \
            sshpass -p "$SERVER_PASSWORD" ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" "cd /opt/iget && for site_pkg in venv/lib/python*/site-packages; do [ -d \"\$site_pkg\" ] && cd \"\$site_pkg\" && tar -xzf - && break; done"
    else
        ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
            cd /opt/iget
            for site_pkg in venv/lib/python*/site-packages; do
                if [ -d "$site_pkg" ]; then
                    rm -rf "$site_pkg/iget"* 2>/dev/null || true
                fi
            done
ENDSSH
        
        cd "$LOCAL_DIR" && tar --exclude='__pycache__' --exclude='*.pyc' -czf - -C venv/Lib/site-packages iget iget*.dist-info 2>/dev/null | \
            ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" "cd /opt/iget && for site_pkg in venv/lib/python*/site-packages; do [ -d \"\$site_pkg\" ] && cd \"\$site_pkg\" && tar -xzf - && break; done"
    fi
    
    echo "✅ iget скопирован"
fi

# Создание systemd сервиса
echo "⚙️  Создание systemd сервиса для iGet..."
if command -v sshpass > /dev/null 2>&1; then
    sshpass -p "$SERVER_PASSWORD" ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
    cat > /etc/systemd/system/iget.service << 'EOF'
[Unit]
Description=iGet Application
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/iget
Environment="PATH=/opt/iget/venv/bin"
ExecStart=/opt/iget/venv/bin/python /opt/iget/start_iget.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable iget
ENDSSH
else
    ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
    cat > /etc/systemd/system/iget.service << 'EOF'
[Unit]
Description=iGet Application
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/iget
Environment="PATH=/opt/iget/venv/bin"
ExecStart=/opt/iget/venv/bin/python /opt/iget/start_iget.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable iget
ENDSSH
fi
echo "✅ Systemd сервис создан"
echo ""

# Обновление Nginx конфигурации
echo "🌐 Обновление конфигурации Nginx..."
if command -v sshpass > /dev/null 2>&1; then
    sshpass -p "$SERVER_PASSWORD" ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
    # Определяем тип системы
    if [ -d "/etc/nginx/sites-available" ]; then
        # Ubuntu/Debian
        cat > /etc/nginx/sites-available/iget << 'NGINXEOF'
server {
    listen 80;
    server_name 85.198.84.197;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
NGINXEOF
        ln -sf /etc/nginx/sites-available/iget /etc/nginx/sites-enabled/
        rm -f /etc/nginx/sites-enabled/job-stalker 2>/dev/null || true
    else
        # CentOS/RHEL
        cat > /etc/nginx/conf.d/iget.conf << 'NGINXEOF'
server {
    listen 80;
    server_name 85.198.84.197;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
NGINXEOF
        rm -f /etc/nginx/conf.d/job-stalker.conf 2>/dev/null || true
    fi
    
    nginx -t && systemctl restart nginx || echo "⚠️  Nginx не запустился, но продолжаем..."
ENDSSH
else
    ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
    # Определяем тип системы
    if [ -d "/etc/nginx/sites-available" ]; then
        # Ubuntu/Debian
        cat > /etc/nginx/sites-available/iget << 'NGINXEOF'
server {
    listen 80;
    server_name 85.198.84.197;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
NGINXEOF
        ln -sf /etc/nginx/sites-available/iget /etc/nginx/sites-enabled/
        rm -f /etc/nginx/sites-enabled/job-stalker 2>/dev/null || true
    else
        # CentOS/RHEL
        cat > /etc/nginx/conf.d/iget.conf << 'NGINXEOF'
server {
    listen 80;
    server_name 85.198.84.197;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
NGINXEOF
        rm -f /etc/nginx/conf.d/job-stalker.conf 2>/dev/null || true
    fi
    
    nginx -t && systemctl restart nginx || echo "⚠️  Nginx не запустился, но продолжаем..."
ENDSSH
fi
echo "✅ Nginx настроен"
echo ""

# Запуск сервиса
echo "🚀 Запуск нового сервиса iGet..."
ssh_exec "systemctl start iget"
sleep 3
ssh_exec "systemctl status iget --no-pager -l | head -20"
echo ""

# Проверка статуса
echo "✅ Проверка статуса..."
sleep 2
if ssh_exec "systemctl is-active --quiet iget"; then
    echo "✅ iGet успешно установлен и запущен!"
    echo ""
    echo "🌐 Приложение доступно по адресам:"
    echo "   - http://85.198.84.197 (через Nginx)"
    echo "   - http://85.198.84.197:8000 (напрямую)"
    echo ""
    echo "📝 Полезные команды:"
    echo "   Просмотр логов: ssh $SERVER_USER@$SERVER_IP 'journalctl -u iget -f'"
    echo "   Статус: ssh $SERVER_USER@$SERVER_IP 'systemctl status iget'"
    echo ""
    echo "💾 Бэкап данных сохранен в /opt/backup/ (если был)"
else
    echo "❌ Ошибка при запуске. Проверьте логи:"
    echo "   ssh $SERVER_USER@$SERVER_IP 'journalctl -u iget -n 50'"
    exit 1
fi
