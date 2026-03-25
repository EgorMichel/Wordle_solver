"""
Тесты для универсального решателя Wordle
"""

import unittest
import time

try:
    from wordle_solver import WordleSolver
    SOLVER_AVAILABLE = True
except ImportError:
    SOLVER_AVAILABLE = False
    print("[!] Не удалось загрузить решатель. Установите: pip install numba numpy")


@unittest.skipIf(not SOLVER_AVAILABLE, "Решатель не доступен")
class TestWordleSolver(unittest.TestCase):
    """Базовые тесты решателя"""
    
    @classmethod
    def setUpClass(cls):
        print("\nИнициализация решателя...")
        cls.solver = WordleSolver(verbose=False)
    
    def test_word_list_loaded(self):
        """Словарь должен быть загружен"""
        self.assertGreater(len(self.solver.all_words), 0, "Словарь пуст")
    
    def test_language_detected(self):
        """Язык должен быть определён"""
        self.assertIn(self.solver.language, ['ru', 'en'], "Неизвестный язык")
    
    def test_pattern_all_green(self):
        """Одинаковые слова дают 22222"""
        sample = self.solver.all_words[0]
        pattern = self.solver.get_pattern(sample, sample)
        self.assertEqual(pattern, "22222")
    
    def test_entropy_positive(self):
        """Энтропия положительна"""
        candidates = self.solver.all_words[:100]
        word = candidates[0]
        entropy = self.solver.calculate_entropy(word, candidates)
        self.assertGreater(entropy, 0)
    
    def test_solver_can_find_best(self):
        """Решатель находит лучшее слово"""
        best_word, entropy = self.solver.find_best_word()
        self.assertIsNotNone(best_word)
        self.assertGreater(entropy, 0)
    
    def test_update_remaining(self):
        """Обновление кандидатов работает"""
        self.solver.reset()
        initial = len(self.solver.remaining_words)
        
        word = self.solver.all_words[0]
        pattern = "00000"  # Все буквы не подходят
        self.solver.update_remaining(word, pattern)
        
        # Должно остаться меньше слов
        self.assertLess(len(self.solver.remaining_words), initial)


def run_tests():
    """Запуск всех тестов"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    if SOLVER_AVAILABLE:
        suite.addTests(loader.loadTestsFromTestCase(TestWordleSolver))
    else:
        print("\n[!] Тесты пропущены: решатель не доступен")
        return True
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)