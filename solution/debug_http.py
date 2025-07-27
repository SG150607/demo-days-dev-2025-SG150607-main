#!/usr/bin/env python3
"""Отладочный скрипт для анализа HTTP API."""

import requests
import base64
import wave
import io
import numpy as np
import sys
import os

# Добавляем путь к модулю app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import _decode_fsk_signal, _binary_to_text

def analyze_http_wav(test_str):
    """Анализирует WAV файл из HTTP API."""
    url = "http://127.0.0.1:8000"
    
    print(f"Анализ HTTP WAV для: '{test_str}'")
    
    # Кодируем через HTTP
    encode_response = requests.post(
        f"{url}/encode",
        json={"text": test_str},
        headers={"Content-Type": "application/json"}
    )
    
    if encode_response.status_code != 200:
        print(f"❌ Ошибка кодирования: {encode_response.status_code}")
        return
    
    encode_data = encode_response.json()
    wav_base64 = encode_data["data"]
    print(f"  Base64 размер: {len(wav_base64)} символов")
    
    # Декодируем base64
    wav_bytes = base64.b64decode(wav_base64)
    print(f"  WAV размер: {len(wav_bytes)} байт")
    
    # Анализируем WAV
    with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
        print(f"  WAV параметры: каналы={wf.getnchannels()}, частота={wf.getframerate()}, биты={wf.getsampwidth()*8}")
        audio_data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
        print(f"  Аудио данные: {len(audio_data)} сэмплов, диапазон [{audio_data.min()}, {audio_data.max()}]")
    
    # Декодируем FSK напрямую
    binary = _decode_fsk_signal(audio_data)
    print(f"  Декодированная бинарная строка: {binary[:50]}...")
    print(f"  Длина бинарной строки: {len(binary)}")
    
    # Конвертируем в текст
    text = _binary_to_text(binary)
    print(f"  Декодированный текст: '{text}'")
    
    # Проверяем результат
    if text == test_str:
        print("  ✅ Успех!")
    else:
        print(f"  ❌ Ошибка! Ожидалось: '{test_str}', Получено: '{text}'")
    
    print()

# Тестируем различные строки
test_strings = [
    "ABC",
    "Hello World!",
    "123",
]

for text in test_strings:
    analyze_http_wav(text) 