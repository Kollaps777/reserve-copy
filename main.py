import os
import requests
import json
import datetime
from dotenv import load_dotenv
from tqdm import tqdm  # Импортируем прогресс-бар

# Загружаем переменные из .env
load_dotenv()

VK_TOKEN = os.getenv("VK_TOKEN")  # Загружаем токен VK
YANDEX_TOKEN = os.getenv("YANDEX_TOKEN")  # Загружаем токен Яндекс.Диска

# Проверяем, загружены ли токены
if not VK_TOKEN or not YANDEX_TOKEN:
    raise ValueError("Ошибка: Токены VK или Яндекс.Диска не загружены. Проверьте файл .env")

# Запрашиваем id пользователя VK
VK_USER_ID = input("Введите ID пользователя VK: ")

class VK:
    def __init__(self, VK_TOKEN, user_id, version='5.131'):
        self.token = VK_TOKEN
        self.id = user_id
        self.version = version
        self.params = {'access_token': self.token, 'v': self.version}

        if not user_id.isdigit():  # Если ID не число, получаем числовой ID
            self.id = self.get_numeric_id()

    def users_info(self):
        """Получает информацию о пользователе VK"""
        url = 'https://api.vk.com/method/users.get'
        params = {'user_ids': self.id}
        response = requests.get(url, params={**self.params, **params})
        data = response.json()

        if "error" in data:
            raise ValueError(f"Ошибка VK API: {data['error']['error_msg']}")

        return data

    def get_photos(self):
        """Получает фото из профиля VK"""
        url = "https://api.vk.com/method/photos.get"
        params = {
            'owner_id': int(self.id),
            'album_id': 'profile',
            'extended': 1,
            'photo_sizes': 1
        }
        response = requests.get(url, params={**self.params, **params})
        data = response.json()

        photos = []
        for item in data['response']['items']:
            largest_photo_url = self.get_largest_photo_url(item['sizes'])
            photos.append({
                'id': item['id'],
                'url': largest_photo_url,
                'likes': item['likes']['count'],
                'date': item['date']
            })

        # Сохраняем данные в JSON-файл
        with open("photos_info.json", "w", encoding="utf-8") as f:
            json.dump(photos, f, ensure_ascii=False, indent=4)

        print("Файл photos_info.json успешно создан.")

        return photos


    def get_numeric_id(self):
        """Преобразует буквенный ID в числовой"""
        url = "https://api.vk.com/method/users.get"
        params = {'user_ids': self.id}
        response = requests.get(url, params={**self.params, **params})
        data = response.json()

        if 'response' in data:
            return data['response'][0]['id']
        else:
            raise ValueError(f"Ошибка VK API: {data['error']['error_msg']}")

    def get_largest_photo_url(self, sizes):
        """Выбирает фото наибольшего размера"""
        return max(sizes, key=lambda size: size['width'])['url']


class YandexDisk:
    def __init__(self, YANDEX_TOKEN):
        self.token = YANDEX_TOKEN
        self.base_url = "https://cloud-api.yandex.net/v1/disk"

    def create_folder(self, folder_name):
        """Создает папку на Яндекс.Диске"""
        url = f"{self.base_url}/resources"
        headers = {"Authorization": f"OAuth {self.token}"}
        params = {"path": folder_name}
        response = requests.put(url, headers=headers, params=params)

        if response.status_code == 201:
            print(f"Папка '{folder_name}' создана.")
        elif response.status_code == 409:
            print(f"Папка '{folder_name}' уже существует.")
        else:
            print(f"Ошибка при создании папки: {response.json()}")

    def upload_photos(self, photos, folder_name="VK_Photos"):
        """Загружает фото с прогресс-баром"""
        self.create_folder(folder_name)
        headers = {"Authorization": f"OAuth {self.token}"}

        photo_names = {}

        for photo in tqdm(photos, desc="Загрузка фотографий", unit="фото"):
            likes = photo['likes']
            date_uploaded = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

            if likes in photo_names:
                file_name = f"{likes}_{date_uploaded}.jpg"
            else:
                file_name = f"{likes}.jpg"

            photo_names[likes] = file_name

            file_path = f"{folder_name}/{file_name}"
            upload_url = f"{self.base_url}/resources/upload"
            params = {"path": file_path, "url": photo["url"]}
            response = requests.post(upload_url, headers=headers, params=params)

            if response.status_code != 202:
                print(f"Ошибка загрузки {file_name}: {response.json()}")


# Основной код
vk = VK(VK_TOKEN, VK_USER_ID)
photos = vk.get_photos()

yandex = YandexDisk(YANDEX_TOKEN)
yandex.upload_photos(photos)
