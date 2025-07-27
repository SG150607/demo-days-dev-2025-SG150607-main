#!/usr/bin/env python3
"""Отладочный тест для проверки алгоритма."""

import base64
import json
import requests
import numpy as np
import wave
import io
import sys
import os

# Добавляем путь к модулю app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import text_to_audio, audio_to_text, _text_to_binary, _binary_to_text, _generate_fsk_signal, _decode_fsk_signal

def test_audio_to_text_direct():
    """Прямой тест функции audio_to_text."""
    test_str = "ABC"
    
    print(f"Тестируем строку: '{test_str}'")
    
    # Генерируем WAV через text_to_audio
    wav_bytes = text_to_audio(test_str)
    print(f"WAV файл: {len(wav_bytes)} байт")
    
    # Декодируем через audio_to_text
    decoded_text = audio_to_text(wav_bytes)
    print(f"Декодированный текст: '{decoded_text}'")
    
    # Проверяем результат
    if decoded_text == test_str:
        print("✅ Успех!")
    else:
        print(f"❌ Ошибка! Ожидалось: '{test_str}', Получено: '{decoded_text}'")
        
        # Анализируем WAV файл
        try:
            with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
                print(f"WAV параметры: каналы={wf.getnchannels()}, частота={wf.getframerate()}, биты={wf.getsampwidth()*8}")
                audio_data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
                print(f"Аудио данные: {len(audio_data)} сэмплов, диапазон [{audio_data.min()}, {audio_data.max()}]")
                
                # Декодируем FSK напрямую
                binary = _decode_fsk_signal(audio_data)
                print(f"Декодированная бинарная строка: {binary}")
                
                # Конвертируем в текст
                text = _binary_to_text(binary)
                print(f"Прямое декодирование: '{text}'")
        except Exception as e:
            print(f"Ошибка анализа WAV: {e}")

def test_wav_roundtrip():
    """Тест сохранения и чтения WAV файла."""
    test_str = "ABC"
    
    print(f"Тестируем строку: '{test_str}'")
    
    # Шаг 1: Конвертируем текст в бинарную строку
    binary = _text_to_binary(test_str)
    print(f"Бинарная строка: {binary}")
    
    # Шаг 2: Генерируем FSK сигнал
    signal = _generate_fsk_signal(binary)
    print(f"FSK сигнал: {len(signal)} сэмплов, диапазон [{signal.min()}, {signal.max()}]")
    
    # Шаг 3: Сохраняем в WAV
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(44100)
        wf.writeframes(signal.tobytes())
    
    wav_bytes = buf.getvalue()
    print(f"WAV файл: {len(wav_bytes)} байт")
    
    # Шаг 4: Читаем WAV
    with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
        audio_data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
    
    print(f"Прочитанный аудио: {len(audio_data)} сэмплов, диапазон [{audio_data.min()}, {audio_data.max()}]")
    
    # Шаг 5: Декодируем FSK сигнал
    decoded_binary = _decode_fsk_signal(audio_data)
    print(f"Декодированная бинарная строка: {decoded_binary}")
    
    # Шаг 6: Конвертируем в текст
    decoded_text = _binary_to_text(decoded_binary)
    print(f"Декодированный текст: '{decoded_text}'")
    
    # Проверяем результат
    if decoded_text == test_str:
        print("✅ Успех!")
    else:
        print(f"❌ Ошибка! Ожидалось: '{test_str}', Получено: '{decoded_text}'")
        
        # Сравниваем сигналы
        print(f"Оригинальный сигнал: {len(signal)} сэмплов")
        print(f"Прочитанный сигнал: {len(audio_data)} сэмплов")
        
        if len(signal) == len(audio_data):
            differences = np.sum(signal != audio_data)
            print(f"Различий в сигналах: {differences} из {len(signal)}")
            
            if differences > 0:
                print(f"Первые 10 различий:")
                for i in range(min(10, len(signal))):
                    if signal[i] != audio_data[i]:
                        print(f"  [{i}]: {signal[i]} != {audio_data[i]}")

