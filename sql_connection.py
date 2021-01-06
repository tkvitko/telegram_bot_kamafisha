import configparser

import mysql.connector
import sshtunnel

config = configparser.ConfigParser()
config.read("config.ini")
ssh_username = (config["ssh"]["ssh_username"])
ssh_password = (config["ssh"]["ssh_password"])
ssh_host = (config["ssh"]["ssh_host"])
sql_user = (config["mysql"]["user"])
sql_password = (config["mysql"]["password"])
sql_host = (config["mysql"]["host"])


def get_news_from_db():
    # Получение новостей

    with sshtunnel.SSHTunnelForwarder(
            (ssh_host, 22),
            ssh_username=ssh_username,
            ssh_password=ssh_password,
            remote_bind_address=(sql_host, 3306),
            local_bind_address=('0.0.0.0', 3307)
    ) as tunnel:
        connection = mysql.connector.connect(
            user=sql_user,
            password=sql_password,
            host='0.0.0.0',
            database='p570893_afisha',
            port=3307)

        # Получение всех новостей за дату
        # query = f'''
        # SELECT id, post_title, guid from wp_2_posts where
        # (post_type = 'post') AND
        # (post_date BETWEEN '{date_string} 00:00:00' AND '{date_string} 23:59:59')
        # '''

        # Получение последних 15 новостей
        query = f'''
        SELECT id, post_title, guid from wp_2_posts 
        WHERE post_type = 'post' ORDER BY post_date DESC limit 15
        '''
        cursor = connection.cursor()
        cursor.execute(query)
        data = cursor.fetchall()

        return data


def get_events_from_db_by_category(category_id, date_string, date_limit):
    # Получение событий по конкретной категории

    with sshtunnel.SSHTunnelForwarder(
            (ssh_host, 22),
            ssh_username=ssh_username,
            ssh_password=ssh_password,
            remote_bind_address=(sql_host, 3306),
            local_bind_address=('0.0.0.0', 3307)
    ) as tunnel:
        connection = mysql.connector.connect(
            user=sql_user,
            password=sql_password,
            host='0.0.0.0',
            database='p570893_afisha',
            port=3307)

        query = f'''
        SELECT id, post_title, guid, start_date from
        (
        SELECT t1.id, t1.post_title, t1.guid, t1.meta_value as start_date, t2.meta_value as end_date
        FROM (
        SELECT p.id, p.post_title, p.guid, m.meta_value, m.meta_key from wp_2_posts p
        JOIN wp_2_postmeta m ON p.id = m.post_id
        JOIN wp_2_term_relationships r ON p.ID = r.object_id
        WHERE (post_type='tribe_events') AND
        r.term_taxonomy_id = {category_id} AND
        (post_date >='{date_limit} 00:00:00') AND
        (m.meta_key = '_EventStartDate' OR m.meta_key = '_EventEndDate')
        ) t1
        INNER JOIN (
        SELECT p.id, p.post_title, p.guid, m.meta_value, m.meta_key from wp_2_posts p
        JOIN wp_2_postmeta m ON p.id = m.post_id
        JOIN wp_2_term_relationships r ON p.ID = r.object_id
        WHERE (post_type='tribe_events') AND
        r.term_taxonomy_id = {category_id} AND
        (post_date >='{date_limit} 00:00:00') AND
        (m.meta_key = '_EventStartDate' OR m.meta_key = '_EventEndDate')
        ) t2 ON t2.id = t1.id AND t2.meta_key='_EventEndDate'
        WHERE t1.meta_key='_EventStartDate'
        ) t3
        WHERE 
        t3.end_date >='{date_string} 00:00:00'
        '''
        cursor = connection.cursor()
        cursor.execute(query)
        data = cursor.fetchall()

        return data


def get_events_from_db_by_date(date_string, date_limit):
    # Получение событий за конкретную дату

    with sshtunnel.SSHTunnelForwarder(
            (ssh_host, 22),
            ssh_username=ssh_username,
            ssh_password=ssh_password,
            remote_bind_address=(sql_host, 3306),
            local_bind_address=('0.0.0.0', 3307)
    ) as tunnel:
        connection = mysql.connector.connect(
            user=sql_user,
            password=sql_password,
            host='0.0.0.0',
            database='p570893_afisha',
            port=3307)

        query = f'''
        SELECT id, post_title, guid, start_date from
        (
        SELECT t1.id, t1.post_title, t1.guid, t1.meta_value as start_date, t2.meta_value as end_date
        FROM (
        SELECT p.id, p.post_title, p.guid, m.meta_value, m.meta_key from wp_2_posts p
        JOIN wp_2_postmeta m ON p.id = m.post_id
        WHERE (post_type='tribe_events') AND 
        (post_date >='{date_limit} 00:00:00') AND
        (m.meta_key = '_EventStartDate' OR m.meta_key = '_EventEndDate')
        ) t1
        INNER JOIN (
        SELECT p.id, p.post_title, p.guid, m.meta_value, m.meta_key from wp_2_posts p
        JOIN wp_2_postmeta m ON p.id = m.post_id
        WHERE (post_type='tribe_events') AND 
        (post_date >='{date_limit} 00:00:00') AND
        (m.meta_key = '_EventStartDate' OR m.meta_key = '_EventEndDate')
        ) t2 ON t2.id = t1.id AND t2.meta_key='_EventEndDate'
        WHERE t1.meta_key='_EventStartDate'
        ) t3
        WHERE 
        t3.start_date <='{date_string} 00:00:00' AND
        t3.end_date >='{date_string} 00:00:00'
        '''
        cursor = connection.cursor()
        cursor.execute(query)
        data = cursor.fetchall()

        return data


if __name__ == '__main__':
    # Тестирование
    print(get_news_from_db(date_string='2020-12-18'))
    # print(get_events_from_db_by_category(category_id=26, date_string='2020-12-16', date_limit='2020-07-01'))
    # print(get_events_by_date('2020-12-16'))
