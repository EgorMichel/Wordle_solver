"""
Wordle Assistant - Помощник для игры в реальный Wordle
Вводите результаты попыток, получайте рекомендации
"""

import pygame
import sys
from typing import List, Tuple

from wordle_solver import WordleSolver

# Константы
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 700
CELL_SIZE = 70
CELL_MARGIN = 8
GRID_START_X = 50
GRID_START_Y = 80
MAX_ATTEMPTS = 10

# Цвета
COLOR_BG = (18, 18, 19)
COLOR_CELL_EMPTY = (58, 58, 60)
COLOR_CELL_GRAY = (58, 58, 60)
COLOR_CELL_YELLOW = (181, 159, 59)
COLOR_CELL_GREEN = (83, 141, 78)
COLOR_TEXT = (255, 255, 255)
COLOR_TEXT_DIM = (150, 150, 150)
COLOR_BUTTON = (70, 70, 75)
COLOR_BUTTON_HOVER = (90, 90, 95)
COLOR_ACCENT = (100, 100, 255)


class WordleAssistant:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Wordle Assistant - Помощник")
        
        # Шрифты
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        self.font_tiny = pygame.font.Font(None, 20)
        
        # Решатель (с подробными выводами для помощника)
        self.solver = WordleSolver(words_file="words_en.txt", language="en", verbose=True)
        
        # Состояние ввода
        self.current_row = 0
        self.current_col = 0
        self.grid = [['' for _ in range(5)] for _ in range(MAX_ATTEMPTS)]
        self.patterns = [[0 for _ in range(5)] for _ in range(MAX_ATTEMPTS)]  # 0=серый, 1=желтый, 2=зеленый
        self.row_submitted = [False for _ in range(MAX_ATTEMPTS)]
        
        # Рекомендации
        self.top_suggestions = []
        self.TOP_N = 10  # Показывать топ-10 слов
        
        # Кнопки
        self.buttons = {
            'submit': pygame.Rect(450, 100 + (CELL_SIZE + CELL_MARGIN) * self.current_row, 120, 50),
            'reset': pygame.Rect(WINDOW_WIDTH - 150, 20, 120, 40),
        }
        
        print("=" * 60)
        print("WORDLE ASSISTANT - Помощник для игры в Wordle")
        print("=" * 60)
        print("\nИнструкция:")
        print("1. Введите слово с клавиатуры")
        print("2. Кликайте по буквам для установки цвета:")
        print("   - 1 клик = Желтый (буква есть, не на месте)")
        print("   - 2 клика = Зеленый (буква на месте)")
        print("   - 3 клика = Серый (буквы нет)")
        print("3. Нажмите 'Отправить' или Enter")
        print("4. Используйте рекомендованные слова в игре")
        print("\n" + "=" * 60)
        self._print_initial_suggestions()
    
    def _print_initial_suggestions(self):
        """Вывести начальные рекомендации"""
        print(f"\n>>> Всего слов в словаре: {len(self.solver.remaining_words)}")
        print("\nРасчет лучших стартовых слов...")
        self._calculate_and_show_suggestions()
    
    def _calculate_and_show_suggestions(self):
        """Рассчитать и показать лучшие слова"""
        if not self.solver.remaining_words:
            print("\n!!! Нет оставшихся кандидатов. Проверьте правильность ввода.")
            self.top_suggestions = []
            return
        
        if len(self.solver.remaining_words) == 1:
            print(f"\n>>> Осталось одно слово: {self.solver.remaining_words[0].upper()}")
            self.top_suggestions = [(self.solver.remaining_words[0], 0.0)]
            return
        
        # Показываем все оставшиеся слова в консоль
        candidates = self.solver.remaining_words
        print(f"\n>>> Осталось кандидатов: {len(candidates)}")
        
        if len(candidates) <= 50:
            print("\nВсе оставшиеся слова:")
            for i, word in enumerate(candidates):
                print(f"  {word}", end="")
                if (i + 1) % 10 == 0:
                    print()  # Новая строка каждые 10 слов
            print()
        
        # Получаем оценки всех слов
        # Всегда ищем среди всех слов для максимальной информативности
        word_scores = self.solver.get_all_word_scores(candidates, search_all=True)
        
        # Сохраняем топ для GUI
        self.top_suggestions = word_scores[:self.TOP_N]
        
        # Выводим топ-20 в консоль
        print(f"\n{'='*60}")
        print(f"ТОП-20 ЛУЧШИХ СЛОВ (по убыванию энтропии):")
        print(f"{'='*60}")
        for i, (word, entropy) in enumerate(word_scores[:20], 1):
            in_candidates = "[+]" if word in candidates else "[ ]"
            print(f"{i:2}. {word.upper():8} | Entropy: {entropy:.4f} | In candidates: {in_candidates}")
        print(f"{'='*60}\n")
    
    @property
    def attempts(self):
        """Получить список попыток"""
        return [(
            ''.join(self.grid[i]),
            ''.join(str(p) for p in self.patterns[i])
        ) for i in range(MAX_ATTEMPTS) if self.row_submitted[i]]
    
    def get_cell_color(self, state: int) -> tuple:
        """Получить цвет ячейки по состоянию"""
        if state == 0:
            return COLOR_CELL_GRAY
        elif state == 1:
            return COLOR_CELL_YELLOW
        else:  # state == 2
            return COLOR_CELL_GREEN
    
    def draw_cell(self, x: int, y: int, char: str, state: int, clickable: bool = False):
        """Нарисовать ячейку"""
        rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
        
        # Цвет фона
        if not char:
            color = COLOR_CELL_EMPTY
        else:
            color = self.get_cell_color(state)
        
        pygame.draw.rect(self.screen, color, rect)
        
        # Подсветка при наведении (если кликабельна)
        if clickable:
            mouse_pos = pygame.mouse.get_pos()
            if rect.collidepoint(mouse_pos):
                pygame.draw.rect(self.screen, COLOR_TEXT, rect, 3)
            else:
                pygame.draw.rect(self.screen, COLOR_TEXT_DIM, rect, 2)
        else:
            pygame.draw.rect(self.screen, COLOR_BG, rect, 2)
        
        # Буква
        if char:
            text_surface = self.font_large.render(char.upper(), True, COLOR_TEXT)
            text_rect = text_surface.get_rect(center=rect.center)
            self.screen.blit(text_surface, text_rect)
        
        return rect
    
    def draw_grid(self):
        """Нарисовать сетку ввода"""
        self.cell_rects = []  # Для обработки кликов
        
        for row in range(min(self.current_row + 1, MAX_ATTEMPTS)):
            row_rects = []
            for col in range(5):
                x = GRID_START_X + col * (CELL_SIZE + CELL_MARGIN)
                y = GRID_START_Y + row * (CELL_SIZE + CELL_MARGIN)
                
                char = self.grid[row][col]
                state = self.patterns[row][col]
                
                # Текущая строка кликабельна, если слово введено полностью
                clickable = (row == self.current_row and 
                           not self.row_submitted[row] and 
                           len(''.join(self.grid[row])) == 5)
                
                rect = self.draw_cell(x, y, char, state, clickable)
                row_rects.append(rect)
            
            self.cell_rects.append(row_rects)
    
    def draw_suggestions(self):
        """Нарисовать топ рекомендаций"""
        x_start = 500
        y_start = 150  # Опустили ниже
        
        # Заголовок
        title = self.font_medium.render(f"ТОП-{self.TOP_N} СЛОВ", True, COLOR_ACCENT)
        self.screen.blit(title, (x_start, y_start - 40))
        
        # Список слов
        for i, (word, entropy) in enumerate(self.top_suggestions):
            y = y_start + i * 40  # Увеличили интервал
            
            # Номер
            num_text = self.font_small.render(f"{i+1}.", True, COLOR_TEXT_DIM)
            self.screen.blit(num_text, (x_start, y))
            
            # Слово
            word_text = self.font_medium.render(word.upper(), True, COLOR_TEXT)
            self.screen.blit(word_text, (x_start + 35, y - 3))
            
            # Энтропия
            entropy_text = self.font_small.render(f"{entropy:.3f}", True, COLOR_TEXT_DIM)
            self.screen.blit(entropy_text, (x_start + 185, y))
            
            # Метка "в кандидатах" - используем текст вместо символа
            if word in self.solver.remaining_words:
                check_text = self.font_small.render("[+]", True, COLOR_CELL_GREEN)
                self.screen.blit(check_text, (x_start + 265, y))
    
    def draw_buttons(self):
        """Нарисовать кнопки"""
        # Кнопка Submit
        submit_rect = self.buttons['submit']
        submit_rect.y = GRID_START_Y + self.current_row * (CELL_SIZE + CELL_MARGIN)
        
        mouse_pos = pygame.mouse.get_pos()
        
        # Submit button
        if len(''.join(self.grid[self.current_row])) == 5 and not self.row_submitted[self.current_row]:
            if submit_rect.collidepoint(mouse_pos):
                color = COLOR_BUTTON_HOVER
            else:
                color = COLOR_BUTTON
            
            pygame.draw.rect(self.screen, color, submit_rect, border_radius=5)
            pygame.draw.rect(self.screen, COLOR_TEXT_DIM, submit_rect, 2, border_radius=5)
            
            text = self.font_small.render("Отправить", True, COLOR_TEXT)
            text_rect = text.get_rect(center=submit_rect.center)
            self.screen.blit(text, text_rect)
        
        # Reset button
        reset_rect = self.buttons['reset']
        if reset_rect.collidepoint(mouse_pos):
            color = COLOR_BUTTON_HOVER
        else:
            color = COLOR_BUTTON
        
        pygame.draw.rect(self.screen, color, reset_rect, border_radius=5)
        pygame.draw.rect(self.screen, COLOR_TEXT_DIM, reset_rect, 2, border_radius=5)
        
        text = self.font_small.render("Сброс", True, COLOR_TEXT)
        text_rect = text.get_rect(center=reset_rect.center)
        self.screen.blit(text, text_rect)
    
    def draw_info(self):
        """Нарисовать информацию"""
        # Заголовок
        title = self.font_large.render("WORDLE ASSISTANT", True, COLOR_TEXT)
        self.screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 15))
        
        # Статистика
        y = GRID_START_Y + (CELL_SIZE + CELL_MARGIN) * (self.current_row + 1) + 20
        
        remaining = len(self.solver.remaining_words)
        info_text = f"Осталось кандидатов: {remaining}"
        info_surface = self.font_medium.render(info_text, True, COLOR_TEXT)
        self.screen.blit(info_surface, (50, y))
        
        # Инструкция
        y += 50
        if self.current_col < 5:
            instruction = "Введите слово из 5 букв..."
            color = COLOR_TEXT_DIM
        elif not self.row_submitted[self.current_row]:
            instruction = "Кликайте по буквам для установки цвета"
            color = COLOR_ACCENT
        else:
            instruction = "Готово! Введите следующее слово"
            color = COLOR_CELL_GREEN
        
        inst_surface = self.font_small.render(instruction, True, color)
        self.screen.blit(inst_surface, (50, y))
    
    def draw(self):
        """Отрисовать все"""
        self.screen.fill(COLOR_BG)
        
        self.draw_grid()
        self.draw_suggestions()
        self.draw_buttons()
        self.draw_info()
        
        pygame.display.flip()
    
    def handle_cell_click(self, row: int, col: int):
        """Обработка клика по ячейке для изменения цвета"""
        if row == self.current_row and not self.row_submitted[row]:
            if len(''.join(self.grid[row])) == 5:  # Слово должно быть введено полностью
                # Циклически меняем цвет: 0 -> 1 -> 2 -> 0
                self.patterns[row][col] = (self.patterns[row][col] + 1) % 3
    
    def submit_current_row(self):
        """Отправить текущую строку"""
        word = ''.join(self.grid[self.current_row])
        pattern = ''.join(str(p) for p in self.patterns[self.current_row])
        
        if len(word) != 5:
            print("\n!!! Слово должно содержать 5 букв")
            return
        
        if word not in self.solver.all_words:
            print(f"\n!!! Слово '{word}' не найдено в словаре")
            return
        
        # Отмечаем строку как отправленную
        self.row_submitted[self.current_row] = True
        
        # Обновляем решатель
        print(f"\n>>> Попытка {self.current_row + 1}: {word.upper()} | Паттерн: {pattern}")
        self.solver.update_remaining(word, pattern)
        
        # Переходим к следующей строке
        if self.current_row < MAX_ATTEMPTS - 1:
            self.current_row += 1
            self.current_col = 0
        
        # Пересчитываем рекомендации
        self._calculate_and_show_suggestions()
    
    def handle_keypress(self, event):
        """Обработка нажатия клавиш"""
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
            # Проверяем английские буквы
            char = event.unicode.lower()
            if ('a' <= char <= 'z') and self.current_col < 5:
                self.grid[self.current_row][self.current_col] = char
                self.current_col += 1
    
    def handle_mouse_click(self, pos):
        """Обработка клика мыши"""
        # Проверка кликов по ячейкам
        if self.current_row < len(self.cell_rects):
            for col, rect in enumerate(self.cell_rects[self.current_row]):
                if rect.collidepoint(pos):
                    self.handle_cell_click(self.current_row, col)
                    return
        
        # Проверка кнопок
        if self.buttons['submit'].collidepoint(pos):
            if self.current_col == 5:
                self.submit_current_row()
        
        elif self.buttons['reset'].collidepoint(pos):
            self.reset()
    
    def reset(self):
        """Сброс состояния"""
        print("\n" + "="*60)
        print("СБРОС - Начинаем заново")
        print("="*60)
        
        self.solver.reset()
        self.current_row = 0
        self.current_col = 0
        self.grid = [['' for _ in range(5)] for _ in range(MAX_ATTEMPTS)]
        self.patterns = [[0 for _ in range(5)] for _ in range(MAX_ATTEMPTS)]
        self.row_submitted = [False for _ in range(MAX_ATTEMPTS)]
        self.top_suggestions = []
        
        self._print_initial_suggestions()
    
    def run(self):
        """Главный цикл"""
        clock = pygame.time.Clock()
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                elif event.type == pygame.KEYDOWN:
                    self.handle_keypress(event)
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Левая кнопка
                        self.handle_mouse_click(event.pos)
            
            self.draw()
            clock.tick(60)


if __name__ == '__main__':
    assistant = WordleAssistant()
    assistant.run()
