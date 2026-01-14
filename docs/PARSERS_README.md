# Инструкция по использованию парсеров LinkedIn и HeadHunter

## Что было добавлено

В проект добавлена поддержка парсинга вакансий с двух дополнительных источников:
- **HeadHunter** - через официальный API
- **LinkedIn** - через веб-парсинг (требует осторожности)

## Структура файлов

```
iget-data/
├── parsers/                    # Новый модуль парсеров
│   ├── __init__.py
│   ├── base_parser.py          # Базовый класс для всех парсеров
│   ├── headhunter_parser.py   # Парсер HeadHunter
│   └── linkedin_parser.py     # Парсер LinkedIn
├── multi_parser.py             # Интеграция всех парсеров
├── requirements_parsers.txt     # Дополнительные зависимости
└── data/
    └── settings.json           # Обновлен с новыми настройками
```

## Настройка

### 1. HeadHunter

Откройте `data/settings.json` и настройте:

```json
{
  "enable_headhunter": true,
  "hh_search_query": "Python разработчик",
  "hh_area": 1,
  "hh_max_pages": 5
}
```

**Параметры:**
- `enable_headhunter` - включить/выключить парсинг HeadHunter
- `hh_search_query` - поисковый запрос (например, "Python разработчик", "DevOps")
- `hh_area` - ID региона:
  - `1` - Москва
  - `2` - Санкт-Петербург
  - `113` - Россия
  - [Полный список регионов](https://api.hh.ru/areas)
- `hh_max_pages` - максимальное количество страниц для парсинга (по 50 вакансий на странице)

### 2. LinkedIn

```json
{
  "enable_linkedin": true,
  "linkedin_search_query": "Python Developer",
  "linkedin_location": "Moscow, Russia",
  "linkedin_email": "your_email@example.com",
  "linkedin_password": "your_password"
}
```

**Параметры:**
- `enable_linkedin` - включить/выключить парсинг LinkedIn
- `linkedin_search_query` - поисковый запрос
- `linkedin_location` - локация (например, "Moscow, Russia", "Remote")
- `linkedin_email` - email для авторизации (опционально)
- `linkedin_password` - пароль для авторизации (опционально)

**⚠️ Внимание:** LinkedIn активно блокирует автоматический парсинг. Простой HTTP-парсер может не работать. Для надежной работы используйте Selenium-версию (см. `LinkedInSeleniumParser` в `parsers/linkedin_parser.py`).

## Использование

### Автоматический запуск

Парсеры автоматически запускаются при старте мониторинга через веб-интерфейс:

1. Запустите проект: `python start_jobstalker.py`
2. Откройте веб-интерфейс (обычно http://localhost:8000)
3. Нажмите кнопку "Start" для начала мониторинга
4. Парсеры запустятся автоматически после парсинга Telegram каналов

### Ручной запуск

Вы можете запустить парсеры отдельно:

```python
import asyncio
from multi_parser import parse_all_sources

async def main():
    results = await parse_all_sources()
    print(f"Найдено вакансий: {results}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Как это работает

1. **HeadHunter**: Использует официальный API HeadHunter (`https://api.hh.ru/vacancies`)
   - Получает список вакансий по поисковому запросу
   - Для каждой вакансии получает полное описание
   - Сохраняет вакансии в том же формате, что и Telegram

2. **LinkedIn**: Пытается парсить через HTTP запросы
   - ⚠️ Может быть заблокирован LinkedIn
   - Для надежной работы рекомендуется использовать Selenium

3. **Фильтрация**: Все вакансии проходят через те же фильтры, что и Telegram:
   - Фильтр по ключевым словам (`keyword_filter`)
   - AI-анализ (если включен `search_mode: "advanced"`)

## Устранение проблем

### HeadHunter не работает

1. Проверьте, что `hh_search_query` не пустой
2. Убедитесь, что интернет-соединение работает
3. Проверьте логи на наличие ошибок API

### LinkedIn не работает

LinkedIn активно блокирует автоматический парсинг. Решения:

1. **Используйте Selenium-версию парсера:**
   ```python
   from parsers import LinkedInSeleniumParser
   
   parser = LinkedInSeleniumParser(email="...", password="...")
   vacancies = await parser.parse_vacancies(...)
   ```

2. **Используйте прокси** для обхода блокировок

3. **Используйте официальный LinkedIn API** (требует регистрации приложения)

### Ошибка импорта модулей

Если возникает ошибка `ModuleNotFoundError: No module named 'parsers'`:

1. Убедитесь, что вы запускаете проект из корневой директории
2. Проверьте, что папка `parsers` существует в корне проекта
3. Убедитесь, что `start_jobstalker.py` правильно добавляет путь в `sys.path`

## Дополнительные возможности

### Добавление новых парсеров

Вы можете легко добавить новые источники:

1. Создайте новый класс, наследующий `BaseParser`
2. Реализуйте метод `parse_vacancies()`
3. Добавьте парсер в `multi_parser.py`

Пример:

```python
from parsers.base_parser import BaseParser
from iget.models import VacancySource

class MyCustomParser(BaseParser):
    def __init__(self):
        super().__init__(VacancySource.CUSTOM)
    
    async def parse_vacancies(self, **kwargs) -> List[Dict]:
        # Ваша логика парсинга
        vacancies = []
        # ...
        return vacancies
```

## Зависимости

Все необходимые зависимости установлены через `requirements_parsers.txt`:
- `aiohttp` - для асинхронных HTTP запросов
- `selenium` - для парсинга JavaScript-сайтов (LinkedIn)
- `webdriver-manager` - автоматическая установка ChromeDriver
- `beautifulsoup4` - парсинг HTML

## Безопасность

⚠️ **Важно:**
- Не храните пароли LinkedIn в открытом виде в `settings.json`
- Используйте переменные окружения для чувствительных данных
- Соблюдайте правила использования API и веб-сайтов
- Не злоупотребляйте частыми запросами

## Поддержка

При возникновении проблем:
1. Проверьте логи в консоли
2. Убедитесь, что все зависимости установлены
3. Проверьте настройки в `data/settings.json`
