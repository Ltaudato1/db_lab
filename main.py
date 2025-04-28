import os
from dotenv import load_dotenv
import telebot
from telebot import types
import mysql.connector
from mysql.connector import Error
from tabulate import tabulate

import db_utils
import ui

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

try:
    connection = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )
    if connection.is_connected():
        print("Подключение к базе данных успешно установлено")
except Error as e:
    print(f"Ошибка подключения: {e}")

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT 'Подключение к базе данных успешно' AS status;")
        result = cursor.fetchone()
        bot.send_message(chat_id, f"Добро пожаловать! {result[0]}")
    else:
        bot.send_message(chat_id, "Не удалось подключиться к базе данных")
    bot.send_message(chat_id, "Выберите действие:", reply_markup=ui.main_menu())

@bot.message_handler(commands=['reset'])
def reset_database(message):
    cursor = connection.cursor()

    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

    tables = ["SaleDetails", "Sales"]
    for table in tables:
        cursor.execute(f"DELETE FROM {table};")

    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")


    cursor.execute("UPDATE UserInfo SET balance = 30000")

    connection.commit()

    cursor.close()

def purchase_product(message, order_id = db_utils.get_id_of_last_order(connection) + 1):
    chat_id = message.chat.id
    bot.send_message(chat_id, db_utils.get_products_from_warehouse(connection), parse_mode='Markdown')
    bot.send_message(chat_id, "Введите id товара который вы хотите купить", reply_markup=ui.back_menu())
    bot.register_next_step_handler(message, process_product_choice, order_id)

def process_product_choice(message, order_id):
    chat_id = message.chat.id
    if message.text.strip().lower() == 'назад':
        bot.send_message(chat_id, "Возврат в главное меню", reply_markup=ui.main_menu())
        return
    product_id = message.text.strip().lower()
    offers = db_utils.get_supplier_offers(connection, product_id)
    headers = ['id', 'Название', 'Цена', 'Скидка за опт', 'Кол-во для опта']
    table = tabulate(offers, headers, tablefmt='fancy_grid', floatfmt=".2f")
    
    if not offers:
        bot.send_message(chat_id, "Такого товара нет")
        purchase_product(message)

    bot.send_message(chat_id, f"```\n{table}\n```", parse_mode='Markdown')
    bot.send_message(chat_id, "Введите id продавца и количество товара через пробел", reply_markup=ui.back_menu())
    bot.register_next_step_handler(message, init_purchase, product_id, order_id)

def init_purchase(message, product_id, order_id):
    chat_id = message.chat.id
    if message.text.strip().lower() == 'назад':
        bot.send_message(chat_id, "Возврат в главное меню", reply_markup=ui.main_menu())
        return

    try:
        parts = message.text.strip().split()
        supplier_choice = int(parts[0])
        qty = int(parts[1])
    except (IndexError, ValueError):
        bot.send_message(chat_id, "Неверный формат. Пожалуйста, введите данные в формате: номер поставщика и количество (например, `1 20`).")
        message.text = str(product_id)
        process_product_choice(message)
        return
    
    if supplier_choice <= 0 or supplier_choice > db_utils.get_suppliers_num(connection):
        bot.send_message(chat_id, "Выбран неверный номер поставщика.")
        purchase_product(message)
        return

    print(db_utils.get_offer(connection, supplier_choice, product_id))
    base_price, discount, bulk_min_quantity = db_utils.get_offer(connection, supplier_choice, product_id)

    if qty >= bulk_min_quantity:
        final_unit_price = base_price * (1 - discount)
    else:
        discount = 0
        final_unit_price = base_price
    total_price = final_unit_price * qty

    if total_price > db_utils.check_balance(connection):
        bot.send_message(chat_id, "Недостаточно средств!")
        purchase_product(message)
        return

    db_utils.change_balance(connection, -total_price)
    db_utils.add_product_to_warehouse(connection, product_id, qty)
    try:
        db_utils.add_new_order_detail(connection, order_id, product_id, base_price, qty, discount, supplier_choice)
    except Error:
        db_utils.add_new_order(connection, order_id)
        db_utils.add_new_order_detail(connection, order_id, product_id, base_price, qty, discount, supplier_choice)
     
    bot.send_message(chat_id, "Товары успешно заказаны! Продолжить заказ?", reply_markup=ui.choice_menu())
    bot.register_next_step_handler(message, process_next_step_for_ordering, order_id)


def process_next_step_for_ordering(message, order_id):
    chat_id = message.chat.id
    answer = message.text.strip().lower()
    if answer == 'да':
        purchase_product(message, order_id)
    else:
        bot.send_message(chat_id, "Спасибо за покупку, хорошего дня!", reply_markup=ui.main_menu())

