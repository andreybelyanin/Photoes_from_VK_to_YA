import requests
from datetime import datetime
import json
from tqdm import tqdm


def main():
    app_id = input('Введите id пользователя VK, чьи фото нужно скопировать\n'
                   '(для примера можно использовать: 552934290): ')
    TOKEN = input('Введите token пользователя VK, чьи фото нужно скопировать\n'
                  '(для примера можно использовать:\n'
                  '958eb5d439726565e9333aa30e50e0f937ee432e927f0dbd541c541887d919a7c56f95c04217915c32008): ')

    token = f'{TOKEN}'

    album_id = choose_album()
    resp = requests.get(
        'https://api.vk.com/method/photos.get',
        params={
            'owner_id': app_id,
            'access_token': token,
            'v': 5.21,
            'album_id': album_id,
            'photo_sizes': 1,
            'extended': 1
        }
    )

    ya_token = input('Введите ваш token Яндекс.Диска: ')
    folder = input('Введите название для новой папки на Яндекс.Диске, куда нужно скопировать фотографии: ')
    data_list = resp.json()['response']['items']
    count = int(input('Сколько фотографий скопировать (если все, то введите 0): '))

    requests.put('https://cloud-api.yandex.net:443/v1/disk/resources',
                 params={
                     'path': folder
                 },
                 headers={
                     'Authorization': ya_token
                 }
            )
    return ya_token, data_list, folder, count


def choose_album():
    while True:
        ALBUM_ID = input('Введите альбом, с которого скопировать фотографии\n'
                     '(p - profile(фото с профиля), w - wall(фото со стены)): ')
        if ALBUM_ID == 'p':
            return 'profile'
        elif ALBUM_ID == 'w':
            return 'wall'
        print('Вы ввели неправильное значение - попробуйте заново')


class CopyPhotosFromVKtoYADisk:
    def __init__(self, ya_token, data_list, folder, count):
        self.ya_token = ya_token
        self.data_list = data_list
        self.folder = folder
        self.count = count
        self.date_link_dict = {}
        self.link_list = []
        self.type_list = []
        self.filename_list = []
        self.json_data = []

    def get_likes_date(self):
        if self.count == 0 or self.count > len(self.data_list):
            times = len(self.data_list)
        else:
            times = self.count
        for item in self.data_list[:times]:
            date = str(datetime.fromtimestamp(item['date']))
            like = item['likes']['user_likes'] + item['likes']['count']
            self.date_link_dict[date] = like
        return self.date_link_dict

    def get_links(self):
        if self.count == 0 or self.count > len(self.data_list):
            times = len(self.data_list)
        else:
            times = self.count
        for item in self.data_list[:times]:
            for dictionary in item['sizes']:
                if dictionary['type'] == 'w':
                    break
            self.link_list.append(dictionary['src'])
            self.type_list.append(dictionary['type'])
        return self.link_list, self.type_list

    def get_filenames(self):
        for date, like in self.date_link_dict.items():
            filename = str(like) + '.jpg'
            new_filename = str(like) + '. ' + date.replace(':', '-') + '.jpg'
            if filename not in self.filename_list:
                self.filename_list.append(filename)
            else:
                self.filename_list.append(new_filename)
        return self.filename_list

    def put_data_to_ya(self):
        for filename, link in tqdm(zip(self.filename_list, self.link_list), total=len(self.filename_list)):
            response_from_link = requests.get(link)
            response = requests.get(
                'https://cloud-api.yandex.net:443/v1/disk/resources/upload',
                params={
                    'path': f'{self.folder}/ {filename}'
                },
                headers={
                     'Authorization': self.ya_token
                 }
            )
            href = response.json()['href']
            requests.put(href, data=response_from_link.content)

    def create_json_dict(self):
        json = dict(zip(self.filename_list, self.type_list))
        self.json_data.append(json)
        return self.json_data

    def create_json_file(self):
        with open("data_file.json", "w") as write_file:
            json.dump(self.json_data, write_file)
        print('Файлы успешно загружены')


ya_token, data_list, folder, count = main()
copy = CopyPhotosFromVKtoYADisk(ya_token, data_list, folder, count)
copy.get_likes_date()
copy.get_links()
copy.get_filenames()
copy.put_data_to_ya()
copy.create_json_dict()
copy.create_json_file()
