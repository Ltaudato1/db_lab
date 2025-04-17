import mysql.connector
from tabulate import tabulate

def get_products_from_warehouse(connection):
    cursor = connection.cursor()
    cursor.execute(""" 
        SELECT
            p.product_id,
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

    headers = ["id", "Тип продукта", "Название", "Цена", "Кол-во", "Ед. изм."]

    table = tabulate(rows, headers, tablefmt="fancy_grid", floatfmt=".2f")
    
    cursor.close()

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
    
    cursor.close()

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
    
    cursor.close()

    return "Текущее количество денег: " + str(round(money[0], 2)) + " руб." + f"\n```\n{table}\n```"


def get_supplier_offers(connection, product_id):
    cursor = connection.cursor()
    cursor.execute(f"""
        SELECT s.seller_id, s.name, p.price, so.discount, so.bulk_min_quantity
        FROM Products p
        JOIN SellerOffers so ON p.product_type_id = so.product_type_id
        JOIN Sellers s ON so.seller_id = s.seller_id
        WHERE p.product_id = {product_id};
    """)
    rows = cursor.fetchall()
    cursor.close()
    return rows

def get_offer(connection, seller_id, product_id):
    cursor = connection.cursor()
    cursor.execute(f"""
        SELECT p.price, so.discount, so.bulk_min_quantity
        FROM SellerOffers AS so INNER JOIN Products AS p ON p.product_type_id = so.product_type_id
        WHERE so.seller_id = {seller_id};
        """)
    offer = cursor.fetchone()
    cursor.close()
    return offer

def get_suppliers_num(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM Sellers;")
    num = cursor.fetchone()
    cursor.close()
    return num[0]

def check_balance(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT balance FROM UserInfo")
    balance = cursor.fetchone()
    cursor.close()
    return balance[0]

def change_balance(connection, money):
    money += check_balance(connection)
    cursor = connection.cursor()
    cursor.execute(f"UPDATE UserInfo SET balance={money}")
    connection.commit()
    cursor.close()

def check_products(connection, product_id):
    cursor = connection.cursor()
    cursor.execute(f"SELECT quantity_in_warehouse FROM Products WHERE product_id = {product_id}")
    quantity = cursor.fetchone()
    cursor.close()
    return quantity[0]

def get_price_of_product(connection, product_id):
    cursor = connection.cursor()
    cursor.execute(f"SELECT price FROM Products WHERE product_id = {product_id}")
    price = cursor.fetchone()
    cursor.close()
    return price[0]

def add_product_to_warehouse(connection, product_id, quantity):
    cursor = connection.cursor()
    quantity += check_products(connection, product_id)
    cursor.execute(f"UPDATE Products SET quantity_in_warehouse = {quantity} WHERE product_id = {product_id}")
    connection.commit()
    cursor.close()

def get_id_of_last_sale(connection):
    cursor = connection.cursor()
    cursor.execute(f"SELECT sale_id FROM Sales ORDER BY sale_id DESC LIMIT 1;")
    id = cursor.fetchone()
    cursor.close()
    if id:
        return id[0]
    else:
        return 0

def get_id_of_last_order(connection):
    cursor = connection.cursor()
    cursor.execute(f"SELECT order_id FROM Orders ORDER BY order_id DESC LIMIT 1;")
    id = cursor.fetchone()
    cursor.close()
    if id:
        return id[0]
    else:
        return 0

def add_new_sale(connection, sale_id):
    cursor = connection.cursor()
    cursor.execute(f"INSERT INTO Sales VALUES ({sale_id}, CURDATE())")
    connection.commit()
    cursor.close()

def add_new_sale_detail(connection, sale_id, product_id, price, quantity):
    cursor = connection.cursor()
    cursor.execute(f"SELECT quantity FROM SaleDetails WHERE sale_id = {sale_id} AND product_id = {product_id};")
    result = cursor.fetchone()
    if result:
        cursor.execute(f"SELECT sale_details_id FROM SaleDetails WHERE sale_id = {sale_id} AND product_id = {product_id}")
        res = cursor.fetchone()
        sale_details_id = res[0]
        quantity += result[0]
        cursor.execute(f"UPDATE SaleDetails SET quantity = {quantity} WHERE sale_details_id = {sale_details_id};")
        cursor.execute(f"UPDATE Returns SET quantity = {quantity} WHERE sale_details_id = {sale_details_id}")
    else:
        cursor.execute(f"INSERT INTO SaleDetails (sale_id, product_id, unit_price, quantity) VALUES ({sale_id}, {product_id}, {price}, {quantity});")
        sale_details_id = cursor.lastrowid
        cursor.execute(f"INSERT INTO Returns (sale_details_id, quantity) VALUES ({sale_details_id}, {quantity});")

    connection.commit()
    cursor.close()

def add_new_order(connection, order_id):
    cursor = connection.cursor()
    cursor.execute(f"INSERT INTO Orders VALUES ({order_id}, CURDATE())")
    connection.commit()
    cursor.close()

def add_new_order_detail(connection, order_id, product_id, price, quantity, discount, seller_id):
    cursor = connection.cursor()
    cursor.execute(f"SELECT quantity FROM OrderDetails WHERE order_id = {order_id} AND product_id = {product_id} AND seller_id = {seller_id};")
    result = cursor.fetchone()
    if result:
        quantity += result[0]
        cursor.execute(f"UPDATE OrderDetails SET quantity = {quantity} WHERE order_id = {order_id} AND product_id = {product_id} AND seller_id = {seller_id}")
    else:
        cursor.execute(f"INSERT INTO OrderDetails (order_id, product_id, unit_price, quantity, discount, seller_id) VALUES ({order_id}, {product_id}, {price}, {quantity}, {discount}, {seller_id});")
    connection.commit()
    cursor.close()

def get_sale_history(connection):
    cursor = connection.cursor()
    cursor.execute("""
        SELECT
            s.sale_id,
            s.sale_date,
            SUM(sd.unit_price * sd.quantity) AS income
        FROM Sales AS s INNER JOIN SaleDetails AS sd ON s.sale_id = sd.sale_id
        GROUP BY s.sale_id;
    """)
    rows = cursor.fetchall()
    if not rows:
        return "Нет продаж"
    
    headers = ['id чека', 'Дата', 'Выручка']
    table = tabulate(rows, headers, tablefmt='fancy_grid', floatfmt='.2f')
    
    cursor.close()
    
    return f"\n```{table}\n```"

def get_sale_details(connection, sale_id):
    cursor = connection.cursor()
    cursor.execute(f"""
        SELECT
            sd.product_id,
            p.product_name,
            sd.quantity,
            CASE WHEN pt.can_be_returned = 1 THEN "да" ELSE "нет" END
        FROM SaleDetails AS sd INNER JOIN Products AS p ON p.product_id = sd.product_id INNER JOIN ProductTypes AS pt ON pt.product_type_id = p.product_type_id
        WHERE sd.sale_id = {sale_id};
        """)
    rows = cursor.fetchall()
    cursor.close()
    return rows

def get_quantity_from_history(connection, sale_details_id):
    cursor = connection.cursor()
    cursor.execute(f"SELECT quantity FROM Returns WHERE sale_details_id = {sale_details_id};")
    quantity = cursor.fetchone()
    cursor.close()
    return quantity[0]

def get_sale_detail_id(connection, sale_id, product_id):
    cursor = connection.cursor()
    cursor.execute(f"SELECT sale_details_id FROM SaleDetails WHERE sale_id = {sale_id} AND product_id = {product_id};")
    id = cursor.fetchone()
    cursor.close()
    return id[0]

def reduce_products_from_returns(connection, sale_id, product_id, quantity_to_remove):
    sale_details_id = get_sale_detail_id(connection, sale_id, product_id)
    quantity = get_quantity_from_history(connection, sale_details_id)
    if not quantity or quantity < quantity_to_remove:
        return False
    new_quantity = quantity - quantity_to_remove
    cursor = connection.cursor()
    cursor.execute(f"UPDATE Returns SET quantity = {new_quantity} WHERE sale_details_id = {sale_details_id};")
    connection.commit()
    cursor.close()
    return True

def can_be_returned(connection, product_id):
    cursor = connection.cursor()
    cursor.execute(f"SELECT can_be_returned FROM Products AS p INNER JOIN ProductTypes AS pt ON p.product_type_id = pt.product_type_id WHERE p.product_id = {product_id};")
    flag = cursor.fetchone()
    cursor.close()
    if flag[0] == 1:
        return True
    else:
        return False
    
def get_financial_report_by_quartal(connection, year, quartal):
    cursor = connection.cursor()
    left_month = (quartal - 1) * 3 + 1
    right_month = quartal * 3
    sql = f"""
    WITH
    revenue AS (
        SELECT 
        MONTHNAME(s.sale_date) AS month,
        SUM(sd.unit_price * r.quantity) AS rev
        FROM Sales     s
        JOIN SaleDetails sd ON s.sale_id = sd.sale_id
        JOIN Returns     r ON r.sale_details_id = sd.sale_details_id
        WHERE YEAR(s.sale_date) = {year}
        AND MONTH(s.sale_date) BETWEEN {left_month} AND {right_month}
        GROUP BY MONTHNAME(s.sale_date)
    ),

    cost AS (
        SELECT
        MONTHNAME(o.order_date) AS month,
        SUM(od.quantity * od.unit_price * (1 - od.discount)) AS cst
        FROM Orders       o
        JOIN OrderDetails od ON o.order_id = od.order_id
        WHERE YEAR(o.order_date) = {year}
        AND MONTH(o.order_date) BETWEEN {left_month} AND {right_month}
        GROUP BY MONTHNAME(o.order_date)
    ),
    
    total AS (
        SELECT revenue.month, rev, cst, rev - cst AS income
        FROM revenue INNER JOIN cost ON revenue.month = cost.month
        UNION ALL
        SELECT
        "Итог", SUM(rev), SUM(cst), SUM(rev - cst)
        FROM revenue INNER JOIN cost ON revenue.month = cost.month
    )


    SELECT * FROM total;
    """

    cursor.execute(sql)
    headers = ['Месяц', 'Выручка', 'Издержки', 'Доход']
    rows = cursor.fetchall()
    table = tabulate(rows, headers, tablefmt='fancy_grid', floatfmt='.2f')
    cursor.close()
    return f"```\n{table}\n```"