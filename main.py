"""Wordle Assistant - универсальная точка входа

Поддерживает русский и английский языки.
Обязательно нужно указать язык через флаг -l/--language

Использование:
    python main.py -l ru    # Русская версия
    python main.py -l en    # English version
"""

import sys
import argparse
from wordle_assistant import WordleAssistant
from wordle_solver import WordleSolver


def setup_assistant(language: str, words_file: str = None, target_words_file: str = None):
    """
    Настройка ассистента для указанного языка
    
    Args:
        language: 'ru' или 'en'
        words_file: Путь к файлу с валидными словами (опционально)
        target_words_file: Путь к файлу с загадываемыми словами (опционально)
    """
    # Патчим класс для использования нужного словаря
    original_init = WordleAssistant.__init__
    
    def new_init(self):
        import pygame
        pygame.init()
        self.screen = pygame.display.set_mode((900, 700))
        
        # Заголовок окна в зависимости от языка
        if language == 'ru':
            pygame.display.set_caption("Wordle Assistant - Русский")
            default_words_file = "words_ru.txt"
        else:
            pygame.display.set_caption("Wordle Assistant - English")
            default_words_file = "words_en.txt"
        
        # Используем переданный файл или дефолтный
        actual_words_file = words_file if words_file else default_words_file
        
        # Шрифты
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        self.font_tiny = pygame.font.Font(None, 20)
        
        # Решатель с нужным словарем (или словарями)
        self.solver = WordleSolver(
            words_file=actual_words_file,
            target_words_file=target_words_file,
            language=language,
            verbose=True
        )
        
        # Состояние ввода
        self.current_row = 0
        self.current_col = 0
        self.grid = [['' for _ in range(5)] for _ in range(10)]
        self.patterns = [[0 for _ in range(5)] for _ in range(10)]
        self.row_submitted = [False for _ in range(10)]
        
        # Рекомендации
        self.top_suggestions = []
        self.TOP_N = 10
        
        # Кнопки
        self.buttons = {
            'submit': pygame.Rect(450, 100 + (70 + 8) * self.current_row, 120, 50),
            'reset': pygame.Rect(900 - 150, 20, 120, 40),
        }
        
        # Выводим инструкции в зависимости от языка
        print("=" * 60)
        if language == 'ru':
            print("WORDLE ASSISTANT - Русская версия")
            print("=" * 60)
            print("\nИнструкция:")
            print("1. Введите слово с клавиатуры")
            print("2. Кликайте по буквам для установки цвета:")
            print("   - 1 клик = Желтый (буква есть, не на месте)")
            print("   - 2 клика = Зеленый (буква на месте)")
            print("   - 3 клика = Серый (буквы нет)")
            print("3. Нажмите 'Отправить' или Enter")
            print("4. Используйте рекомендованные слова в игре")
        else:
            print("WORDLE ASSISTANT - English Version")
            print("=" * 60)
            print("\nInstructions:")
            print("1. Type a word from keyboard")
            print("2. Click on letters to set colors:")
            print("   - 1 click = Yellow (letter exists, wrong position)")
            print("   - 2 clicks = Green (letter in correct position)")
            print("   - 3 clicks = Gray (letter doesn't exist)")
            print("3. Press 'Submit' or Enter")
            print("4. Use recommended words in your game")
        print("\n" + "=" * 60)
        self._print_initial_suggestions()
    
    WordleAssistant.__init__ = new_init
    
    # Патчим обработку клавиш для нужного языка
    original_handle = WordleAssistant.handle_keypress
    
    def new_handle_keypress(self, event):
        import pygame
        if self.row_submitted[self.current_row]:
            return
        
        if event.key == pygame.K_BACKSPACE:
            if self.current_col > 0:
                self.current_col -= 1
                self.grid[self.current_row][self.current_col] = ''
                self.patterns[self.current_row][self.current_col] = 0
        
        elif event.key == pygame.K_RETURN:
            if self.current_col == 5:
                self.submit_current_row()
        
        else:
            char = event.unicode.lower()
            if language == 'ru':
                # Проверяем русские буквы
                if ('а' <= char <= 'я' or char == 'ё') and self.current_col < 5:
                    self.grid[self.current_row][self.current_col] = char
                    self.current_col += 1
            else:
                # Check English letters
                if ('a' <= char <= 'z') and self.current_col < 5:
                    self.grid[self.current_row][self.current_col] = char
                    self.current_col += 1
    
    WordleAssistant.handle_keypress = new_handle_keypress


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description='Wordle Assistant - умный помощник для игры в Wordle',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  # Запустить на русском языке
  python main.py -l ru
  
  # Запустить на английском языке
  python main.py -l en
  
  # Использовать два словаря (как в настоящем Wordle)
  python main.py -l en --dict-file allowed.txt --target-dict-file targets.txt

Управление:
  - Печатайте слова на клавиатуре
  - Кликайте по буквам для установки цветов (серый → желтый → зеленый)
  - Enter - отправить слово
  - Backspace - удалить последнюю букву
  - Кнопка "Сброс" - начать заново
"""
    )
    
    # Обязательный аргумент для выбора языка
    parser.add_argument(
        '-l', '--language',
        type=str,
        required=True,
        choices=['ru', 'en'],
        help='Язык словаря (ОБЯЗАТЕЛЬНО): ru - русский, en - английский'
    )
    
    parser.add_argument(
        '--dict-file',
        type=str,
        default=None,
        help='Путь к файлу с валидными словами (по умолчанию: words_{language}.txt)'
    )
    
    parser.add_argument(
        '--target-dict-file',
        type=str,
        default=None,
        help='Путь к файлу с загадываемыми словами (опционально, для режима с двумя словарями)'
    )
    
    args = parser.parse_args()
    
    try:
        # Настраиваем ассистента для выбранного языка
        setup_assistant(args.language, args.dict_file, args.target_dict_file)
        
        # Запускаем ассистента
        assistant = WordleAssistant()
        assistant.run()
        
    except FileNotFoundError as e:
        print(f"\n[ОШИБКА] {e}")
        print(f"\nУбедитесь, что файл словаря существует:")
        if args.dict_file:
            print(f"  - {args.dict_file}")
        else:
            print(f"  - words_{args.language}.txt")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n[ОШИБКА] Не удалось запустить ассистента: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()