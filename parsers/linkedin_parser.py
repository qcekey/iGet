"""
Парсер вакансий с LinkedIn
Внимание: LinkedIn имеет защиту от парсинга, поэтому используйте осторожно
"""
import asyncio
import aiohttp
from typing import List, Dict, Optional
from datetime import datetime
import logging

from .base_parser import BaseParser
from iget.models import VacancySource

log = logging.getLogger("linkedin_parser")


class LinkedInParser(BaseParser):
    """Парсер вакансий с LinkedIn"""
    
    def __init__(self, email: str = None, password: str = None):
        super().__init__(VacancySource.LINKEDIN)
        self.base_url = "https://www.linkedin.com"
        self.email = email
        self.password = password
        self.session = None
        self.cookies = None
    
    async def _get_session(self):
        """Создает aiohttp сессию"""
        if not self.session:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            }
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers=headers,
                cookies=self.cookies
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
        location: str = "",
        days_back: int = 7,
        max_results: int = 100
    ) -> List[Dict]:
        """
        Парсит вакансии с LinkedIn
        
        Внимание: LinkedIn активно блокирует парсинг. 
        Для работы может потребоваться:
        1. Авторизация через браузер
        2. Использование прокси
        3. Очень медленные запросы с задержками
        
        Args:
            search_query: Поисковый запрос
            location: Локация (например, "Moscow, Russia")
            days_back: Сколько дней назад искать
            max_results: Максимальное количество результатов
        """
        log.warning("LinkedIn парсинг может быть заблокирован. Используйте осторожно!")
        
        session = await self._get_session()
        vacancies = []
        
        try:
            # LinkedIn использует сложную систему поиска через JavaScript
            # Простой парсинг HTML может не работать
            # Рекомендуется использовать официальный API LinkedIn или Selenium
            
            # Базовый URL поиска
            search_url = f"{self.base_url}/jobs/search"
            params = {
                "keywords": search_query,
            }
            if location:
                params["location"] = location
            
            # Пробуем получить страницу
            try:
                async with session.get(search_url, params=params) as response:
                    if response.status != 200:
                        log.warning(f"LinkedIn вернул статус {response.status}")
                        log.warning("LinkedIn может требовать авторизацию или блокировать запросы")
                        return []
                    
                    html = await response.text()
                    
                    # Парсим HTML (это упрощенный вариант, может не работать)
                    # LinkedIn загружает данные через JavaScript, поэтому нужен Selenium
                    log.warning("Парсинг LinkedIn через простой HTTP запрос может не работать")
                    log.warning("Рекомендуется использовать Selenium или официальный API")
                    
            except aiohttp.ClientError as e:
                log.error(f"Ошибка запроса к LinkedIn: {e}")
                log.error("LinkedIn может блокировать автоматические запросы")
            
        except Exception as e:
            log.error(f"Критическая ошибка парсинга LinkedIn: {e}")
        finally:
            await self.close()
        
        return vacancies


