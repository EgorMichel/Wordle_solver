"""
Скрипт для предварительного расчета энтропий всех слов для первого хода
Запустите один раз для создания кэша
"""

from wordle_solver import WordleSolver
import pickle
import time
import sys

def generate_first_move_cache(words_file="words_en.txt", language="en"):
    print("=" * 60)
    print(f"ГЕНЕРАЦИЯ КЭША ДЛЯ ПЕРВОГО ХОДА ({language.upper()})")
    print("=" * 60)
    
    solver = WordleSolver(words_file=words_file, language=language)
    
    print(f"\nВсего слов в словаре: {len(solver.all_words)}")
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
        
        entropy = solver.calculate_entropy(word, solver.all_words)
        
        # Небольшой бонус для слова из кандидатов
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
    cache_file = f"first_move_cache_{solver.language}.pkl"
    cache_data = {
        'word_count': len(solver.all_words),
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
    if len(sys.argv) > 1:
        words_file = sys.argv[1]
        language = sys.argv[2] if len(sys.argv) > 2 else "en"
    else:
        # По умолчанию английский
        words_file = "words_en.txt"
        language = "en"
    
    print(f"Словарь: {words_file}")
    print(f"Язык: {language}")
    print()
    
    generate_first_move_cache(words_file, language)