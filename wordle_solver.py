"""
Оптимизированный решатель Wordle с использованием Numba
Ускоряет расчеты в 10-50 раз за счет JIT-компиляции
"""

import math
import pickle
import os
import numpy as np
from typing import List, Dict, Tuple, Optional
from numba import njit, prange
import time


# ============================================================================
# Утилиты для преобразования строк в числа и обратно
# ============================================================================

def detect_language(words: List[str]) -> str:
    """Автоопределение языка по словам"""
    if not words:
        return 'en'
    
    # Проверяем первое слово
    sample = words[0].lower()
    if any('а' <= c <= 'я' for c in sample):
        return 'ru'
    elif any('a' <= c <= 'z' for c in sample):
        return 'en'
    return 'en'  # по умолчанию


def char_to_num_ru(char: str) -> int:
    """Русский: а=0, б=1, ..., я=32"""
    num = ord(char) - ord('а')
    if num < 0 or num > 32:
        raise ValueError(f"Недопустимый символ: '{char}'")
    return num


def char_to_num_en(char: str) -> int:
    """Английский: a=0, b=1, ..., z=25"""
    num = ord(char) - ord('a')
    if num < 0 or num > 25:
        raise ValueError(f"Invalid character: '{char}'")
    return num


def num_to_char_ru(num: int) -> str:
    """Число → русский символ"""
    return chr(num + ord('а'))


def num_to_char_en(num: int) -> str:
    """Число → английский символ"""
    return chr(num + ord('a'))


# Глобальные переменные для хранения текущего языка
_LANGUAGE = 'ru'
_CHAR_TO_NUM = char_to_num_ru
_NUM_TO_CHAR = num_to_char_ru


def set_language(language: str):
    """Установить язык для преобразований"""
    global _LANGUAGE, _CHAR_TO_NUM, _NUM_TO_CHAR
    _LANGUAGE = language
    if language == 'ru':
        _CHAR_TO_NUM = char_to_num_ru
        _NUM_TO_CHAR = num_to_char_ru
    else:
        _CHAR_TO_NUM = char_to_num_en
        _NUM_TO_CHAR = num_to_char_en


def word_to_array(word: str) -> np.ndarray:
    """Преобразовать слово в массив чисел"""
    return np.array([_CHAR_TO_NUM(c) for c in word], dtype=np.int8)


def array_to_word(arr: np.ndarray) -> str:
    """Преобразовать массив чисел в слово"""
    return ''.join(_NUM_TO_CHAR(int(n)) for n in arr)


# ============================================================================
# Numba-оптимизированные функции (компилируются в машинный код)
# ============================================================================

@njit
def get_pattern_numba(guess: np.ndarray, target: np.ndarray) -> int:
    """
    Быстрая версия get_pattern с Numba
    
    Возвращает паттерн как число в троичной системе:
    pattern[0] + pattern[1]*3 + pattern[2]*9 + pattern[3]*27 + pattern[4]*81
    
    Это позволяет использовать простой int вместо строки для скорости
    """
    pattern = np.zeros(5, dtype=np.int8)
    target_used = np.zeros(5, dtype=np.int8)  # 0 = не использована, 1 = использована
    guess_used = np.zeros(5, dtype=np.int8)
    
    # Шаг 1: Помечаем зеленые (точные совпадения)
    for i in range(5):
        if guess[i] == target[i]:
            pattern[i] = 2
            target_used[i] = 1
            guess_used[i] = 1
    
    # Шаг 2: Помечаем желтые (буква есть, но не на месте)
    for i in range(5):
        if guess_used[i] == 0:  # Если еще не обработана
            for j in range(5):
                if target_used[j] == 0 and guess[i] == target[j]:
                    pattern[i] = 1
                    target_used[j] = 1
                    break
    
    # Кодируем паттерн в число (троичная система)
    result = 0
    multiplier = 1
    for i in range(5):
        result += pattern[i] * multiplier
        multiplier *= 3
    
    return result


@njit
def pattern_to_string_numba(pattern_num: int) -> np.ndarray:
    """Декодировать число паттерна обратно в массив [0,1,2,0,1]"""
    pattern = np.zeros(5, dtype=np.int8)
    for i in range(5):
        pattern[i] = pattern_num % 3
        pattern_num //= 3
    return pattern