def sell_product(message, sale_id = db_utils.get_id_of_last_sale(connection) + 1):
    chat_id = message.chat.id
    bot.send_message(chat_id, db_utils.get_products_from_warehouse(connection), parse_mode='Markdown')
    bot.send_message(chat_id, "Введите id товара который хотят купить и количество через пробел (пример: 1 2)", reply_markup=ui.back_menu())
    bot.register_next_step_handler(message, process_product_choice_for_sale, sale_id)

def order_missing_products(product_id, quantity):
    offers = db_utils.get_supplier_offers(connection, product_id)
    base_price = db_utils.get_price_of_product(connection, product_id)
    min_cost = base_price * quantity
    seller_id = offers[0][0]
    for row in offers:
        id, name, price, discount, bulk_min_quantity = row
        if quantity >= bulk_min_quantity:
            price *= (1 - discount)
        if quantity * price < min_cost:
            min_cost = quantity * price
            seller_id = id
    order_id = db_utils.get_id_of_last_order(connection) + 1
    
    db_utils.add_new_order(connection, order_id)
    db_utils.add_new_order_detail(connection, order_id, product_id, base_price, quantity, discount, seller_id)
    db_utils.change_balance(connection, -min_cost)
    db_utils.add_product_to_warehouse(connection, product_id, quantity)
    return True

def process_product_choice_for_sale(message, sale_id):
    chat_id = message.chat.id

    if message.text.strip().lower() == 'назад':
        bot.send_message(chat_id, "Возврат в главное меню", reply_markup=ui.main_menu())
        return
    try:
        parts = message.text.strip().split()
        buyer_choice = int(parts[0])
        qty = int(parts[1])
    except (IndexError, ValueError):
        bot.send_message(chat_id, "Неверный формат. Пожалуйста, введите данные в формате: номер поставщика и количество (например, `1 20`).")
        sell_product(message)
        return

    quantity_in_warehouse = db_utils.check_products(connection, buyer_choice)
    if quantity_in_warehouse < qty:
        bot.send_message(chat_id, f"Не хватает {qty - quantity_in_warehouse} единиц товара, инициализируем покупку товара...")
        success = order_missing_products(buyer_choice, qty - quantity_in_warehouse)
        if success:
            bot.send_message(chat_id, f"Товар успешно докуплен, инициализируем продажу...")
    
    price = db_utils.get_price_of_product(connection, buyer_choice)
    db_utils.change_balance(connection, price * qty)
    db_utils.add_product_to_warehouse(connection, buyer_choice, -qty)
    try:
        db_utils.add_new_sale_detail(connection, sale_id, buyer_choice, price, qty)
    except Error:
        db_utils.add_new_sale(connection, sale_id)
        db_utils.add_new_sale_detail(connection, sale_id, buyer_choice, price, qty)
        
    bot.send_message(chat_id, "Товар успешно продан, продолжить покупку?", reply_markup=ui.choice_menu())

    bot.register_next_step_handler(message, process_next_step_for_buying, sale_id)

def process_next_step_for_buying(message, sale_id):
    chat_id = message.chat.id
    answer = message.text.strip().lower()
    if answer == 'да':
        sell_product(message, sale_id)
    else:
        bot.send_message(chat_id, "Спасибо за покупку, хорошего дня!", reply_markup=ui.main_menu())


def return_product(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, db_utils.get_sale_history(connection), parse_mode='Markdown')
    bot.send_message(chat_id, "Введите id чека", reply_markup=ui.back_menu())
    bot.register_next_step_handler(message, process_check_to_return)

def process_check_to_return(message):
    chat_id = message.chat.id
    if message.text.strip().lower() == 'назад':
        bot.send_message(chat_id, "Возврат в главное меню", reply_markup=ui.main_menu())
        return
    try:
        sale_id = int(message.text.strip())
        rows = db_utils.get_sale_details(connection, sale_id)
        if not rows:
            bot.send_message(chat_id, "Такого чека нет")
            return_product(message)
        headers = ['id', 'Наименование товара', 'Проданное количество', 'Можно ли вернуть']
        table = tabulate(rows, headers, tablefmt='fancy_grid', floatfmt='.2f')
        bot.send_message(chat_id, f"```\n{table}\n```", parse_mode='markdown')
        bot.send_message(chat_id, "Введите id товара и возвращаемое количество через пробел (пример 1 5)", reply_markup=ui.back_menu())
        bot.register_next_step_handler(message, init_product_return, sale_id)
    except ValueError:
        bot.send_message(chat_id, "Неккоректное значение id")
        return_product(message)
        return
        
