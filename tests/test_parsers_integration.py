"""
Интеграционный тест парсеров - проверяет полный цикл от парсинга до сохранения
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

async def test_full_cycle():
    """Тестирует полный цикл: парсинг -> сохранение -> проверка файла"""
    print("=" * 60)
    print("ИНТЕГРАЦИОННЫЙ ТЕСТ ПАРСЕРОВ")
    print("=" * 60)
    
    try:
        from parsers import HeadHunterParser
        from iget.vacancy_storage import save_vacancy, load_all_vacancies, VACANCIES_FILE
        
        print("\n📊 Состояние до теста:")
        vacancies_before = load_all_vacancies()
        hh_before = len([v for v in vacancies_before if v.get("source") == "headhunter"])
        print(f"   Всего вакансий: {len(vacancies_before)}")
        print(f"   HeadHunter вакансий: {hh_before}")
        
        print("\n🔍 Тестируем HeadHunter парсер...")
        parser = HeadHunterParser()
        
        # Парсим небольшое количество для теста
        vacancies = await parser.parse_vacancies(
            search_query="Python разработчик",
            area=1,
            days_back=7,
            max_pages=1,  # Только первая страница
            per_page=5    # Только 5 вакансий для теста
        )
        
        print(f"\n✅ Получено {len(vacancies)} вакансий от парсера")
        
        if not vacancies:
            print("\n❌ Парсер не вернул вакансии!")
            print("   Проверьте:")
            print("   1. Интернет-соединение")
            print("   2. Доступность api.hh.ru")
            return
        
        # Пробуем сохранить первую вакансию
        test_vacancy = vacancies[0]
        print(f"\n💾 Сохраняем тестовую вакансию:")
        print(f"   ID: {test_vacancy.get('id')[:8]}...")
        print(f"   Title: {test_vacancy.get('title', 'N/A')}")
        print(f"   Source: {test_vacancy.get('source', 'N/A')}")
        
        try:
            save_vacancy(test_vacancy)
            print("✅ Вакансия сохранена через save_vacancy()")
        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Проверяем, что вакансия в файле
        vacancies_after = load_all_vacancies()
        hh_after = len([v for v in vacancies_after if v.get("source") == "headhunter"])
        
        print(f"\n📊 Состояние после теста:")
        print(f"   Всего вакансий: {len(vacancies_after)}")
        print(f"   HeadHunter вакансий: {hh_after}")
        print(f"   Добавлено HeadHunter вакансий: {hh_after - hh_before}")
        
        # Ищем нашу тестовую вакансию
        test_found = any(v.get("id") == test_vacancy.get("id") for v in vacancies_after)
        
        if test_found:
            print("\n✅ ТЕСТ ПРОЙДЕН!")
            print("   Вакансия успешно сохранена и найдена в файле")
        else:
            print("\n❌ ТЕСТ НЕ ПРОЙДЕН!")
            print("   Вакансия не найдена в файле после сохранения")
            print(f"   Путь к файлу: {VACANCIES_FILE.absolute()}")
        
        await parser.close()
        
    except Exception as e:
        print(f"\n❌ Ошибка теста: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(test_full_cycle())
