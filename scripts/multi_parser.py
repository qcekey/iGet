"""
Модуль для парсинга вакансий с нескольких источников
Интегрируется с существующей системой iGet
"""
import asyncio
import logging
from typing import List, Dict, Optional

from parsers import HeadHunterParser, LinkedInParser, LinkedInSeleniumParser
from iget.vacancy_storage import save_vacancy
from iget.web_ui import broadcast_vacancy, broadcast_status, get_current_settings
from iget.main import keyword_filter_check
from iget.models import VacancySource
from vacancy_storage_with_dedup import save_vacancy_with_dedup

log = logging.getLogger("multi_parser")


def check_search_query_match(vacancy: Dict, search_query: str) -> bool:
    """
    Проверяет, соответствует ли вакансия поисковому запросу.
    Если search_query пустой, возвращает True (все вакансии проходят).
    Если search_query указан, строго проверяет наличие ключевого слова в названии или описании.
    
    Args:
        vacancy: Словарь с данными вакансии
        search_query: Поисковый запрос (например, "Backend")
    
    Returns:
        True если вакансия соответствует запросу, False иначе
    """
    if not search_query or not search_query.strip():
        return True  # Если запрос пустой, пропускаем все вакансии
    
    search_keyword = search_query.strip().lower()
    
    # Получаем текст вакансии
    vacancy_text = vacancy.get("text", "").lower()
    vacancy_title = vacancy.get("title", "").lower()
    
    # Приоритет 1: Проверяем наличие ключевого слова в названии вакансии
    # Это самый строгий критерий - если ключевое слово есть в названии, вакансия точно релевантна
    if search_keyword in vacancy_title:
        return True
    
    # Приоритет 2: Проверяем первые 300 символов описания (обычно там указывается основная информация)
    # Это помогает отфильтровать вакансии, где ключевое слово упоминается только в контексте, не относящемся к вакансии
    text_start = vacancy_text[:300]
    if search_keyword in text_start:
        return True
    
    # Приоритет 3: Проверяем весь текст, но только если ключевое слово встречается несколько раз
    # Это помогает отфильтровать случайные упоминания
    if vacancy_text.count(search_keyword) >= 2:
        return True
    
    # Если ключевое слово не найдено в названии и не встречается достаточно часто в описании,
    # вакансия не соответствует запросу
    return False


