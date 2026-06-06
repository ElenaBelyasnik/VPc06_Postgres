# PostgreSQL Driver Module

Драйвер для работы с PostgreSQL базой данных с поддержкой CRUD-операций.

## Установка зависимостей

```powershell
pip install psycopg2-binary python-dotenv
```

## Настройка

Создайте файл `.env` с параметрами подключения:

```env
HOST=localhost
PORT=5432
NAME=test
USER=user
PASSWORD=111
```

## Использование

### Базовое подключение

```python
from postgres_driver import PostgreSQLDriver

# Через контекстный менеджер (автоматическое подключение/отключение)
with PostgreSQLDriver() as db:
    # Работа с базой данных
    result = db.select_all('users')
```

### CRUD-операции

#### Создание таблицы

```python
db.create_table('users', {
    'id': 'SERIAL PRIMARY KEY',
    'name': 'VARCHAR(100) NOT NULL',
    'email': 'VARCHAR(100) UNIQUE',
    'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
}, primary_key='id')
```

#### Вставка записей

```python
# Вставка одной записи
user_id = db.insert('users', {
    'name': 'John Doe',
    'email': 'john@example.com'
}, returning='id')

# Массовая вставка
db.insert_many('users', [
    {'name': 'User 1', 'email': 'user1@example.com'},
    {'name': 'User 2', 'email': 'user2@example.com'}
])
```

#### Выборка записей

```python
# Одна запись
user = db.select_one('users', where={'id': 1})

# Все записи
users = db.select_all('users')

# С фильтрацией
active_users = db.select_all('users', where={'status': 'active'})

# С сортировкой и лимитом
recent_users = db.select_all(
    'users',
    order_by='created_at DESC',
    limit=10
)

# Выборка конкретных колонок
names = db.select_all('users', columns=['name', 'email'])
```

#### Обновление записей

```python
db.update(
    'users',
    data={'name': 'New Name', 'email': 'new@example.com'},
    where={'id': 1}
)
```

#### Удаление записей

```python
db.delete('users', where={'id': 1})
```

### Выполнение произвольных SQL-запросов

```python
# Запрос без возврата результатов
db.execute_query("DELETE FROM users WHERE age < 18")

# Запрос с возвратом результатов
result = db.execute_query_with_result("SELECT * FROM users WHERE age > 18")

# Массовое выполнение
db.execute_many(
    "INSERT INTO logs (message, created_at) VALUES (%s, NOW())",
    [('Log 1',), ('Log 2',), ('Log 3',)]
)
```

### Транзакции

```python
# Автоматическая (через контекстный менеджер)
with PostgreSQLDriver() as db:
    db.execute_query("INSERT INTO accounts (balance) VALUES (100)")
    db.execute_query("UPDATE accounts SET balance = balance - 50 WHERE id = 1")
    db.execute_query("UPDATE accounts SET balance = balance + 50 WHERE id = 2")
    # Commit происходит автоматически при успешном завершении

# Ручное управление
db.begin_transaction()
try:
    db.execute_query("INSERT INTO accounts (balance) VALUES (100)")
    db.commit()
except Exception as e:
    db.rollback()
    raise e
```

### Вспомогательные методы

```python
# Проверка существования таблицы
exists = db.table_exists('users')

# Получение колонок таблицы
columns = db.get_table_columns('users')

# Количество записей в таблице
count = db.get_row_count('users')
```

### Специализированные методы для users и orders

```python
# Создание таблиц users и orders
db.create_tables()

# Добавление пользователя
user_id = db.add_user('John Doe', 28)

# Добавление заказа
order_id = db.add_order(user_id, 99.99)

# Получение суммы заказов по пользователям
totals = db.get_user_totals()
for row in totals:
    print(f"{row['name']}: {row['total_amount']}")
```

## Методы класса PostgreSQLDriver

| Метод | Описание |
|-------|----------|
| `connect()` | Установить подключение к БД |
| `disconnect()` | Закрыть подключение к БД |
| `create_table()` | Создать таблицу |
| `create_tables()` | Создать таблицы users и orders |
| `drop_table()` | Удалить таблицу |
| `insert()` | Вставить одну запись |
| `insert_many()` | Массовая вставка записей |
| `select_one()` | Выборка одной записи |
| `select_all()` | Выборка всех записей |
| `update()` | Обновление записей |
| `delete()` | Удаление записей |
| `execute_query()` | Выполнить SQL-запрос |
| `execute_query_with_result()` | Выполнить SELECT с возвратом результатов |
| `execute_many()` | Массовое выполнение запросов |
| `execute_in_transaction()` | Выполнить запросы в транзакции |
| `begin_transaction()` | Начать транзакцию |
| `commit()` | Зафиксировать транзакцию |
| `rollback()` | Откатить транзакцию |
| `add_user(name, age)` | Добавить пользователя |
| `add_order(user_id, amount)` | Добавить заказ |
| `get_user_totals()` | Сумма заказов по пользователям (LEFT JOIN) |
| `table_exists()` | Проверить существование таблицы |
| `get_table_columns()` | Получить колонки таблицы |
| `get_row_count()` | Получить количество записей |

## Безопасность

- Все запросы используют параметризованные запросы (%s) для защиты от SQL-инъекций
- Идентификаторы (имена таблиц, колонок) экранируются через `sql.Identifier`
- Пароли и учётные данные хранятся в `.env` файле (не коммитится в Git)

## Обработка ошибок

```python
from postgres_driver import PostgreSQLDriver
from psycopg2 import Error

try:
    with PostgreSQLDriver() as db:
        db.insert('users', {'name': 'Test'})
except Error as e:
    print(f"Ошибка базы данных: {e}")
except ConnectionError as e:
    print(f"Ошибка подключения: {e}")
```