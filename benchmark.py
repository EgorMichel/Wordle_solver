"""Бенчмарк для оценки эффективности Wordle решателя
Тестирует алгоритм на случайных словах и собирает статистику

Поддерживаемые языки:
- ru: Русский (5-буквенные слова на кириллице)
- en: English (5-letter words)

Использование:
    python benchmark.py -l ru -n 100          # 100 игр на русском
    python benchmark.py -l en -n 500 -v       # 500 игр на английском с подробным выводом
"""

import random
import time
import os
from collections import defaultdict
from typing import List, Tuple

from wordle_solver import WordleSolver


class WordleBenchmark:
    def __init__(self, language: str = 'ru', words_file: str = None, 
                 target_words_file: str = None, max_attempts: int = 6):
        """
        Args:
            language: язык словаря ('ru' или 'en')
            words_file: путь к файлу с валидными словами (если None, используется words_{language}.txt)
            target_words_file: путь к файлу с загадываемыми словами (опционально)
            max_attempts: максимальное количество попыток
        """
        # Определяем файл словаря
        if words_file is None:
            words_file = f"words_{language}.txt"
            # Проверяем наличие файла
            if not os.path.exists(words_file):
                # Пробуем альтернативный вариант
                words_file = "words.txt"
        
        self.language = language.lower()
        self.solver = WordleSolver(
            words_file=words_file,
            target_words_file=target_words_file,
            language=self.language,
            verbose=False  # Отключаем подробные выводы
        )
        self.max_attempts = max_attempts
        
    def simulate_game(self, target_word: str, verbose: bool = False) -> Tuple[bool, int, List[str]]:
        """
        Симулировать одну игру
        
        Returns:
            (победа, количество_попыток, история_попыток)
        """
        # Сбрасываем состояние решателя
        self.solver.reset()
        
        attempts = []
        
        for attempt_num in range(1, self.max_attempts + 1):
            # Получаем лучшее слово
            # Всегда ищем среди всех слов для максимальной информативности
            best_word, entropy = self.solver.find_best_word(search_all=True)
            
            if verbose:
                print(f"  Попытка {attempt_num}: {best_word} ", end="")
            
            attempts.append(best_word)
            
            # Получаем паттерн
            pattern = self.solver.get_pattern(best_word, target_word)
            
            if verbose:
                print(f"-> {pattern} (энтропия: {entropy:.3f}, осталось: {len(self.solver.remaining_words)})")
            
            # Проверяем победу
            if pattern == "22222":
                if verbose:
                    print(f"  [OK] Угадано за {attempt_num} попыток\n")
                return True, attempt_num, attempts
            
            # Обновляем состояние
            self.solver.update_remaining(best_word, pattern)
            
            # Проверка на корректность - целевое слово должно быть в кандидатах
            if target_word not in self.solver.remaining_words:
                if verbose:
                    print(f"  ОШИБКА: целевое слово '{target_word}' исчезло из кандидатов!")
                return False, attempt_num, attempts
        
        return False, self.max_attempts, attempts
    
    def run_benchmark(self, n_games: int = 100, sample_words: List[str] = None, verbose: bool = False):
        """
        Запустить бенчмарк на N играх
        
        Args:
            n_games: количество игр для тестирования
            sample_words: список слов для тестирования (если None, выбираются случайно)
            verbose: подробный вывод каждой игры
        """
        print("=" * 70)
        print(f"WORDLE SOLVER BENCHMARK")
        print("=" * 70)
        lang_name = "Русский" if self.solver.language == 'ru' else "English"
        print(f"Язык: {lang_name}")
        print(f"Валидных слов: {len(self.solver.all_words)}")
        if self.solver.target_words is not self.solver.all_words:
            print(f"Загадываемых слов: {len(self.solver.target_words)}")
        print(f"Количество игр: {n_games}")
        print(f"Максимум попыток: {self.max_attempts}")
        print("=" * 70)
        
        # Выбираем слова для тестирования (только из загадываемых)
        if sample_words is None:
            test_words = random.sample(self.solver.target_words, n_games)
        else:
            test_words = sample_words[:n_games]
        
        # Статистика
        wins = 0
        total_attempts = 0
        attempts_distribution = defaultdict(int)
        failed_words = []
        worst_cases = []  # (слово, количество_попыток, история)
        
        start_time = time.time()
        
        for i, target_word in enumerate(test_words, 1):
            if verbose:
                print(f"\n{'='*70}")
                print(f"Игра {i}/{n_games}: Целевое слово = {target_word.upper()}")
                print(f"{'='*70}")
            elif i == 1 or i % 10 == 0 or i == n_games:
                elapsed = time.time() - start_time
                avg_time = elapsed / i
                remaining = (n_games - i) * avg_time
                print(f"Прогресс: {i}/{n_games} ({i*100//n_games:3d}%) | "
                      f"Побед: {wins}/{i} ({wins*100//i if i > 0 else 0:5.1f}%) | "
                      f"Осталось: ~{remaining:.0f}с", end="\r" if i < n_games else "\n")
            
            won, num_attempts, history = self.simulate_game(target_word, verbose=verbose)
            
            if won:
                wins += 1
                total_attempts += num_attempts
                attempts_distribution[num_attempts] += 1
                
                # Сохраняем худшие случаи (даже если выиграли)
                if num_attempts >= 5:
                    worst_cases.append((target_word, num_attempts, history))
            else:
                failed_words.append((target_word, history))
                attempts_distribution['failed'] += 1
                
                if not verbose:
                    # Показываем проваленные слова
                    print(f"\n[X] Не решено: {target_word.upper()} (попытки: {' -> '.join(history)})")
            
            if verbose and not won:
                print(f"  [X] Не решено за {num_attempts} попыток\n")
        
        elapsed_time = time.time() - start_time
        
        # Вывод результатов
        print("\n" + "=" * 70)
        print("РЕЗУЛЬТАТЫ БЕНЧМАРКА")
        print("=" * 70)
        
        print(f"\nОбщая статистика:")
        print(f"  Всего игр:           {n_games}")
        print(f"  Побед:               {wins} ({wins*100/n_games:.1f}%)")
        print(f"  Поражений:           {len(failed_words)} ({len(failed_words)*100/n_games:.1f}%)")
        
        if wins > 0:
            avg_attempts = total_attempts / wins
            print(f"  Среднее попыток:     {avg_attempts:.2f}")
        
        print(f"\nВремя выполнения:")
        print(f"  Общее время:         {elapsed_time:.1f}с")
        print(f"  Среднее на игру:     {elapsed_time/n_games:.2f}с")
        
        print(f"\nРаспределение по попыткам:")
        for attempt in range(1, self.max_attempts + 1):
            count = attempts_distribution[attempt]
            if count > 0:
                bar = "#" * int(count * 40 / n_games)
                print(f"  {attempt} попытка:  {count:4d} ({count*100/n_games:5.1f}%) {bar}")
        
        if attempts_distribution['failed'] > 0:
            count = attempts_distribution['failed']
            bar = "#" * int(count * 40 / n_games)
            print(f"  Не решено:  {count:4d} ({count*100/n_games:5.1f}%) {bar}")
        
        # Худшие случаи
        if worst_cases:
            worst_cases.sort(key=lambda x: x[1], reverse=True)
            print(f"\nХудшие случаи (топ-10):")
            for i, (word, num_attempts, history) in enumerate(worst_cases[:10], 1):
                print(f"  {i:2}. {word.upper():8} - {num_attempts} попыток: {' -> '.join(history)}")
        
        # Проваленные слова
        if failed_words:
            print(f"\nНе решенные слова ({len(failed_words)}):")
            for word, history in failed_words[:10]:  # Показываем первые 10
                print(f"  - {word.upper():8}: {' -> '.join(history)}")
            if len(failed_words) > 10:
                print(f"  ... и еще {len(failed_words) - 10} слов")
        
        print("\n" + "=" * 70)
        
        return {
            'total_games': n_games,
            'wins': wins,
            'win_rate': wins / n_games,
            'avg_attempts': total_attempts / wins if wins > 0 else 0,
            'distribution': dict(attempts_distribution),
            'failed_words': failed_words,
            'worst_cases': worst_cases,
            'elapsed_time': elapsed_time
        }


