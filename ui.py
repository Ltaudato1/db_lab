from telebot import types
import db_utils

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

def back_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row('Назад')
    return markup


def reports_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row('Состояние склада', 'Удовлетворённые заказы')
    markup.row('Финансовая картина', 'Фин. отчёт (квартал/год)')
    markup.row('Назад')
    return markup

def choice_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row('Да', 'Нет')
    return markup