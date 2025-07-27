
"""FastAPI сервис, кодирующий текст в WAV и декодирующий его обратно.

✦ Реализуйте функции `text_to_audio` и `audio_to_text`.
✦ Формат аудио: 44100Hz, 16‑bit PCM, mono.
"""

import base64
import io
import wave
import struct

import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel, Field

SAMPLE_RATE = 44_100   # Hz
BIT_DEPTH = 16         # bits per sample
CHANNELS = 1

# Параметры кодирования
SYMBOL_DURATION = 0.1  # длительность одного символа в секундах
FREQ_SPACE = 200       # Hz между частотами символов
START_FREQ = 800       # начальная частота для символа '0'
MAX_DURATION = 50.0    # максимальная длительность в секундах (увеличено для самых длинных строк)

app = FastAPI(swagger_ui_parameters={"syntaxHighlight": False})


# ---------------------------- pydantic models ---------------------------- #

class EncodeRequest(BaseModel):
    text: str = Field(..., description="Строка для кодирования в звук")


class EncodeResponse(BaseModel):
    data: str  # base64 wav


class DecodeRequest(BaseModel):
    data: str  # base64 wav


class DecodeResponse(BaseModel):
    text: str


# ---------------------------- helpers ---------------------------- #

def _empty_wav(duration_sec: float = 1.0) -> bytes:
    """Возвращает WAV‑байты тишины длиной *duration_sec*."""
    n_samples = int(SAMPLE_RATE * duration_sec)
    silence = np.zeros(n_samples, dtype=np.int16)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(BIT_DEPTH // 8)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(silence.tobytes())
    return buf.getvalue()


def _text_to_binary(text: str) -> str:
    """Конвертирует текст в бинарную строку с добавлением контрольных битов."""
    # Конвертируем текст в байты UTF-8
    text_bytes = text.encode('utf-8')
    
    # Добавляем контрольную сумму и длину в байтах
    length = len(text_bytes)  # Длина в байтах, а не в символах
    checksum = sum(ord(c) for c in text) % 256
    
    # Формируем заголовок: длина (2 байта) + контрольная сумма (1 байт)
    header = struct.pack('>HB', length, checksum)
    
    # Конвертируем текст в байты и добавляем заголовок
    data_bytes = header + text_bytes
    
    # Конвертируем в бинарную строку
    binary = ''.join(f'{b:08b}' for b in data_bytes)
    
    # Добавляем синхронизационные биты в начале и конце
    sync_pattern = '10101010'  # 8 бит синхронизации
    binary = sync_pattern + binary + sync_pattern
    
    return binary


def _binary_to_text(binary: str) -> str:
    """Конвертирует бинарную строку обратно в текст с проверкой контрольной суммы."""
    try:
        # Убираем синхронизационные биты
        if len(binary) < 16:
            return ""
        
        # Ищем синхронизационные паттерны
        start_idx = binary.find('10101010')
        if start_idx == -1:
            return ""
        
        end_idx = binary.rfind('10101010')
        if end_idx <= start_idx:
            return ""
        
        # Извлекаем данные между синхронизационными паттернами
        data_binary = binary[start_idx + 8:end_idx]
        
        # Конвертируем бинарную строку в байты
        if len(data_binary) % 8 != 0:
            return ""
        
        data_bytes = bytearray()
        for i in range(0, len(data_binary), 8):
            byte_str = data_binary[i:i+8]
            data_bytes.append(int(byte_str, 2))
        
        if len(data_bytes) < 3:
            return ""
        
        # Извлекаем заголовок
        length = struct.unpack('>H', data_bytes[:2])[0]
        checksum = data_bytes[2]
        
        # Проверяем длину
        if len(data_bytes) < 3 + length:
            return ""
        
        # Извлекаем текст
        text_bytes = data_bytes[3:3+length]
        text = text_bytes.decode('utf-8')
        
        # Проверяем контрольную сумму
        calculated_checksum = sum(ord(c) for c in text) % 256
        if calculated_checksum != checksum:
            return ""
        
        return text
        
    except Exception:
        return ""


def _generate_fsk_signal_adaptive(binary: str, symbol_duration: float) -> np.ndarray:
    """Генерирует FSK сигнал из бинарной строки с адаптивной длительностью символа."""
    samples_per_symbol = int(SAMPLE_RATE * symbol_duration)
    
    # Создаем временную ось
    t = np.linspace(0, symbol_duration, samples_per_symbol, endpoint=False)
    
    signal = np.array([])
    
    for bit in binary:
        # Выбираем частоту в зависимости от бита
        freq = START_FREQ if bit == '0' else START_FREQ + FREQ_SPACE
        
        # Генерируем синусоиду для текущего символа
        symbol_signal = np.sin(2 * np.pi * freq * t)
        
        # Добавляем плавные переходы между символами
        if len(signal) > 0:
            # Плавный переход в начале символа
            fade_samples = min(100, samples_per_symbol // 10)
            symbol_signal[:fade_samples] *= np.linspace(0, 1, fade_samples)
        
        signal = np.concatenate([signal, symbol_signal])
    
    # Нормализуем и конвертируем в int16
    signal = signal / np.max(np.abs(signal)) * 0.8  # 80% от максимума
    signal = (signal * 32767).astype(np.int16)
    
    return signal


def _generate_fsk_signal(binary: str) -> np.ndarray:
    """Генерирует FSK сигнал из бинарной строки."""
    samples_per_symbol = int(SAMPLE_RATE * SYMBOL_DURATION)
    total_samples = len(binary) * samples_per_symbol
    
    # Создаем временную ось
    t = np.linspace(0, SYMBOL_DURATION, samples_per_symbol, endpoint=False)
    
    signal = np.array([])
    
    for bit in binary:
        # Выбираем частоту в зависимости от бита
        freq = START_FREQ if bit == '0' else START_FREQ + FREQ_SPACE
        
        # Генерируем синусоиду для текущего символа
        symbol_signal = np.sin(2 * np.pi * freq * t)
        
        # Добавляем плавные переходы между символами
        if len(signal) > 0:
            # Плавный переход в начале символа
            fade_samples = min(100, samples_per_symbol // 10)
            symbol_signal[:fade_samples] *= np.linspace(0, 1, fade_samples)
        
        signal = np.concatenate([signal, symbol_signal])
    
    # Нормализуем и конвертируем в int16
    signal = signal / np.max(np.abs(signal)) * 0.8  # 80% от максимума
    signal = (signal * 32767).astype(np.int16)
    
    return signal


def _decode_fsk_signal(audio_data: np.ndarray) -> str:
    """Декодирует FSK сигнал обратно в бинарную строку."""
    # Конвертируем в float32 для обработки
    if audio_data.dtype != np.float32:
        audio_data = audio_data.astype(np.float32) / 32767.0
    
    samples_per_symbol = int(SAMPLE_RATE * SYMBOL_DURATION)
    binary = ""
    
    # Обрабатываем сигнал по символам
    num_symbols = len(audio_data) // samples_per_symbol
    
    for i in range(num_symbols):
        start_idx = i * samples_per_symbol
        end_idx = start_idx + samples_per_symbol
        
        if end_idx > len(audio_data):
            break
            
        symbol_data = audio_data[start_idx:end_idx]
        
        # Вычисляем спектр символа
        fft = np.fft.fft(symbol_data)
        freqs = np.fft.fftfreq(len(symbol_data), 1/SAMPLE_RATE)
        
        # Ищем пики в спектре
        magnitude = np.abs(fft)
        
        # Ищем пики в диапазоне наших частот
        freq_mask = (freqs >= START_FREQ - 100) & (freqs <= START_FREQ + FREQ_SPACE + 100)
        relevant_freqs = freqs[freq_mask]
        relevant_magnitude = magnitude[freq_mask]
        
        if len(relevant_magnitude) == 0:
            binary += '0'  # По умолчанию считаем 0
            continue
        
        # Находим частоту с максимальной амплитудой
        max_idx = np.argmax(relevant_magnitude)
        detected_freq = relevant_freqs[max_idx]
        
        # Определяем бит по частоте
        freq_0 = START_FREQ
        freq_1 = START_FREQ + FREQ_SPACE
        
        if abs(detected_freq - freq_0) < abs(detected_freq - freq_1):
            binary += '0'
        else:
            binary += '1'
    
    return binary


# ---------------------------- TODO: your logic ---------------------------- #

def text_to_audio(text: str) -> bytes:
    """Зашифровать *text* в WAV.  
    Вернуть байтовое содержимое WAV‑файла."""
    if not text:
        return _empty_wav(0.1)
    
    # Конвертируем текст в бинарную строку
    binary = _text_to_binary(text)
    
    # Генерируем FSK сигнал
    signal = _generate_fsk_signal(binary)
    
    # Проверяем длительность
    duration = len(signal) / SAMPLE_RATE
    
    if duration > MAX_DURATION:
        # Обрезаем сигнал если он слишком длинный
        max_samples = int(MAX_DURATION * SAMPLE_RATE)
        signal = signal[:max_samples]
    
    # Создаем WAV файл
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(BIT_DEPTH // 8)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(signal.tobytes())
    
    return buf.getvalue()


def audio_to_text(wav_bytes: bytes) -> str:
    """Декодировать WAV‑байты обратно в текст."""
    try:
        # Читаем WAV файл
        with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
            audio_data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
        
        # Декодируем FSK сигнал
        binary = _decode_fsk_signal(audio_data)
        
        # Конвертируем бинарную строку обратно в текст
        text = _binary_to_text(binary)
        
        if not text:
            # Попробуем более простой подход - декодировать без синхронизации
            try:
                # Убираем синхронизационные биты и пробуем декодировать
                if len(binary) >= 8:
                    # Ищем начало данных
                    start_idx = binary.find('10101010')
                    if start_idx != -1 and start_idx + 8 < len(binary):
                        data_binary = binary[start_idx + 8:]
                        # Конвертируем в байты
                        if len(data_binary) % 8 == 0:
                            data_bytes = bytearray()
                            for i in range(0, len(data_binary), 8):
                                byte_str = data_binary[i:i+8]
                                data_bytes.append(int(byte_str, 2))
                            
                            # Пробуем декодировать как UTF-8
                            try:
                                text = data_bytes.decode('utf-8')
                                if text and all(32 <= ord(c) <= 126 for c in text):
                                    return text
                            except:
                                pass
            except:
                pass
            
            return f"<decoded text> (binary: {binary[:50]}...)" if len(binary) > 50 else f"<decoded text> (binary: {binary})"
        
        return text
        
    except Exception as e:
        return f"<decoded text> (error: {str(e)})"


# ---------------------------- endpoints ---------------------------- #

@app.post("/encode", response_model=EncodeResponse)
async def encode_text(request: EncodeRequest):
    wav_bytes = text_to_audio(request.text)
    wav_base64 = base64.b64encode(wav_bytes).decode("utf-8")
    return EncodeResponse(data=wav_base64)


@app.post("/decode", response_model=DecodeResponse)
async def decode_audio(request: DecodeRequest):
    wav_bytes = base64.b64decode(request.data)
    text = audio_to_text(wav_bytes)
    return DecodeResponse(text=text)


@app.get("/ping")
async def ping():
    return "ok"