async def parse_headhunter(settings: Dict) -> int:
    """
    Парсит вакансии с HeadHunter
    
    Returns:
        Количество найденных вакансий
    """
    if not settings.get("enable_headhunter", False):
        return 0
    
    try:
        await broadcast_status("Парсинг HeadHunter...", "Search")
        log.info("Начинаем парсинг HeadHunter")
        
        parser = HeadHunterParser()
        
        search_query = settings.get("hh_search_query", "").strip()
        area = settings.get("hh_area", 1)  # 1 = Москва
        days_back = settings.get("days_back", 7)
        max_pages = settings.get("hh_max_pages", 5)
        
        # Если search_query пустой, используем общий запрос для IT вакансий
        if not search_query:
            log.info("HeadHunter: search_query пустой, используем общий запрос для IT вакансий")
            search_query = "IT разработчик программист"
            await broadcast_status("HeadHunter: поиск всех IT вакансий...", "Search")
        else:
            log.info(f"HeadHunter: используем поисковый запрос: '{search_query}'")
            await broadcast_status(f"HeadHunter: поиск по запросу '{search_query}'...", "Search")
        
        vacancies = await parser.parse_vacancies(
            search_query=search_query,
            area=area,
            days_back=days_back,
            max_pages=max_pages
        )
        
        log.info(f"HeadHunter: получено {len(vacancies)} вакансий")
        
        # Проверяем путь к файлу
        from iget.vacancy_storage import VACANCIES_FILE
        log.info(f"HeadHunter: путь к файлу вакансий: {VACANCIES_FILE.absolute()}")
        log.info(f"HeadHunter: файл существует: {VACANCIES_FILE.exists()}")
        
        saved_count = 0
        skipped_duplicates = 0
        keyword_filter = settings.get("keyword_filter", "")
        enable_dedup = settings.get("enable_duplicate_detection", True)
        similarity_threshold = settings.get("duplicate_similarity_threshold", 0.85)
        merge_duplicates = settings.get("merge_duplicates", False)
        
        log.info(f"HeadHunter: keyword_filter = '{keyword_filter}'")
        log.info(f"HeadHunter: детекция дубликатов = {enable_dedup}, порог = {similarity_threshold}")
        log.info(f"HeadHunter: начинаем сохранение {len(vacancies)} вакансий")
        
        # Получаем оригинальный search_query из настроек для фильтрации
        original_search_query = settings.get("hh_search_query", "").strip()
        
        for vacancy in vacancies:
            try:
                # Проверяем соответствие search_query (строгая фильтрация)
                if original_search_query and not check_search_query_match(vacancy, original_search_query):
                    log.debug(f"HeadHunter: вакансия '{vacancy.get('title', 'unknown')[:50]}...' отфильтрована по search_query '{original_search_query}'")
                    continue
                
                # Проверяем keyword_filter (дополнительный фильтр)
                # Проверяем и заголовок, и текст для более точной фильтрации
                vacancy_title = vacancy.get("title", "")
                if keyword_filter and not keyword_filter_check(vacancy["text"], keyword_filter, vacancy_title):
                    log.debug(f"HeadHunter: вакансия {vacancy.get('id', 'unknown')[:8]}... отфильтрована по keyword_filter")
                    continue
                
                # Добавляем поле analysis для совместимости с форматом Telegram
                if "analysis" not in vacancy:
                    vacancy["analysis"] = f"HeadHunter: {search_query}"
                
                # Сохраняем вакансию с проверкой дубликатов
                vacancy_id = vacancy.get('id', 'unknown')[:8]
                log.debug(f"HeadHunter: сохраняем вакансию {vacancy_id}...")
                
                if enable_dedup:
                    # Используем сохранение с проверкой дубликатов
                    result = save_vacancy_with_dedup(
                        vacancy,
                        check_duplicates=True,
                        similarity_threshold=similarity_threshold,
                        merge_duplicates=merge_duplicates
                    )
                    
                    if result["is_duplicate"]:
                        skipped_duplicates += 1
                        if not merge_duplicates:
                            log.debug(f"HeadHunter: вакансия {vacancy_id}... пропущена (дубликат)")
                            continue
                        else:
                            log.info(f"HeadHunter: вакансия {vacancy_id}... объединена с дубликатом")
                    
                    # Отправляем через broadcast для обновления UI
                    if result["saved"]:
                        await broadcast_vacancy(vacancy if not result["merged"] else vacancy)
                        saved_count += 1
                else:
                    # Стандартное сохранение без проверки дубликатов
                    await broadcast_vacancy(vacancy)
                    saved_count += 1
                
                log.debug(f"HeadHunter: вакансия {vacancy_id}... успешно сохранена")
                
            except Exception as e:
                log.error(f"HeadHunter: ошибка сохранения вакансии {vacancy.get('id', 'unknown')[:8]}...: {e}", exc_info=True)
                # Пробуем сохранить напрямую как fallback
                try:
                    save_vacancy(vacancy)
                    saved_count += 1
                    log.info(f"HeadHunter: вакансия {vacancy.get('id', 'unknown')[:8]}... сохранена напрямую")
                except Exception as e2:
                    log.error(f"HeadHunter: ошибка прямого сохранения: {e2}", exc_info=True)
        
        log.info(f"HeadHunter: сохранено {saved_count} вакансий, пропущено дубликатов: {skipped_duplicates}")
        status_msg = f"HeadHunter: найдено {saved_count} вакансий"
        if skipped_duplicates > 0:
            status_msg += f", пропущено дубликатов: {skipped_duplicates}"
        await broadcast_status(status_msg, "Done")
        
        return saved_count
        
    except Exception as e:
        log.error(f"Ошибка парсинга HeadHunter: {e}")
        await broadcast_status(f"Ошибка HeadHunter: {str(e)[:50]}", "Error")
        return 0


