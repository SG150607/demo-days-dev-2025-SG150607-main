#!/usr/bin/env python3
"""Тест для проверки сервиса кодирования/декодирования."""

import requests
import base64
import json

def test_service():
    """Тестирует сервис с различными строками."""
    url = "http://127.0.0.1:8000"
    
    # Тестовые строки
    test_cases = [
        "ABC",
        "Hello World!",
        "123",
        "Привет мир!",
        "!@#$%^&*()",
        "0123456789",
        "The quick brown fox jumps over the lazy dog",
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for test_str in test_cases:
        print(f"Тестируем: '{test_str}'")
        
        try:
            # Кодируем
            encode_response = requests.post(
                f"{url}/encode",
                json={"text": test_str},
                headers={"Content-Type": "application/json"}
            )
            
            if encode_response.status_code != 200:
                print(f"  ❌ Ошибка кодирования: {encode_response.status_code}")
                continue
            
            encode_data = encode_response.json()
            wav_base64 = encode_data["data"]
            
            # Декодируем
            decode_response = requests.post(
                f"{url}/decode",
                json={"data": wav_base64},
                headers={"Content-Type": "application/json"}
            )
            
            if decode_response.status_code != 200:
                print(f"  ❌ Ошибка декодирования: {decode_response.status_code}")
                continue
            
            decode_data = decode_response.json()
            decoded_text = decode_data["text"]
            
            # Проверяем результат
            if decoded_text == test_str:
                print(f"  ✅ Успех!")
                success_count += 1
            else:
                print(f"  ❌ Ошибка! Ожидалось: '{test_str}', Получено: '{decoded_text}'")
                
        except Exception as e:
            print(f"  ❌ Исключение: {e}")
    
    print(f"\nРезультат: {success_count}/{total_count} успешных тестов ({success_count/total_count*100:.1f}%)")
    
    # Требуем минимум 90% успешных тестов
    assert success_count / total_count >= 0.9, f"Только {success_count/total_count*100:.1f}% тестов прошли успешно"

if __name__ == "__main__":
    test_service() 