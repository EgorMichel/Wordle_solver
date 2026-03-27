"""
Скрипт для предварительного расчета энтропий всех слов для первого хода
Запустите один раз для создания кэша
"""

from wordle_solver import WordleSolver
import pickle
import time
import sys
import os

def generate_first_move_cache(words_file="words_ru.txt", target_words_file=None, language="ru"):
    print("=" * 60)
    print(f"ГЕНЕРАЦИЯ КЭША ДЛЯ ПЕРВОГО ХОДА ({language.upper()})")
    print("=" * 60)
    
    solver = WordleSolver(words_file=words_file, target_words_file=target_words_file, language=language)
    
    print(f"\nВалидных слов: {len(solver.all_words)}")
    if target_words_file:
        print(f"Загадываемых слов: {len(solver.target_words)}")
    print("Начинается расчет энтропии для всех слов...")
    print("Это может занять 3-5 минут...\n")
    
    start_time = time.time()
    
    word_scores = {}
    total = len(solver.all_words)
    
    for i, word in enumerate(solver.all_words):
        if i % 100 == 0:
            elapsed = time.time() - start_time
            if i > 0:
                avg_time = elapsed / i
                remaining = (total - i) * avg_time
                print(f"  Прогресс: {i}/{total} ({i*100//total}%) | "
                      f"Осталось: ~{remaining//60:.0f}м {remaining%60:.0f}с")
        
        # Энтропия считается относительно загадываемых слов (target_words)
        entropy = solver.calculate_entropy(word, solver.target_words)
        
        # Небольшой бонус для слова из кандидатов
        if word in solver.target_words:
            entropy += 0.01
        
        word_scores[word] = entropy
    
    # Сортируем и выводим топ-20
    sorted_words = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)
    
    print("\n" + "=" * 60)
    print("РАСЧЕТ ЗАВЕРШЕН!")
    print("=" * 60)
    
    elapsed = time.time() - start_time
    print(f"\nВремя расчета: {elapsed//60:.0f}м {elapsed%60:.0f}с")
    
    print("\nТОП-20 ЛУЧШИХ СТАРТОВЫХ СЛОВ:")
    print("-" * 60)
    for i, (word, entropy) in enumerate(sorted_words[:20], 1):
        print(f"{i:2}. {word.upper():8} | Энтропия: {entropy:.4f}")
    print("-" * 60)
    
    # Сохраняем кэш
    cache_file = solver.cache_file
    cache_data = {
        'valid_word_count': len(solver.all_words),
        'target_word_count': len(solver.target_words),
        'word_count': len(solver.all_words),  # Для обратной совместимости
        'scores': word_scores,
        'generated_at': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    with open(cache_file, 'wb') as f:
        pickle.dump(cache_data, f)
    
    print(f"\n[OK] Кэш сохранен в файл: {cache_file}")
    print(f"  Размер файла: {len(pickle.dumps(cache_data)) / 1024:.1f} KB")
    print("\nТеперь программа будет загружаться мгновенно!")
    print("=" * 60)

if __name__ == '__main__':
    # Поддержка аргументов командной строки
    # Использование:
    #   python generate_cache.py words_en.txt en
    #   python generate_cache.py allowed_words.txt target_words.txt en
    
    words_file = "words_ru.txt"
    target_words_file = None
    language = "ru"
    
    if len(sys.argv) > 1:
        words_file = sys.argv[1]
        
        if len(sys.argv) > 2:
            # Проверяем, это файл или язык?
            if os.path.exists(sys.argv[2]):
                # Это второй файл словаря
                target_words_file = sys.argv[2]
                language = sys.argv[3] if len(sys.argv) > 3 else "en"
            else:
                # Это язык
                language = sys.argv[2]
    
    print(f"Валидные слова: {words_file}")
    if target_words_file:
        print(f"Загадываемые слова: {target_words_file}")
    print(f"Язык: {language}")
    print()
    
    generate_first_move_cache(words_file, target_words_file, language)