def main():
    """Главная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Бенчмарк Wordle решателя',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  # Тест на русском языке (100 игр)
  python benchmark.py -l ru
  
  # Тест на английском (500 игр)
  python benchmark.py -l en -n 500
  
  # Подробный вывод для конкретных слов
  python benchmark.py -l ru --words crane slate trace -v
  
  # Указать свой файл словаря
  python benchmark.py -l en --dict-file custom_words.txt -n 100
  
  # Использовать два словаря (как в настоящем Wordle)
  python benchmark.py -l en --dict-file allowed.txt --target-dict-file targets.txt -n 1000
"""
    )
    
    # Обязательный аргумент для выбора языка
    parser.add_argument('-l', '--language', type=str, required=True,
                       choices=['ru', 'en'],
                       help='Язык словаря (ОБЯЗАТЕЛЬНО): ru - русский, en - английский')
    
    parser.add_argument('-n', '--games', type=int, default=100,
                       help='Количество игр для тестирования (по умолчанию: 100)')
    
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Подробный вывод каждой игры')
    
    parser.add_argument('--max-attempts', type=int, default=6,
                       help='Максимальное количество попыток (по умолчанию: 6)')
    
    parser.add_argument('--words', type=str, nargs='+',
                       help='Конкретные слова для тестирования')
    
    parser.add_argument('--dict-file', type=str, default=None,
                       help='Путь к файлу с валидными словами (по умолчанию: words_{language}.txt)')
    
    parser.add_argument('--target-dict-file', type=str, default=None,
                       help='Путь к файлу с загадываемыми словами (опционально, для режима с двумя словарями)')
    
    args = parser.parse_args()
    
    # Создаем бенчмарк с выбранным языком
    try:
        benchmark = WordleBenchmark(
            language=args.language,
            words_file=args.dict_file,
            target_words_file=args.target_dict_file,
            max_attempts=args.max_attempts
        )
    except FileNotFoundError as e:
        print(f"\n[ОШИБКА] {e}")
        print(f"\nУбедитесь, что файл словаря существует:")
        if args.dict_file:
            print(f"  - {args.dict_file}")
        else:
            print(f"  - words_{args.language}.txt")
            print(f"  - или words.txt")
        return
    except Exception as e:
        print(f"\n[ОШИБКА] Не удалось инициализировать бенчмарк: {e}")
        return
    
    sample_words = args.words if args.words else None
    n_games = len(sample_words) if sample_words else args.games
    
    # Запускаем бенчмарк
    try:
        results = benchmark.run_benchmark(
            n_games=n_games,
            sample_words=sample_words,
            verbose=args.verbose
        )
    except KeyboardInterrupt:
        print("\n\n[!] Бенчмарк прерван пользователем")
    except Exception as e:
        print(f"\n[ОШИБКА] Ошибка во время выполнения бенчмарка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()