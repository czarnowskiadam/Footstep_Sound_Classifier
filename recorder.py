"""Moduł recorder.py odpowiada za funkcjonalność nagrywania dźwięków z rozszerzeniem .wav"""

import pyaudio
import numpy as np
import data_reader as dr
import wave
import matplotlib.pyplot as plt


STARTER = dr.read('data.json')
"""Wczytanie zmiennych z pliku data.json przy użyciu stworzonego modułu data_reader.py"""
COUNTER = STARTER['COUNTER']
"""COUNTER - liczba nagrań"""
FRAMES_PER_BUFFER = STARTER['FRAMES_PER_BUFFER']
"""FRAMES_PER_BUFFER - liczba klatek na bufor podczas nagrywania"""
FORMAT = pyaudio.paInt16
"""FORMAT - format nagrania, 16-bitowy string binarny, 15 bitów przechowywane jako liczba, 1 jako znak specjalny"""
CHANNELS = STARTER['CHANNELS']
"""CHANNELS - liczba kanałów nagrywania"""
RATE = STARTER['RATE']
"""RATE - częstotliwość nagrywania (16k)"""


def start_recording(path):
    """Funkcja start_recording uruchamia się po użyciu przycisku Rozpocznij w zakładce Nagrywanie

        args:

            path - string - ścieżka zapisu pliku"""

    """Inicjalizacja pliku audio oraz otwarcie strumienia transmisji"""
    pa = pyaudio.PyAudio()
    stream = pa.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=FRAMES_PER_BUFFER
    )

    """Ustawienie nagrywania na stałe 8 sekund oraz odczyt nagrania"""
    seconds = STARTER['SECONDS']
    frames = []
    second_tracking = 0
    seconds_counter = STARTER['SECONDS_COUNTER']
    for i in range(0, int(RATE / FRAMES_PER_BUFFER * seconds)):
        data = stream.read(FRAMES_PER_BUFFER)
        frames.append(data)
        second_tracking += 1
        if second_tracking == RATE / FRAMES_PER_BUFFER:
            seconds_counter += 1
            second_tracking = 0

    stream.stop_stream()
    stream.close()
    pa.terminate()

    """Edycja oraz konfiguracja zapisanego pliku z rozszerzeniem .wav"""
    obj = wave.open(path, 'wb')
    obj.setnchannels(CHANNELS)
    obj.setsampwidth(pa.get_sample_size(FORMAT))
    obj.setframerate(RATE)
    obj.writeframes(b''.join(frames))
    obj.close()

    """Przygotowanie zmiennych do stworzenia wykresu fali dźwiękowej od czasu"""
    file = wave.open(path, 'rb')

    sample_freq = file.getframerate()
    frames = file.getnframes()
    signal_wave = file.readframes(-1)

    file.close()

    time = frames / sample_freq

    audio_array = np.frombuffer(signal_wave, dtype=np.int16)

    times = np.linspace(0, time, num=frames)

    """Tworzenie oraz wyświetlenie wykresu nagranego pliku dźwiękowego"""
    plt.figure(figsize=(15, 5))
    plt.plot(times, audio_array)
    plt.ylabel('Signal Wave')
    plt.xlabel('Time (s)')
    plt.xlim(0, time)
    plt.title(f'Record{COUNTER}')
    plt.show()

    """Nadpisanie zmiennych dotyczących nagrania w pliku data.json"""
    STARTER['COUNTER'] += 1
    dr.write('data.json', STARTER)
