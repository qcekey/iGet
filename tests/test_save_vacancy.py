"""
Тестовый скрипт для проверки сохраненных вакансий
Показывает статистику по источникам и примеры вакансий
"""
import json
import sys
import codecs
from pathlib import Path
from collections import Counter

# Настройка кодировки для Windows
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def check_vacancies():
    """Проверяет сохраненные вакансии"""
    vacancies_file = Path("data/vacancies.json")
    
    if not vacancies_file.exists():
        print("❌ Файл vacancies.json не найден")
        print("   Убедитесь, что вы запускали парсинг")
        return
    
    try:
        with open(vacancies_file, "r", encoding="utf-8") as f:
            vacancies = json.load(f)
    except Exception as e:
        print(f"❌ Ошибка чтения файла: {e}")
        return
    
    if not vacancies:
        print("⚠️  Файл vacancies.json пуст")
        print("   Запустите парсинг через веб-интерфейс")
        return
    
    print("=" * 60)
    print("СТАТИСТИКА ВАКАНСИЙ")
    print("=" * 60)
    print(f"\n📊 Всего вакансий: {len(vacancies)}")
    
    # Подсчитываем по источникам
    sources = Counter()
    channels = Counter()
    new_count = 0
    
    for v in vacancies:
        source = v.get("source", "telegram")  # По умолчанию telegram для старых вакансий
        sources[source] += 1
        
        channel = v.get("channel", "Unknown")
        channels[channel] += 1
        
        if v.get("is_new", False):
            new_count += 1
    
    print(f"\n📈 По источникам:")
    for source, count in sources.most_common():
        source_name = {
            "telegram": "📱 Telegram",
            "headhunter": "🎯 HeadHunter",
            "linkedin": "🔗 LinkedIn",
            "habr": "💼 Habr",
            "custom": "📝 Custom"
        }.get(source, f"❓ {source}")
        print(f"   {source_name}: {count}")
    
    print(f"\n📌 Новых вакансий: {new_count}")
    
    # Показываем вакансии с HeadHunter/LinkedIn
    hh_vacancies = [v for v in vacancies if v.get("source") == "headhunter"]
    li_vacancies = [v for v in vacancies if v.get("source") == "linkedin"]
    
    print(f"\n🎯 HeadHunter вакансий: {len(hh_vacancies)}")
    print(f"🔗 LinkedIn вакансий: {len(li_vacancies)}")
    
    if hh_vacancies:
        print("\n" + "=" * 60)
        print("ПРИМЕРЫ ВАКАНСИЙ С HEADHUNTER")
        print("=" * 60)
        for i, vac in enumerate(hh_vacancies[:3], 1):
            print(f"\n{i}. ID: {vac.get('id', 'N/A')[:8]}...")
            print(f"   Название: {vac.get('title', 'N/A')}")
            print(f"   Компания: {vac.get('channel', 'N/A')}")
            print(f"   Дата: {vac.get('date', 'N/A')}")
            print(f"   Ссылка: {vac.get('link', 'N/A')}")
            print(f"   Новое: {'Да' if vac.get('is_new') else 'Нет'}")
            text_preview = vac.get('text', '')[:150].replace('\n', ' ')
            print(f"   Текст: {text_preview}...")
    
    if li_vacancies:
        print("\n" + "=" * 60)
        print("ПРИМЕРЫ ВАКАНСИЙ С LINKEDIN")
        print("=" * 60)
        for i, vac in enumerate(li_vacancies[:3], 1):
            print(f"\n{i}. ID: {vac.get('id', 'N/A')[:8]}...")
            print(f"   Название: {vac.get('title', 'N/A')}")
            print(f"   Компания: {vac.get('channel', 'N/A')}")
            print(f"   Дата: {vac.get('date', 'N/A')}")
            print(f"   Ссылка: {vac.get('link', 'N/A')}")
            print(f"   Новое: {'Да' if vac.get('is_new') else 'Нет'}")
            text_preview = vac.get('text', '')[:150].replace('\n', ' ')
            print(f"   Текст: {text_preview}...")
    
    # Проверяем наличие обязательных полей
    print("\n" + "=" * 60)
    print("ПРОВЕРКА СТРУКТУРЫ ДАННЫХ")
    print("=" * 60)
    
    required_fields = ["id", "channel", "text", "date"]
    missing_fields = Counter()
    
    for vac in vacancies:
        for field in required_fields:
            if field not in vac:
                missing_fields[field] += 1
    
    if missing_fields:
        print("⚠️  Обнаружены вакансии с отсутствующими полями:")
        for field, count in missing_fields.items():
            print(f"   {field}: отсутствует в {count} вакансиях")
    else:
        print("✅ Все вакансии имеют обязательные поля")
    
    # Проверяем поле source
    vacancies_without_source = [v for v in vacancies if "source" not in v]
    if vacancies_without_source:
        print(f"\n⚠️  Найдено {len(vacancies_without_source)} вакансий без поля 'source'")
        print("   Это старые вакансии из Telegram (до добавления парсеров)")
        print("   Они будут отображаться как 'telegram'")
    else:
        print("\n✅ Все вакансии имеют поле 'source'")
    
    print("\n" + "=" * 60)
    print("РЕКОМЕНДАЦИИ")
    print("=" * 60)
    
    if len(hh_vacancies) == 0 and len(li_vacancies) == 0:
        print("\n⚠️  Вакансии с HeadHunter и LinkedIn не найдены")
        print("\n💡 Проверьте:")
        print("   1. Включены ли парсеры в настройках (enable_headhunter, enable_linkedin)")
        print("   2. Указаны ли поисковые запросы (hh_search_query, linkedin_search_query)")
        print("   3. Запускался ли парсинг после включения парсеров")
        print("   4. Проверьте логи на наличие ошибок")
    else:
        print("\n✅ Вакансии с HeadHunter/LinkedIn найдены и сохранены!")
        print("   Если они не отображаются в интерфейсе:")
        print("   1. Обновите страницу (F5)")
        print("   2. Проверьте, что WebSocket подключен")
        print("   3. Проверьте консоль браузера на наличие ошибок")

if __name__ == "__main__":
    check_vacancies()
