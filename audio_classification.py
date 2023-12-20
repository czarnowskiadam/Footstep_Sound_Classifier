import librosa
from librosa import display
import matplotlib.pyplot as plt
import numpy as np
import os

import keras.utils as ku
import sklearn.model_selection as ms

from keras.models import Sequential
from keras.layers import Flatten, Dense

from keras.applications import MobileNetV2
from keras.applications.mobilenet import preprocess_input
from keras.models import save_model, load_model

from sklearn.metrics import confusion_matrix
import seaborn as sns

import warnings

warnings.filterwarnings("ignore")


def create_spectrogram(audio_file, image_file):
    """Funkcja create_spectrogram wykorzystuje bibliotekę matplotlib do stworzenia spektrogramu

       args:

            audio_file - plik dźwiękowy (nagranie) z rozszerzeniem .wav
            image_file - plik zawierający widmo nagrania (audio_file) z rozszerzeniem .png"""
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)

    y, sr = librosa.load(audio_file)
    ms = librosa.feature.melspectrogram(y=y, sr=sr)
    log_ms = librosa.power_to_db(ms, ref=np.max)
    librosa.display.specshow(log_ms, sr=sr)

    fig.savefig(image_file)
    plt.close(fig)


def create_pngs_from_wavs(input_path, output_path):
    """Funkcja create_pngs_from_wavs przetwarza pliki dźwiękowe (.wav) na widmo pliku dźwiękowego (.png)

       args:

            input_path - ścieżka do pliku dźwiękowego, z którego będzie tworzone widmo
            output_path - ścieżka, do której utworzony plik widma zostanie zapisany"""

    if not os.path.exists(output_path):
        """Sprawdzenie czy ścieżka wyjściowa istnieje"""
        os.makedirs(output_path)

    dir = os.listdir(input_path)

    for i, file in enumerate(dir):
        """Wykonanie dla każdego pliku w folderze"""
        input_file = os.path.join(input_path, file)
        output_file = os.path.join(output_path, file.replace('.wav', '.png'))
        create_spectrogram(input_file, output_file)
        print(f'File {i + 1}/{len(dir)}')


def load_images_from_path(path, label):
    """Funkcja load_images_from_path jest funkcją wspomagającą, mającaą na celu wczytanie obrazu z podanej ścieżki

       args:

            path - ścieżka, z której następuje wczytanie obrazu
            label - 0 bądź 1, oznaczenie plików nagraniowych,
                    gdzie 0 oznacza próbki negatywne, a 1 oznacza próbki pozytywne"""
    images = []
    labels = []

    for file in os.listdir(path):
        images.append(ku.img_to_array(ku.load_img(os.path.join(path, file), target_size=(224, 224, 3))))
        labels.append(label)

    return images, labels


def show_images(images):
    """Funkcja show_images pozwala na wyświetlenie obrazu spektrogramu modelowi podczas uczenia

       args:

            images - zbiór obrazów spektrogramów potrzebnych do uczenia modelu"""
    fig, axes = plt.subplots(1, 8, figsize=(20, 20), subplot_kw={'xticks': [], 'yticks': []})

    for i, ax in enumerate(axes.flat):
        ax.imshow(images[i] / 255)

    plt.close()


def start_proces(epochs):
    """Wywołanie funkcji start_proces powoduje rozpoczęcie uczenia modelu CNN.
       W tej funkcji odbywa się przygotowanie danych (preprocessing) wykorzystywanych w uczeniu maszynowym

       args:

            epochs - liczba epok, przez którą model będzie się uczył"""
    create_pngs_from_wavs('Sounds/pos', 'Spectrograms/pos')
    create_pngs_from_wavs('Sounds/neg', 'Spectrograms/neg')

    img_list = []
    lbl_list = []

    images, labels = load_images_from_path('Spectrograms/pos', 0)
    show_images(images)

    img_list += images
    lbl_list += labels

    images, labels = load_images_from_path('Spectrograms/neg', 1)
    show_images(images)

    img_list += images
    lbl_list += labels

    img_train, img_test, lbl_train, lbl_test = ms.train_test_split(img_list, lbl_list,
                                                                   stratify=lbl_list,
                                                                   test_size=0.3,
                                                                   random_state=0)

    base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(224, 224, 3))

    x_train_norm = preprocess_input(np.array(img_train))
    x_test_norm = preprocess_input(np.array(img_test))

    y_train_encoded = ku.to_categorical(lbl_train)
    y_test_encoded = ku.to_categorical(lbl_test)

    train_features = base_model.predict(x_train_norm)
    test_features = base_model.predict(x_test_norm)

    model = Sequential()
    model.add(Flatten(input_shape=train_features.shape[1:]))
    model.add(Dense(1024, activation='relu'))
    model.add(Dense(2, activation='softmax'))
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

    hist = model.fit(train_features, y_train_encoded, validation_data=(test_features, y_test_encoded), batch_size=10,
                     epochs=epochs)

    acc = hist.history['accuracy']
    val_acc = hist.history['val_accuracy']
    epochs = range(1, len(acc) + 1)

    plt.plot(epochs, acc, '-', label='Training Accuracy')
    plt.plot(epochs, val_acc, ':', label='Validation Accuracy')
    plt.title('Training and Validation Accuracy')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.legend(loc='lower right')
    plt.savefig(f'Output/training_validation_accuracy.png')
    plt.close()

    sns.set()

    y_predicted = model.predict(test_features)
    mat = confusion_matrix(y_test_encoded.argmax(axis=1), y_predicted.argmax(axis=1))
    class_labels = ['Owner', 'Stranger']

    sns.heatmap(mat, square=True, annot=True, fmt='d', cbar=False, cmap='Blues',
                xticklabels=class_labels,
                yticklabels=class_labels)

    plt.xlabel('Predicted label')
    plt.ylabel('Actual label')
    plt.savefig(f'Output/confusion_matrix.png')
    plt.close()

    base_model.save("base_model.h5")
    model.save("model.h5")


def comp_data(sound_path, spectro_path):
    """Funkcja comp_data odpowiada za porównanie nagranej próbki z wyszkolonym już modelem

       args:

            sound_path - ścieżka do pliku nagrania, które będzie porównywane z modelem
            spectro_path - ścieżka do spektrogramu nagrania"""
    subs = ''
    class_labels = ['Owner', 'Stranger']
    base_model = load_model("base_model.h5")
    model = load_model("model.h5")
    create_spectrogram(f'{sound_path}', f'{spectro_path}')

    x = ku.load_img(f'{spectro_path}', target_size=(224, 224))
    x = ku.img_to_array(x)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)

    y = base_model.predict(x)
    predictions = model.predict(y)

    for i, label in enumerate(class_labels):
        if label == 'Owner':
            temp = int(float(predictions[0][i]) * 100)
            subs = 'Domownik: ' + str(temp) + '%\n'
        else:
            temp = int(float(predictions[0][i]) * 100)
            subs += 'Obcy: ' + str(temp) + '%'

    print(subs)
    return subs


if __name__ == '__main__':
    start_proces(3)
