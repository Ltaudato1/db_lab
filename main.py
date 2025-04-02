import os
from dotenv import load_dotenv
import telebot
from telebot import types
import mysql.connector
from mysql.connector import Error

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

def create_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        if connection.is_connected():
            print("Подключение к базе данных успешно установлено")
            return connection
    except Error as e:
        print(f"Ошибка подключения: {e}")
    return

# Функция для формирования главного меню
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row('Оформить заказ', 'Возврат товара')
    markup.row('Отчёты')
    return markup


# Функция для меню заказов
def order_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row('Заказ для потребителя', 'Заказ для поставщика')
    markup.row('Назад')
    return markup


# Функция для меню отчётов
def reports_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row('Состояние склада', 'Удовлетворённые заказы')
    markup.row('Финансовая картина', 'Фин. отчёт (квартал/год)')
    markup.row('Назад')
    return markup


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT 'Подключение успешно' AS status;")
        result = cursor.fetchone()
        connection.close()
        bot.send_message(message.chat.id, f"Добро пожаловать! {result[0]}")
    else:
        bot.send_message(message.chat.id, "Не удалось подключиться к базе данных")
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=main_menu())



# Основной обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
def menu_handler(message):
    text = message.text.strip().lower()

    if text == 'оформить заказ':
        bot.send_message(message.chat.id, "Выберите тип заказа:", reply_markup=order_menu())
    elif text == 'заказ для потребителя':
        bot.send_message(message.chat.id, "В процессе реализации...")
    elif text == 'заказ для поставщика':
        bot.send_message(message.chat.id, "В процессе реализации...")
    elif text == 'возврат товара':
        bot.send_message(message.chat.id, "В процессе реализации...")
    elif text == 'отчёты':
        bot.send_message(message.chat.id, "Выберите тип отчёта:", reply_markup=reports_menu())
    elif text == 'состояние склада':
        bot.send_message(message.chat.id, "В процессе реализации...")
    elif text == 'удовлетворённые заказы':
        bot.send_message(message.chat.id, "В процессе реализации...")
    elif text == 'финансовая картина':
        bot.send_message(message.chat.id, "В процессе реализации...")
    elif text == 'фин. отчёт (квартал/год)':
        bot.send_message(message.chat.id, "В процессе реализации...")
    elif text == 'назад':
        bot.send_message(message.chat.id, "Возврат в главное меню", reply_markup=main_menu())
    else:
        bot.send_message(message.chat.id, "Неизвестная команда. Пожалуйста, выберите действие из меню.", reply_markup=main_menu())


if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling(none_stop=True)
