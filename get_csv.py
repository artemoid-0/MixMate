import os
from kaggle.api.kaggle_api_extended import KaggleApi

# Инициализация API
api = KaggleApi()
api.authenticate()

# Задание пути для скачивания
download_path = "data/"  # Укажи путь для сохранения файлов

# Скачивание данных
dataset_name = "aadyasingh55/cocktails"
api.dataset_download_files(dataset_name, path=download_path, unzip=True)