def test_direct():
    """Прямой тест функций без HTTP."""
    test_str = "ABC"
    
    print(f"Тестируем строку: '{test_str}'")
    
    # Шаг 1: Конвертируем текст в бинарную строку
    binary = _text_to_binary(test_str)
    print(f"Бинарная строка: {binary}")
    
    # Шаг 2: Генерируем FSK сигнал
    signal = _generate_fsk_signal(binary)
    print(f"FSK сигнал: {len(signal)} сэмплов, диапазон [{signal.min()}, {signal.max()}]")
    
    # Шаг 3: Декодируем FSK сигнал обратно в бинарную строку
    decoded_binary = _decode_fsk_signal(signal)
    print(f"Декодированная бинарная строка: {decoded_binary}")
    
    # Шаг 4: Конвертируем бинарную строку обратно в текст
    decoded_text = _binary_to_text(decoded_binary)
    print(f"Декодированный текст: '{decoded_text}'")
    
    # Проверяем результат
    if decoded_text == test_str:
        print("✅ Успех!")
    else:
        print(f"❌ Ошибка! Ожидалось: '{test_str}', Получено: '{decoded_text}'")
        
        # Сравниваем бинарные строки
        print(f"Ожидаемая бинарная строка: {binary}")
        print(f"Полученная бинарная строка: {decoded_binary}")
        
        # Находим различия
        min_len = min(len(binary), len(decoded_binary))
        differences = sum(1 for i in range(min_len) if binary[i] != decoded_binary[i])
        print(f"Различий в бинарных строках: {differences} из {min_len}")

def test_simple():
    """Простой тест с отладкой."""
    url = "http://127.0.0.1:8000"
    test_str = "ABC"
    
    print(f"Тестируем строку: '{test_str}'")
    
    # Кодируем
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
    print(f"Получен WAV файл размером: {len(wav_base64)} символов base64")
    
    # Декодируем
    decode_response = requests.post(
        f"{url}/decode",
        json={"data": wav_base64},
        headers={"Content-Type": "application/json"}
    )
    
    if decode_response.status_code != 200:
        print(f"❌ Ошибка декодирования: {decode_response.status_code}")
        return
    
    decode_data = decode_response.json()
    decoded_text = decode_data["text"]
    print(f"Декодированный текст: '{decoded_text}'")
    
    # Проверяем результат
    if decoded_text == test_str:
        print("✅ Успех!")
    else:
        print(f"❌ Ошибка! Ожидалось: '{test_str}', Получено: '{decoded_text}'")
        
        # Анализируем WAV файл
        try:
            wav_bytes = base64.b64decode(wav_base64)
            with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
                print(f"WAV параметры: каналы={wf.getnchannels()}, частота={wf.getframerate()}, биты={wf.getsampwidth()*8}")
                audio_data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
                print(f"Аудио данные: {len(audio_data)} сэмплов, диапазон [{audio_data.min()}, {audio_data.max()}]")
        except Exception as e:
            print(f"Ошибка анализа WAV: {e}")

def test_base64_roundtrip():
    """Тест base64 кодирования/декодирования."""
    test_str = "ABC"
    
    print(f"Тестируем строку: '{test_str}'")
    
    # Генерируем WAV
    wav_bytes = text_to_audio(test_str)
    print(f"WAV файл: {len(wav_bytes)} байт")
    
    # Кодируем в base64
    wav_base64 = base64.b64encode(wav_bytes).decode("utf-8")
    print(f"Base64: {len(wav_base64)} символов")
    
    # Декодируем из base64
    decoded_wav_bytes = base64.b64decode(wav_base64)
    print(f"Декодированный WAV: {len(decoded_wav_bytes)} байт")
    
    # Проверяем, что байты идентичны
    if wav_bytes == decoded_wav_bytes:
        print("✅ Base64 roundtrip успешен!")
    else:
        print("❌ Base64 roundtrip не удался!")
        print(f"Оригинальные байты: {wav_bytes[:20]}...")
        print(f"Декодированные байты: {decoded_wav_bytes[:20]}...")
    
    # Декодируем через audio_to_text
    decoded_text = audio_to_text(decoded_wav_bytes)
    print(f"Декодированный текст: '{decoded_text}'")
    
    # Проверяем результат
    if decoded_text == test_str:
        print("✅ Успех!")
    else:
        print(f"❌ Ошибка! Ожидалось: '{test_str}', Получено: '{decoded_text}'")

if __name__ == "__main__":
    print("=== Прямой тест ===")
    test_direct()
    print("\n=== WAV roundtrip тест ===")
    test_wav_roundtrip()
    print("\n=== audio_to_text прямой тест ===")
    test_audio_to_text_direct()
    print("\n=== Base64 roundtrip тест ===")
    test_base64_roundtrip()
    print("\n=== HTTP тест ===")
    test_simple() 