@njit
def calculate_entropy_numba(word_idx: int, words_array: np.ndarray, 
                           candidates_indices: np.ndarray, is_candidate: bool) -> float:
    """
    Быстрый расчет энтропии для одного слова
    
    Args:
        word_idx: индекс слова в words_array
        words_array: массив всех слов (shape: [n_words, 5])
        candidates_indices: индексы слов-кандидатов
        is_candidate: является ли слово кандидатом
    
    Returns:
        Энтропия в битах (с бонусом для кандидатов)
    """
    if len(candidates_indices) == 0:
        return 0.0
    
    guess = words_array[word_idx]
    
    # Подсчитываем частоты паттернов
    # Максимум 243 паттерна (3^5)
    pattern_counts = np.zeros(243, dtype=np.int32)
    
    # БЕЗ prange - избегаем race condition при обновлении счетчиков
    for i in range(len(candidates_indices)):
        target = words_array[candidates_indices[i]]
        pattern = get_pattern_numba(guess, target)
        pattern_counts[pattern] += 1
    
    # Рассчитываем энтропию: H = -Σ p*log2(p)
    total = float(len(candidates_indices))
    entropy = 0.0
    
    for count in pattern_counts:
        if count > 0:
            probability = float(count) / total
            entropy -= probability * math.log2(probability)
    
    # Бонус для кандидатов: учитываем шанс победы
    if is_candidate:
        bonus = math.log2(total) / total
        entropy += bonus
    
    return entropy


@njit(parallel=True)
def calculate_all_entropies_numba(words_array: np.ndarray,
                                  search_indices: np.ndarray,
                                  candidates_indices: np.ndarray,
                                  is_candidate_mask: np.ndarray) -> np.ndarray:
    """
    Рассчитать энтропии для всех слов из search_indices параллельно
    
    Args:
        words_array: массив всех слов [n_words, 5]
        search_indices: индексы слов для оценки
        candidates_indices: индексы слов-кандидатов
        is_candidate_mask: маска (1 если слово в кандидатах, 0 иначе)
    
    Returns:
        Массив энтропий для каждого слова из search_indices
    """
    n_search = len(search_indices)
    entropies = np.zeros(n_search, dtype=np.float64)
    
    # Параллельный расчет
    for i in prange(n_search):
        word_idx = search_indices[i]
        is_candidate = is_candidate_mask[i] > 0
        entropy = calculate_entropy_numba(word_idx, words_array, candidates_indices, is_candidate)
        
        entropies[i] = entropy
    
    return entropies


# ============================================================================
# Основной класс решателя
# ============================================================================

