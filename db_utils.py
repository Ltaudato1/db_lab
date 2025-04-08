import mysql.connector
from tabulate import tabulate

def get_products_from_warehouse(connection):
    cursor = connection.cursor()
    cursor.execute(""" 
        SELECT
            pt.type_name,
            p.product_name,
            p.price,
            p.quantity_in_warehouse,
            p.measurement_unit
        FROM Products AS p
        INNER JOIN ProductTypes AS pt ON p.product_type_id = pt.product_type_id;
    """)
    rows = cursor.fetchall()

    if not rows:
        return "Склад пуст."

    headers = ["Тип продукта", "Название", "Цена", "Кол-во", "Ед. изм."]

    table = tabulate(rows, headers, tablefmt="fancy_grid", floatfmt=".2f")

    return f"```\n{table}\n```"

def get_sellers(connection):
    cursor = connection.cursor()
    cursor.execute(""" 
        SELECT
            name,
            contact_number
        FROM Sellers
    """)
    rows = cursor.fetchall()

    if not rows:
        return "Список поставщиков пуст."

    headers = ["Поставщик", "Контактный телефон"]

    table = tabulate(rows, headers, tablefmt="fancy_grid", floatfmt=".2f")

    return f"```\n{table}\n```"

def get_financial_situation(connection):
    cursor = connection.cursor()
    cursor.execute(""" 
        SELECT
            balance
        FROM UserInfo
    """)
    money = cursor.fetchone()
    cursor.execute(""" 
        SELECT
            pt.type_name,
            SUM(p.price * p.quantity_in_warehouse) AS summary_cost
        FROM ProductTypes AS pt INNER JOIN Products AS p ON pt.product_type_id = p.product_type_id
        GROUP BY p.product_type_id;
    """)
    rows = cursor.fetchall()

    headers = ["Тип продукта", "Суммарная стоимость на складе"]

    table = tabulate(rows, headers, tablefmt="fancy_grid", floatfmt=".2f")

    return "Текущее количество денег: " + str(round(money[0], 2)) + " руб." + f"\n```\n{table}\n```"