def init_product_return(message, sale_id):
    chat_id = message.chat.id
    if message.text.strip().lower() == 'назад':
        bot.send_message(chat_id, "Возврат в главное меню", reply_markup=ui.main_menu())
        return
    try:
        parts = message.text.strip().split()
        product_id = int(parts[0])
        qty = int(parts[1])
    except (IndexError, ValueError):
        bot.send_message(chat_id, "Неверный формат. Пожалуйста, введите данные в формате: id продукта количество (например, `1 20`).")
        message.text = str(sale_id)
        process_check_to_return(message)

    price = db_utils.get_price_of_product(connection, product_id)
    if db_utils.reduce_products_from_returns(connection, sale_id, product_id, qty):
        db_utils.change_balance(connection, -price * qty)
        db_utils.add_product_to_warehouse(connection, product_id, qty)

        bot.send_message(chat_id, "Товар успешно возвращен", reply_markup=ui.main_menu())
        db_utils.add_new_return(connection, sale_id, product_id, qty)
        
    else:
        bot.send_message(chat_id, "Недостаточное количества товара в чеке или такого товара нет в чеке")
        message.text = str(sale_id)
        process_check_to_return(message)

def get_financial_report(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Введите год за который Вы хотите получить финансовый отчет (все 4 цифры)", reply_markup=ui.back_menu())
    bot.register_next_step_handler(message, print_report)

def print_report(message):
    chat_id = message.chat.id
    year = message.text.lower()
    if year == 'назад':
        bot.send_message(chat_id, "Возврат в главное меню", reply_markup=ui.main_menu())
        return

    if not(year and year.isdigit()):
        bot.send_message(chat_id, "Некорректный год")
        get_financial_report(message)
        return
    
    for quartal in range(1, 5):
        bot.send_message(chat_id, f"{quartal} квартал\n" + db_utils.get_financial_report_by_quartal(connection, year, quartal), parse_mode='Markdown')
    
    bot.send_message(chat_id, "Итог по году\n" + db_utils.get_financial_report_by_year(connection, year), parse_mode='Markdown', reply_markup=ui.main_menu())
    

def sale_history(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, db_utils.get_sale_history(connection), parse_mode='Markdown')
    bot.send_message(chat_id, "Введите id чека", reply_markup=ui.back_menu())
    bot.register_next_step_handler(message, check_details)

def check_details(message):
    chat_id = message.chat.id
    id = message.text.strip()
    if not id.isdigit():
        bot.send_message(chat_id, "Некорректный id чека")
        sale_history(message)
        return
    id = int(id)
    details = db_utils.get_sale_details(connection, id)
    headers = ['Артикул', 'Название', 'Кол-во', 'Возвратный']
    table = tabulate(details, headers, tablefmt='fancy_grid', floatfmt='.2f')
    bot.send_message(chat_id, f"```\n{table}\n```", parse_mode='Markdown', reply_markup=ui.main_menu())
    
    

# Основной обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
def menu_handler(message):
    text = message.text.strip().lower()
    chat_id = message.chat.id

    match text:
        case 'оформить заказ':
            bot.send_message(chat_id, "Выберите тип заказа:", reply_markup=ui.order_menu())
        case 'исполнить заказ для потребителя':
            sell_product(message)
        case 'заказать товар у поставщика':
            purchase_product(message)
        case 'возврат товара':
            return_product(message)
        case 'отчёты':
            bot.send_message(chat_id, "Выберите тип отчёта:", reply_markup=ui.reports_menu())
        case 'состояние склада':
            bot.send_message(chat_id, db_utils.get_products_from_warehouse(connection), parse_mode='Markdown', reply_markup=ui.reports_menu())
        case 'удовлетворённые заказы':
            sale_history(message)
        case 'финансовая картина':
            bot.send_message(chat_id, db_utils.get_financial_situation(connection), parse_mode='Markdown', reply_markup=ui.reports_menu())
        case 'фин. отчёт (квартал/год)':
            get_financial_report(message)
        case 'поставщики':
            bot.send_message(chat_id, db_utils.get_sellers(connection), parse_mode='Markdown', reply_markup=ui.main_menu())
        case 'назад':
            bot.send_message(chat_id, "Возврат в главное меню", reply_markup=ui.main_menu())
        case _:
            bot.send_message(chat_id, "Неизвестная команда. Пожалуйста, выберите действие из меню.", reply_markup=ui.main_menu())


if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling(none_stop=True)
