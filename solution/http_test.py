#!/usr/bin/env python3
"""Простой HTTP тест."""

import requests
import json

def test_http_single(test_str):
    """Тест HTTP API с одной строкой."""
    url = "http://127.0.0.1:8000"
    
    print(f"Тестируем строку: '{test_str}'")
    
    # Кодируем
    encode_response = requests.post(
        f"{url}/encode",
        json={"text": test_str},
        headers={"Content-Type": "application/json"}
    )
    
    if encode_response.status_code != 200:
        print(f"❌ Ошибка кодирования: {encode_response.status_code}")
        return False
    
    encode_data = encode_response.json()
    wav_base64 = encode_data["data"]
    print(f"  Получен WAV файл размером: {len(wav_base64)} символов base64")
    
    # Декодируем
    decode_response = requests.post(
        f"{url}/decode",
        json={"data": wav_base64},
        headers={"Content-Type": "application/json"}
    )
    
    if decode_response.status_code != 200:
        print(f"❌ Ошибка декодирования: {decode_response.status_code}")
        return False
    
    decode_data = decode_response.json()
    decoded_text = decode_data["text"]
    print(f"  Декодированный текст: '{decoded_text}'")
    
    # Проверяем результат
    if decoded_text == test_str:
        print("  ✅ Успех!")
        return True
    else:
        print(f"  ❌ Ошибка! Ожидалось: '{test_str}', Получено: '{decoded_text}'")
        return False

def test_http():
    """Тест HTTP API с различными строками."""
    test_strings = [
        "ABC",
        "Hello World!",
        "123",
        "Привет мир!",
        "A" * 50,
        "98127634167239612345987612384796123",
        "!@#$%^&*()",
        "The quick brown fox jumps over the lazy dog",
        "0123456789",
        "abcdefghijklmnopqrstuvwxyz"
    ]
    
    success_count = 0
    total_count = len(test_strings)
    
    for test_str in test_strings:
        if test_http_single(test_str):
            success_count += 1
        print()
    
    print(f"Результат: {success_count}/{total_count} успешных тестов ({success_count/total_count*100:.1f}%)")

if __name__ == "__main__":
    test_http() 