class WordleSolver:
    """Универсальный решатель Wordle с Numba-оптимизацией"""
    
    def __init__(self, words_file: str = "words.txt", 
                 target_words_file: str = None,
                 cache_file: str = None,
                 language: str = None,
                 verbose: bool = True):
        """
        Инициализация решателя
        
        Args:
            words_file: Файл со всеми валидными словами (можно вводить)
            target_words_file: Файл со словами, которые могут быть загаданы.
                             Если None, то используется words_file для обоих словарей.
            cache_file: Файл кэша для первого хода
            language: Язык ('ru' или 'en'). Если None - автоопределение
            verbose: Показывать ли отладочную информацию
        """
        self.verbose = verbose
        

        # Загружаем словарь валидных слов
        self.all_words = self._load_words_raw(words_file)
        
        # Загружаем словарь загадываемых слов
        if target_words_file is not None:
            self.target_words = self._load_words_raw(target_words_file)
        else:
            # Если не указан отдельный файл - используем один словарь
            self.target_words = self.all_words
        
        # Определяем язык
        if language is None:
            self.language = detect_language(self.all_words)
        else:
            self.language = language.lower()
        
        # Устанавливаем глобальный язык для преобразований
        set_language(self.language)
        
        if self.verbose:
            lang_name = "Русский" if self.language == 'ru' else "English"
            print(f"Язык: {lang_name}")
        
        # Фильтруем слова по языку
        self.all_words = self._filter_words(self.all_words)
        self.target_words = self._filter_words(self.target_words)
        
        # Проверяем, что target_words ⊆ all_words
        target_set = set(self.target_words)
        all_set = set(self.all_words)
        if not target_set.issubset(all_set):
            extra_words = target_set - all_set
            if self.verbose:
                print(f"⚠ Внимание: {len(extra_words)} загадываемых слов отсутствуют в валидных словах")
                print(f"  Примеры: {list(extra_words)[:5]}")
            # Добавляем недостающие слова в валидные
            self.all_words.extend(list(extra_words))
        
        if self.verbose:
            print(f"Валидных слов: {len(self.all_words)}")
            if self.target_words is not self.all_words:
                print(f"Загадываемых слов: {len(self.target_words)}")
        
        # Устанавливаем имя файла кэша
        if cache_file is None:

            # Учитываем размеры обоих словарей в имени кэша
            cache_suffix = f"{len(self.all_words)}_{len(self.target_words)}"
            cache_file = f"first_move_cache_{self.language}_{cache_suffix}.pkl"
        self.cache_file = cache_file
        

        self.remaining_words = self.target_words.copy()
        self.attempts = []
        self.used_words = set()  # Отслеживаем использованные слова
        
        # Преобразуем все слова в numpy массив для Numba
        if self.verbose:
            print("Подготовка данных для Numba...")
        self.words_array = np.array([word_to_array(w) for w in self.all_words], dtype=np.int8)
        self.word_to_idx = {word: i for i, word in enumerate(self.all_words)}
        
        # Загружаем кэш
        self.first_move_cache = self._load_first_move_cache()
        
        # Прогрев JIT-компилятора
        if self.verbose:
            print("Прогрев JIT-компилятора...")
        self._warmup_jit()
    
    def _load_words_raw(self, filename: str) -> List[str]:
        """Загрузка словаря из файла (без фильтрации)"""
        with open(filename, 'r', encoding='utf-8') as f:
            words = [line.strip().lower().replace('ё', 'е') for line in f if len(line.strip()) == 5]
        return words
    
    def _filter_words(self, words: List[str]) -> List[str]:
        """Фильтрация слов по языку"""
        filtered = []
        skipped = 0
        
        for word in words:
            if self.language == 'ru':
                if all('а' <= c <= 'я' for c in word):
                    filtered.append(word)
                else:
                    skipped += 1
            else:  # english
                if all('a' <= c <= 'z' for c in word):
                    filtered.append(word)
                else:
                    skipped += 1
        
        if self.verbose:
            print(f"Загружено {len(filtered)} слов из словаря")
            if skipped > 0:
                print(f"Пропущено {skipped} слов с недопустимыми символами")
        
        return filtered
    
    def _warmup_jit(self):
        """Прогрев JIT компилятора на маленьком примере"""
        # Вызываем функции на маленьких данных для компиляции
        sample_indices = np.array([0, 1, 2, 3, 4], dtype=np.int32)
        _ = calculate_entropy_numba(0, self.words_array, sample_indices, True)
        
        # Прогреваем параллельную версию
        is_candidate_mask = np.ones(5, dtype=np.int8)
        _ = calculate_all_entropies_numba(self.words_array, sample_indices, sample_indices, is_candidate_mask)
        
        if self.verbose:
            print("[OK] JIT компилятор готов")
    
    def _load_first_move_cache(self) -> Optional[Dict[str, float]]:
        """Загрузить кэш для первого хода"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'rb') as f:
                    cache = pickle.load(f)

                    # Проверяем совпадение размеров обоих словарей
                    valid_cache = (
                        cache.get('valid_word_count') == len(self.all_words) and
                        cache.get('target_word_count') == len(self.target_words)
                    )
                    # Для обратной совместимости со старыми кэшами
                    if not valid_cache and 'word_count' in cache:
                        valid_cache = cache.get('word_count') == len(self.all_words)
                    
                    if valid_cache:
                        if self.verbose:
                            print(f"[OK] Загружен кэш первого хода ({len(cache['scores'])} слов)")
                            if 'generated_at' in cache:
                                print(f"  Дата создания: {cache['generated_at']}")
                        return cache['scores']
                    else:
                        if self.verbose:

                            print(f"! Кэш устарел (словари изменились)")
            except Exception as e:
                if self.verbose:
                    print(f"! Ошибка загрузки кэша: {e}")
        else:
            if self.verbose:
                print(f"! Кэш не найден. Запустите 'python generate_cache.py' для создания.")
        return None
    
    def get_pattern(self, guess: str, target: str) -> str:
        """Получить паттерн ответа (для совместимости с тестами)"""
        guess_arr = word_to_array(guess)
        target_arr = word_to_array(target)
        pattern_num = get_pattern_numba(guess_arr, target_arr)
        
        # Декодируем из троичной системы в строку
        pattern = []
        for _ in range(5):
            pattern.append(str(pattern_num % 3))
            pattern_num //= 3
        
        return ''.join(pattern)
    
    def calculate_entropy(self, word: str, candidates: List[str]) -> float:
        """Рассчитать энтропию (для совместимости)"""
        if not candidates:
            return 0.0
        
        word_idx = self.word_to_idx[word]
        candidates_indices = np.array([self.word_to_idx[c] for c in candidates], dtype=np.int32)
        is_candidate = word in candidates
        return calculate_entropy_numba(word_idx, self.words_array, candidates_indices, is_candidate)
    
    def get_all_word_scores(self, candidates: List[str] = None,
                           search_all: bool = True) -> List[Tuple[str, float]]:
        """
        Получить оценки энтропии для всех слов
        
        ОПТИМИЗИРОВАНО: Использует Numba для параллельного расчета
        """
        if candidates is None:
            candidates = self.remaining_words
        
        if len(candidates) == 1:
            return [(candidates[0], 0.0)]
        
        # Проверяем, это первый ход?


        is_first_move = (len(candidates) == len(self.target_words) and
                        len(self.remaining_words) == len(self.target_words))
        
        if is_first_move and self.first_move_cache is not None:
            # Используем кэш
            word_scores = [(word, score) for word, score in self.first_move_cache.items()]
        else:
            # Быстрый расчет с Numba
            search_pool = self.all_words if search_all else candidates
            
            # Исключаем уже использованные слова
            search_pool = [w for w in search_pool if w not in self.used_words]
            
            if not search_pool:
                # Если все слова использованы, возвращаем любое из кандидатов
                if candidates:
                    return [(candidates[0], 0.0)]
                return []
            
            if self.verbose:
                print(f"Анализирую {len(search_pool)} слов для {len(candidates)} кандидатов...")
                start_time = time.time()
            
            # Подготовка индексов
            search_indices = np.array([self.word_to_idx[w] for w in search_pool], dtype=np.int32)
            candidates_indices = np.array([self.word_to_idx[c] for c in candidates], dtype=np.int32)
            
            # Маска: 1 если слово - кандидат, 0 иначе
            candidates_set = set(candidates)
            is_candidate_mask = np.array([1 if w in candidates_set else 0 for w in search_pool], dtype=np.int8)
            
            # БЫСТРЫЙ параллельный расчет всех энтропий
            entropies = calculate_all_entropies_numba(
                self.words_array, 
                search_indices,
                candidates_indices, 
                is_candidate_mask
            )
            
            if self.verbose:
                elapsed = time.time() - start_time
                print(f"  Расчет завершен за {elapsed:.2f}с")
            
            # Формируем результат
            word_scores = [(search_pool[i], entropies[i]) for i in range(len(search_pool))]
        
        # Сортируем по убыванию энтропии
        word_scores.sort(key=lambda x: x[1], reverse=True)
        return word_scores
    
    def find_best_word(self, candidates: List[str] = None,
                       search_all: bool = True) -> Tuple[str, float]:
        """Найти лучшее слово для следующей попытки"""
        word_scores = self.get_all_word_scores(candidates, search_all)
        
        if word_scores:
            best_word, best_entropy = word_scores[0]
            if self.verbose:
                print(f"Лучшее слово: {best_word} (энтропия: {best_entropy:.3f})")
            return best_word, best_entropy
        
        return None, 0.0
    
    def update_remaining(self, guess: str, pattern: str):
        """Обновить список оставшихся слов"""
        self.attempts.append((guess, pattern))
        self.used_words.add(guess)  # Отмечаем слово как использованное
        
        # Фильтруем слова
        self.remaining_words = [
            word for word in self.remaining_words
            if self.get_pattern(guess, word) == pattern
        ]
        
        if self.verbose:
            print(f"Осталось {len(self.remaining_words)} кандидатов")
            if len(self.remaining_words) <= 10:
                print(f"Возможные слова: {', '.join(self.remaining_words)}")
    
    def reset(self):
        """Сбросить состояние решателя"""

        self.remaining_words = self.target_words.copy()
        self.attempts = []
        self.used_words = set()
    
    def get_suggestion(self) -> str:
        """Получить рекомендацию для следующего хода"""
        # Всегда ищем среди всех слов для максимальной информативности
        word, _ = self.find_best_word(search_all=True)
        return word


# Алиас для обратной совместимости
WordleSolverFast = WordleSolver