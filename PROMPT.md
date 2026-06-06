# Промпт создания проекта

## Цель

Создать Python-проект для работы с PostgreSQL базой данных, демонстрирующий CRUD-операции и использование транзакций.

## Требования

### 1. Модуль драйвера (postgres_driver.py)

Создать класс `PostgreSQLDriver` с методами:

- **Подключение:**
  - `connect()` — подключение к БД через `psycopg2` и `load_dotenv()`
  - `disconnect()` — закрытие соединения
  - Контекстный менеджер (`__enter__`, `__exit__`)

- **Создание таблиц:**
  - `create_tables()` — создание таблиц `users` и `orders` с констрайнтами:
    - `users`: PRIMARY KEY, CHECK (age >= 0)
    - `orders`: PRIMARY KEY, FOREIGN KEY с ON DELETE CASCADE

- **CRUD-операции:**
  - `add_user(name, age)` — добавление пользователя
  - `add_order(user_id, amount)` — добавление заказа
  - `get_user_totals()` — сумма заказов по пользователям (LEFT JOIN)

- **Вспомогательные методы:**
  - `select_one()`, `select_all()` — выборка данных
  - `insert()`, `update()`, `delete()` — CRUD
  - `execute_query()`, `execute_query_with_result()` — выполнение SQL
  - `table_exists()` — проверка существования таблицы

### 2. Основной скрипт (main.py)

Написать `main.py`, который:

1. **Подключается к БД** через `psycopg2` и `load_dotenv()`
2. **Создаёт таблицы:**
   ```sql
   CREATE TABLE users (
       id   SERIAL,
       name TEXT NOT NULL,
       age  INT,
       CONSTRAINT users_pkey PRIMARY KEY (id),
       CONSTRAINT users_age_check CHECK (age >= 0)
   );
   CREATE TABLE orders (
       id         SERIAL,
       user_id    INT NOT NULL,
       amount     NUMERIC(10,2) NOT NULL,
       created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
       CONSTRAINT orders_pkey PRIMARY KEY (id),
       CONSTRAINT orders_user_id_fkey FOREIGN KEY (user_id)
           REFERENCES public.users (id) MATCH SIMPLE
           ON UPDATE NO ACTION
           ON DELETE CASCADE
   );
   ```
3. **Добавляет данные:**
   - ≥3 пользователей через `add_user()`
   - ≥2 заказов у разных пользователей через `add_order()`
   - Использовать параметризованные запросы (%s) и транзакции
4. **Выполняет агрегирующий запрос:**
   ```sql
   SELECT u.name,
          COALESCE(SUM(o.amount), 0) AS total_amount
   FROM users u
   LEFT JOIN orders o ON o.user_id = u.id
   GROUP BY u.id, u.name
   ORDER BY total_amount DESC;
   ```
   Вывести результат: `Имя — 1250.00`
5. **Обрабатывает исключения** (`psycopg2.Error`) и гарантирует закрытие соединения
6. **Проверяет ON DELETE CASCADE:**
   - Удаляет пользователя с заказами
   - Выводит сообщение о удалении и сумме его заказов
   - Проверяет, что заказы тоже удалены

### 3. SQL-скрипт (creation.sql)

Создать файл для инициализации БД:

- Создать базу данных `test`
- Создать пользователя `user` с паролем
- Создать таблицы `users` и `orders`
- Назначить права

### 4. Документация

- **README.md** — инструкция по запуску
- **PROMPT.md** — описание промпта (этот файл)
- **.envExample** — шаблон настроек подключения

## Технические требования

- Python 3.10+
- PostgreSQL 16+
- Зависимости: `psycopg2-binary`, `python-dotenv`
- Виртуальное окружение
- `.env` не коммитится в Git

## Структура проекта

```
├── main.py
├── postgres_driver.py
├── creation.sql
├── requirements.txt
├── .env
├── .envExample
├── .gitignore
├── README.md
└── PROMPT.md
```