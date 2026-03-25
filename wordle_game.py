"""
Визуализация Wordle с помощью Pygame
Интерактивная игра с подсказками от решателя
"""

import pygame
import sys
from wordle_solver import WordleSolver
from typing import List, Optional


# Константы
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 900
CELL_SIZE = 80
CELL_MARGIN = 10
GRID_START_X = 180
GRID_START_Y = 100
MAX_ATTEMPTS = 6

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


class WordleGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Wordle Solver - Русский")
        
        # Шрифты
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)
        
        # Игровое состояние
        self.solver = WordleSolver()
        self.target_word = None
        self.current_row = 0
        self.current_col = 0
        self.grid = [['' for _ in range(5)] for _ in range(MAX_ATTEMPTS)]
        self.patterns = [None for _ in range(MAX_ATTEMPTS)]
        self.game_over = False
        self.won = False
        
        # Подсказка от решателя
        self.suggestion = None
        self.show_suggestion = False
        
        # Кнопки
        self.buttons = {
            'new_game': pygame.Rect(50, 750, 150, 50),
            'solve': pygame.Rect(220, 750, 150, 50),
            'hint': pygame.Rect(390, 750, 150, 50),
            'auto': pygame.Rect(560, 750, 150, 50),
        }
        
        self.start_new_game()
    
    def start_new_game(self):
        """Начать новую игру"""
        import random
        self.target_word = random.choice(self.solver.all_words)
        self.current_row = 0
        self.current_col = 0
        self.grid = [['' for _ in range(5)] for _ in range(MAX_ATTEMPTS)]
        self.patterns = [None for _ in range(MAX_ATTEMPTS)]
        self.game_over = False
        self.won = False
        self.solver.reset()
        self.suggestion = None
        self.show_suggestion = False
        print(f"\n=== Новая игра ===")
        print(f"Загаданное слово: {self.target_word}")
    
    def get_suggestion(self):
        """Получить подсказку от решателя"""
        if not self.game_over and self.solver.remaining_words:
            self.suggestion = self.solver.get_suggestion()
            self.show_suggestion = True
    
    def auto_solve_step(self):
        """Автоматический шаг решателя"""
        if not self.game_over:
            suggestion = self.solver.get_suggestion()
            # Вводим слово
            for i, char in enumerate(suggestion):
                self.grid[self.current_row][i] = char
            self.current_col = 5
            # Сразу отправляем
            self.submit_word()
    
    def draw_cell(self, x: int, y: int, char: str, state: Optional[int] = None):
        """
        Нарисовать ячейку
        state: None (пустая), 0 (серая), 1 (желтая), 2 (зеленая)
        """
        # Выбор цвета
        if state is None:
            if char:
                color = COLOR_CELL_EMPTY
            else:
                color = COLOR_CELL_EMPTY
        elif state == 0:
            color = COLOR_CELL_GRAY
        elif state == 1:
            color = COLOR_CELL_YELLOW
        else:  # state == 2
            color = COLOR_CELL_GREEN
        
        # Рисуем прямоугольник
        rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, COLOR_BG, rect, 2)
        
        # Рисуем букву
        if char:
            text_surface = self.font_large.render(char.upper(), True, COLOR_TEXT)
            text_rect = text_surface.get_rect(center=rect.center)
            self.screen.blit(text_surface, text_rect)
    
    def draw_grid(self):
        """Нарисовать игровую сетку"""
        for row in range(MAX_ATTEMPTS):
            for col in range(5):
                x = GRID_START_X + col * (CELL_SIZE + CELL_MARGIN)
                y = GRID_START_Y + row * (CELL_SIZE + CELL_MARGIN)
                
                char = self.grid[row][col]
                
                # Определяем состояние ячейки
                if self.patterns[row] is not None:
                    state = int(self.patterns[row][col])
                elif row == self.current_row:
                    state = None  # Текущая строка - без цвета
                else:
                    state = None
                
                self.draw_cell(x, y, char, state)
    
    def draw_button(self, name: str, text: str):
        """Нарисовать кнопку"""
        rect = self.buttons[name]
        mouse_pos = pygame.mouse.get_pos()
        
        # Проверка наведения
        if rect.collidepoint(mouse_pos):
            color = COLOR_BUTTON_HOVER
        else:
            color = COLOR_BUTTON
        
        pygame.draw.rect(self.screen, color, rect, border_radius=5)
        pygame.draw.rect(self.screen, COLOR_TEXT_DIM, rect, 2, border_radius=5)
        
        # Текст кнопки
        text_surface = self.font_small.render(text, True, COLOR_TEXT)
        text_rect = text_surface.get_rect(center=rect.center)
        self.screen.blit(text_surface, text_rect)
    
    def draw_info(self):
        """Нарисовать информацию"""
        # Заголовок
        title = self.font_large.render("WORDLE SOLVER", True, COLOR_TEXT)
        self.screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 20))
        
        # Информация о состоянии
        y_offset = 820
        
        if self.game_over:
            if self.won:
                status_text = f"Победа! Слово: {self.target_word.upper()}"
                color = COLOR_CELL_GREEN
            else:
                status_text = f"Проигрыш! Слово: {self.target_word.upper()}"
                color = COLOR_CELL_GRAY
            
            status_surface = self.font_medium.render(status_text, True, color)
            self.screen.blit(status_surface, (WINDOW_WIDTH // 2 - status_surface.get_width() // 2, y_offset))
        else:
            # Количество оставшихся кандидатов
            remaining = len(self.solver.remaining_words)
            info_text = f"Осталось кандидатов: {remaining}"
            info_surface = self.font_small.render(info_text, True, COLOR_TEXT_DIM)
            self.screen.blit(info_surface, (WINDOW_WIDTH // 2 - info_surface.get_width() // 2, y_offset))
            
            # Подсказка
            if self.show_suggestion and self.suggestion:
                y_offset += 30
                hint_text = f"Подсказка: {self.suggestion.upper()}"
                hint_surface = self.font_small.render(hint_text, True, COLOR_CELL_YELLOW)
                self.screen.blit(hint_surface, (WINDOW_WIDTH // 2 - hint_surface.get_width() // 2, y_offset))
    
    def draw(self):
        """Отрисовать все элементы"""
        self.screen.fill(COLOR_BG)
        
        self.draw_grid()
        self.draw_button('new_game', 'Новая игра')
        self.draw_button('solve', 'Решить')
        self.draw_button('hint', 'Подсказка')
        self.draw_button('auto', 'Авто шаг')
        self.draw_info()
        
        pygame.display.flip()
    
    def handle_keypress(self, event):
        """Обработка нажатия клавиш"""
        if self.game_over:
            return
        
        if event.key == pygame.K_BACKSPACE:
            if self.current_col > 0:
                self.current_col -= 1
                self.grid[self.current_row][self.current_col] = ''
                self.show_suggestion = False
        
        elif event.key == pygame.K_RETURN:
            if self.current_col == 5:
                self.submit_word()
        
        else:
            # Проверяем, является ли символ русской буквой
            char = event.unicode.lower()
            if 'а' <= char <= 'я' or char == 'ё':
                if self.current_col < 5:
                    self.grid[self.current_row][self.current_col] = char
                    self.current_col += 1
                    self.show_suggestion = False
    
    def submit_word(self):
        """Отправить слово"""
        word = ''.join(self.grid[self.current_row])
        
        if len(word) != 5:
            print("Слово должно содержать 5 букв")
            return
        
        if word not in self.solver.all_words:
            print(f"Слово '{word}' не найдено в словаре")
            return
        
        # Получаем паттерн
        pattern = self.solver.get_pattern(word, self.target_word)
        self.patterns[self.current_row] = pattern
        
        # Обновляем решатель
        self.solver.update_remaining(word, pattern)
        
        # Проверяем победу
        if pattern == '22222':
            self.game_over = True
            self.won = True
            print(f"Победа на попытке {self.current_row + 1}!")
            return
        
        # Переходим к следующей строке
        self.current_row += 1
        self.current_col = 0
        
        # Проверяем проигрыш
        if self.current_row >= MAX_ATTEMPTS:
            self.game_over = True
            self.won = False
            print(f"Проигрыш! Слово было: {self.target_word}")
        
        # Сбрасываем подсказку
        self.show_suggestion = False
        self.suggestion = None
    
    def handle_mouse_click(self, pos):
        """Обработка клика мыши"""
        for name, rect in self.buttons.items():
            if rect.collidepoint(pos):
                if name == 'new_game':
                    self.start_new_game()
                elif name == 'hint':
                    self.get_suggestion()
                elif name == 'auto':
                    self.auto_solve_step()
                elif name == 'solve':
                    # Автоматическое решение до конца
                    while not self.game_over:
                        self.auto_solve_step()
                        pygame.time.wait(500)  # Задержка для визуализации
                        self.draw()
    
    def run(self):
        """Главный игровой цикл"""
        clock = pygame.time.Clock()
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                elif event.type == pygame.KEYDOWN:
                    self.handle_keypress(event)
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Левая кнопка мыши
                        self.handle_mouse_click(event.pos)
            
            self.draw()
            clock.tick(60)


if __name__ == '__main__':
    game = WordleGame()
    game.run()