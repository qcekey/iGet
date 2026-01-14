"""
Модуль для детекции дубликатов вакансий

Использует несколько стратегий:
1. Проверка по ссылке (link) - самый надежный способ
2. Проверка по комбинации title + company
3. Проверка по извлеченному ID из ссылки (для HeadHunter, LinkedIn)
4. Проверка по текстовому сходству (fuzzy matching)
"""
import re
import logging
from typing import List, Dict, Optional, Tuple, Set
from urllib.parse import urlparse, parse_qs
from difflib import SequenceMatcher

log = logging.getLogger("duplicate_detector")


class DuplicateDetector:
    """Детектор дубликатов вакансий"""
    
    def __init__(self, similarity_threshold: float = 0.85):
        """
        Args:
            similarity_threshold: Порог схожести для текстового сравнения (0.0-1.0)
        """
        self.similarity_threshold = similarity_threshold
    
    def extract_vacancy_id_from_link(self, link: str) -> Optional[str]:
        """
        Извлекает ID вакансии из ссылки
        
        Поддерживает:
        - HeadHunter: https://hh.ru/vacancy/12345678
        - LinkedIn: https://www.linkedin.com/jobs/view/1234567890
        - Telegram: может содержать ссылку на hh.ru или linkedin.com
        """
        if not link:
            return None
        
        # HeadHunter
        hh_pattern = r'hh\.ru/vacancy/(\d+)'
        match = re.search(hh_pattern, link)
        if match:
            return f"hh_{match.group(1)}"
        
        # LinkedIn
        linkedin_pattern = r'linkedin\.com/jobs/view/(\d+)'
        match = re.search(linkedin_pattern, link)
        if match:
            return f"li_{match.group(1)}"
        
        return None
    
    def normalize_text(self, text: str) -> str:
        """Нормализует текст для сравнения"""
        if not text:
            return ""
        
        # Приводим к нижнему регистру
        text = text.lower()
        
        # Удаляем лишние пробелы
        text = re.sub(r'\s+', ' ', text)
        
        # Удаляем HTML теги
        text = re.sub(r'<[^>]+>', '', text)
        
        # Удаляем спецсимволы (оставляем только буквы, цифры, пробелы)
        text = re.sub(r'[^\w\s]', '', text)
        
        return text.strip()
    
    def extract_company_from_channel(self, channel: str) -> Optional[str]:
        """Извлекает название компании из channel"""
        if not channel:
            return None
        
        # Формат: "HeadHunter - Название компании" или "LinkedIn - Название компании"
        parts = channel.split(' - ', 1)
        if len(parts) == 2:
            return parts[1].strip()
        
        return None
    
    def text_similarity(self, text1: str, text2: str) -> float:
        """Вычисляет схожесть двух текстов (0.0-1.0)"""
        if not text1 or not text2:
            return 0.0
        
        norm1 = self.normalize_text(text1)
        norm2 = self.normalize_text(text2)
        
        if not norm1 or not norm2:
            return 0.0
        
        # Используем SequenceMatcher для сравнения
        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        
        return similarity
    
    def title_similarity(self, title1: str, title2: str) -> float:
        """Вычисляет схожесть заголовков"""
        if not title1 or not title2:
            return 0.0
        
        # Нормализуем заголовки
        norm1 = self.normalize_text(title1)
        norm2 = self.normalize_text(title2)
        
        if norm1 == norm2:
            return 1.0
        
        # Проверяем, содержит ли один заголовок другой
        if norm1 in norm2 or norm2 in norm1:
            return 0.9
        
        # Вычисляем схожесть
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    def is_duplicate_by_link(self, vacancy: Dict, existing_vacancies: List[Dict]) -> Optional[Dict]:
        """
        Проверяет дубликат по ссылке (самый надежный способ)
        
        Returns:
            Найденный дубликат или None
        """
        vacancy_link = vacancy.get("link", "").strip()
        if not vacancy_link:
            return None
        
        # Нормализуем ссылку (убираем параметры, фрагменты)
        parsed = urlparse(vacancy_link)
        normalized_link = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".lower()
        
        for existing in existing_vacancies:
            existing_link = existing.get("link", "").strip()
            if not existing_link:
                continue
            
            existing_parsed = urlparse(existing_link)
            existing_normalized = f"{existing_parsed.scheme}://{existing_parsed.netloc}{existing_parsed.path}".lower()
            
            # Точное совпадение нормализованных ссылок
            if normalized_link == existing_normalized:
                return existing
            
            # Проверяем, содержит ли одна ссылка другую (для разных форматов)
            if normalized_link in existing_normalized or existing_normalized in normalized_link:
                return existing
        
        return None
    
    def is_duplicate_by_id(self, vacancy: Dict, existing_vacancies: List[Dict]) -> Optional[Dict]:
        """
        Проверяет дубликат по извлеченному ID из ссылки
        
        Returns:
            Найденный дубликат или None
        """
        vacancy_id = self.extract_vacancy_id_from_link(vacancy.get("link", ""))
        if not vacancy_id:
            return None
        
        for existing in existing_vacancies:
            existing_id = self.extract_vacancy_id_from_link(existing.get("link", ""))
            if existing_id and vacancy_id == existing_id:
                return existing
        
        return None
    
    def is_duplicate_by_title_company(self, vacancy: Dict, existing_vacancies: List[Dict]) -> Optional[Dict]:
        """
        Проверяет дубликат по комбинации title + company
        
        Returns:
            Найденный дубликат или None
        """
        vacancy_title = vacancy.get("title", "").strip()
        vacancy_company = self.extract_company_from_channel(vacancy.get("channel", ""))
        
        if not vacancy_title:
            return None
        
        vacancy_title_norm = self.normalize_text(vacancy_title)
        
        for existing in existing_vacancies:
            existing_title = existing.get("title", "").strip()
            existing_company = self.extract_company_from_channel(existing.get("channel", ""))
            
            if not existing_title:
                continue
            
            existing_title_norm = self.normalize_text(existing_title)
            
            # Проверяем совпадение заголовков
            title_sim = self.title_similarity(vacancy_title, existing_title)
            
            if title_sim >= 0.9:  # Очень похожие заголовки
                # Если компании совпадают или обе не указаны - это дубликат
                if vacancy_company and existing_company:
                    if self.normalize_text(vacancy_company) == self.normalize_text(existing_company):
                        return existing
                elif not vacancy_company and not existing_company:
                    return existing
        
        return None
    
    def is_duplicate_by_text_similarity(self, vacancy: Dict, existing_vacancies: List[Dict]) -> Optional[Dict]:
        """
        Проверяет дубликат по текстовому сходству
        
        Returns:
            Найденный дубликат или None
        """
        vacancy_text = vacancy.get("text", "")
        vacancy_title = vacancy.get("title", "")
        
        if not vacancy_text and not vacancy_title:
            return None
        
        # Создаем комбинированный текст для сравнения
        vacancy_combined = f"{vacancy_title} {vacancy_text}" if vacancy_title else vacancy_text
        
        for existing in existing_vacancies:
            existing_text = existing.get("text", "")
            existing_title = existing.get("title", "")
            
            if not existing_text and not existing_title:
                continue
            
            existing_combined = f"{existing_title} {existing_text}" if existing_title else existing_text
            
            # Сравниваем тексты
            similarity = self.text_similarity(vacancy_combined, existing_combined)
            
            if similarity >= self.similarity_threshold:
                # Дополнительная проверка: заголовки тоже должны быть похожи
                if vacancy_title and existing_title:
                    title_sim = self.title_similarity(vacancy_title, existing_title)
                    if title_sim >= 0.7:  # Заголовки должны быть похожи
                        return existing
                else:
                    return existing
        
        return None
    
    def find_duplicate(self, vacancy: Dict, existing_vacancies: List[Dict]) -> Optional[Dict]:
        """
        Ищет дубликат вакансии используя все доступные методы
        
        Проверяет в следующем порядке (от наиболее надежных к менее надежным):
        1. По ссылке
        2. По ID из ссылки
        3. По title + company
        4. По текстовому сходству
        
        Returns:
            Найденный дубликат или None
        """
        if not existing_vacancies:
            return None
        
        # 1. Проверка по ссылке (самый надежный)
        duplicate = self.is_duplicate_by_link(vacancy, existing_vacancies)
        if duplicate:
            log.debug(f"Дубликат найден по ссылке: {vacancy.get('link', '')[:50]}...")
            return duplicate
        
        # 2. Проверка по ID из ссылки
        duplicate = self.is_duplicate_by_id(vacancy, existing_vacancies)
        if duplicate:
            log.debug(f"Дубликат найден по ID: {self.extract_vacancy_id_from_link(vacancy.get('link', ''))}")
            return duplicate
        
        # 3. Проверка по title + company
        duplicate = self.is_duplicate_by_title_company(vacancy, existing_vacancies)
        if duplicate:
            log.debug(f"Дубликат найден по title+company: {vacancy.get('title', '')[:30]}...")
            return duplicate
        
        # 4. Проверка по текстовому сходству (самый медленный, но самый гибкий)
        duplicate = self.is_duplicate_by_text_similarity(vacancy, existing_vacancies)
        if duplicate:
            log.debug(f"Дубликат найден по текстовому сходству: {vacancy.get('title', '')[:30]}...")
            return duplicate
        
        return None
    
    def find_all_duplicates(self, vacancies: List[Dict]) -> List[Tuple[Dict, Dict]]:
        """
        Находит все дубликаты в списке вакансий
        
        Returns:
            Список кортежей (вакансия, дубликат)
        """
        duplicates = []
        seen = set()
        
        for i, vacancy in enumerate(vacancies):
            vacancy_id = vacancy.get("id")
            if vacancy_id in seen:
                continue
            
            # Ищем дубликаты среди оставшихся вакансий
            remaining = vacancies[i+1:]
            duplicate = self.find_duplicate(vacancy, remaining)
            
            if duplicate:
                duplicates.append((vacancy, duplicate))
                seen.add(vacancy_id)
                seen.add(duplicate.get("id"))
        
        return duplicates
    
    def merge_duplicates(self, vacancy: Dict, duplicate: Dict) -> Dict:
        """
        Объединяет два дубликата в одну вакансию
        
        Сохраняет:
        - Более полное описание
        - Все уникальные ссылки
        - Более раннюю дату
        - Все источники
        """
        merged = vacancy.copy()
        
        # Объединяем ссылки
        links = {vacancy.get("link", ""), duplicate.get("link", "")}
        links.discard("")
        if links:
            merged["link"] = list(links)[0]  # Основная ссылка
            if len(links) > 1:
                merged["alternate_links"] = list(links)[1:]
        
        # Выбираем более полное описание
        if len(duplicate.get("text", "")) > len(vacancy.get("text", "")):
            merged["text"] = duplicate.get("text", "")
            merged["title"] = duplicate.get("title", merged.get("title", ""))
        
        # Выбираем более раннюю дату
        try:
            from datetime import datetime
            date1 = datetime.strptime(vacancy.get("date", ""), "%Y-%m-%d %H:%M:%S")
            date2 = datetime.strptime(duplicate.get("date", ""), "%Y-%m-%d %H:%M:%S")
            if date2 < date1:
                merged["date"] = duplicate.get("date", "")
        except:
            pass
        
        # Объединяем источники
        sources = {vacancy.get("source", ""), duplicate.get("source", "")}
        sources.discard("")
        if len(sources) > 1:
            merged["sources"] = list(sources)
        
        # Добавляем метаданные о слиянии
        merged["merged_from"] = [vacancy.get("id"), duplicate.get("id")]
        merged["is_duplicate_merged"] = True
        
        return merged


