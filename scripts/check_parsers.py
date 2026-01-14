"""
Скрипт для проверки работоспособности парсеров
"""
import asyncio
import sys
import os
import json
from pathlib import Path

# Настройка кодировки для Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def check_parsers():
    """Проверяет работоспособность всех парсеров"""
    print("=" * 70)
    print("ПРОВЕРКА РАБОТОСПОСОБНОСТИ ПАРСЕРОВ")
    print("=" * 70)
    
    # Проверяем настройки
    settings_file = Path("data/settings.json")
    if not settings_file.exists():
        print("\n❌ Файл настроек не найден: data/settings.json")
        return
    
    with open(settings_file, "r", encoding="utf-8") as f:
        settings = json.load(f)
    
    print("\n📋 ТЕКУЩИЕ НАСТРОЙКИ:")
    print(f"   HeadHunter: {'✅ ВКЛЮЧЕН' if settings.get('enable_headhunter') else '❌ ВЫКЛЮЧЕН'}")
    if settings.get('enable_headhunter'):
        print(f"      Запрос: '{settings.get('hh_search_query', '')}'")
        print(f"      Регион: {settings.get('hh_area', 1)}")
        print(f"      Страниц: {settings.get('hh_max_pages', 5)}")
    
    print(f"   LinkedIn: {'✅ ВКЛЮЧЕН' if settings.get('enable_linkedin') else '❌ ВЫКЛЮЧЕН'}")
    if settings.get('enable_linkedin'):
        print(f"      Запрос: '{settings.get('linkedin_search_query', '')}'")
        print(f"      Локация: '{settings.get('linkedin_location', '')}'")
        email = settings.get('linkedin_email', '')
        print(f"      Email: {'✅ Указан' if email else '❌ Не указан'}")
    
    # Проверяем HeadHunter
    print("\n" + "=" * 70)
    print("ПРОВЕРКА HEADHUNTER")
    print("=" * 70)
    
    try:
        from parsers import HeadHunterParser
        print("✅ Модуль HeadHunterParser импортирован")
        
        # Проверяем подключение к API
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.hh.ru/vacancies?text=Python&area=1&per_page=1", 
                                 timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    print("✅ HeadHunter API доступен")
                    data = await resp.json()
                    found = data.get("found", 0)
                    print(f"   Найдено вакансий: {found}")
                else:
                    print(f"❌ HeadHunter API недоступен (статус {resp.status})")
        
        # Тестируем парсер
        if settings.get('enable_headhunter'):
            print("\n🔍 Тестируем парсер (1 страница, 3 вакансии)...")
            parser = HeadHunterParser()
            try:
                vacancies = await parser.parse_vacancies(
                    search_query=settings.get('hh_search_query', 'Python'),
                    area=settings.get('hh_area', 1),
                    days_back=7,
                    max_pages=1,
                    per_page=3
                )
                print(f"✅ Парсер работает! Получено {len(vacancies)} вакансий")
                if vacancies:
                    print(f"   Пример: {vacancies[0].get('title', 'N/A')}")
            except Exception as e:
                print(f"❌ Ошибка парсера: {e}")
            finally:
                await parser.close()
        else:
            print("⚠️  HeadHunter отключен в настройках")
            
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("   Убедитесь, что установлены зависимости: pip install -r requirements_parsers.txt")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    # Проверяем LinkedIn
    print("\n" + "=" * 70)
    print("ПРОВЕРКА LINKEDIN")
    print("=" * 70)
    
    try:
        from parsers import LinkedInSeleniumParser, LinkedInParser
        print("✅ Модули LinkedIn парсеров импортированы")
        
        # Проверяем Selenium
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            print("✅ Selenium установлен")
            
            # Проверяем ChromeDriver
            try:
                driver_path = ChromeDriverManager().install()
                print(f"✅ ChromeDriver доступен: {driver_path}")
            except Exception as e:
                print(f"⚠️  ChromeDriver: {e}")
                print("   Убедитесь, что Chrome установлен")
        except ImportError:
            print("❌ Selenium не установлен")
            print("   Установите: pip install selenium webdriver-manager")
        
        if settings.get('enable_linkedin'):
            print("\n⚠️  LinkedIn парсинг:")
            print("   - Требует Selenium (установлен автоматически)")
            print("   - Может быть медленным (открывает браузер)")
            print("   - Может требовать авторизацию")
            print("   - Рекомендуется указать email и password в настройках")
        else:
            print("⚠️  LinkedIn отключен в настройках")
            
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # Проверяем сохранение
    print("\n" + "=" * 70)
    print("ПРОВЕРКА СОХРАНЕНИЯ")
    print("=" * 70)
    
    try:
        from iget.vacancy_storage import VACANCIES_FILE, load_all_vacancies
        
        if VACANCIES_FILE.exists():
            vacancies = load_all_vacancies()
            print(f"✅ Файл вакансий существует: {VACANCIES_FILE}")
            print(f"   Всего вакансий: {len(vacancies)}")
            
            hh_count = len([v for v in vacancies if v.get("source") == "headhunter"])
            linkedin_count = len([v for v in vacancies if v.get("source") == "linkedin"])
            telegram_count = len([v for v in vacancies if v.get("source") == "telegram"])
            
            print(f"   HeadHunter: {hh_count}")
            print(f"   LinkedIn: {linkedin_count}")
            print(f"   Telegram: {telegram_count}")
        else:
            print(f"⚠️  Файл вакансий не существует: {VACANCIES_FILE}")
            print("   Будет создан при первом сохранении")
            
    except Exception as e:
        print(f"❌ Ошибка проверки сохранения: {e}")
    
    # Итоги
    print("\n" + "=" * 70)
    print("ИТОГИ")
    print("=" * 70)
    
    hh_ok = settings.get('enable_headhunter') and 'HeadHunterParser' in sys.modules
    linkedin_ok = settings.get('enable_linkedin')
    
    if hh_ok:
        print("✅ HeadHunter: настроен и готов к работе")
    elif settings.get('enable_headhunter'):
        print("❌ HeadHunter: включен, но есть проблемы")
    else:
        print("⚠️  HeadHunter: отключен в настройках")
    
    if linkedin_ok:
        print("⚠️  LinkedIn: включен, но требует Selenium и может работать медленно")
    else:
        print("⚠️  LinkedIn: отключен в настройках")
    
    print("\n💡 РЕКОМЕНДАЦИИ:")
    if settings.get('enable_headhunter'):
        print("   1. HeadHunter должен работать автоматически при запуске приложения")
        print("   2. Проверьте логи в консоли при запуске start_jobstalker.py")
    if settings.get('enable_linkedin'):
        print("   3. LinkedIn требует Selenium - убедитесь, что Chrome установлен")
        print("   4. LinkedIn парсинг может занять много времени")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(check_parsers())
