"""
Тестовый скрипт для проверки сохранения вакансий
Проверяет, работает ли функция save_vacancy
"""
import sys
import os
import json
from datetime import datetime
import uuid

# Настройка кодировки для Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from iget.vacancy_storage import save_vacancy, VACANCIES_FILE, load_all_vacancies
    
    print("=" * 60)
    print("ТЕСТ СОХРАНЕНИЯ ВАКАНСИЙ")
    print("=" * 60)
    
    print(f"\n📁 Путь к файлу: {VACANCIES_FILE.absolute()}")
    print(f"📁 Файл существует: {VACANCIES_FILE.exists()}")
    print(f"📁 Родительская директория: {VACANCIES_FILE.parent.absolute()}")
    print(f"📁 Родительская директория существует: {VACANCIES_FILE.parent.exists()}")
    
    # Проверяем текущую рабочую директорию
    print(f"\n📂 Текущая рабочая директория: {os.getcwd()}")
    
    # Загружаем существующие вакансии
    existing_count = len(load_all_vacancies())
    print(f"📊 Существующих вакансий в файле: {existing_count}")
    
    # Создаем тестовую вакансию
    test_vacancy = {
        "id": str(uuid.uuid4()),
        "channel": "Test - HeadHunter",
        "text": "Тестовая вакансия для проверки сохранения. Это вакансия создана автоматически для тестирования функции save_vacancy.",
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "link": "https://test.com",
        "source": "headhunter",
        "title": "Test Vacancy",
        "analysis": "Test save function"
    }
    
    print(f"\n🧪 Тестовая вакансия:")
    print(f"   ID: {test_vacancy['id'][:8]}...")
    print(f"   Source: {test_vacancy['source']}")
    print(f"   Channel: {test_vacancy['channel']}")
    
    print("\n💾 Пробуем сохранить тестовую вакансию...")
    try:
        save_vacancy(test_vacancy)
        print("✅ Вакансия сохранена через save_vacancy()!")
        
        # Проверяем, что она в файле
        vacancies = load_all_vacancies()
        test_found = any(v.get("id") == test_vacancy["id"] for v in vacancies)
        
        if test_found:
            print(f"✅ Вакансия найдена в файле!")
            print(f"📊 Всего вакансий в файле: {len(vacancies)}")
            
            # Находим нашу тестовую вакансию
            test_vac = next((v for v in vacancies if v.get("id") == test_vacancy["id"]), None)
            if test_vac:
                print(f"\n📋 Данные сохраненной вакансии:")
                print(f"   ID: {test_vac.get('id')[:8]}...")
                print(f"   Source: {test_vac.get('source')}")
                print(f"   Channel: {test_vac.get('channel')}")
                print(f"   Added at: {test_vac.get('added_at')}")
                print(f"   Is new: {test_vac.get('is_new')}")
        else:
            print("❌ Вакансия НЕ найдена в файле после сохранения!")
            print("   Возможна проблема с путем к файлу или правами доступа")
            
    except Exception as e:
        print(f"❌ Ошибка при сохранении: {e}")
        import traceback
        print("\n📋 Полный traceback:")
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("ТЕСТ ЗАВЕРШЕН")
    print("=" * 60)
    
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("\n💡 Убедитесь, что:")
    print("   1. Вы запускаете скрипт из корневой директории проекта")
    print("   2. Виртуальное окружение активировано")
    print("   3. iget установлен в venv")
    import traceback
    traceback.print_exc()
