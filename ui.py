import os
import os.path
import threading as thr
import time
import tkinter
import tkinter.messagebox
from tkinter import filedialog as fd
from PIL import Image
from pygame import mixer

import customtkinter
from win32api import GetSystemMetrics

import recorder as rec
import audio_classification as ac

"""Określenie motywu aplikacji oraz rozmiaru towrzonego okna. 
   Program automatycznie dobiera rozdzielczość monitora użytkownika."""
customtkinter.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

WIDTH = GetSystemMetrics(0)
HEIGHT = GetSystemMetrics(1)


class App(customtkinter.CTk):
    """Klasa App jest odpowiedzialna za wyświetlanie graficznego interfejsu użytkownika"""
    def __init__(self):
        """Konstruktor głównego okna aplikacji"""
        super().__init__()

        """Konfiguracja okna - ustalenie tytułu, rozmiaru, zakaz zmiany rozmiaru okna"""
        self.title("FootFoot")
        self.geometry(f"{WIDTH}x{HEIGHT - 65}+{-10}+{-10}")
        self.deiconify()
        self.resizable(False, False)

        """Konfiguracja layout'u typu grid o rozmiarze (4x4)"""
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)

        """Poniższy kod tyczy się lewego MENU, gdzie znajdują się podstawowe opcje wyboru/usunięcia pliku, odsłuchania nagrania
           wyświetlania spektrogramów, przycisk pomocy 
           zawierający instrukcję oraz najważniejsze informacje o programie"""
        self.sidebar_frame = customtkinter.CTkFrame(self, width=int(WIDTH * 0.1), corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=7, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(7, weight=1)
        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="ICK Projekt\nAdam Czarnowski\nKrzysztof "
                                                                          "Mikulka",
                                                 font=customtkinter.CTkFont(size=30, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.menu_label = customtkinter.CTkLabel(self.sidebar_frame, text="MENU",
                                                 font=customtkinter.CTkFont(size=20, weight="bold"))
        self.menu_label.grid(row=1, column=0, padx=20, pady=(40, 10))

        self.choose_file_btn = customtkinter.CTkButton(self.sidebar_frame,
                                                       text='Wybierz plik',
                                                       width=int(WIDTH * 0.15),
                                                       height=int(HEIGHT * 0.05),
                                                       font=customtkinter.CTkFont(size=20, weight="bold"),
                                                       command=lambda: self.file_selection(
                                                           path='Sounds', where='sidebar'))
        self.choose_file_btn.grid(row=3, column=0, padx=20, pady=(10, 10))

        self.chosen_file = tkinter.StringVar()
        self.chosen_file.set('-')

        self.chosen_file_label_text = customtkinter.CTkLabel(self.sidebar_frame,
                                                             text='Wybrany plik:',
                                                             font=customtkinter.CTkFont(size=20, weight="bold"),
                                                             anchor="n")
        self.chosen_file_label_text.grid(row=4, column=0, padx=20, pady=15)

        self.chosen_file_label = customtkinter.CTkLabel(self.sidebar_frame,
                                                        textvariable=self.chosen_file,
                                                        font=customtkinter.CTkFont(size=20, weight="bold"),
                                                        anchor="n")
        self.chosen_file_label.grid(row=5, column=0, padx=20, pady=3)

        self.file_buttons_frame = customtkinter.CTkFrame(self.sidebar_frame)
        self.file_buttons_frame.grid(row=6, column=0, padx=20, pady=10)

        self.open_file_button = customtkinter.CTkButton(self.file_buttons_frame,
                                                        text='Nagranie',
                                                        width=int(WIDTH * 0.1),
                                                        height=int(HEIGHT * 0.05),
                                                        font=customtkinter.CTkFont(size=20, weight="bold"),
                                                        command=lambda: self.create_toplevel(
                                                            self.chosen_file_path.get(),
                                                            self.chosen_file.get()))
        self.open_file_button.grid(row=0, column=0)
        self.spectro_file_button = customtkinter.CTkButton(self.file_buttons_frame,
                                                           text='Spektrogram',
                                                           width=int(WIDTH * 0.1),
                                                           height=int(HEIGHT * 0.05),
                                                           font=customtkinter.CTkFont(size=20, weight="bold"),
                                                           command=lambda: self.create_toplevel(
                                                               self.get_spectrogram_path(),
                                                               self.chosen_file.get()))
        self.spectro_file_button.grid(row=0, column=1)

        self.delete_files = customtkinter.CTkButton(self.file_buttons_frame,
                                                    text='Usuń pliki',
                                                    width=int(WIDTH * 0.2),
                                                    height=int(HEIGHT * 0.05),
                                                    font=customtkinter.CTkFont(size=20, weight="bold"),
                                                    command=lambda: self.ask_if_sure(self.chosen_file_path.get(),
                                                                                     self.get_spectrogram_path()))
        self.delete_files.grid(row=1, column=0, columnspan=2)

        self.help_button = customtkinter.CTkButton(self.file_buttons_frame,
                                                   text='POMOC',
                                                   width=int(WIDTH * 0.2),
                                                   height=int(HEIGHT * 0.05),
                                                   font=customtkinter.CTkFont(size=20, weight="bold"),
                                                   fg_color=('#fc0303', '#fc0303'),
                                                   command=self.help_window)
        self.help_button.grid(row=2, column=0, columnspan=2, pady=(20, 0))

        self.appearance_mode_label = customtkinter.CTkLabel(self.sidebar_frame, text="Motyw UI", anchor="s")
        self.appearance_mode_label.grid(row=8, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame,
                                                                       values=["Light", "Dark", "System"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=9, column=0, padx=20, pady=(10, 10))


        """Poniższy kod odpowiada za wyświetlanie panelu wyboru okien podstawowych funkcjonalności"""
        """NAGRYWANIE, PORÓWNANIE, UCZENIE MODELU"""
        self.tabview = customtkinter.CTkTabview(self, width=int(WIDTH * 0.83), height=500)
        self.tabview.grid(row=0, column=1, padx=(20, 0), pady=(20, 0), sticky="nsew")
        self.tabview.add("Nagrywanie")
        self.tabview.add("Porównanie")
        self.tabview.add("Uczenie modelu")
        self.tabview.tab("Nagrywanie").grid_columnconfigure(0, weight=1)  # configure grid of individual tabs

        self.tabview.tab("Porównanie").grid_columnconfigure(0, weight=1)
        self.tabview.tab("Uczenie modelu").grid_columnconfigure(0, weight=1)

        """Inicjalizacja zakładki NAGRYWANIE"""
        self.total_record_number = len(os.listdir('Sounds/pos')) + \
                                   len(os.listdir('Sounds/neg')) + \
                                   len(os.listdir('Sounds/probe'))
        self.rec_num = tkinter.StringVar()
        self.rec_num.set(f'Nagranie #{self.total_record_number}')

        self.recording_num = customtkinter.CTkLabel(self.tabview.tab("Nagrywanie"),
                                                    textvariable=self.rec_num,
                                                    font=customtkinter.CTkFont(size=30, weight='bold'))
        self.recording_num.grid(row=0, column=0, padx=20, pady=(20, 10))

        """Wyświetlanie slidera odpowiadającego za wybór opóźnienia startu nagrywania pliku dźwiękowego,
        przyjmuje wartości od 0 do 10 [s]"""
        self.delay_label = customtkinter.CTkLabel(self.tabview.tab("Nagrywanie"),
                                                  text=f'Opóźnienie startu nagrywania',
                                                  font=customtkinter.CTkFont(size=25, weight='bold'))
        self.delay_label.grid(row=1, column=0, padx=20, pady=(50, 10))
        self.slider_frame = customtkinter.CTkFrame(self.tabview.tab("Nagrywanie"),
                                                   width=int(WIDTH * 0.5))
        self.slider_frame.grid(row=2, column=0, columnspan=3, padx=20, pady=(20, 10))
        self.delay_label2 = customtkinter.CTkLabel(self.slider_frame,
                                                   text=f'0s',
                                                   font=customtkinter.CTkFont(size=25, weight='bold'))
        self.delay_label2.grid(row=0, column=0, padx=20, pady=(20, 10))
        self.delay_slider = customtkinter.CTkSlider(self.slider_frame,
                                                    from_=0,
                                                    to=10,
                                                    number_of_steps=10,
                                                    orientation="horizontal",
                                                    width=int(WIDTH * 0.25),
                                                    height=int(HEIGHT * 0.025))
        self.delay_slider.grid(row=0, column=1, padx=20, pady=(20, 10))
        self.delay_label3 = customtkinter.CTkLabel(self.slider_frame,
                                                   text=f'10s',
                                                   font=customtkinter.CTkFont(size=25, weight='bold'))
        self.delay_label3.grid(row=0, column=2, padx=20, pady=(20, 10))

        """Lista checkbox'owa - wymagany wybór przez użytkownika,
        Domownik - próbki pozytywne
        Nieznajomy - próbki negatywne
        Otoczenie - próbki nagrań wykorzystywane w procesie porównania z modelem"""
        self.checkbox_label = customtkinter.CTkLabel(self.tabview.tab("Nagrywanie"),
                                                     text=f'Typ nagrania',
                                                     font=customtkinter.CTkFont(size=25, weight='bold'))
        self.checkbox_label.grid(row=3, column=0, padx=20, pady=(20, 10))
        self.checkbox_frame = customtkinter.CTkFrame(self.tabview.tab("Nagrywanie"),
                                                     width=int(WIDTH * 0.5))
        self.checkbox_frame.grid(row=4, column=0, padx=20, pady=(20, 10))
        self.checkbox_1 = customtkinter.CTkCheckBox(master=self.checkbox_frame,
                                                    font=customtkinter.CTkFont(size=20, weight="bold"),
                                                    text='Domownik',
                                                    command=lambda: self.secure_one_option(checkbox_id=1))
        self.checkbox_1.grid(row=1, column=0, pady=(20, 10), padx=20, sticky="w")
        self.checkbox_2 = customtkinter.CTkCheckBox(master=self.checkbox_frame,
                                                    font=customtkinter.CTkFont(size=20, weight="bold"),
                                                    text='Nieznajomy',
                                                    command=lambda: self.secure_one_option(checkbox_id=2))
        self.checkbox_2.grid(row=2, column=0, pady=10, padx=20, sticky="w")
        self.checkbox_3 = customtkinter.CTkCheckBox(master=self.checkbox_frame,
                                                    font=customtkinter.CTkFont(size=20, weight="bold"),
                                                    text='Otoczenie',
                                                    command=lambda: self.secure_one_option(checkbox_id=3))
        self.checkbox_3.grid(row=3, column=0, pady=10, padx=20, sticky="w")

        """Wyświetlanie przycisku Rozpocznij nagrywanie, 
        który wykorzystuje funkcje start_recording z modułu recorder.py"""
        self.start_recording = customtkinter.CTkButton(self.tabview.tab("Nagrywanie"),
                                                       text='Rozpocznij nagrywanie',
                                                       width=int(WIDTH * 0.1),
                                                       height=int(HEIGHT * 0.05),
                                                       font=customtkinter.CTkFont(size=20, weight="bold"),
                                                       command=self.start_recording_event)
        self.start_recording.grid(row=5, column=0, padx=20, pady=(50, 10))

        """Wyświetlanie elementu określającego aktualny czas nagrania"""
        self.recording_label = customtkinter.CTkLabel(self.tabview.tab("Nagrywanie"), text=f'Czas nagrywania',
                                                      font=customtkinter.CTkFont(size=25, weight='bold'))
        self.recording_label.grid(row=6, column=0, padx=20, pady=(20, 10))
        self.progress_bar_frame = customtkinter.CTkFrame(self.tabview.tab("Nagrywanie"),
                                                         width=int(WIDTH * 0.5))
        self.progress_bar_frame.grid(row=7, column=0, columnspan=3, padx=20, pady=(20, 10))
        self.recording_time_from = customtkinter.CTkLabel(self.progress_bar_frame,
                                                          text=f'0s',
                                                          font=customtkinter.CTkFont(size=25, weight='bold'))
        self.recording_time_from.grid(row=0, column=0, padx=20, pady=(20, 10))
        self.progress_bar = customtkinter.CTkProgressBar(self.progress_bar_frame,
                                                         width=int(WIDTH * 0.45),
                                                         height=15,
                                                         border_width=0,
                                                         corner_radius=20,
                                                         orientation="horizontal",
                                                         mode="determinate",
                                                         determinate_speed=0.185)
        self.progress_bar.grid(row=0, column=1, padx=20, pady=(20, 10))
        self.recording_time_to = customtkinter.CTkLabel(self.progress_bar_frame,
                                                        text=f'8s',
                                                        font=customtkinter.CTkFont(size=25, weight='bold'))
        self.recording_time_to.grid(row=0, column=2, padx=20, pady=(20, 10))

        """Inicjalizacja zakładki UCZENIE MODELU"""

        """Inicjalizacja licznika epok"""
        self.counter = 1
        self.counter_str = tkinter.StringVar()
        self.counter_str.set('1')

        """Wyświetlanie okna wyboru liczby epok, przez które model będzie się uczył"""
        self.epochs_label = customtkinter.CTkLabel(self.tabview.tab("Uczenie modelu"),
                                                   text='')
        self.epochs_label.grid(row=0, column=0, pady=(20, 10))

        self.epochs_info = customtkinter.CTkLabel(self.epochs_label,
                                                  text='Podaj ilość epok',
                                                  font=customtkinter.CTkFont(size=25, weight="bold"))
        self.epochs_info.grid(row=0, column=0, columnspan=3, pady=(10, 4))

        self.sub_button = customtkinter.CTkButton(self.epochs_label,
                                                  text='-',
                                                  width=int(WIDTH * 0.05),
                                                  height=int(HEIGHT * 0.05),
                                                  font=customtkinter.CTkFont(size=20, weight="bold"),
                                                  command=lambda: self.add_sub_btn(option='sub'))
        self.sub_button.grid(row=1, column=0, padx=10, pady=(10, 4))

        self.epochs_counter = customtkinter.CTkLabel(self.epochs_label,
                                                     font=customtkinter.CTkFont(size=25, weight="bold"),
                                                     textvariable=self.counter_str)
        self.epochs_counter.grid(row=1, column=1, padx=10, pady=(10, 4))

        self.add_button = customtkinter.CTkButton(self.epochs_label,
                                                  text='+',
                                                  width=int(WIDTH * 0.05),
                                                  height=int(HEIGHT * 0.05),
                                                  font=customtkinter.CTkFont(size=25, weight="bold"),
                                                  command=lambda: self.add_sub_btn(option='add'))
        self.add_button.grid(row=1, column=2, padx=10, pady=(10, 4))

        """Wyświetlanie przycisku Rozpocznij, który uruchamie funkcję start_proces z modułu audio_classification.py"""
        self.start_processing_btn = customtkinter.CTkButton(self.tabview.tab("Uczenie modelu"),
                                                            text='Rozpocznij',
                                                            width=int(WIDTH * 0.1),
                                                            height=int(HEIGHT * 0.05),
                                                            font=customtkinter.CTkFont(size=20, weight="bold"),
                                                            command=self.begin_event)
        self.start_processing_btn.grid(row=1, column=0, pady=(10, 4))

        self.data_label = customtkinter.CTkLabel(self.tabview.tab("Uczenie modelu"),
                                                 text='')

        """Wyświetlanie poziomego paska ładowania"""
        self.loading = customtkinter.CTkProgressBar(self.data_label,
                                                    width=250,
                                                    height=25,
                                                    border_width=0,
                                                    corner_radius=25,
                                                    orientation="horizontal",
                                                    mode="determinate",
                                                    determinate_speed=1)
        self.loading.grid(row=0, column=0, padx=20, pady=(10, 4))
        self.data_label.grid(row=2, column=0, pady=(10, 4))

        """Wyświetlanie plików .png z folderu Output"""
        self.validation_accuracy = customtkinter.CTkLabel(self.epochs_label,
                                                          text='Podaj ilość epok',
                                                          font=customtkinter.CTkFont(size=25, weight="bold"))
        self.epochs_info.grid(row=0, column=0, columnspan=3, pady=(10, 4))

        self.image_label = customtkinter.CTkLabel(self.tabview.tab("Uczenie modelu"), text="")
        self.image_label.grid(row=3, column=0, pady=(10, 4))
        self.img_cm = Image.open('Output/confusion_matrix.png')
        self.my_image_cm = customtkinter.CTkImage(light_image=self.img_cm,
                                                  dark_image=self.img_cm,
                                                  size=(int(WIDTH * 0.3), int(HEIGHT * 0.25)))

        self.img_cm_label = customtkinter.CTkLabel(self.image_label, image=self.my_image_cm, text='')
        self.img_cm_label.grid(row=0, column=0, columnspan=3, pady=(10, 4))

        self.img_tva = Image.open('Output/training_validation_accuracy.png')
        self.my_image_tva = customtkinter.CTkImage(light_image=self.img_tva,
                                                   dark_image=self.img_tva,
                                                   size=(int(WIDTH * 0.3), int(HEIGHT * 0.25)))

        self.img_tva_label = customtkinter.CTkLabel(self.image_label, image=self.my_image_tva, text='')
        self.img_tva_label.grid(row=1, column=0, columnspan=3, pady=(10, 4))


        """Wyświetlanie zawartości zakładki PORÓWNANIE"""

        """Poniżej wyświetlanie przycisku, który uaktywnia funkcję odpowiadającą za wybór pliku dźwiękowego"""
        self.choose_probe_btn = customtkinter.CTkButton(self.tabview.tab("Porównanie"),
                                                        text='Wybierz plik',
                                                        width=int(WIDTH * 0.15),
                                                        height=int(HEIGHT * 0.05),
                                                        font=customtkinter.CTkFont(size=20, weight="bold"),
                                                        command=lambda: self.file_selection(
                                                            path='Sounds/probe', where='comp'))
        self.choose_probe_btn.grid(row=0, column=0, padx=20, pady=(10, 10))

        self.chosen_probe = tkinter.StringVar()
        self.chosen_probe.set('-')

        self.chosen_probe_label_text = customtkinter.CTkLabel(self.tabview.tab("Porównanie"),
                                                              text='Wybrany plik:',
                                                              font=customtkinter.CTkFont(size=20, weight="bold"),
                                                              anchor="n")
        self.chosen_probe_label_text.grid(row=1, column=0, padx=20, pady=15)

        self.chosen_probe_label = customtkinter.CTkLabel(self.tabview.tab("Porównanie"),
                                                         textvariable=self.chosen_probe,
                                                         font=customtkinter.CTkFont(size=20, weight="bold"),
                                                         anchor="n")
        self.chosen_probe_label.grid(row=2, column=0, padx=20, pady=3)

        """Wyświetlanie przycisku odpowiedzialnego za rozpoczęcie porównania nagrania z wyuczonym modelem, 
        realizujący funkcję comp_data z modułu audio_classification.py"""
        self.start_comp_btn = customtkinter.CTkButton(self.tabview.tab("Porównanie"),
                                                      text='Rozpocznij',
                                                      width=int(WIDTH * 0.15),
                                                      height=int(HEIGHT * 0.05),
                                                      font=customtkinter.CTkFont(size=20, weight="bold"),
                                                      command=self.start_comparision)
        self.start_comp_btn.grid(row=3, column=0, padx=20, pady=(10, 10))

        """Wyświetlanie poziomego paska ładowania"""
        self.loading_bar = customtkinter.CTkProgressBar(self.tabview.tab("Porównanie"),
                                                        width=250,
                                                        height=25,
                                                        border_width=0,
                                                        corner_radius=25,
                                                        orientation="horizontal",
                                                        mode="determinate",
                                                        determinate_speed=1)
        self.loading_bar.grid(row=4, column=0, padx=20, pady=(10, 10))

        """Inicjacja zmiennych początkowych"""
        self.record_path = ''
        self.chosen_file_path = tkinter.StringVar()
        self.comp_result = tkinter.StringVar()
        self.comp_result.set('BRAK')
        self.appearance_mode_optionemenu.set("Dark")
        self.progress_bar.set(0)
        self.loading.set(0)
        self.loading_bar.set(0)

    def change_appearance_mode_event(self, new_appearance_mode: str):
        """Funkcja change_appearance_mode_event odpowiada za zmianę motywu wyświetlania aplikacji

            args:

                new_appearance_mode - string"""
        customtkinter.set_appearance_mode(new_appearance_mode)

    def check_progress_bar(self):
        """Funkcja check_progress_bar odpowiada za śledzenie wizualnego postępu paska ładowania"""
        while True:
            if self.progress_bar.get() >= 0.92:
                self.progress_bar.stop()
                self.progress_bar.set(0)
                break
            else:
                print(self.progress_bar.get())

    def start_recording_event(self):
        """Funkcja start_recording_event wykorzystuje multithreading, co pozwala na wykonanie funkcji nagrywania oraz
        wizualny postęp paska ładowania"""
        time.sleep(int(self.delay_slider.get()))
        t1 = thr.Thread(target=rec.start_recording, args=[self.record_path])
        t2 = thr.Thread(target=self.check_progress_bar)
        self.progress_bar.start()

        t1.start()
        t2.start()

    def secure_one_option(self, checkbox_id):
        """Funkcja secure_one_option odpowiada za przypisanie odpowiednich ścieżek do zapisu pliku dźwiękowego podczas
        nagrań. Odpowiada checkbox'om Domownik/Nieznajomy/Otoczenie.

            args:

                checkbox_id - int"""

        if checkbox_id == 1:
            self.checkbox_2.deselect()
            self.checkbox_3.deselect()
            temp_path = os.listdir('Sounds/pos')
            self.record_path = f'Sounds/pos/{len(temp_path)}sound.wav'
        elif checkbox_id == 2:
            self.checkbox_1.deselect()
            self.checkbox_3.deselect()
            temp_path = os.listdir('Sounds/neg')
            self.record_path = f'Sounds/neg/{len(temp_path)}sound.wav'
        elif checkbox_id == 3:
            self.checkbox_1.deselect()
            self.checkbox_2.deselect()
            temp_path = os.listdir('Sounds/probe')
            self.record_path = f'Sounds/probe/{len(temp_path)}sound.wav'
        else:
            pass

    def file_selection(self, path, where):
        """Funkcja file_selection odpowiada za wybór plików o odpowiednich rozszerzeniach.

        args:

            path - string - ścieżka do pliku .wav
            where - string - zmienna określająca, w którym oknie nastąpił wybór pliku"""
        filetypes = (
            ('All files', '*.*'),
            ('Sound files', '*.wav'),
            ('Spectrogram files', '*.png')
        )
        filename = fd.askopenfilename(
            title='Open a file',
            initialdir=path,
            filetypes=filetypes)

        self.chosen_file_path.set(filename)
        temp = self.chosen_file_path.get()
        if 'pos' in temp:
            y = os.path.split(temp)
            if where == 'sidebar':
                self.chosen_file.set(y[1])
            elif where == 'comp':
                self.chosen_probe.set(y[1])
        elif 'neg' in temp:
            y = os.path.split(temp)
            if where == 'sidebar':
                self.chosen_file.set(y[1])
            elif where == 'comp':
                self.chosen_probe.set(y[1])
        elif 'probe' in temp:
            y = os.path.split(temp)
            if where == 'sidebar':
                self.chosen_file.set(y[1])
            elif where == 'comp':
                self.chosen_probe.set(y[1])

        self.get_spectrogram_path()

    def get_spectrogram_path(self):
        """Funkcja get_spectrogram_path pobiera ścieżkę wybranego pliku dźwiękowego i zamienia ją na ścieżkę spektrogramu
        odpowiadającego plikowi .wav"""
        if self.chosen_file_path.get() != '-':
            chosen_file_spectro = self.chosen_file_path.get().replace('Sounds', 'Spectrograms')
            chosen_file_spectro = chosen_file_spectro.replace('wav', 'png')
            return chosen_file_spectro

    def create_toplevel(self, path, file):
        """Funkcja create_toplevel odpowiada za wyświetlanie okien nad główną aplikacją.
        Tutaj następuje wybór czy wyświetlony ma zostać plik dźwiękowy do odsłuchu czy spektrogram tego pliku.

        args:

            path - string - ścieżka do pliku dźwiękowego
            file - string - nazwa wybranego pliku dźwiękowego"""
        def close_audio():
            """Funkcja close_audio odpowiada za zamknięcie strumienii audio. WYMAGANE ABY PROGRAM DZIAŁAŁ POPRAWNIE"""
            if file != '-':
                if 'png' in path:
                    img.close()
                    window.destroy()
                elif 'wav' in path:
                    mixer.music.unload()
                    window.destroy()

        if file != '-':
            window = customtkinter.CTkToplevel(self)
            window.protocol('WM_DELETE_WINDOW', close_audio)
            if 'png' in path:
                window.title('Viewer')
                window.geometry(f"{WIDTH}x{HEIGHT - 65}+{-10}+{-10}")
                window.deiconify()
                window.resizable(False, False)
                img = Image.open(path)
                my_image = customtkinter.CTkImage(light_image=img,
                                                  dark_image=img,
                                                  size=(int(WIDTH * 0.9), int(HEIGHT * 0.9)))

                label = customtkinter.CTkLabel(window, image=my_image, text='')
                label.pack(side="top", fill="both", expand=True, padx=40, pady=40)
            elif 'wav' in path:
                window.title('Player')
                window.geometry(f"{1000}x{300}+{100}+{100}")
                window.deiconify()
                window.resizable(False, False)
                mixer.init()
                mixer.music.load(path)
                sound_len = int(mixer.Sound(path).get_length())

                frame = customtkinter.CTkFrame(window)
                frame.pack(side="top", fill="both", expand=True, padx=20, pady=20)
                button_label = customtkinter.CTkLabel(frame,
                                                      text='')
                button_label.pack()

                play_button = customtkinter.CTkButton(button_label,
                                                      text='START',
                                                      width=int(WIDTH * 0.1),
                                                      height=int(HEIGHT * 0.05),
                                                      font=customtkinter.CTkFont(size=20, weight="bold"),
                                                      command=mixer.music.play)
                play_button.configure(state=customtkinter.NORMAL)
                play_button.grid(row=1, column=0, padx=(20, 20), pady=(20, 20))
                pause_button = customtkinter.CTkButton(button_label,
                                                       text='PAUZA',
                                                       width=int(WIDTH * 0.1),
                                                       height=int(HEIGHT * 0.05),
                                                       font=customtkinter.CTkFont(size=20, weight="bold"),
                                                       command=mixer.music.pause)
                pause_button.configure(state=customtkinter.NORMAL)
                pause_button.grid(row=1, column=1, padx=(20, 20), pady=(20, 20))
                pause_button = customtkinter.CTkButton(button_label,
                                                       text='WZNÓW',
                                                       width=int(WIDTH * 0.1),
                                                       height=int(HEIGHT * 0.05),
                                                       font=customtkinter.CTkFont(size=20, weight="bold"),
                                                       command=mixer.music.unpause)
                pause_button.configure(state=customtkinter.NORMAL)
                pause_button.grid(row=1, column=2, padx=(20, 20), pady=(20, 20))
        else:
            pass

    def ask_if_sure(self, sound_path, spectrogram_path):
        """Funkcja ask_if_sure odpowiada za wyświetlanie okna potwierdzenia usunięcia wybranych plików

        args:

            sound_path - string - ścieżka do pliku dźwiękowego
            spectrogram_path - string - ścieżka do pliku spektrogramu"""

        if self.chosen_file.get() != '-':
            window = customtkinter.CTkToplevel(self)
            window.title('Helper')
            window.geometry(f"{500}x{200}+{100}+{100}")
            window.deiconify()
            window.resizable(False, False)

            window_frame = customtkinter.CTkFrame(window)
            window_frame.grid(row=0, column=0, sticky="nsew", padx=(20, 20), pady=(20, 20))

            label = customtkinter.CTkLabel(window_frame,
                                           text='Czy na pewno chcesz usunąć wybrane pliki?',
                                           font=customtkinter.CTkFont(size=20, weight="bold"))
            label.grid(row=0, column=0, padx=(10, 10), pady=(10, 10))

            btn_label = customtkinter.CTkLabel(window_frame)
            btn_label.grid(row=1, column=0, padx=(50, 10), pady=(10, 10))

            pause_button = customtkinter.CTkButton(btn_label,
                                                   text='TAK',
                                                   width=int(WIDTH * 0.1),
                                                   height=int(HEIGHT * 0.05),
                                                   font=customtkinter.CTkFont(size=20, weight="bold"),
                                                   command=lambda: self.delete_wav_png(sound_path,
                                                                                       spectrogram_path,
                                                                                       window))
            pause_button.grid(row=0, column=0, padx=(20, 20), pady=(20, 20))
            pause_button = customtkinter.CTkButton(btn_label,
                                                   text='NIE',
                                                   width=int(WIDTH * 0.1),
                                                   height=int(HEIGHT * 0.05),
                                                   font=customtkinter.CTkFont(size=20, weight="bold"),
                                                   command=lambda: window.destroy())
            pause_button.grid(row=0, column=1, padx=(20, 20), pady=(20, 20))

        else:
            pass

    def delete_wav_png(self, sound_path, spectrogram_path, window):
        """Funkcja delete_wav_png odpowiada za usunięcie wybranych plików dźwiękowych oraz spektrogramu

        args:

            sound_path - string - ścieżka do pliku dźwiękowego
            spectrogram_path - string - ścieżka do pliku spektrogramu
            window - customtkinter.window - pozwala na zamknięcie okna"""
        if os.path.exists(sound_path):
            os.remove(sound_path)
        else:
            pass

        if os.path.exists(spectrogram_path):
            os.remove(spectrogram_path)
        else:
            pass

        self.chosen_file.set('-')
        window.destroy()

    def help_window(self):
        """Funkcja help_window wyświetla pomoc/instrukcję obsługi oraz ważne informacje dotyczące użytkowania
        programu """
        window = customtkinter.CTkToplevel(self)
        window.title('Help')
        window.geometry(f"{WIDTH}x{HEIGHT - 65}+{-10}+{-10}")
        window.deiconify()
        window.resizable(False, False)


        text = customtkinter.CTkTextbox(window,
                                        font=customtkinter.CTkFont(size=20, weight="bold"),
                                        border_width=0,
                                        corner_radius=10,
                                        text_color="white",
                                        width=int(WIDTH * 0.9),
                                        height=int(HEIGHT - 100),
                                        padx=20,
                                        pady=5)
        text.grid(row=0, column=0, sticky="nsew", padx=80, pady=(20, 20))
        text.insert("0.0", "!!!!! WAŻNE INFORMACJE !!!!!\n"
                           "Utworzony model został stworzony jako projekt pokazowy!\n"
                           "Model uczony na krokach Adama, Krzysztofa oraz osób trzecich!\n"
                           "NIE URUCHAMIAĆ UCZENIA MODELU, przetworzenie dużej ilości"
                           " plików audio .wav i uczenie modelu zajmuje dużo czasu!\n"
                           "Podczas nagrywania otoczenia w warunkach pokazowych wynik "
                           "powinien być równy Domownik: 0% Obcy: 100%\n"
                           "Podczas wyboru pliku, przemieszczenie odbywa się między trzema folderami:\n"
                           "pos - jest folderem nagrań pozytywnych (Domownika)(służy do szkolenia modelu)\n"
                           "neg - jest folderem nagrań negatywnych (Obcego)(służy do szkolenia modelu)\n"
                           "probe - folder neutralny, do którego użytkownik zapisuje nagrania (Otoczenie)"
                           "(służy do porównania) \n\n\n"
                           "OPIS PROGRAMU\n"
                           "Lewa strona aplikacji opisana słowem MENU "
                           "służy do obługi już powstałych plików - nagrania oraz ich spektrogramy.\n\n"
                           "Przycisk Wybierz plik pozwala na załadowanie nagrania oraz "
                           "odpowiadającemu spektrogram.\n"
                           "Następnie po użyciu przycisku wyświetli się nazwa wybranego pliku poniżej przycisku\n"
                           "Aby odsłuchać wybrany plik należy wcisnąć przycisk Nagranie, wyświetlone "
                           "zostanie okno odtwarzacza.\n"
                           "Aby wyświetlić obraz spektrogramu należy użyć przycisku Spektrogram, "
                           "który otworzy wybrany obraz.\n"
                           "Po użyciu przyciusku Usuń pliki, zostanie usunięty plik nagrania jak i spektrogram.\n"
                           "Przycisk Pomoc otwiera okno, w którym Drogi Użytkowniku właśnie się znajdujesz.\n"
                           "W lewym dolnym rogu aplikacji znajduje się wybór koloru motywu w jakim aplikajca"
                           "jest wyświetlana.\n\n\n"
                           "Prawa strona aplikacji zawiera zakładki, dzięki którym w łatwy sposób "
                           "można wybierać funkcje, które oferuje program.\n\n"
                           "Po wybraniu zakładki Nagrywanie wyświetlona zostaje całkowita ilość dostępnych nagrań.\n"
                           "Poniżej znajduje się przesuwak opóźnienia, dzięki któremu można ustalić czas opóźnienia"
                           " nagrywania od 0 do 10 sekund.\n"
                           "Opcja typ nagrania musi zostać zaznaczona, by podczas nagrywania zapisywać ścieżki "
                           "dźwiękowe w odpowiednich lokalizacjach.\n"
                           "Legenda:\n"
                           "Domownik - nagrania poprawne, pozytywne, domowników\n"
                           "Nieznajomy - nagrania negatywne, obcych, ludzi spoza domu\n"
                           "Otoczenie - dźwięki nasłuchiwania, otoczenia, często ciszy\n\n"
                           "Przycisk Rozpocznij nagrywanie pozwala na rozpoczęcie nagrania z odpowiednio dobranym\n"
                           "czasem opóźnienia oraz odpowiedniej lokalizacji.\n\n"
                           "W zakładce Porównanie wybieramy plik, który jest naszym najnowszym nagraniem. "
                           "W warunkach laboratoryjnych\nnajlepszym rozwiązaniem jest nagranie "
                           "nowego dźwięku z typem nagrania OTOCZENIE w zakładce Nagrywanie.\n"
                           "Po wykonaniu powyższych czynności i użyciu przycisku Rozpocznij poniżej "
                           "wyświetli się okienko z dwiema klasami: Domownik oraz Obcy wraz z wartościami procentowymi "
                           "z zakresu od 0 do 100%. Procent określa zgodność, przynależność nagrania do klasy. "
                           "Jeżeli nagranie \nnie jest nagraniem Domownika, przy "
                           "klasie Obcy powinna znajdować się wartość bliska 100%.\n\n"
                           "Zakładka Uczenie modelu służy do trenowania modelu, za pomocą którego, "
                           "będziemy rozpoznawać dźwięki otoczenia.\n"
                           "Ważnym elementem jest określenie ilości epok, przez które będzie się model szkolił.\n"
                    )
        text.configure(state=customtkinter.DISABLED)

    def begin_event(self):
        """Funkcja begin_event wykorzystuje multithreading, dzięki czemu wykonuje symultanicznie funkcję uczenia modelu
        oraz obsługi paska ładowania"""

        self.start_processing_btn.configure(state=customtkinter.DISABLED)
        self.add_button.configure(state=customtkinter.DISABLED)
        self.sub_button.configure(state=customtkinter.DISABLED)

        t1 = thr.Thread(target=ac.start_proces, args=[self.counter])
        t2 = thr.Thread(target=self.is_thread_alive, args=[t1])

        t1.start()
        t2.start()

    def is_thread_alive(self, thread):
        """Funkcja is_thread_alive sprawdza czy wątek jeszcze żyje, jeżeli nie następuje obsługa paska ładowania

            args:

                thread - thread - wątek, który podlega sprawdzeniu"""
        self.loading.start()
        while True:
            if thread.is_alive():
                pass
            else:
                self.loading.stop()
                self.loading.set(0)
                break

    def add_sub_btn(self, option):
        """Funkcja add_sub_btn odpowiada za logikę związaną z przyciskami inkrementacji i dekrementacji

            args:

                option - string - określa czy przycisk dodaje czy odejmuje wartość"""
        if option == 'add':
            if self.counter < 20:
                self.counter += 1
                self.counter_str.set(str(self.counter))
            else:
                pass
        elif option == 'sub':
            if self.counter > 1:
                self.counter -= 1
                self.counter_str.set(str(self.counter))
            else:
                pass

    def is_possible(self):
        """Funkcja is_possible sprawdza czy może się odbyć proces porównania
            pliku nagraniowego otoczenia z wyuczonym modelem oraz odpowiada za porównanie pliku
            nagraniowego otoczenia z wyuczonym modelem
            Wyświetla również wynik porównania"""
        if self.chosen_file_path.get() != '-' and self.chosen_file_path.get() != '':
            result_string = ac.comp_data(self.chosen_file_path.get(),
                                         self.get_spectrogram_path())
            self.comp_result.set(result_string)
            result_label = tkinter.Label(self.tabview.tab("Porównanie"),
                                         textvariable=self.comp_result,
                                         font=customtkinter.CTkFont(size=20, weight="bold"),
                                         anchor="n")
            result_label.grid(row=5, column=0, padx=20, pady=3)
            self.loading_bar.stop()
            self.loading_bar.set(0)

        else:
            pass

    def start_comparision(self):
        """Funkcja start_comparision wykorzystuje multithreading w celu uruchomienia funkcji porównania wyników oraz
        wyświetlania paska ładowania"""
        t1 = thr.Thread(target=self.is_possible)
        t2 = thr.Thread(target=self.loading_bar.start)

        t1.start()
        t2.start()
