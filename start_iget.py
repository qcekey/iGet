#!/usr/bin/env python
"""
Кастомный запуск iGet с предварительной настройкой asyncio
"""
import asyncio
import sys
import os

# ВАЖНО: Настройка asyncio должна быть САМОЙ ПЕРВОЙ
if sys.platform == 'win32':
    # Для Windows устанавливаем правильную политику event loop
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Явно создаем event loop перед любыми импортами
try:
    loop = asyncio.get_event_loop()
    print(f"Используется существующий event loop: {loop}")
except RuntimeError:
    # Если loop не существует - создаем новый
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    print(f"Создан новый event loop: {loop}")

# Теперь можно безопасно импортировать iGet
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Импортируем и запускаем
from iget.run import main

if __name__ == "__main__":
    main()