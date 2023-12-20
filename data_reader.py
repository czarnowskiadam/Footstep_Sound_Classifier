"""Moduł data_reader.py obsługuje odczyt oraz zapis pliku data.json"""

import json


def read(file):
    """Funkcja read() odpowiada za wczytanie pliku data.json

        args:

            file - nazwa pliku z rozszerzeniem .json"""
    try:
        """Dekodowanie pliku w notacji utf-8, by rozpoznawane były polskie znaki"""
        with open(f'{file}', 'r', encoding="utf-8") as f:
            data = json.load(f)
            try:
                """Zwracanie zawartości pliku file"""
                return data
            except OSError:
                """Odczyt pliku jest nie możliwy"""
                return 'Cannot read data!'
    except FileNotFoundError:
        """Podany plik nie istnieje lub nie został znaleziony"""
        return 'File not found!'


def write(file, value):
    """Funckja write() odpowiada za nadpisanie pliku data.json

    args:

        file - nazwa pliku z rozszerzeniem .json
        value - wartość, o którą plik .json zostanie nadpisany"""
    try:
        with open(f'{file}', 'w', encoding="utf-8") as f:
            """Nadpisanie pliku f o wartość value"""
            json.dump(value, f)
    except FileNotFoundError:
        """Podany plik nie istnieje lub nie został znaleziony"""
        return 'File not found!'
