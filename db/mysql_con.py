import mysql.connector as mysql
from db.tools import load_json


def load_credentials():
    PASS = {'host': '127.0.0.1',
            'user': 'root',
            'password': '',
            'database': None,
            'charset': 'utf8'}
    PASS_json = load_json('mysql_config.json')
    if PASS_json:
        PASS = PASS_json
    return PASS


def connect_to_mysql(**kwargs):
    """Połączenie z bazą mysql a następnie zwrócenie słownika z uchwytem do connection i cursor
       x['con'] - connection
       x['cur'] - cursor
       x['err'] - errors"""
    PASS = load_credentials()
    err = ""
    database = kwargs.get('database')
    if database:
        PASS['database'] = database
    try:
        con = mysql.connect(**PASS)
        cur = con.cursor()
    except Exception as e:
        con = False
        cur = False
        err = e
    return {'con': con, 'cur': cur, 'err': err}


def disconnect_mysql(**kwargs):
    """Zamyka połączenie z bazą mysql
       True jeśli połączenie zostało pomyślnie zamknięte
       False jeśli coś poszło nie tak"""
    con = kwargs.get('con')
    cur = kwargs.get('cur')
    if con and cur:
        cur.close()
        con.close()
        return True
    else:
        return False