class LinkedInSeleniumParser(BaseParser):
    """
    Парсер LinkedIn с использованием Selenium
    Требует установки selenium и chromedriver
    """
    def __init__(self, email: str = None, password: str = None, headless: bool = False):
        super().__init__(VacancySource.LINKEDIN)
        self.email = email
        self.password = password
        self.headless = headless
        self.driver = None
    
    def _setup_driver(self):
        """Настройка Selenium WebDriver"""
        import os
        
        # Сначала пробуем Chrome, если не получится - Edge
        try:
            self._setup_chrome_driver()
            return
        except Exception as chrome_error:
            log.warning(f"LinkedIn: Chrome не удалось запустить: {chrome_error}")
            log.info("LinkedIn: пробуем использовать Microsoft Edge...")
        
        try:
            self._setup_edge_driver()
            return
        except Exception as edge_error:
            log.error(f"LinkedIn: Edge тоже не удалось запустить: {edge_error}")
            raise Exception(f"Не удалось запустить ни Chrome, ни Edge. Chrome: {chrome_error}, Edge: {edge_error}")
    
    def _setup_chrome_driver(self):
        """Настройка Chrome WebDriver"""
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        import os
        import tempfile
        
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless=new')
        
        # ВАЖНО: Используем отдельный профиль для парсера (не основной профиль Chrome)
        # Это позволяет сохранять куки между запусками
        profile_path = os.path.join(tempfile.gettempdir(), "linkedin_parser_profile")
        os.makedirs(profile_path, exist_ok=True)
        chrome_options.add_argument(f'--user-data-dir={profile_path}')
        chrome_options.add_argument('--profile-directory=Default')
        log.info(f"LinkedIn: профиль Chrome: {profile_path}")
        
        # Основные опции для стабильной работы
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--start-maximized')
        
        # Отключаем проблемные функции Chrome
        chrome_options.add_argument('--disable-features=OptimizationGuideModelDownloading,OptimizationHintsFetching,OptimizationTargetPrediction,OptimizationHints,TranslateUI')
        chrome_options.add_argument('--disable-background-networking')
        chrome_options.add_argument('--disable-client-side-phishing-detection')
        chrome_options.add_argument('--disable-default-apps')
        chrome_options.add_argument('--disable-hang-monitor')
        chrome_options.add_argument('--disable-popup-blocking')
        chrome_options.add_argument('--disable-prompt-on-repost')
        chrome_options.add_argument('--disable-sync')
        chrome_options.add_argument('--disable-translate')
        chrome_options.add_argument('--metrics-recording-only')
        chrome_options.add_argument('--no-first-run')
        chrome_options.add_argument('--safebrowsing-disable-auto-update')
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--disable-notifications')
        
        # КРИТИЧНЫЕ антидетект опции для LinkedIn
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Актуальный user-agent (Chrome 130+)
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36')
        
        # Добавляем настройки для обхода детектирования
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        
        # Пробуем найти Chrome в стандартных местах Windows
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ]
        
        for chrome_path in chrome_paths:
            if os.path.exists(chrome_path):
                log.info(f"LinkedIn: найден Chrome: {chrome_path}")
                chrome_options.binary_location = chrome_path
                break
        
        # Устанавливаем ChromeDriver
        log.info("LinkedIn: устанавливаем/проверяем ChromeDriver...")
        service = Service(ChromeDriverManager().install())
        
        log.info("LinkedIn: запускаем Chrome...")
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.implicitly_wait(10)
        
        # Убираем ВСЕ признаки автоматизации через CDP
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en', 'ru']});
                window.chrome = {runtime: {}};
            '''
        })
        log.info("LinkedIn: Chrome успешно запущен")
    
    def _setup_edge_driver(self):
        """Настройка Edge WebDriver (fallback если Chrome не работает)"""
        from selenium import webdriver
        from selenium.webdriver.edge.options import Options
        from selenium.webdriver.edge.service import Service
        from webdriver_manager.microsoft import EdgeChromiumDriverManager
        
        edge_options = Options()
        if self.headless:
            edge_options.add_argument('--headless=new')
        
        # Основные опции
        edge_options.add_argument('--no-sandbox')
        edge_options.add_argument('--disable-dev-shm-usage')
        edge_options.add_argument('--disable-gpu')
        edge_options.add_argument('--window-size=1920,1080')
        edge_options.add_argument('--start-maximized')
        
        # Антидетект опции
        edge_options.add_argument('--disable-blink-features=AutomationControlled')
        edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        edge_options.add_experimental_option('useAutomationExtension', False)
        edge_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0')
        
        log.info("LinkedIn: устанавливаем/проверяем EdgeDriver...")
        service = Service(EdgeChromiumDriverManager().install())
        
        log.info("LinkedIn: запускаем Edge...")
        self.driver = webdriver.Edge(service=service, options=edge_options)
        self.driver.implicitly_wait(10)
        
        # Убираем признаки автоматизации
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        log.info("LinkedIn: Edge успешно запущен")
    
    async def parse_vacancies(
        self,
        search_query: str = "",
        location: str = "",
        days_back: int = 7,
        max_results: int = 50
    ) -> List[Dict]:
        """
        Парсит вакансии с LinkedIn используя Selenium
        """
        if not self.driver:
            self._setup_driver()
        
        vacancies = []
        
        try:
            # Проверяем наличие учетных данных
            if not self.email or not self.password:
                log.warning("LinkedIn: email или password не указаны. Парсинг может быть ограничен.")
                log.warning("LinkedIn: рекомендуется указать учетные данные в настройках для полного доступа.")
            
            # Авторизация (если указаны учетные данные)
            if self.email and self.password:
                log.info("LinkedIn: выполняем авторизацию...")
                login_success = await self._login()
                if not login_success:
                    log.warning("LinkedIn: авторизация не удалась, продолжаем без авторизации")
                else:
                    log.info("LinkedIn: авторизация успешна")
            else:
                log.info("LinkedIn: пропускаем авторизацию (учетные данные не указаны)")
            
            # Поиск вакансий
            search_url = f"https://www.linkedin.com/jobs/search/?keywords={search_query.replace(' ', '%20')}"
            if location:
                search_url += f"&location={location.replace(' ', '%20')}"
            
            log.info(f"LinkedIn: открываем страницу поиска: {search_url}")
            
            try:
                self.driver.get(search_url)
            except Exception as nav_error:
                log.error(f"LinkedIn: ошибка при переходе на страницу: {nav_error}")
                # Пробуем переподключиться
                try:
                    self._setup_driver()
                    self.driver.get(search_url)
                except:
                    log.error("LinkedIn: не удалось восстановить соединение с браузером")
                    return []
            
            # Ждем загрузки страницы (увеличенная задержка)
            log.info("LinkedIn: ожидаем загрузки страницы...")
            await asyncio.sleep(8)
            
            # Проверяем, что браузер еще работает
            try:
                current_url = self.driver.current_url
                log.info(f"LinkedIn: текущий URL: {current_url}")
            except Exception as e:
                log.error(f"LinkedIn: потеряно соединение с браузером: {e}")
                return []
            
            # Проверяем, не требуется ли авторизация
            try:
                page_source = self.driver.page_source.lower()
            except Exception as e:
                log.error(f"LinkedIn: не удалось получить страницу: {e}")
                return []
                
            if 'sign in' in page_source or 'войти' in page_source or 'login' in page_source:
                if 'jobs' not in self.driver.current_url.lower():
                    log.warning("LinkedIn: похоже, требуется авторизация для доступа к вакансиям")
                    if not self.email or not self.password:
                        log.error("LinkedIn: для парсинга требуется авторизация, но email/password не указаны")
                        return []
            
            # Импортируем необходимые модули
            from selenium.webdriver.common.by import By
            from bs4 import BeautifulSoup
            
            # Даём странице 3 секунды на загрузку
            log.info("LinkedIn: ждем загрузки списка вакансий...")
            await asyncio.sleep(3)
            
            # Прокручиваем страницу вниз несколько раз для загрузки вакансий
            log.info("LinkedIn: прокручиваем страницу...")
            for i in range(3):
                try:
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    await asyncio.sleep(1.5)
                    self.driver.execute_script("window.scrollTo(0, 0);")
                    await asyncio.sleep(0.5)
                except Exception as e:
                    log.warning(f"LinkedIn: ошибка прокрутки: {e}")
                    break
            
            # Получаем HTML страницы
            log.info("LinkedIn: анализируем страницу...")
            try:
                page_html = self.driver.page_source
            except Exception as e:
                log.error(f"LinkedIn: ошибка получения HTML: {e}")
                return []
            
            # Сохраняем HTML для отладки
            try:
                with open("linkedin_debug.html", "w", encoding="utf-8") as f:
                    f.write(page_html)
                log.info("LinkedIn: HTML сохранен в linkedin_debug.html")
            except:
                pass
            
            soup = BeautifulSoup(page_html, 'html.parser')
            
            # Ищем вакансии - пробуем много разных селекторов
            job_cards = []
            
            # Селекторы для АВТОРИЗОВАННЫХ пользователей (самые актуальные)
            selectors = [
                'li.ember-view.occludable-update',
                'li[data-occludable-job-id]',
                'div.job-card-container',
                'li.jobs-search-results__list-item',
                'div.jobs-search-results__list-item',
                'li.scaffold-layout__list-item',
                # Для гостей
                'div.base-card.base-search-card',
                'div.job-search-card',
                'li.result-card',
            ]
            
            for selector in selectors:
                job_cards = soup.select(selector)
                if job_cards:
                    log.info(f"LinkedIn: найдено {len(job_cards)} карточек с селектором: {selector}")
                    break
            
            # Если не нашли - ищем все ссылки на вакансии
            if not job_cards:
                log.info("LinkedIn: ищем ссылки на вакансии напрямую...")
                job_links = soup.select('a[href*="/jobs/view/"]')
                log.info(f"LinkedIn: найдено {len(job_links)} ссылок на вакансии")
                
                if job_links:
                    # Парсим вакансии из ссылок
                    seen_links = set()
                    for link_elem in job_links[:max_results]:
                        try:
                            href = link_elem.get('href', '')
                            if not href or href in seen_links:
                                continue
                            seen_links.add(href)
                            
                            if not href.startswith('http'):
                                href = f"https://www.linkedin.com{href}"
                            
                            title = link_elem.get_text(strip=True)
                            if not title or len(title) < 3:
                                continue
                            
                            # Ищем компанию рядом
                            parent = link_elem.find_parent(['li', 'div', 'article'])
                            company = "LinkedIn"
                            if parent:
                                # Ищем текст компании
                                company_elem = parent.select_one('span.job-card-container__primary-description, a.job-card-container__company-name, h4, span.base-search-card__subtitle')
                                if company_elem:
                                    company = company_elem.get_text(strip=True)
                            
                            vacancy_text = f"{title}\n\nКомпания: {company}\nИсточник: LinkedIn"
                            
                            vacancy = self.create_vacancy_dict(
                                text=vacancy_text,
                                channel=f"LinkedIn - {company}",
                                date=datetime.now(),
                                link=href,
                                title=title
                            )
                            vacancies.append(vacancy)
                            log.info(f"LinkedIn: добавлена вакансия: {title[:50]}...")
                            
                        except Exception as e:
                            log.debug(f"LinkedIn: ошибка обработки ссылки: {e}")
                            continue
                    
                    log.info(f"LinkedIn: найдено {len(vacancies)} вакансий из ссылок")
                else:
                    log.warning("LinkedIn: вакансии не найдены на странице")
                    log.info(f"LinkedIn: URL: {self.driver.current_url}")
                    return []
            else:
                # Парсим найденные карточки
                log.info(f"LinkedIn: парсим {min(len(job_cards), max_results)} вакансий...")
                
                for idx, card in enumerate(job_cards[:max_results]):
                    try:
                        # Ищем ссылку на вакансию
                        link_elem = card.select_one('a[href*="/jobs/view/"], a.job-card-list__title, a.job-card-container__link')
                        if not link_elem:
                            link_elem = card.find('a')
                        
                        if not link_elem:
                            continue
                        
                        href = link_elem.get('href', '')
                        if not href:
                            continue
                        if not href.startswith('http'):
                            href = f"https://www.linkedin.com{href}"
                        
                        # Ищем заголовок
                        title = None
                        title_elem = card.select_one('strong, h3, a.job-card-list__title, span.job-card-list__title')
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                        if not title:
                            title = link_elem.get_text(strip=True)
                        if not title or len(title) < 3:
                            continue
                        
                        # Ищем компанию
                        company = "Не указано"
                        company_elem = card.select_one('span.job-card-container__primary-description, a.job-card-container__company-name, h4.base-search-card__subtitle, span.base-search-card__subtitle')
                        if company_elem:
                            company = company_elem.get_text(strip=True)
                        
                        # Ищем локацию
                        location_text = ""
                        loc_elem = card.select_one('span.job-card-container__metadata-item, li.job-card-container__metadata-item, span.job-search-card__location')
                        if loc_elem:
                            location_text = loc_elem.get_text(strip=True)
                        
                        vacancy_text = f"{title}\n\nКомпания: {company}\n"
                        if location_text:
                            vacancy_text += f"Локация: {location_text}\n"
                        vacancy_text += "Источник: LinkedIn"
                        
                        vacancy = self.create_vacancy_dict(
                            text=vacancy_text,
                            channel=f"LinkedIn - {company}",
                            date=datetime.now(),
                            link=href,
                            title=title
                        )
                        vacancies.append(vacancy)
                        log.info(f"LinkedIn: [{idx+1}] {title[:40]}... - {company}")
                        
                    except Exception as e:
                        log.debug(f"LinkedIn: ошибка парсинга карточки {idx+1}: {e}")
                        continue
                
                log.info(f"LinkedIn: успешно обработано {len(vacancies)} вакансий")
            
            # Применяем фильтрацию по дате публикации
            vacancies = self.filter_vacancies_by_date(vacancies, days_back)
            log.info(f"LinkedIn: после фильтрации по дате (days_back={days_back}): {len(vacancies)} вакансий")
            
        except Exception as e:
            log.error(f"LinkedIn: критическая ошибка парсинга: {e}", exc_info=True)
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
        
        return vacancies
    
    async def _login(self):
        """Авторизация в LinkedIn"""
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            log.info("LinkedIn: открываем страницу авторизации...")
            self.driver.get("https://www.linkedin.com/login")
            await asyncio.sleep(3)
            
            # Ждем появления поля email
            wait = WebDriverWait(self.driver, 15)
            email_input = wait.until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_input.clear()
            email_input.send_keys(self.email)
            log.debug("LinkedIn: email введен")
            
            # Вводим пароль
            password_input = wait.until(
                EC.presence_of_element_located((By.ID, "password"))
            )
            password_input.clear()
            password_input.send_keys(self.password)
            log.debug("LinkedIn: пароль введен")
            
            # Нажимаем кнопку входа
            login_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
            )
            login_button.click()
            log.debug("LinkedIn: кнопка входа нажата")
            
            # Ждем завершения авторизации
            await asyncio.sleep(5)
            
            # Проверяем, успешна ли авторизация
            current_url = self.driver.current_url
            if 'login' not in current_url.lower() and 'challenge' not in current_url.lower():
                log.info("LinkedIn: авторизация успешна")
                return True
            elif 'challenge' in current_url.lower():
                log.warning("LinkedIn: требуется дополнительная проверка (challenge)")
                log.warning("LinkedIn: возможно, нужно пройти капчу или подтверждение в браузере")
                # Ждем еще немного, может быть автоматическое подтверждение
                await asyncio.sleep(10)
                current_url = self.driver.current_url
                if 'login' not in current_url.lower():
                    log.info("LinkedIn: авторизация успешна после ожидания")
                    return True
            else:
                log.warning("LinkedIn: возможно, авторизация не удалась")
                # Проверяем наличие сообщения об ошибке
                try:
                    error_elem = self.driver.find_element(By.CSS_SELECTOR, ".alert-error, .error, [role='alert']")
                    error_text = error_elem.text
                    log.error(f"LinkedIn: ошибка авторизации: {error_text}")
                except:
                    pass
                return False
            
        except Exception as e:
            log.error(f"LinkedIn: ошибка авторизации: {e}", exc_info=True)
            return False
    
    async def _get_full_description(self, vacancy_url: str) -> Optional[str]:
        """Получает полное описание вакансии"""
        try:
            if not vacancy_url or 'linkedin.com' not in vacancy_url:
                return None
            
            self.driver.get(vacancy_url)
            await asyncio.sleep(3)
            
            # Пробуем нажать кнопку "Показать больше" если есть
            try:
                from selenium.webdriver.common.by import By
                show_more_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                    "button.show-more-less-html__button, button[aria-label*='more'], button[aria-label*='больше']")
                for button in show_more_buttons:
                    if button.is_displayed():
                        button.click()
                        await asyncio.sleep(1)
            except:
                pass
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Пробуем разные селекторы для описания
            desc_elem = None
            for selector in [
                'div.show-more-less-html__markup',
                'div.description__text',
                'div.job-details-jobs-unified-top-card__job-description',
                'div[data-testid="job-details-description"]',
                'section.job-details-section__content'
            ]:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    break
            
            if desc_elem:
                return desc_elem.get_text(separator='\n', strip=True)
        except Exception as e:
            log.debug(f"LinkedIn: ошибка получения описания для {vacancy_url}: {e}")
        
        return None