def check_duplicate(vacancy: Dict, existing_vacancies: List[Dict], similarity_threshold: float = 0.85) -> Optional[Dict]:
    """
    Удобная функция для проверки дубликата одной вакансии
    
    Args:
        vacancy: Вакансия для проверки
        existing_vacancies: Список существующих вакансий
        similarity_threshold: Порог схожести для текстового сравнения
    
    Returns:
        Найденный дубликат или None
    """
    detector = DuplicateDetector(similarity_threshold=similarity_threshold)
    return detector.find_duplicate(vacancy, existing_vacancies)


def find_all_duplicates_in_file(vacancies_file: str = "data/vacancies.json", similarity_threshold: float = 0.85) -> List[Tuple[Dict, Dict]]:
    """
    Находит все дубликаты в файле вакансий
    
    Args:
        vacancies_file: Путь к файлу с вакансиями
        similarity_threshold: Порог схожести для текстового сравнения
    
    Returns:
        Список кортежей (вакансия, дубликат)
    """
    import json
    from pathlib import Path
    
    file_path = Path(vacancies_file)
    if not file_path.exists():
        log.warning(f"Файл {vacancies_file} не найден")
        return []
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            vacancies = json.load(f)
    except Exception as e:
        log.error(f"Ошибка чтения файла {vacancies_file}: {e}")
        return []
    
    detector = DuplicateDetector(similarity_threshold=similarity_threshold)
    return detector.find_all_duplicates(vacancies)
