import os
from dotenv import load_dotenv
import telebot
from telebot import types
import mysql.connector
from mysql.connector import Error

import db_utils

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

# Функция для формирования главного меню
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row('Оформить заказ', 'Возврат товара')
    markup.row('Отчёты', 'Поставщики')
    return markup


def order_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row('Исполнить заказ для потребителя', 'Заказать товар у поставщика')
    markup.row('Назад')
    return markup


def reports_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row('Состояние склада', 'Удовлетворённые заказы')
    markup.row('Финансовая картина', 'Фин. отчёт (квартал/год)')
    markup.row('Назад')
    return markup

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT 'Подключение к базе данных успешно' AS status;")
        result = cursor.fetchone()
        bot.send_message(message.chat.id, f"Добро пожаловать! {result[0]}")
    else:
        bot.send_message(message.chat.id, "Не удалось подключиться к базе данных")
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=main_menu())

@bot.message_handler(commands=['reset'])
def reset_database(message):
    cursor = connection.cursor()

    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

    tables = ["OrderDetails", "SaleDetails", "Orders", "Sales"]
    for table in tables:
        cursor.execute(f"DELETE FROM {table};")

    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")


    cursor.execute("UPDATE UserInfo SET balance = 300")

    connection.commit()

    cursor.close()

# Основной обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
def menu_handler(message):
    text = message.text.strip().lower()

    match text:
        case 'оформить заказ':
            bot.send_message(message.chat.id, "Выберите тип заказа:", reply_markup=order_menu())
        case 'исполнить заказ для потребителя':
            bot.send_message(message.chat.id, "В процессе реализации...")
        case 'заказать товар у поставщика':
            bot.send_message(message.chat.id, "В процессе реализации...")
        case 'возврат товара':
            bot.send_message(message.chat.id, "В процессе реализации...")
        case 'отчёты':
            bot.send_message(message.chat.id, "Выберите тип отчёта:", reply_markup=reports_menu())
        case 'состояние склада':
            bot.send_message(message.chat.id, db_utils.get_products_from_warehouse(connection), parse_mode='Markdown', reply_markup=reports_menu())
        case 'удовлетворённые заказы':
            bot.send_message(message.chat.id, "В процессе реализации...")
        case 'финансовая картина':
            bot.send_message(message.chat.id, db_utils.get_financial_situation(connection), parse_mode='Markdown', reply_markup=reports_menu())
        case 'фин. отчёт (квартал/год)':
            bot.send_message(message.chat.id, "В процессе реализации...")
        case 'поставщики':
            bot.send_message(message.chat.id, db_utils.get_sellers(connection), parse_mode='Markdown', reply_markup=main_menu())
        case 'назад':
            bot.send_message(message.chat.id, "Возврат в главное меню", reply_markup=main_menu())
        case _:
            bot.send_message(message.chat.id, "Неизвестная команда. Пожалуйста, выберите действие из меню.", reply_markup=main_menu())


if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling(none_stop=True)
