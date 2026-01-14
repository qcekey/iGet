# 🚀 Инструкция по развертыванию iGet на сервере

## 📋 Подготовка

### Шаг 1: Подключение к серверу

Используйте SSH для подключения к серверу:

```bash
ssh root@85.198.84.197
```

При запросе пароля введите: `QV%LQ&dzXi9&`

---

## 🔧 Установка зависимостей на сервере

### Шаг 2: Обновление системы

```bash
# Для Ubuntu/Debian
apt update && apt upgrade -y

# Для CentOS/RHEL
yum update -y
```

### Шаг 3: Установка Python и необходимых инструментов

```bash
# Для Ubuntu/Debian
apt install -y python3 python3-pip python3-venv git curl

# Для CentOS/RHEL
yum install -y python3 python3-pip git curl
```

### Шаг 4: Установка Chrome и ChromeDriver (для LinkedIn парсера)

```bash
# Для Ubuntu/Debian
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
apt update
apt install -y google-chrome-stable

# Для CentOS/RHEL
yum install -y wget
wget https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm
yum localinstall -y google-chrome-stable_current_x86_64.rpm
```

---

## 📦 Загрузка проекта на сервер

### Шаг 5: Создание директории для проекта

```bash
mkdir -p /opt/iget
cd /opt/iget
```

### Шаг 6: Загрузка файлов проекта

**Вариант A: Через SCP (с вашего локального компьютера)**

Откройте новый терминал на вашем локальном компьютере и выполните:

```bash
# Windows PowerShell
scp -r C:\Users\FreakNick\Desktop\iget-data\* root@85.198.84.197:/opt/iget/

# Linux/Mac
scp -r ~/Desktop/iget-data/* root@85.198.84.197:/opt/iget/
```

**Вариант B: Через Git (если проект в репозитории)**

```bash
cd /opt/iget
git clone <ваш-репозиторий> .
```

**Вариант C: Через rsync (рекомендуется)**

```bash
# С вашего локального компьютера
rsync -avz --exclude 'venv' --exclude '__pycache__' --exclude '*.pyc' \
  C:\Users\FreakNick\Desktop\iget-data\ root@85.198.84.197:/opt/iget/
```

---

## 🐍 Настройка Python окружения

### Шаг 7: Создание виртуального окружения

```bash
cd /opt/iget
python3 -m venv venv
source venv/bin/activate
```

### Шаг 8: Установка зависимостей

Сначала нужно установить основной пакет `iget` (если он установлен через pip):

```bash
# Если iget установлен как пакет
pip install --upgrade pip
pip install iget  # или путь к вашему пакету

# Установка дополнительных зависимостей для парсеров
pip install -r requirements_parsers.txt

# Если есть основной requirements.txt
# pip install -r requirements.txt
```

**Примечание:** Если `iget` находится в `venv/Lib/site-packages/`, возможно, он уже установлен локально. В этом случае убедитесь, что все зависимости установлены.

---

## ⚙️ Настройка приложения

### Шаг 9: Создание директории для данных

```bash
mkdir -p /opt/iget/data
chmod 755 /opt/iget/data
```

### Шаг 10: Копирование файла настроек

Если у вас уже есть `data/settings.json`, он должен быть скопирован. Если нет, создайте его:

```bash
# Проверьте наличие файла
ls -la /opt/iget/data/settings.json

# Если файла нет, создайте базовый
cat > /opt/iget/data/settings.json << 'EOF'
{
  "model_type": "mistral7",
  "days_back": 30,
  "custom_prompt": "",
  "resume_summary": "",
  "channels": ["opento_igaming"],
  "enable_stage2": false,
  "keyword_filter": "",
  "search_mode": "basic",
  "enable_headhunter": true,
  "hh_search_query": "",
  "hh_area": 113,
  "hh_max_pages": 2,
  "enable_linkedin": false,
  "linkedin_search_query": "",
  "linkedin_location": "",
  "linkedin_email": "",
  "linkedin_password": "",
  "enable_telegram": false
}
EOF
```

---

## 🔥 Настройка Firewall

### Шаг 11: Открытие порта 8000

```bash
# Для Ubuntu/Debian с ufw
ufw allow 8000/tcp
ufw reload

# Для CentOS/RHEL с firewalld
firewall-cmd --permanent --add-port=8000/tcp
firewall-cmd --reload

# Или для iptables
iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
iptables-save
```

---

## 🚀 Запуск приложения

### Шаг 12: Тестовый запуск

```bash
cd /opt/iget
source venv/bin/activate
python start_jobstalker.py
```

Приложение должно запуститься и быть доступным по адресу: `http://85.198.84.197:8000`

Если всё работает, остановите приложение (Ctrl+C) и переходите к следующему шагу.

---

## 🔄 Настройка автозапуска (Systemd)

### Шаг 13: Создание systemd сервиса

