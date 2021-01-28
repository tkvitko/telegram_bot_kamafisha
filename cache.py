import os
import pathlib
import time

CACHE_TIME = 24 * 60 * 60


# CACHE_TIME = 60


def put_to_cache(data, data_type, date=None, category=None):
    # Фукнция сохранения ответа в кеш

    if not category:
        # news, events
        cache_file = f'cache/{data_type}/{date}'
    else:
        # events with category
        cache_file = f'cache/{data_type}/{category}'

    os.makedirs(f'cache/{data_type}', exist_ok=True)

    with open(cache_file, 'w') as f:
        f.write(data)

    print(f'{data_type} for {date} has been saved to {cache_file}')


def get_from_cache(data_type, date=None, category=None):
    # Функция взятия ответа из кеша с учетом устаревания

    if not category:
        # news, events
        cache_file = f'cache/{data_type}/{date}'
    else:
        # events with category
        cache_file = f'cache/{data_type}/{category}'

    try:
        file_props = pathlib.Path(cache_file)
        # время создания кеша
        creation_time = file_props.stat().st_mtime
        # текущее время
        current_time = time.time()

        # если кеш устарел, данные не возвращаем
        if current_time - creation_time > CACHE_TIME:
            data = None
            print(f'{data_type} for {date} are too old in {cache_file}')
        else:
            os.makedirs(f'cache/{data_type}', exist_ok=True)
            with open(cache_file, 'r') as f:
                data = f.read()
            print(f'{data_type} for {date} has been taken from {cache_file}')

    except FileNotFoundError:
        data = None

    # Если данные не вернули, основной модуль возьмет их из БД и запишет в кеш
    return data


if __name__ == '__main__':
    # Тестирование
    test_data = """Новости:"""

    # put_to_cache(data=test_data,
    #              data_type='events',
    #              date='2020-12-19')

    # print(get_from_cache(data_type='news',
    #                      date='2020-12-19'))
