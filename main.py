import mysql.connector
import random
import time
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': 'perf_test'
}

TABLE_SIZES = {
    'table_1k': 1000,
    'table_10k': 10000,
    'table_100k': 100000,
}

OPERATIONS = [
    'find_by_pk',
    'find_by_value',
    'find_by_mask',
    'insert_one',
    'insert_many',
    'update_by_pk',
    'update_by_value',
    'delete_by_pk',
    'delete_by_value',
    'delete_many',
    'optimize_after_200_delete',
    'optimize_after_to_200',
]


def connect_db():
    return mysql.connector.connect(**DB_CONFIG)


def setup_database():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("CREATE DATABASE IF NOT EXISTS `{}` CHARACTER SET utf8mb4".format(DB_CONFIG['database']))
    conn.database = DB_CONFIG['database']
    for table, size in TABLE_SIZES.items():
        cur.execute(f"DROP TABLE IF EXISTS `{table}`")
        cur.execute(
            f"""
            CREATE TABLE `{table}` (
                `id` INT AUTO_INCREMENT PRIMARY KEY,
                `value` INT NOT NULL
            ) ENGINE=InnoDB
            """
        )
        # Наполнение случайными данными
        data = [(random.randint(1, 1000000),) for _ in range(size)]
        cur.executemany(f"INSERT INTO `{table}` (value) VALUES (%s)", data)
        conn.commit()
    cur.close()
    conn.close()


def measure_time(func):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        return result, end - start
    return wrapper

# Операции

@measure_time
def find_by_pk(conn, table, pk):
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM `{table}` WHERE id = %s", (pk,))
    row = cur.fetchone()
    cur.close()
    return row

@measure_time
def find_by_value(conn, table, value):
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM `{table}` WHERE value = %s", (value,))
    row = cur.fetchone()
    cur.close()
    return row

@measure_time
def find_by_mask(conn, table, mask):
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM `{table}` WHERE CAST(value AS CHAR) LIKE %s", (mask,))
    rows = cur.fetchall()
    cur.close()
    return rows

@measure_time
def insert_one(conn, table, value):
    cur = conn.cursor()
    cur.execute(f"INSERT INTO `{table}` (value) VALUES (%s)", (value,))
    conn.commit()
    new_id = cur.lastrowid
    cur.close()
    return new_id

@measure_time
def insert_many(conn, table, values):
    cur = conn.cursor()
    cur.executemany(f"INSERT INTO `{table}` (value) VALUES (%s)", [(v,) for v in values])
    conn.commit()
    cur.close()

@measure_time
def update_by_pk(conn, table, pk, new_value):
    cur = conn.cursor()
    cur.execute(f"UPDATE `{table}` SET value = %s WHERE id = %s", (new_value, pk))
    conn.commit()
    cur.close()

@measure_time
def update_by_value(conn, table, old_value, new_value):
    cur = conn.cursor()
    cur.execute(f"UPDATE `{table}` SET value = %s WHERE value = %s", (new_value, old_value))
    conn.commit()
    cur.close()

@measure_time
def delete_by_pk(conn, table, pk):
    cur = conn.cursor()
    cur.execute(f"DELETE FROM `{table}` WHERE id = %s", (pk,))
    conn.commit()
    cur.close()

@measure_time
def delete_by_value(conn, table, value):
    cur = conn.cursor()
    cur.execute(f"DELETE FROM `{table}` WHERE value = %s LIMIT 1", (value,))
    conn.commit()
    cur.close()

@measure_time
def delete_many(conn, table, count):
    cur = conn.cursor()
    cur.execute(f"DELETE FROM `{table}` LIMIT %s", (count,))
    conn.commit()
    cur.close()

@measure_time
def optimize_table(conn, table):
    cur = conn.cursor()
    cur.execute(f"OPTIMIZE TABLE `{table}`")
    res = cur.fetchall()
    cur.close()
    return res


def run_tests():
    setup_database()

    results = []
    conn = connect_db()
    conn.database = DB_CONFIG['database']

    for table, size in TABLE_SIZES.items():
        print(f"\n=== Testing {table} (rows: {size}) ===")

        # 1. Поиск по PK
        pk = random.randint(1, size)
        _, t1 = find_by_pk(conn, table, pk)
        print(f"find_by_pk: {t1:.6f}s")
        
        # 2. Поиск по не PK
        value = random.randint(1, 1000000)
        _, t2 = find_by_value(conn, table, value)
        print(f"find_by_value: {t2:.6f}s")

        # 3. Поиск по маске
        mask = f"%{str(value)[:2]}%"
        _, t3 = find_by_mask(conn, table, mask)
        print(f"find_by_mask: {t3:.6f}s")

        # 4. Добавление записи
        _, t4 = insert_one(conn, table, random.randint(1, 1000000))
        print(f"insert_one: {t4:.6f}s")

        # 5. Добавление группы записей (100)
        bulk_values = [random.randint(1, 1000000) for _ in range(100)]
        _, t5 = insert_many(conn, table, bulk_values)
        print(f"insert_many(100): {t5:.6f}s")

        # 6. Обновление по PK
        _, t6 = update_by_pk(conn, table, pk, random.randint(1, 1000000))
        print(f"update_by_pk: {t6:.6f}s")

        # 7. Обновление по не PK
        old_val = value
        new_val = random.randint(1, 1000000)
        _, t7 = update_by_value(conn, table, old_val, new_val)
        print(f"update_by_value: {t7:.6f}s")

        # 8. Удаление по PK
        _, t8 = delete_by_pk(conn, table, pk)
        print(f"delete_by_pk: {t8:.6f}s")

        # 9. Удаление по не PK
        _, t9 = delete_by_value(conn, table, value)
        print(f"delete_by_value: {t9:.6f}s")

        # 10. Удаление группы (200)
        _, t10 = delete_many(conn, table, 200)
        print(f"delete_many(200): {t10:.6f}s")

        # 11. Сжатие после удаления 200
        _, t11 = optimize_table(conn, table)
        print(f"optimize_after_200_delete: {t11:.6f}s")

        # 12. Сжатие после удаления до 200 оставшихся
        # Сначала удаляем все кроме 200 строк
        remaining = 200
        delete_count = size + 100 - 200  # size + bulk_inserts - remaining
        _, _ = delete_many(conn, table, delete_count)
        _, t12 = optimize_table(conn, table)
        print(f"optimize_after_to_200: {t12:.6f}s")

    conn.close()

if __name__ == '__main__':
    run_tests()