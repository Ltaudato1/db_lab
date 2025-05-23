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
        WHERE so.seller_id = {seller_id} AND p.product_id = {product_id};
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
    months AS (
    SELECT {left_month}   AS month UNION ALL
    SELECT {left_month}+1 AS month UNION ALL
    SELECT {right_month}  AS month
  ),

  revenue AS (
    SELECT
      m.month,
      MONTHNAME(
        DATE_ADD('2000-01-01', INTERVAL m.month - 1 MONTH)
      ) AS month_name,
      COALESCE(SUM(sd.unit_price * sd.quantity), 0) AS rev
    FROM months m
    LEFT JOIN Sales        s  ON MONTH(s.sale_date) = m.month
                              AND YEAR(s.sale_date) = {year}
    LEFT JOIN SaleDetails  sd ON sd.sale_id = s.sale_id
    GROUP BY m.month
  ),

  cost AS (
    SELECT
      m.month,
      MONTHNAME(
        DATE_ADD('2000-01-01', INTERVAL m.month - 1 MONTH)
      ) AS month_name,
      COALESCE(
        SUM(od.quantity * od.unit_price * (1 - od.discount)),
        0
      ) AS cst
    FROM months m
    LEFT JOIN Orders       o  ON MONTH(o.order_date) = m.month
                              AND YEAR(o.order_date) = {year}
    LEFT JOIN OrderDetails od ON od.order_id = o.order_id
    GROUP BY m.month
  ),

  returns_cte AS (
    SELECT
      m.month,
      MONTHNAME(
        DATE_ADD('2000-01-01', INTERVAL m.month - 1 MONTH)
      ) AS month_name,
      COALESCE(
        SUM(
          COALESCE(p.price, 0) * COALESCE(rh.quantity, 0)
        ),
        0
      ) AS returns_amount
    FROM months m
    LEFT JOIN ReturnsHistory rh
      ON MONTH(rh.return_date) = m.month
     AND YEAR(rh.return_date)  = {year}
    LEFT JOIN Products p
      ON p.product_id = rh.product_id
    GROUP BY m.month
  ),

  total AS (
    -- По-месячные данные
    SELECT
      r.month,
      r.month_name,
      r.rev,
      c.cst,
      rt.returns_amount,
      r.rev - c.cst - rt.returns_amount AS income
    FROM revenue     r
    JOIN cost        c  ON c.month = r.month
    JOIN returns_cte rt ON rt.month = r.month

    UNION ALL

    -- Итоговая строка
    SELECT
      13                 AS month,
      'Итог'             AS month_name,
      SUM(r.rev)         AS rev,
      SUM(c.cst)         AS cst,
      SUM(rt.returns_amount)    AS returns_amount,
      SUM(r.rev - c.cst - rt.returns_amount) AS income
    FROM revenue     r
    JOIN cost        c  ON c.month = r.month
    JOIN returns_cte rt ON rt.month = r.month
  )

    SELECT month_name, rev, cst, returns_amount, income
    FROM total
    ORDER BY month;
    """

    cursor.execute(sql)
    headers = ['Месяц', 'Выручка', 'Издержки', 'Возвраты', 'Доход']
    rows = cursor.fetchall()
    table = tabulate(rows, headers, tablefmt='fancy_grid', floatfmt='.2f')
    cursor.close()
    return f"```\n{table}\n```"

def get_financial_report_by_year(connection, year):
    sql = f"""
    WITH
    revenue AS (
        SELECT
        YEAR(s.sale_date) AS yr,
        SUM(sd.unit_price * sd.quantity) AS rev
        FROM Sales s
        JOIN SaleDetails sd ON sd.sale_id = s.sale_id
        WHERE YEAR(s.sale_date) = {year}
        GROUP BY YEAR(s.sale_date)
    ),
    cost AS (
        SELECT
        YEAR(o.order_date) AS yr,
        SUM(od.unit_price * od.quantity * (1-od.discount)) AS cst
        FROM Orders o
        JOIN OrderDetails od ON od.order_id = o.order_id
        WHERE YEAR(o.order_date) = {year}
        GROUP BY YEAR(o.order_date)
    ),
    returns_cte AS (
        SELECT
        YEAR(rh.return_date) AS yr,
        SUM(COALESCE(p.price,0) * COALESCE(rh.quantity,0)) AS returns_amount
        FROM ReturnsHistory rh
        JOIN Products p ON p.product_id = rh.product_id
        WHERE YEAR(rh.return_date) = {year}
        GROUP BY YEAR(rh.return_date)
    ),
    total AS (
        SELECT
        r.rev,
        c.cst,
        rt.returns_amount,
        r.rev - c.cst - rt.returns_amount AS income
        FROM revenue     r
        JOIN cost        c  ON c.yr = r.yr
        JOIN returns_cte rt ON rt.yr = r.yr
    )
    SELECT rev, cst, returns_amount, income
    FROM total;
    """
    cursor = connection.cursor()
    cursor.execute(sql)
    headers = ['Выручка', 'Издержки', 'Возвраты', 'Доход']
    rows = cursor.fetchall()
    table = tabulate(rows, headers, tablefmt='fancy_grid', floatfmt='.2f')
    cursor.close()
    return f"```\n{table}\n```"
    

def add_new_return(connection, sale_id, product_id, quantity):
    cursor = connection.cursor()
    cursor.execute(f"""
        INSERT INTO ReturnsHistory (sale_id, product_id, return_date, quantity)
        VALUES ({sale_id}, {product_id}, CURDATE(), {quantity});
    """)
    connection.commit()
    cursor.close()