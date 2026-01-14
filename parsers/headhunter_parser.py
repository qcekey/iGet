"""
Парсер вакансий с HeadHunter.ru
Использует официальный API HeadHunter для получения вакансий
"""
import asyncio
import aiohttp
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

from .base_parser import BaseParser
from iget.models import VacancySource

log = logging.getLogger("headhunter_parser")


class HeadHunterParser(BaseParser):
    """Парсер вакансий с HeadHunter.ru через API"""
    
    def __init__(self):
        super().__init__(VacancySource.HEADHUNTER)
        self.api_url = "https://api.hh.ru"
        self.session = None
    
    async def _get_session(self):
        """Создает aiohttp сессию"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Referer': 'https://hh.ru/',
                    'Origin': 'https://hh.ru',
                    'Connection': 'keep-alive',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-site'
                }
            )
        return self.session
    
    async def close(self):
        """Закрывает сессию"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def parse_vacancies(
        self,
        search_query: str = "",
        area: int = 1,  # 1 = Москва, 2 = СПб, 113 = Россия
        days_back: int = 7,
        max_pages: int = 10,
        per_page: int = 50
    ) -> List[Dict]:
        """
        Парсит вакансии с HeadHunter через API
        
        Args:
            search_query: Поисковый запрос (например, "Python разработчик")
            area: ID региона (1 - Москва, 2 - СПб, 113 - Россия)
            days_back: Сколько дней назад искать
            max_pages: Максимальное количество страниц для парсинга
            per_page: Количество вакансий на странице (макс 100)
        """
        session = await self._get_session()
        vacancies = []
        
        try:
            # Параметры поиска
            # Примечание: period может работать некорректно, используем только основные параметры
            params = {
                "text": search_query,
                "area": area,
                "per_page": min(per_page, 100),
                "page": 0,
                "order_by": "publication_time"
            }
            
            # Добавляем period только если days_back <= 30 (API ограничение)
            if days_back <= 30:
                params["period"] = days_back
            
            # Получаем список вакансий
            for page in range(max_pages):
                params["page"] = page
                
                try:
                    log.info(f"HeadHunter: запрашиваем страницу {page + 1}/{max_pages}")
                    async with session.get(f"{self.api_url}/vacancies", params=params) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            log.warning(f"HeadHunter API вернул статус {response.status}: {error_text[:200]}")
                            if response.status == 429:
                                log.warning("HeadHunter: слишком много запросов, ждем 5 секунд...")
                                await asyncio.sleep(5)
                                continue
                            break
                        
                        data = await response.json()
                        items = data.get("items", [])
                        
                        if not items:
                            log.info(f"HeadHunter: больше нет вакансий на странице {page + 1}")
                            break
                        
                        log.info(f"HeadHunter: получено {len(items)} вакансий со страницы {page + 1}")
                        
                        # Парсим каждую вакансию (ограничиваем количество для теста)
                        parsed_count = 0
                        for item in items:
                            try:
                                vacancy = await self._parse_vacancy_item(item, session)
                                if vacancy:
                                    vacancies.append(vacancy)
                                    parsed_count += 1
                                
                                # Задержка между запросами (увеличена для избежания 403)
                                await asyncio.sleep(0.5)
                                
                            except Exception as e:
                                log.error(f"HeadHunter: ошибка парсинга вакансии {item.get('id')}: {e}")
                                continue
                        
                        log.info(f"HeadHunter: успешно распарсено {parsed_count} вакансий со страницы {page + 1}")
                        
                        # Проверяем, есть ли еще страницы
                        pages = data.get("pages", 0)
                        found = data.get("found", 0)
                        log.info(f"HeadHunter: всего найдено {found} вакансий, страниц: {pages}")
                        
                        if page >= pages - 1:
                            log.info("HeadHunter: достигнута последняя страница")
                            break
                        
                        # Задержка между страницами
                        await asyncio.sleep(1)
                        
                except aiohttp.ClientError as e:
                    log.error(f"Ошибка запроса к HeadHunter API: {e}")
                    break
                except Exception as e:
                    log.error(f"Неожиданная ошибка: {e}")
                    break
            
            log.info(f"Всего получено {len(vacancies)} вакансий с HeadHunter")
            
            # Применяем фильтрацию по дате публикации
            vacancies = self.filter_vacancies_by_date(vacancies, days_back)
            log.info(f"После фильтрации по дате (days_back={days_back}): {len(vacancies)} вакансий")
            
        except Exception as e:
            log.error(f"Критическая ошибка парсинга HeadHunter: {e}")
        finally:
            await self.close()
        
        return vacancies
    
    async def _parse_vacancy_item(self, item: Dict, session: aiohttp.ClientSession) -> Optional[Dict]:
        """Парсит одну вакансию из списка"""
        try:
            vacancy_id = item.get("id")
            if not vacancy_id:
                return None
            
            # Стратегия: сначала используем данные из списка (быстрее и надежнее)
            # Полное описание запрашиваем опционально, если нужно больше информации
            use_full_description = True  # Можно установить False для полного отказа от запросов
            
            # Если есть данные в списке, создаем вакансию из них
            if item.get("snippet") or item.get("name"):
                vacancy = self._create_vacancy_from_item(item)
                
                # Опционально: пробуем получить полное описание (но не критично)
                if use_full_description:
                    try:
                        # Небольшая задержка перед запросом полного описания
                        await asyncio.sleep(0.3)
                        
                        async with session.get(f"{self.api_url}/vacancies/{vacancy_id}") as response:
                            if response.status == 403:
                                # 403 - используем данные из списка (это нормально)
                                log.debug(f"HeadHunter: 403 для {vacancy_id}, используем данные из списка")
                                return vacancy
                            
                            if response.status == 200:
                                vacancy_data = await response.json()
                                # Обновляем описание полным текстом, если доступно
                                description = vacancy_data.get("description", "")
                                if description:
                                    # Заменяем краткое описание на полное
                                    title = vacancy_data.get("name", vacancy.get("title", ""))
                                    company_name = vacancy_data.get("employer", {}).get("name", "Не указано")
                                    
                                    # Формируем полный текст
                                    vacancy_text = f"{title}\n\n"
                                    vacancy_text += f"Компания: {company_name}\n"
                                    
                                    # Зарплата
                                    salary = vacancy_data.get("salary")
                                    if salary:
                                        if salary.get("from") and salary.get("to"):
                                            salary_text = f"{salary['from']} - {salary['to']} {salary.get('currency', '')}"
                                        elif salary.get("from"):
                                            salary_text = f"от {salary['from']} {salary.get('currency', '')}"
                                        elif salary.get("to"):
                                            salary_text = f"до {salary['to']} {salary.get('currency', '')}"
                                        else:
                                            salary_text = ""
                                        if salary_text:
                                            vacancy_text += f"Зарплата: {salary_text}\n"
                                    
                                    # Опыт, тип занятости, график
                                    experience = vacancy_data.get("experience", {}).get("name", "")
                                    if experience:
                                        vacancy_text += f"Опыт: {experience}\n"
                                    employment = vacancy_data.get("employment", {}).get("name", "")
                                    if employment:
                                        vacancy_text += f"Тип занятости: {employment}\n"
                                    schedule = vacancy_data.get("schedule", {}).get("name", "")
                                    if schedule:
                                        vacancy_text += f"График: {schedule}\n"
                                    
                                    vacancy_text += f"\n{description}"
                                    
                                    vacancy["text"] = vacancy_text
                                    vacancy["title"] = title
                                    vacancy["channel"] = f"HeadHunter - {company_name}"
                                    
                                    # Обновляем ссылку, если есть
                                    alternate_url = vacancy_data.get("alternate_url")
                                    if alternate_url:
                                        vacancy["link"] = alternate_url
                                
                                return vacancy
                            else:
                                # Другой статус - используем данные из списка
                                log.debug(f"HeadHunter: статус {response.status} для {vacancy_id}, используем данные из списка")
                                return vacancy
                    except aiohttp.ClientError as e:
                        # Ошибка сети - используем данные из списка
                        log.debug(f"HeadHunter: ошибка сети для {vacancy_id}: {e}, используем данные из списка")
                        return vacancy
                    except Exception as e:
                        # Любая другая ошибка - используем данные из списка
                        log.debug(f"HeadHunter: ошибка получения полного описания {vacancy_id}: {e}, используем данные из списка")
                        return vacancy
                
                return vacancy
            
            # Если данных из списка нет, пробуем получить полное описание
            # (это редко, но может быть)
            try:
                async with session.get(f"{self.api_url}/vacancies/{vacancy_id}") as response:
                    if response.status == 403:
                        log.warning(f"HeadHunter: 403 для {vacancy_id}, нет данных в списке - пропускаем")
                        return None
                    
                    if response.status != 200:
                        log.warning(f"HeadHunter: статус {response.status} для {vacancy_id} - пропускаем")
                        return None
                    
                    vacancy_data = await response.json()
                    
                    # Извлекаем данные
                    title = vacancy_data.get("name", "")
                    description = vacancy_data.get("description", "")
                    company_name = vacancy_data.get("employer", {}).get("name", "Не указано")
                    
                    # Зарплата
                    salary = vacancy_data.get("salary")
                    salary_text = ""
                    if salary:
                        if salary.get("from") and salary.get("to"):
                            salary_text = f"{salary['from']} - {salary['to']} {salary.get('currency', '')}"
                        elif salary.get("from"):
                            salary_text = f"от {salary['from']} {salary.get('currency', '')}"
                        elif salary.get("to"):
                            salary_text = f"до {salary['to']} {salary.get('currency', '')}"
                    
                    # Опыт работы
                    experience = vacancy_data.get("experience", {}).get("name", "")
                    
                    # Тип занятости
                    employment = vacancy_data.get("employment", {}).get("name", "")
                    
                    # График работы
                    schedule = vacancy_data.get("schedule", {}).get("name", "")
                    
                    # Дата публикации
                    published_at = vacancy_data.get("published_at", "")
                    try:
                        if published_at:
                            pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                        else:
                            pub_date = datetime.now()
                    except:
                        pub_date = datetime.now()
                    
                    # Ссылка на вакансию
                    alternate_url = vacancy_data.get("alternate_url", f"https://hh.ru/vacancy/{vacancy_id}")
                    
                    # Формируем текст вакансии
                    vacancy_text = f"{title}\n\n"
                    vacancy_text += f"Компания: {company_name}\n"
                    
                    if salary_text:
                        vacancy_text += f"Зарплата: {salary_text}\n"
                    if experience:
                        vacancy_text += f"Опыт: {experience}\n"
                    if employment:
                        vacancy_text += f"Тип занятости: {employment}\n"
                    if schedule:
                        vacancy_text += f"График: {schedule}\n"
                    
                    vacancy_text += f"\n{description}"
                    
                    # Создаем словарь вакансии
                    vacancy = self.create_vacancy_dict(
                        text=vacancy_text,
                        channel=f"HeadHunter - {company_name}",
                        date=pub_date,
                        link=alternate_url,
                        title=title
                    )
                    
                    return vacancy
            except aiohttp.ClientError as e:
                log.error(f"HeadHunter: ошибка сети при получении вакансии {vacancy_id}: {e}")
                return None
            except Exception as e:
                log.error(f"HeadHunter: ошибка получения описания вакансии {vacancy_id}: {e}")
                return None
            
        except Exception as e:
            log.error(f"HeadHunter: ошибка парсинга элемента вакансии: {e}")
            return None
    
    def _create_vacancy_from_item(self, item: Dict) -> Optional[Dict]:
        """Создает вакансию из данных списка (без полного описания)"""
        try:
            vacancy_id = item.get("id")
            if not vacancy_id:
                return None
            
            title = item.get("name", "")
            snippet = item.get("snippet", {}).get("requirement", "") or item.get("snippet", {}).get("responsibility", "")
            company_name = item.get("employer", {}).get("name", "Не указано")
            
            # Зарплата из списка
            salary = item.get("salary")
            salary_text = ""
            if salary:
                if salary.get("from") and salary.get("to"):
                    salary_text = f"{salary['from']} - {salary['to']} {salary.get('currency', '')}"
                elif salary.get("from"):
                    salary_text = f"от {salary['from']} {salary.get('currency', '')}"
                elif salary.get("to"):
                    salary_text = f"до {salary['to']} {salary.get('currency', '')}"
            
            # Дата публикации
            published_at = item.get("published_at", "")
            try:
                if published_at:
                    pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                else:
                    pub_date = datetime.now()
            except:
                pub_date = datetime.now()
            
            # Ссылка
            alternate_url = item.get("alternate_url", f"https://hh.ru/vacancy/{vacancy_id}")
            
            # Формируем текст
            vacancy_text = f"{title}\n\n"
            vacancy_text += f"Компания: {company_name}\n"
            if salary_text:
                vacancy_text += f"Зарплата: {salary_text}\n"
            if snippet:
                vacancy_text += f"\n{snippet}"
            else:
                vacancy_text += "\nОписание: Полное описание недоступно. См. ссылку на вакансию."
            
            vacancy = self.create_vacancy_dict(
                text=vacancy_text,
                channel=f"HeadHunter - {company_name}",
                date=pub_date,
                link=alternate_url,
                title=title
            )
            
            return vacancy
            
        except Exception as e:
            log.error(f"HeadHunter: ошибка создания вакансии из списка: {e}")
            return None
