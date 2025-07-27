#!/usr/bin/env python3
"""Отладочный скрипт для анализа FSK декодирования."""

import sys
import os

# Добавляем путь к модулю app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import _text_to_binary, _generate_fsk_signal, _decode_fsk_signal, _binary_to_text

def analyze_fsk(text):
    """Анализирует FSK кодирование/декодирование для текста."""
    print(f"Анализ FSK для текста: '{text}'")
    
    # Шаг 1: Конвертируем в бинарную строку
    binary = _text_to_binary(text)
    print(f"Бинарная строка: {binary}")
    print(f"Длина бинарной строки: {len(binary)}")
    
    # Шаг 2: Генерируем FSK сигнал
    signal = _generate_fsk_signal(binary)
    print(f"FSK сигнал: {len(signal)} сэмплов")
    
    # Шаг 3: Декодируем FSK сигнал
    decoded_binary = _decode_fsk_signal(signal)
    print(f"Декодированная бинарная строка: {decoded_binary}")
    print(f"Длина декодированной бинарной строки: {len(decoded_binary)}")
    
    # Шаг 4: Конвертируем в текст
    decoded_text = _binary_to_text(decoded_binary)
    print(f"Декодированный текст: '{decoded_text}'")
    
    # Проверяем результат
    if decoded_text == text:
        print("✅ Успех!")
    else:
        print(f"❌ Ошибка! Ожидалось: '{text}', Получено: '{decoded_text}'")
        
        # Сравниваем бинарные строки
        if len(binary) == len(decoded_binary):
            differences = sum(1 for i in range(len(binary)) if binary[i] != decoded_binary[i])
            print(f"Различий в бинарных строках: {differences} из {len(binary)}")
            
            if differences > 0:
                print("Первые 10 различий:")
                count = 0
                for i in range(len(binary)):
                    if binary[i] != decoded_binary[i] and count < 10:
                        print(f"  [{i}]: {binary[i]} != {decoded_binary[i]}")
                        count += 1
        else:
            print(f"Разная длина: оригинал {len(binary)}, декодированный {len(decoded_binary)}")
    
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
    analyze_fsk(text) 