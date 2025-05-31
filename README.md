# Базы данных ПМИ 4 семестр

Учебный проект на Python для работы с базой данных MySQL и вывода результатов в табличном формате при помощи библиотеки `tabulate`. Позволяет выполнять простейшие операции (создание таблиц, вставка, чтение, обновление, удаление) через Telegram-бота. Выполнен в рамках лабораторной работы по дисциплине "Базы данных"

---

## 📋 Требования

* Python 3.x
* MySQL
* Библиотека `tabulate`

Установка `tabulate`:

```bash
pip install tabulate
```

---

## 🚀 Установка

1. Клонируйте репозиторий:

```bash
git clone https://github.com/Ltaudato1/db_lab.git
cd db_lab
```

2. Установите tabulate, если еще не установлена:

```bash
pip install tabulate
```

3. Отредактируйте `db_utils.py`, замените `DB_CONFIG` на свои данные:

```python
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "your_user",
    "password": "your_password",
    "database": "your_database"
}
```

4. Создайте базу данных в MySQL, если нет:

```sql
CREATE DATABASE your_database CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
```

---

## 📂 Структура проекта

```
db_lab/
├── db_utils.py       # Работа с MySQL
├── ui.py             # Консольный интерфейс
├── main.py           # Точка входа
├── README.md         # Этот файл
```

---

## ⚙️ Использование

Запуск:

```bash
python3 main.py
```

В меню будут доступны операции:

1. Создание таблиц
2. Вставка записи
3. Вывод всех записей
4. Обновление записи
5. Удаление записи

---

## 📊 Пример вывода

```
+----+-----------+--------+
| ID |   name    | price  |
+----+-----------+--------+
| 1  | Widget    | 199.00 |
| 2  | Gizmo     | 299.00 |
+----+-----------+--------+
```

---

## 🚧 Зависимости

* Python 3.x
* MySQL
* tabulate

```bash
pip install tabulate
```

---

## 🛡️ Лицензия

Проект распространяется по лицензии MIT.
