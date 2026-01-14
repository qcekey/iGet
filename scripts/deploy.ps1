# PowerShell скрипт для развертывания iGet на сервере
# Использование: .\deploy.ps1

$SERVER_IP = "85.198.84.197"
$SERVER_USER = "root"
$SERVER_PASSWORD = "QV%LQ&dzXi9&"
$PROJECT_DIR = "/opt/iget"
$LOCAL_DIR = "."

Write-Host "🚀 Начало развертывания iGet на сервере $SERVER_IP" -ForegroundColor Green
Write-Host ""

# Функция для выполнения SSH команд
function Invoke-SSHCommand {
    param(
        [string]$Command,
        [string]$Server = "$SERVER_USER@$SERVER_IP"
    )
    
    $sshCommand = "ssh -o StrictHostKeyChecking=no $Server `"$Command`""
    Write-Host "Выполняется: $Command" -ForegroundColor Gray
    
    # Используем plink или ssh с паролем через expect-подобный механизм
    # Для Windows можно использовать Posh-SSH модуль или просто ssh с ключами
    try {
        # Попробуем использовать ssh с передачей через stdin
        $Command | ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" 2>&1
    } catch {
        Write-Host "Ошибка выполнения SSH команды. Убедитесь, что SSH настроен." -ForegroundColor Red
        return $false
    }
}

# Проверка подключения
Write-Host "📡 Проверка подключения к серверу..." -ForegroundColor Yellow
try {
    $testConnection = Test-Connection -ComputerName $SERVER_IP -Count 1 -Quiet
    if ($testConnection) {
        Write-Host "✅ Сервер доступен" -ForegroundColor Green
    } else {
        Write-Host "❌ Сервер недоступен" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "⚠️  Не удалось проверить доступность сервера. Продолжаем..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📝 Для автоматического развертывания используйте один из вариантов:" -ForegroundColor Cyan
Write-Host ""
Write-Host "Вариант 1: Используйте WSL или Git Bash для запуска deploy.sh" -ForegroundColor Yellow
Write-Host "   wsl bash deploy.sh" -ForegroundColor White
Write-Host "   или" -ForegroundColor White
Write-Host "   bash deploy.sh  (в Git Bash)" -ForegroundColor White
Write-Host ""
Write-Host "Вариант 2: Выполните команды вручную (см. РАЗВЕРТЫВАНИЕ.md)" -ForegroundColor Yellow
Write-Host ""
Write-Host "Вариант 3: Используйте SSH вручную:" -ForegroundColor Yellow
Write-Host "   ssh root@85.198.84.197" -ForegroundColor White
Write-Host "   Пароль: QV%LQ&dzXi9&" -ForegroundColor White
Write-Host ""

# Инструкции по ручному развертыванию
Write-Host "📋 Команды для выполнения на сервере:" -ForegroundColor Cyan
Write-Host ""
Write-Host "# 1. Установка зависимостей" -ForegroundColor Gray
Write-Host "apt update && apt install -y python3 python3-pip python3-venv git curl wget nginx" -ForegroundColor White
Write-Host ""
Write-Host "# 2. Установка Chrome" -ForegroundColor Gray
Write-Host "wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -" -ForegroundColor White
Write-Host "echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' > /etc/apt/sources.list.d/google-chrome.list" -ForegroundColor White
Write-Host "apt update && apt install -y google-chrome-stable" -ForegroundColor White
Write-Host ""
Write-Host "# 3. Создание директории" -ForegroundColor Gray
Write-Host "mkdir -p $PROJECT_DIR && mkdir -p $PROJECT_DIR/data" -ForegroundColor White
Write-Host ""

Write-Host "📤 Для загрузки файлов используйте (с этого компьютера):" -ForegroundColor Cyan
Write-Host ""
Write-Host "# Через SCP" -ForegroundColor Gray
Write-Host "scp -r $LOCAL_DIR\* root@$SERVER_IP`:$PROJECT_DIR/" -ForegroundColor White
Write-Host ""
Write-Host "# Или через rsync (в WSL/Git Bash)" -ForegroundColor Gray
Write-Host "rsync -avz --exclude 'venv' --exclude '__pycache__' --exclude '*.pyc' $LOCAL_DIR/ root@$SERVER_IP`:$PROJECT_DIR/" -ForegroundColor White
Write-Host ""

Write-Host "✅ Подробные инструкции см. в файле РАЗВЕРТЫВАНИЕ.md" -ForegroundColor Green
