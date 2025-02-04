import os
from kaggle.api.kaggle_api_extended import KaggleApi

api = KaggleApi()
api.authenticate()

download_path = "data/"

dataset_name = "aadyasingh55/cocktails"
api.dataset_download_files(dataset_name, path=download_path, unzip=True)
