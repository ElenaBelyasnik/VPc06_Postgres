# PostgreSQL Driver Project

Проект демонстрирует работу с PostgreSQL базой данных через Python-драйвер.

## Структура проекта

```
├── main.py                 # Основной скрипт с демонстрацией CRUD-операций
├── postgres_driver.py      # Драйвер для работы с PostgreSQL
├── creation.sql            # Скрипт создания БД, пользователя и таблиц
├── requirements.txt        # Зависимости Python
├── .env                    # Настройки подключения (не коммитится)
├── .envExample             # Шаблон настроек
├── .gitignore              # Исключения для Git
└── README.md               # Эта документация
```

## Требования

- Python 3.10+
- PostgreSQL 16+

## Установка

### 1. Клонируйте репозиторий

```powershell
git clone <repository-url>
cd VPc06_Postgres
```

### 2. Создайте виртуальное окружение

```powershell
python -m venv venv
.\venv\Scripts\Activate
```

### 3. Установите зависимости

```powershell
pip install -r requirements.txt
```

### 4. Настройте подключение

Скопируйте `.envExample` в `.env` и отредактируйте:

```powershell
copy .envExample .env
```

Редактируйте `.env`:

```env
HOST=localhost
PORT=5432
NAME=test
USER=user
PASSWORD=111
```

### 5. Создайте базу данных

Запустите скрипт `creation.sql` через psql:

```powershell
# Войдите как суперпользователь (postgres)
psql -U postgres -f creation.sql
```

Или вручную:

```sql
-- Создать пользователя
CREATE USER "user" WITH PASSWORD '111';

-- Создать базу данных
CREATE DATABASE test OWNER "user";

-- Подключиться к БД
\c test

-- Создать таблицы (см. creation.sql)
```

## Запуск

```powershell
python main.py
```

## Результат

```
✓ Успешно подключено к PostgreSQL!

--- Создание таблиц ---
✓ Таблицы users и orders созданы

--- Добавление данных ---
  Добавлен пользователь: Алиса (ID=1)
  Добавлен пользователь: Борис (ID=2)
  Добавлен пользователь: Виктор (ID=3)
  Добавлен пользователь: Галина (ID=4)
  Добавлен заказ ID=1 для пользователя ID=1, сумма=499.9
  ...

--- Итоги заказов по пользователям ---
  Виктор — 2100.00 руб.
  Алиса — 1749.90 руб.
  Борис — 750.50 руб.
  Галина — 0.00 руб.

=== ПРОВЕРКА ON DELETE CASCADE ===
  Удаляем пользователя ID=2 (Борис)...
  Сумма заказов удаляемого пользователя: 750.50 руб.
  ...
```

## Возможности драйвера

| Метод | Описание |
|-------|----------|
| `create_tables()` | Создание таблиц users и orders |
| `add_user(name, age)` | Добавление пользователя |
| `add_order(user_id, amount)` | Добавление заказа |
| `get_user_totals()` | Сумма заказов по пользователям (LEFT JOIN) |
| `select_all()` | Выборка всех записей |
| `select_one()` | Выборка одной записи |
| `insert()` | Вставка записей |
| `update()` | Обновление записей |
| `delete()` | Удаление записей |

## Зависимости

```
psycopg2-binary>=2.9.0
python-dotenv>=1.0.0
```