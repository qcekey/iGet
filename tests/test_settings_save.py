"""
Тестовый скрипт для проверки сохранения настроек парсеров
"""
import sys
import os
import json
import codecs

# Настройка кодировки для Windows
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from iget.models import AppSettings
    from pathlib import Path
    
    print("=" * 60)
    print("ТЕСТ СОХРАНЕНИЯ НАСТРОЕК ПАРСЕРОВ")
    print("=" * 60)
    
    # Проверяем модель
    print("\n📋 Проверяем модель AppSettings...")
    
    # Создаем тестовые настройки с парсерами
    test_settings = {
        "model_type": "mistral7",
        "days_back": 30,
        "channels": ["test_channel"],
        "enable_headhunter": True,
        "hh_search_query": "Python разработчик",
        "hh_area": 1,
        "hh_max_pages": 5,
        "enable_linkedin": True,
        "linkedin_search_query": "Python Developer",
        "linkedin_location": "Moscow, Russia"
    }
    
    print("\n🧪 Тестовые настройки:")
    for key, value in test_settings.items():
        print(f"   {key}: {value}")
    
    # Пробуем создать модель
    try:
        settings = AppSettings(**test_settings)
        print("\n✅ Модель AppSettings приняла настройки парсеров!")
        
        # Проверяем, что поля есть
        print("\n📊 Проверяем поля модели:")
        print(f"   enable_headhunter: {settings.enable_headhunter}")
        print(f"   hh_search_query: {settings.hh_search_query}")
        print(f"   enable_linkedin: {settings.enable_linkedin}")
        print(f"   linkedin_search_query: {settings.linkedin_search_query}")
        
        # Пробуем получить словарь
        if hasattr(settings, 'model_dump'):
            settings_dict = settings.model_dump()
        else:
            settings_dict = settings.dict()
        
        print("\n✅ Настройки успешно преобразованы в словарь!")
        print(f"   enable_headhunter в словаре: {settings_dict.get('enable_headhunter')}")
        print(f"   enable_linkedin в словаре: {settings_dict.get('enable_linkedin')}")
        
    except Exception as e:
        print(f"\n❌ Ошибка при создании модели: {e}")
        import traceback
        traceback.print_exc()
    
    # Проверяем текущий файл настроек
    settings_file = Path("data/settings.json")
    if settings_file.exists():
        print("\n📁 Текущий файл settings.json:")
        with open(settings_file, "r", encoding="utf-8") as f:
            current_settings = json.load(f)
        
        print(f"   enable_headhunter: {current_settings.get('enable_headhunter', 'NOT FOUND')}")
        print(f"   enable_linkedin: {current_settings.get('enable_linkedin', 'NOT FOUND')}")
        print(f"   hh_search_query: {current_settings.get('hh_search_query', 'NOT FOUND')}")
        print(f"   linkedin_search_query: {current_settings.get('linkedin_search_query', 'NOT FOUND')}")
    
    print("\n" + "=" * 60)
    print("РЕКОМЕНДАЦИИ")
    print("=" * 60)
    print("\n💡 После исправлений:")
    print("   1. Перезапустите сервер (остановите и запустите заново)")
    print("   2. Откройте веб-интерфейс")
    print("   3. Включите переключатели HeadHunter и LinkedIn")
    print("   4. Проверьте data/settings.json - поля должны быть true")
    print("   5. Запустите парсинг и проверьте логи")
    
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("\n💡 Убедитесь, что:")
    print("   1. Виртуальное окружение активировано")
    print("   2. Вы запускаете скрипт из корневой директории проекта")
    import traceback
    traceback.print_exc()