```bash
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
```

### Шаг 14: Запуск и включение сервиса

```bash
# Перезагрузка systemd
systemctl daemon-reload

# Запуск сервиса
systemctl start iget

# Включение автозапуска при загрузке системы
systemctl enable iget

# Проверка статуса
systemctl status iget

# Просмотр логов
journalctl -u iget -f
```

---

## 🌐 Настройка Nginx (опционально, но рекомендуется)

### Шаг 15: Установка Nginx

```bash
# Ubuntu/Debian
apt install -y nginx

# CentOS/RHEL
yum install -y nginx
```

### Шаг 16: Создание конфигурации Nginx

```bash
cat > /etc/nginx/sites-available/iget << 'EOF'
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
EOF
```

### Шаг 17: Активация конфигурации

```bash
# Ubuntu/Debian
ln -s /etc/nginx/sites-available/iget /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx

# CentOS/RHEL (используйте /etc/nginx/conf.d/)
cp /etc/nginx/sites-available/iget /etc/nginx/conf.d/iget.conf
nginx -t
systemctl restart nginx
```

### Шаг 18: Открытие порта 80 в firewall

```bash
# Ubuntu/Debian
ufw allow 80/tcp
ufw allow 443/tcp

# CentOS/RHEL
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --reload
```

Теперь приложение будет доступно по адресу: `http://85.198.84.197`

---

## 🔒 Настройка SSL (опционально, но рекомендуется для продакшена)

### Шаг 19: Установка Certbot

```bash
# Ubuntu/Debian
apt install -y certbot python3-certbot-nginx

# CentOS/RHEL
yum install -y certbot python3-certbot-nginx
```

### Шаг 20: Получение SSL сертификата

```bash
# Если у вас есть доменное имя
certbot --nginx -d your-domain.com

# Или для IP-адреса (требует специальной настройки)
# certbot certonly --standalone -d 85.198.84.197
```

---

## 📝 Полезные команды для управления

### Управление сервисом

```bash
# Запуск
systemctl start iget

# Остановка
systemctl stop iget

# Перезапуск
systemctl restart iget

# Статус
systemctl status iget

# Просмотр логов
journalctl -u iget -f
journalctl -u iget --since "1 hour ago"
```

### Обновление приложения

```bash
cd /opt/iget
source venv/bin/activate

# Остановите сервис
systemctl stop iget

# Обновите код (через git, scp, rsync и т.д.)
# ...

# Обновите зависимости (если нужно)
pip install -r requirements_parsers.txt --upgrade

# Запустите сервис
systemctl start iget
```

---

## 🐛 Решение проблем

### Проблема: Приложение не запускается

1. Проверьте логи:
   ```bash
   journalctl -u iget -n 50
   ```

2. Проверьте, что все зависимости установлены:
   ```bash
   cd /opt/iget
   source venv/bin/activate
   python -c "import iget; print('OK')"
   ```

3. Проверьте права доступа:
   ```bash
   ls -la /opt/iget/data/
   chmod 755 /opt/iget/data
   ```

### Проблема: Не могу подключиться к приложению

1. Проверьте, что приложение запущено:
   ```bash
   systemctl status iget
   netstat -tlnp | grep 8000
   ```

2. Проверьте firewall:
   ```bash
   ufw status
   # или
   firewall-cmd --list-all
   ```

3. Проверьте, что порт открыт извне:
   ```bash
   curl http://localhost:8000
   ```

### Проблема: LinkedIn парсер не работает

1. Убедитесь, что Chrome установлен:
   ```bash
   google-chrome --version
   ```

2. Для headless режима может потребоваться установка дополнительных пакетов:
   ```bash
   apt install -y xvfb  # для виртуального дисплея
   ```

---

## 📊 Мониторинг

### Проверка использования ресурсов

```bash
# CPU и память
htop

# Дисковое пространство
df -h

# Логи приложения
tail -f /var/log/syslog | grep iget
```

---

## ✅ Чек-лист развертывания

- [ ] Подключение к серверу выполнено
- [ ] Python 3 и pip установлены
- [ ] Chrome установлен (для LinkedIn парсера)
- [ ] Проект загружен на сервер
- [ ] Виртуальное окружение создано
- [ ] Зависимости установлены
- [ ] Файл настроек создан/скопирован
- [ ] Порт 8000 открыт в firewall
- [ ] Приложение запускается вручную
- [ ] Systemd сервис создан и запущен
- [ ] Nginx настроен (опционально)
- [ ] SSL настроен (опционально)
- [ ] Приложение доступно извне

---

## 🎉 Готово!

После выполнения всех шагов ваше приложение будет доступно по адресу:
- **С Nginx:** `http://85.198.84.197` (или `https://...` с SSL)
- **Без Nginx:** `http://85.198.84.197:8000`

Приложение будет автоматически запускаться при перезагрузке сервера.
