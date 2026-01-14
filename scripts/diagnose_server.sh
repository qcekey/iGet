#!/bin/bash

# Команды для диагностики на сервере
# Скопируйте и выполните эти команды на сервере

cat << 'EOF'
# ============================================
# ДИАГНОСТИКА НА СЕРВЕРЕ
# Выполните эти команды на сервере:
# ============================================

cd /opt/iget
source venv/bin/activate

echo "=== Проверка Python ==="
which python
python --version

echo ""
echo "=== Проверка установленных пакетов ==="
python -c "import pyrogram; print('✅ pyrogram:', pyrogram.__version__)" 2>&1
python -c "import psutil; print('✅ psutil:', psutil.__version__)" 2>&1
python -c "import fastapi; print('✅ fastapi:', fastapi.__version__)" 2>&1
python -c "import pydantic; print('✅ pydantic:', pydantic.__version__)" 2>&1
python -c "import uvicorn; print('✅ uvicorn:', uvicorn.__version__)" 2>&1
python -c "import jinja2; print('✅ jinja2:', jinja2.__version__)" 2>&1

echo ""
echo "=== Попытка импорта iget ==="
python -c "from iget.run import main; print('✅ Импорт успешен')" 2>&1

echo ""
echo "=== Последние логи ==="
journalctl -u iget -n 30 --no-pager

EOF
