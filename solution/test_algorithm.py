#!/usr/bin/env python3
"""Тестовый скрипт для проверки алгоритма кодирования/декодирования."""

import base64
import json
import requests

def levenshtein_distance(s1, s2):
    """Простая реализация расстояния Левенштейна."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

def test_encode_decode():
    """Тестирует encode и decode эндпоинты."""
    url = "http://127.0.0.1:8000"
    
    # Тестовые строки
    test_strings = [
        "Hello World!",
        "123",
        "98127634167239612345987612384796123",
        "Привет мир!",
        "A" * 50,  # Длинная строка
    ]
    
    for test_str in test_strings:
        print(f"\nТестируем строку: '{test_str}'")
        
        # Кодируем
        encode_response = requests.post(
            f"{url}/encode",
            json={"text": test_str},
            headers={"Content-Type": "application/json"}
        )
        
        if encode_response.status_code != 200:
            print(f"Ошибка кодирования: {encode_response.status_code}")
            continue
            
        wav_base64 = encode_response.json()["data"]
        print(f"Получен WAV файл размером: {len(wav_base64)} символов base64")
        
        # Декодируем
        decode_response = requests.post(
            f"{url}/decode",
            json={"data": wav_base64},
            headers={"Content-Type": "application/json"}
        )
        
        if decode_response.status_code != 200:
            print(f"Ошибка декодирования: {decode_response.status_code}")
            continue
            
        decoded_text = decode_response.json()["text"]
        print(f"Декодированный текст: '{decoded_text}'")
        
        # Проверяем точность
        if decoded_text == test_str:
            print("✅ Успешно! Текст восстановлен точно.")
        else:
            print(f"❌ Ошибка! Ожидалось: '{test_str}'")
            print(f"   Получено: '{decoded_text}'")
            
            # Вычисляем расстояние Левенштейна
            distance = levenshtein_distance(test_str, decoded_text)
            accuracy = max(0, (len(test_str) - distance) / len(test_str) * 100)
            print(f"   Расстояние Левенштейна: {distance}")
            print(f"   Точность: {accuracy:.1f}%")

if __name__ == "__main__":
    test_encode_decode() 