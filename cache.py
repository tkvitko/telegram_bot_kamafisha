import os
import pathlib
import time

CACHE_TIME = 24 * 60 * 60   # a day


def put_to_cache(data, data_type, date=None, category=None):
    """Function to save data from answer to file cache"""

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
    """Function to get data from file cache"""

    if not category:
        # news, events
        cache_file = f'cache/{data_type}/{date}'
    else:
        # events with category
        cache_file = f'cache/{data_type}/{category}'

    try:
        file_props = pathlib.Path(cache_file)
        creation_time = file_props.stat().st_mtime  # the time when cache has been created
        current_time = time.time()  # the current time

        if current_time - creation_time > CACHE_TIME:
            # don't return data if cache is out of date
            data = None
            print(f'{data_type} for {date} are too old in {cache_file}')
        else:
            # return data
            os.makedirs(f'cache/{data_type}', exist_ok=True)
            with open(cache_file, 'r') as f:
                data = f.read()
            print(f'{data_type} for {date} has been taken from {cache_file}')

    except FileNotFoundError:
        data = None

    # If no data has been returned from cache, the main module will get it from source and put to the cache
    return data


if __name__ == '__main__':

    # Testing
    test_data = """Новости:"""

    # put_to_cache(data=test_data,
    #              data_type='events',
    #              date='2020-12-19')

    # print(get_from_cache(data_type='news',
    #                      date='2020-12-19'))
