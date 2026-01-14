"""
Тестовый скрипт для диагностики парсеров HeadHunter и LinkedIn
"""
import asyncio
import sys
import os

# Настройка кодировки для Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_headhunter():
    """Тестируем HeadHunter парсер"""
    print("=" * 60)
    print("ТЕСТ HEADHUNTER ПАРСЕРА")
    print("=" * 60)
    
    try:
        from parsers import HeadHunterParser
        
        parser = HeadHunterParser()
        
        print("\n📡 Подключаемся к HeadHunter API...")
        print("   Запрос: Python разработчик")
        print("   Регион: Москва (area=1)")
        print("   Страниц: 1 (тест)")
        
        vacancies = await parser.parse_vacancies(
            search_query="Python разработчик",
            area=1,  # Москва
            days_back=7,
            max_pages=1  # Только первая страница для теста
        )
        
        print(f"\n✅ Получено вакансий: {len(vacancies)}")
        
        if vacancies:
            print("\n📋 Первая вакансия:")
            vac = vacancies[0]
            print(f"   Название: {vac.get('title', 'N/A')}")
            print(f"   Компания: {vac.get('channel', 'N/A')}")
            print(f"   Ссылка: {vac.get('link', 'N/A')}")
            print(f"   Дата: {vac.get('date', 'N/A')}")
            
            text_preview = vac.get('text', '')[:200]
            print(f"   Текст (первые 200 символов): {text_preview}...")
            
            print("\n✅ HeadHunter парсер работает корректно!")
        else:
            print("\n❌ Вакансии не найдены")
            print("\n🔍 Возможные причины:")
            print("  1. Проверьте интернет-соединение")
            print("  2. Проверьте доступность api.hh.ru в браузере")
            print("  3. API может временно недоступен")
            print("  4. Попробуйте другой поисковый запрос")
            print("\n💡 Попробуйте открыть в браузере:")
            print("   https://api.hh.ru/vacancies?text=Python&area=1&per_page=1")
            
    except ImportError as e:
        print(f"\n❌ Ошибка импорта: {e}")
        print("   Убедитесь, что модуль parsers установлен правильно")
    except Exception as e:
        print(f"\n❌ Ошибка: {type(e).__name__}: {e}")
        import traceback
        print("\n📋 Полный traceback:")
        traceback.print_exc()
    finally:
        try:
            await parser.close()
        except:
            pass

async def test_linkedin():
    """Тестируем LinkedIn парсер"""
    print("\n" + "=" * 60)
    print("ТЕСТ LINKEDIN ПАРСЕРА")
    print("=" * 60)
    
    print("\n⚠️  ВАЖНО: LinkedIn блокирует простой HTTP-парсинг")
    print("    Данные загружаются через JavaScript")
    print("    Для работы нужен Selenium-парсер")
    print("\n📋 Проверяем доступность Selenium...")
    
    try:
        from selenium import webdriver
        from webdriver_manager.chrome import ChromeDriverManager
        print("✅ Selenium установлен")
        print("✅ WebDriver Manager установлен")
        
        print("\n💡 Для использования LinkedIn парсера:")
        print("   1. Убедитесь, что Chrome установлен")
        print("   2. Укажите email и password в настройках (опционально)")
        print("   3. Парсер автоматически установит ChromeDriver")
        print("\n⚠️  LinkedIn может требовать авторизацию")
        print("    Рекомендуется указать email и password в настройках")
        
    except ImportError:
        print("❌ Selenium не установлен")
        print("\n📦 Установите зависимости:")
        print("   pip install selenium webdriver-manager")
        print("\n⚠️  Без Selenium LinkedIn парсер не будет работать")
    
    print("\n" + "=" * 60)
    print("ТЕСТ ЗАВЕРШЕН")
    print("=" * 60)

async def test_api_connection():
    """Тестируем прямое подключение к HeadHunter API"""
    print("\n" + "=" * 60)
    print("ТЕСТ ПРЯМОГО ПОДКЛЮЧЕНИЯ К HEADHUNTER API")
    print("=" * 60)
    
    try:
        import aiohttp
        
        url = "https://api.hh.ru/vacancies"
        params = {
            "text": "Python",
            "area": 1,
            "per_page": 1
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
        }
        
        print(f"\n📡 Отправляем запрос: {url}")
        print(f"   Параметры: {params}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                print(f"\n📊 Статус ответа: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    items = data.get("items", [])
                    print(f"✅ API доступен!")
                    print(f"   Найдено вакансий: {data.get('found', 0)}")
                    print(f"   Страниц: {data.get('pages', 0)}")
                    print(f"   Получено элементов: {len(items)}")
                    
                    if items:
                        print(f"\n📋 Первая вакансия из API:")
                        item = items[0]
                        print(f"   ID: {item.get('id')}")
                        print(f"   Название: {item.get('name')}")
                        print(f"   URL: {item.get('alternate_url', 'N/A')}")
                elif response.status == 403:
                    print("❌ Доступ запрещен (403)")
                    print("   Возможно, проблема с User-Agent")
                elif response.status == 429:
                    print("❌ Слишком много запросов (429)")
                    print("   Подождите немного и попробуйте снова")
                else:
                    text = await response.text()
                    print(f"❌ Неожиданный статус: {response.status}")
                    print(f"   Ответ: {text[:200]}")
                    
    except aiohttp.ClientError as e:
        print(f"❌ Ошибка подключения: {e}")
        print("   Проверьте интернет-соединение")
    except Exception as e:
        print(f"❌ Ошибка: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    print("\n" + "=" * 60)
    print("ДИАГНОСТИКА ПАРСЕРОВ")
    print("=" * 60)
    
    # Сначала тестируем прямое подключение к API
    asyncio.run(test_api_connection())
    
    # Затем тестируем парсеры
    asyncio.run(test_headhunter())
    asyncio.run(test_linkedin())
    
    print("\n✅ Диагностика завершена!")
    print("\n💡 Если HeadHunter не работает:")
    print("   1. Проверьте логи выше на наличие ошибок")
    print("   2. Убедитесь, что интернет работает")
    print("   3. Попробуйте открыть API в браузере")
    print("\n💡 Если LinkedIn не работает:")
    print("   1. Установите Selenium: pip install selenium webdriver-manager")
    print("   2. Убедитесь, что Chrome установлен")
    print("   3. Укажите email и password в настройках")