async def parse_linkedin(settings: Dict) -> int:
    """
    Парсит вакансии с LinkedIn
    
    Returns:
        Количество найденных вакансий
    """
    if not settings.get("enable_linkedin", False):
        return 0
    
    try:
        await broadcast_status("Парсинг LinkedIn...", "Search")
        log.info("Начинаем парсинг LinkedIn")
        
        # Проверяем наличие учетных данных
        linkedin_email = settings.get("linkedin_email", "").strip()
        linkedin_password = settings.get("linkedin_password", "").strip()
        
        if not linkedin_email or not linkedin_password:
            log.warning("LinkedIn: email или password не указаны в настройках")
            log.warning("LinkedIn: парсинг может быть ограничен без авторизации")
            await broadcast_status("LinkedIn: рекомендуется указать email и password", "Warning")
        
        # Используем Selenium-парсер для надежной работы с LinkedIn
        # Простой HTTP-парсер не работает из-за защиты LinkedIn
        parser = None
        try:
            parser = LinkedInSeleniumParser(
                email=linkedin_email if linkedin_email else None,
                password=linkedin_password if linkedin_password else None,
                headless=False  # Оставляем видимым для отладки
            )
            log.info("LinkedIn: используем Selenium-парсер")
        except ImportError:
            log.error("LinkedIn: Selenium не установлен!")
            log.error("LinkedIn: установите: pip install selenium webdriver-manager")
            await broadcast_status("LinkedIn: установите selenium и webdriver-manager", "Error")
            return 0
        except Exception as e:
            log.error(f"LinkedIn: ошибка инициализации Selenium-парсера: {e}", exc_info=True)
            await broadcast_status(f"LinkedIn: ошибка инициализации - {str(e)[:50]}", "Error")
            return 0
        
        if not parser:
            log.error("LinkedIn: не удалось создать парсер")
            await broadcast_status("LinkedIn: ошибка инициализации парсера", "Error")
            return 0
        
        search_query = settings.get("linkedin_search_query", "").strip()
        location = settings.get("linkedin_location", "").strip()
        days_back = settings.get("days_back", 7)
        
        # Если search_query пустой, используем общий запрос для IT вакансий
        if not search_query:
            log.info("LinkedIn: search_query пустой, используем общий запрос для IT вакансий")
            search_query = "IT developer programmer"
            await broadcast_status("LinkedIn: поиск всех IT вакансий...", "Search")
        else:
            log.info(f"LinkedIn: используем поисковый запрос: '{search_query}'")
            await broadcast_status(f"LinkedIn: поиск по запросу '{search_query}'...", "Search")
        
        # Для Selenium парсера используем max_results
        try:
            if isinstance(parser, LinkedInSeleniumParser):
                log.info("LinkedIn: запускаем Selenium-парсер (это может занять время)")
                log.info(f"LinkedIn: параметры поиска - запрос: '{search_query}', локация: '{location}'")
                await broadcast_status("LinkedIn: открываем браузер...", "Search")
                vacancies = await parser.parse_vacancies(
                    search_query=search_query,
                    location=location,
                    days_back=days_back,
                    max_results=50
                )
                log.info(f"LinkedIn: парсер вернул {len(vacancies)} вакансий")
            else:
                log.warning("LinkedIn: используем простой HTTP-парсер (может не работать)")
                vacancies = await parser.parse_vacancies(
                    search_query=search_query,
                    location=location,
                    days_back=days_back
                )
        except KeyboardInterrupt:
            log.warning("LinkedIn: парсинг прерван пользователем")
            await broadcast_status("LinkedIn: парсинг прерван", "Warning")
            return 0
        except Exception as e:
            log.error(f"LinkedIn: ошибка при парсинге: {e}", exc_info=True)
            error_msg = str(e)
            if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                await broadcast_status("LinkedIn: таймаут - проверьте интернет", "Error")
            elif "chrome" in error_msg.lower() or "webdriver" in error_msg.lower():
                await broadcast_status("LinkedIn: ошибка браузера - проверьте Chrome", "Error")
            else:
                await broadcast_status(f"LinkedIn: ошибка - {error_msg[:50]}", "Error")
            return 0
        
        log.info(f"LinkedIn: получено {len(vacancies)} вакансий")
        
        # Проверяем путь к файлу
        from iget.vacancy_storage import VACANCIES_FILE
        log.info(f"LinkedIn: путь к файлу вакансий: {VACANCIES_FILE.absolute()}")
        log.info(f"LinkedIn: файл существует: {VACANCIES_FILE.exists()}")
        
        saved_count = 0
        skipped_duplicates = 0
        keyword_filter = settings.get("keyword_filter", "")
        enable_dedup = settings.get("enable_duplicate_detection", True)
        similarity_threshold = settings.get("duplicate_similarity_threshold", 0.85)
        merge_duplicates = settings.get("merge_duplicates", False)
        
        log.info(f"LinkedIn: keyword_filter = '{keyword_filter}'")
        log.info(f"LinkedIn: детекция дубликатов = {enable_dedup}, порог = {similarity_threshold}")
        log.info(f"LinkedIn: начинаем сохранение {len(vacancies)} вакансий")
        
        # Получаем оригинальный search_query из настроек для фильтрации
        original_search_query = settings.get("linkedin_search_query", "").strip()
        
        for vacancy in vacancies:
            try:
                # Проверяем соответствие search_query (строгая фильтрация)
                if original_search_query and not check_search_query_match(vacancy, original_search_query):
                    log.debug(f"LinkedIn: вакансия '{vacancy.get('title', 'unknown')[:50]}...' отфильтрована по search_query '{original_search_query}'")
                    continue
                
                # Проверяем keyword_filter (дополнительный фильтр)
                # Проверяем и заголовок, и текст для более точной фильтрации
                vacancy_title = vacancy.get("title", "")
                if keyword_filter and not keyword_filter_check(vacancy["text"], keyword_filter, vacancy_title):
                    log.debug(f"LinkedIn: вакансия {vacancy.get('id', 'unknown')[:8]}... отфильтрована по keyword_filter")
                    continue
                
                # Добавляем поле analysis для совместимости с форматом Telegram
                if "analysis" not in vacancy:
                    vacancy["analysis"] = f"LinkedIn: {search_query}"
                
                # Сохраняем вакансию с проверкой дубликатов
                vacancy_id = vacancy.get('id', 'unknown')[:8]
                log.debug(f"LinkedIn: сохраняем вакансию {vacancy_id}...")
                
                if enable_dedup:
                    # Используем сохранение с проверкой дубликатов
                    result = save_vacancy_with_dedup(
                        vacancy,
                        check_duplicates=True,
                        similarity_threshold=similarity_threshold,
                        merge_duplicates=merge_duplicates
                    )
                    
                    if result["is_duplicate"]:
                        skipped_duplicates += 1
                        if not merge_duplicates:
                            log.debug(f"LinkedIn: вакансия {vacancy_id}... пропущена (дубликат)")
                            continue
                        else:
                            log.info(f"LinkedIn: вакансия {vacancy_id}... объединена с дубликатом")
                    
                    # Отправляем через broadcast для обновления UI
                    if result["saved"]:
                        await broadcast_vacancy(vacancy if not result["merged"] else vacancy)
                        saved_count += 1
                else:
                    # Стандартное сохранение без проверки дубликатов
                    await broadcast_vacancy(vacancy)
                    saved_count += 1
                
                log.debug(f"LinkedIn: вакансия {vacancy_id}... успешно сохранена")
                
            except Exception as e:
                log.error(f"LinkedIn: ошибка сохранения вакансии {vacancy.get('id', 'unknown')[:8]}...: {e}", exc_info=True)
                # Пробуем сохранить напрямую как fallback
                try:
                    save_vacancy(vacancy)
                    saved_count += 1
                    log.info(f"LinkedIn: вакансия {vacancy.get('id', 'unknown')[:8]}... сохранена напрямую")
                except Exception as e2:
                    log.error(f"LinkedIn: ошибка прямого сохранения: {e2}", exc_info=True)
        
        log.info(f"LinkedIn: сохранено {saved_count} вакансий, пропущено дубликатов: {skipped_duplicates}")
        status_msg = f"LinkedIn: найдено {saved_count} вакансий"
        if skipped_duplicates > 0:
            status_msg += f", пропущено дубликатов: {skipped_duplicates}"
        await broadcast_status(status_msg, "Done")
        
        return saved_count
        
    except Exception as e:
        log.error(f"Ошибка парсинга LinkedIn: {e}")
        await broadcast_status(f"Ошибка LinkedIn: {str(e)[:50]}", "Error")
        return 0


