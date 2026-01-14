"""
Базовый класс для всех парсеров вакансий
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import uuid
from iget.models import VacancySource


class BaseParser(ABC):
    """Базовый класс для всех парсеров вакансий"""
    
    def __init__(self, source: VacancySource):
        self.source = source
    
    @abstractmethod
    async def parse_vacancies(self, **kwargs) -> List[Dict]:
        """
        Основной метод парсинга вакансий
        Возвращает список словарей с вакансиями
        """
        pass
    
    def create_vacancy_dict(
        self,
        text: str,
        channel: str,
        date: Optional[datetime] = None,
        link: Optional[str] = None,
        title: Optional[str] = None
    ) -> Dict:
        """Создает стандартизированный словарь вакансии"""
        return {
            "id": str(uuid.uuid4()),
            "channel": channel,
            "text": text,
            "date": date.strftime("%Y-%m-%d %H:%M:%S") if date else datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "link": link,
            "source": self.source.value,
            "title": title,
            "is_new": True,
        }
    
    def filter_vacancies_by_date(self, vacancies: List[Dict], days_back: int) -> List[Dict]:
        """
        Фильтрует вакансии по дате публикации.
        Оставляет только те вакансии, которые были опубликованы в пределах days_back дней от текущей даты.
        
        Args:
            vacancies: Список вакансий для фильтрации
            days_back: Количество дней назад для фильтрации
            
        Returns:
            Отфильтрованный список вакансий
        """
        if not vacancies or days_back <= 0:
            return vacancies
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        filtered_vacancies = []
        
        for vacancy in vacancies:
            vacancy_date_str = vacancy.get("date", "")
            if not vacancy_date_str:
                # Если дата отсутствует, пропускаем вакансию
                continue
            
            try:
                # Парсим дату из строки (формат: "%Y-%m-%d %H:%M:%S")
                vacancy_date = datetime.strptime(vacancy_date_str, "%Y-%m-%d %H:%M:%S")
                if vacancy_date >= cutoff_date:
                    filtered_vacancies.append(vacancy)
            except (ValueError, TypeError):
                # Если не удалось распарсить дату, пропускаем вакансию
                continue
        
        return filtered_vacancies
