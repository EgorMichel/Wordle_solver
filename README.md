# Wordle Assistant - Умный помощник для Wordle

## Описание

Интеллектуальный помощник для игры в Wordle с поддержкой **русского** и **английского** языков. Программа использует алгоритм максимизации информационной энтропии для подбора оптимальных слов.

**Как работает:** Вы играете в настоящий Wordle, вводите попытки в программу вместе с цветовой обратной связью, а программа показывает лучшие слова для следующего хода.

## Алгоритм

Решатель использует **информационную энтропию** для выбора оптимальных слов:

```
H(слово) = -Σ P(паттерн) × log₂(P(паттерн))
```

На каждом шаге выбирается слово с максимальной энтропией - то, которое в среднем даст больше всего информации.

### 📖 Подробная документация

👉 **[ALGORITHM.md](ALGORITHM.md)** - Детальное описание алгоритма с формулами и примерами

## Поддержка языков

- 🇷🇺 **Русский**: `words_ru.txt` (4302 слова)
- 🇬🇧 **English**: `words_en.txt` (3932 слова)

## Установка

### 1. Установка зависимостей

**Рекомендуется:**
```bash
pip install -r requirements.txt
```

Это установит: `pygame`, `numba`, `numpy`

**Минимальные требования:**
```bash
pip install pygame
```

### 2. Создание кэша (ОБЯЗАТЕЛЬНО при первом запуске!)

**Для русского:**
```bash
python generate_cache.py words_ru.txt ru
```

**Для английского:**
```bash
python generate_cache.py words_en.txt en
```

Процесс займет 3-5 минут для каждого языка, но выполняется **один раз**. Создаст файлы `first_move_cache_ru.pkl` и `first_move_cache_en.pkl`.

## Использование

### 🎮 Запуск GUI помощника

**Обязательно** указывайте язык через флаг `-l`:

```bash
# Русская версия
python main.py -l ru

# English version
python main.py -l en
```

**Управление:**
- Печатайте буквы на клавиатуре
- Кликайте по буквам для установки цвета:
  - **1 клик** = 🟨 Желтый (буква есть, но не на месте)
  - **2 клика** = 🟩 Зеленый (буква на правильном месте)
  - **3 клика** = ⬜ Серый (буквы нет)
- `Enter` - отправить слово
- `Backspace` - удалить букву
- Кнопка "Сброс" - начать заново

### 📊 Запуск бенчмарка

**Обязательно** указывайте язык через флаг `-l`:

```bash
# Русский: 100 случайных игр
python benchmark.py -l ru

# Английский: 500 игр
python benchmark.py -l en -n 500

# Подробный вывод
python benchmark.py -l ru -n 10 -v

# Конкретные слова
python benchmark.py -l en --words crane slate trace
```

**Показывает:**
- ✅ Процент побед
- 📊 Среднее количество попыток
- 📈 Распределение по попыткам
- ⚠️ Худшие случаи
- ❌ Нерешенные слова

### 💻 Использование только решателя (без GUI)

```python
from wordle_solver import WordleSolver

# Создаем решатель для русского языка
solver = WordleSolver(words_file="words_ru.txt", language="ru")

# Получаем рекомендацию
word = solver.get_suggestion()
print(f"Рекомендуемое слово: {word}")

# После попытки обновляем состояние
# pattern: '0' = серый, '1' = желтый, '2' = зеленый
solver.update_remaining(word, "01220")

# Следующая рекомендация
next_word = solver.get_suggestion()
```

## Эффективность алгоритма

### Результаты бенчмарка (1000 игр)

**🇷🇺 Русский язык:**
- **Побед**: ~99%+
- **Среднее попыток**: 3.7-3.9
- **Распределение**:
  - 1 попытка: ~0.2%
  - 2 попытки: ~5-8%
  - 3 попытки: ~35-40%
  - 4 попытки: ~40-45%
  - 5 попыток: ~10-12%
  - 6 попыток: ~1-2%

**🇬🇧 English:**
- **Win rate**: ~99%+
- **Average**: 3.8-4.0 tries
- **Distribution**:
  - 1 try: ~0.2%
  - 2 tries: ~4-7%
  - 3 tries: ~33-38%
  - 4 tries: ~42-47%
  - 5 tries: ~10-13%
  - 6 tries: ~1-2%

## Лучшие стартовые слова

### 🇬🇧 English (Top-10)
1. **ARIES** - Entropy: 6.0431
2. **ARCES** - Entropy: 6.0379
3. **CARES** - Entropy: 6.0280
4. **ARLES** - Entropy: 5.9714
5. **BARES** - Entropy: 5.9689
6. **CARSE** - Entropy: 5.9584
7. **ARISE** - Entropy: 5.9455
8. **CRAIE** - Entropy: 5.9415
9. **BARIE** - Entropy: 5.9383
10. **BRAES** - Entropy: 5.9301

### 🇷🇺 Русский (Top-10)
Запустите `python generate_cache.py words_ru.txt ru` для полного списка.

## Производительность

### С Numba (рекомендуется)
- ⚡ **10-50x** быстрее
- 🔄 Параллельный расчет энтропий
- Последующие ходы: 0.05-0.2 сек
- Бенчмарк 100 игр: ~30-60 сек

### Без Numba
- Последующие ходы: 0.5-2 сек
- Бенчмарк 100 игр: ~3-5 минут

## Структура проекта

```
main.py                   # 🎮 Точка входа - запуск GUI помощника
benchmark.py              # 📊 Бенчмарк для оценки эффективности
wordle_solver.py          # 🧠 Основная логика решателя (с Numba)
wordle_assistant.py       # 🖥️ GUI помощник в Pygame
generate_cache.py         # 🔧 Создание кэша энтропий

words_ru.txt              # 📚 Русский словарь (4302 слова)
words_en.txt              # 📚 English dictionary (3932 words)
first_move_cache_ru.pkl   # 💾 Кэш для русского
first_move_cache_en.pkl   # 💾 Кэш для английского

ALGORITHM.md              # 📖 Подробное описание алгоритма
README.md                 # 📄 Документация
requirements.txt          # 📦 Зависимости
```

## Тестирование

```bash
# Базовые тесты
python test_solver.py

# Показать справку
python main.py --help
python benchmark.py --help
```

## Быстрый старт

```bash
# 1. Установить зависимости
pip install -r requirements.txt

# 2. Создать кэш для нужного языка
python generate_cache.py words_ru.txt ru
python generate_cache.py words_en.txt en

# 3. Запустить помощника
python main.py -l ru
# или
python main.py -l en

# 4. (Опционально) Запустить бенчмарк
python benchmark.py -l ru -n 100
```

## Примеры использования

### GUI помощник
```bash
# Русский
python main.py -l ru

# English
python main.py -l en
```

### Бенчмарк
```bash
# Русский: 100 игр
python benchmark.py -l ru

# English: 500 игр с подробным выводом
python benchmark.py -l en -n 500 -v

# Тест конкретных слов
python benchmark.py -l ru --words кошка собака мышка
```

### Программный доступ
```python
from wordle_solver import WordleSolver

# Русский
solver = WordleSolver(words_file="words_ru.txt", language="ru")

# English
solver = WordleSolver(words_file="words_en.txt", language="en")

# Получить рекомендацию
word = solver.get_suggestion()

# Обновить после попытки (pattern: '0'=серый, '1'=желтый, '2'=зеленый)
solver.update_remaining(word, "01220")
```

## Лицензия

MIT License

## Автор

Создано с использованием алгоритма информационной энтропии для оптимального решения Wordle.