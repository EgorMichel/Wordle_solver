import json

# Читаем файл с Unicode escape-последовательностями
with open('Words/test.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# Парсим JSON-массив
words = json.loads(content)

# Записываем слова по одному на строку
with open('Words/test.txt', 'w', encoding='utf-8') as f:
    for word in words:
        f.write(word + '\n')

print(f"Преобразовано {len(words)} слов")