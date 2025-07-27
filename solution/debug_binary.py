#!/usr/bin/env python3
"""Отладочный скрипт для анализа бинарных строк."""

import sys
import os

# Добавляем путь к модулю app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import _text_to_binary, _binary_to_text

def analyze_binary(text):
    """Анализирует бинарную строку для текста."""
    print(f"Анализ для текста: '{text}'")
    
    # Кодируем
    binary = _text_to_binary(text)
    print(f"Бинарная строка: {binary}")
    print(f"Длина бинарной строки: {len(binary)}")
    
    # Декодируем
    decoded_text = _binary_to_text(binary)
    print(f"Декодированный текст: '{decoded_text}'")
    
    # Анализируем структуру
    if len(binary) >= 16:
        sync_start = binary[:8]
        sync_end = binary[-8:]
        data_part = binary[8:-8]
        
        print(f"Синхронизация начало: {sync_start}")
        print(f"Синхронизация конец: {sync_end}")
        print(f"Данные: {data_part}")
        print(f"Длина данных: {len(data_part)}")
        
        # Проверяем, делится ли на 8
        if len(data_part) % 8 == 0:
            print(f"Данные делятся на 8: да")
            
            # Конвертируем в байты
            data_bytes = bytearray()
            for i in range(0, len(data_part), 8):
                byte_str = data_part[i:i+8]
                data_bytes.append(int(byte_str, 2))
            
            print(f"Байты: {list(data_bytes)}")
            
            # Пробуем декодировать как UTF-8
            try:
                decoded = data_bytes.decode('utf-8')
                print(f"UTF-8 декодирование: '{decoded}'")
            except Exception as e:
                print(f"UTF-8 ошибка: {e}")
        else:
            print(f"Данные делятся на 8: нет (остаток {len(data_part) % 8})")
    
    print("-" * 50)

# Тестируем различные строки
test_strings = [
    "ABC",
    "Hello World!",
    "123",
    "Привет мир!",
    "A" * 50,
]

for text in test_strings:
    analyze_binary(text) 