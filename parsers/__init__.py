"""
Модуль парсеров вакансий с различных платформ
"""
from .base_parser import BaseParser
from .headhunter_parser import HeadHunterParser
from .linkedin_parser import LinkedInParser, LinkedInSeleniumParser

__all__ = ['BaseParser', 'HeadHunterParser', 'LinkedInParser', 'LinkedInSeleniumParser']
