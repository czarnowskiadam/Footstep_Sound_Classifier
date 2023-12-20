"""Moduł rozpoczynający działanie programu. Zainicjowanie aplikacji w głównej pętli programu."""
"""Foldery Sounds i Spectrograms zawierają podfoldery pos, neg, probe, które odpowiadają za przechowywanie 
plików dźwiękowych i obrazów spektrogramów."""
"""pos - podfolder przechowywujący próbki pozytywne, domowników"""
"""neg - podfolder przechowywujący próbki negatywne, nieznajomych"""
"""probe - podfolder przechowywujący nagrania otoczenia"""
"""W folderze Output zapisywane są wykresy opisujące uczenie modelu"""

from ui import App

if __name__ == "__main__":
    app = App()
    app.mainloop()
