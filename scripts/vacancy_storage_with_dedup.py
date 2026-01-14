"""
Обертка для сохранения вакансий с проверкой дубликатов
"""
import logging
from typing import Dict, Optional
from iget.vacancy_storage import save_vacancy, load_all_vacancies
from duplicate_detector import DuplicateDetector, check_duplicate

log = logging.getLogger("vacancy_storage_dedup")


def save_vacancy_with_dedup(
    vacancy: Dict,
    check_duplicates: bool = True,
    similarity_threshold: float = 0.85,
    merge_duplicates: bool = False
) -> Dict[str, any]:
    """
    Сохраняет вакансию с проверкой дубликатов
    
    Args:
        vacancy: Вакансия для сохранения
        check_duplicates: Включить проверку дубликатов
        similarity_threshold: Порог схожести для текстового сравнения (0.0-1.0)
        merge_duplicates: Объединять дубликаты вместо пропуска
    
    Returns:
        Словарь с результатом:
        {
            "saved": bool,  # Сохранена ли вакансия
            "is_duplicate": bool,  # Является ли дубликатом
            "duplicate_id": str,  # ID найденного дубликата (если есть)
            "merged": bool  # Была ли вакансия объединена с дубликатом
        }
    """
    result = {
        "saved": False,
        "is_duplicate": False,
        "duplicate_id": None,
        "merged": False
    }
    
    if not check_duplicates:
        # Просто сохраняем без проверки
        save_vacancy(vacancy)
        result["saved"] = True
        return result
    
    # Загружаем существующие вакансии
    existing_vacancies = load_all_vacancies()
    
    # Проверяем на дубликаты
    detector = DuplicateDetector(similarity_threshold=similarity_threshold)
    duplicate = detector.find_duplicate(vacancy, existing_vacancies)
    
    if duplicate:
        result["is_duplicate"] = True
        result["duplicate_id"] = duplicate.get("id")
        
        log.info(f"Найден дубликат: {vacancy.get('title', '')[:50]}... (ID: {duplicate.get('id', '')[:8]}...)")
        log.info(f"  Новая вакансия: {vacancy.get('link', '')[:80]}")
        log.info(f"  Существующая: {duplicate.get('link', '')[:80]}")
        
        if merge_duplicates:
            # Объединяем дубликаты
            merged = detector.merge_duplicates(vacancy, duplicate)
            
            # Удаляем старую вакансию и добавляем объединенную
            from iget.vacancy_storage import VACANCIES_FILE
            import json
            
            vacancies = load_all_vacancies()
            # Удаляем дубликат
            vacancies = [v for v in vacancies if v.get("id") != duplicate.get("id")]
            # Добавляем объединенную
            merged["added_at"] = vacancy.get("added_at", duplicate.get("added_at"))
            merged["is_new"] = True
            vacancies.append(merged)
            
            # Сохраняем
            try:
                with open(VACANCIES_FILE, "w", encoding="utf-8") as f:
                    json.dump(vacancies, f, ensure_ascii=False, indent=2)
                log.info(f"Дубликаты объединены: {merged.get('id', '')[:8]}...")
                result["saved"] = True
                result["merged"] = True
            except Exception as e:
                log.error(f"Ошибка сохранения объединенной вакансии: {e}")
        else:
            # Просто пропускаем дубликат
            log.debug(f"Дубликат пропущен: {vacancy.get('title', '')[:50]}...")
    else:
        # Дубликатов нет, сохраняем
        save_vacancy(vacancy)
        result["saved"] = True
        log.debug(f"Вакансия сохранена: {vacancy.get('title', '')[:50]}...")
    
    return result


def get_duplicate_stats(vacancies_file: str = "data/vacancies.json") -> Dict:
    """
    Получает статистику по дубликатам в файле
    
    Returns:
        Словарь со статистикой:
        {
            "total": int,
            "duplicates_count": int,
            "duplicate_pairs": List[Tuple[Dict, Dict]]
        }
    """
    from duplicate_detector import find_all_duplicates_in_file
    
    duplicate_pairs = find_all_duplicates_in_file(vacancies_file)
    
    # Собираем уникальные ID дубликатов
    duplicate_ids = set()
    for vac1, vac2 in duplicate_pairs:
        duplicate_ids.add(vac1.get("id"))
        duplicate_ids.add(vac2.get("id"))
    
    from iget.vacancy_storage import load_all_vacancies
    all_vacancies = load_all_vacancies()
    
    return {
        "total": len(all_vacancies),
        "duplicates_count": len(duplicate_ids),
        "duplicate_pairs": len(duplicate_pairs),
        "unique_vacancies": len(all_vacancies) - len(duplicate_ids)
    }
