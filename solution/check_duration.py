#!/usr/bin/env python3
"""Скрипт для проверки длительности сигналов."""

import sys
import os

# Добавляем путь к модулю app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import _text_to_binary, _generate_fsk_signal, SAMPLE_RATE

def check_duration(text):
    """Проверяет длительность сигнала для текста."""
    binary = _text_to_binary(text)
    signal = _generate_fsk_signal(binary)
    duration = len(signal) / SAMPLE_RATE
    print(f"'{text}': {len(text)} символов, {len(binary)} бит, {duration:.2f} секунд")

# Тестируем различные строки
test_strings = [
    "ABC",
    "Hello World!",
    "123",
    "Привет мир!",
    "!@#$%^&*()",
    "0123456789",
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "98127634167239612345987612384796123",
    "The quick brown fox jumps over the lazy dog",
    "abcdefghijklmnopqrstuvwxyz",
]

for text in test_strings:
    check_duration(text) 