async def parse_all_sources() -> Dict[str, int]:
    """
    Парсит вакансии со всех включенных источников
    
    Returns:
        Словарь с количеством найденных вакансий по источникам
    """
    settings = get_current_settings()
    results = {
        "headhunter": 0,
        "linkedin": 0,
        "telegram": 0  # Telegram парсится отдельно через main.py
    }
    
    log.info("=" * 60)
    log.info("НАЧАЛО ПАРСИНГА ДОПОЛНИТЕЛЬНЫХ ИСТОЧНИКОВ")
    log.info("=" * 60)
    log.info(f"Настройки парсеров:")
    log.info(f"  HeadHunter: enabled={settings.get('enable_headhunter', False)}, query='{settings.get('hh_search_query', '')}'")
    log.info(f"  LinkedIn: enabled={settings.get('enable_linkedin', False)}, query='{settings.get('linkedin_search_query', '')}'")
    
    # Парсим HeadHunter
    if settings.get("enable_headhunter", False):
        log.info("\n" + "=" * 60)
        log.info("ПАРСИНГ HEADHUNTER")
        log.info("=" * 60)
        try:
            results["headhunter"] = await parse_headhunter(settings)
            log.info(f"HeadHunter: завершено, найдено {results['headhunter']} вакансий")
        except Exception as e:
            log.error(f"HeadHunter: критическая ошибка: {e}", exc_info=True)
            results["headhunter"] = 0
        await asyncio.sleep(1)  # Небольшая задержка между источниками
    else:
        log.info("HeadHunter: отключен в настройках")
    
    # Парсим LinkedIn
    if settings.get("enable_linkedin", False):
        log.info("\n" + "=" * 60)
        log.info("ПАРСИНГ LINKEDIN")
        log.info("=" * 60)
        try:
            results["linkedin"] = await parse_linkedin(settings)
            log.info(f"LinkedIn: завершено, найдено {results['linkedin']} вакансий")
        except Exception as e:
            log.error(f"LinkedIn: критическая ошибка: {e}", exc_info=True)
            results["linkedin"] = 0
        await asyncio.sleep(1)
    else:
        log.info("LinkedIn: отключен в настройках")
    
    total = sum(results.values())
    log.info("\n" + "=" * 60)
    log.info(f"ПАРСИНГ ЗАВЕРШЕН. Всего найдено вакансий: {total}")
    log.info(f"  HeadHunter: {results['headhunter']}")
    log.info(f"  LinkedIn: {results['linkedin']}")
    log.info("=" * 60)
    
    return results
