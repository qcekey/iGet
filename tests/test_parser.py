# test_parser.py в папке iget-data
import asyncio
import sys
from pyrogram import Client
from dotenv import load_dotenv
import os

load_dotenv()

async def test_telegram():
    """Тестируем подключение к Telegram"""
    print("=" * 60)
    print("ТЕСТ ПОДКЛЮЧЕНИЯ К TELEGRAM")
    print("=" * 60)
    
    async with Client(
        "test_session",
        api_id=int(os.getenv("API_ID")),
        api_hash=os.getenv("API_HASH"),
    ) as app:
        # Проверяем авторизацию
        me = await app.get_me()
        print(f"✅ Авторизован как: {me.first_name}")
        
        # Тестируем каналы
        test_channels = ["@hh_ru", "@rabota_ru", "@job_rus"]
        
        for channel in test_channels:
            print(f"\n📢 Проверяем канал: {channel}")
            try:
                # Пробуем получить информацию о канале
                chat = await app.get_chat(channel)
                print(f"   Название: {chat.title}")
                print(f"   Участников: {chat.members_count if hasattr(chat, 'members_count') else 'N/A'}")
                
                # Пробуем получить последние сообщения
                print(f"   Получаем сообщения...")
                count = 0
                async for message in app.get_chat_history(chat.id, limit=5):
                    if hasattr(message, 'text') and message.text:
                        # Проверяем на ключевые слова о вакансиях
                        text_lower = message.text.lower()
                        if any(word in text_lower for word in ['ваканс', 'работа', 'требуется', 'ищем', 'найм']):
                            print(f"   ✅ Вакансия найдена: {message.text[:80]}...")
                        else:
                            print(f"   📄 Сообщение: {message.text[:80]}...")
                        count += 1
                
                print(f"   📊 Получено сообщений: {count}")
                
            except Exception as e:
                print(f"   ❌ Ошибка: {type(e).__name__}: {str(e)[:100]}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(test_telegram())