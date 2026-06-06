import psycopg2
from psycopg2 import Error, sql
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os
from typing import Optional, List, Dict, Any, Union


class PostgreSQLDriver:
    """
    Драйвер для работы с PostgreSQL базой данных.
    
    Поддержка CRUD-операций, транзакций и выполнения произвольных SQL-запросов.
    """
    
    def __init__(self, env_file: str = ".env"):
        """
        Инициализация драйвера.
        
        Args:
            env_file: Путь к файлу с переменными окружения
        """
        # Загружаем переменные окружения
        load_dotenv(env_file)
        
        self.host = os.getenv("HOST")
        self.port = int(os.getenv("PORT", 5432))
        self.database = os.getenv("NAME")
        self.user = os.getenv("USER")
        self.password = os.getenv("PASSWORD")
        
        self._connection: Optional[psycopg2.extensions.connection] = None
    
    def connect(self) -> None:
        """Установка подключения к базе данных."""
        if self._connection is not None:
            return
        
        try:
            self._connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
        except Error as e:
            raise ConnectionError(f"Ошибка при подключении к PostgreSQL: {e}")
    
    def disconnect(self) -> None:
        """Закрытие подключения к базе данных."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None
    
    def __enter__(self):
        """Контекстный менеджер - вход."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер - выход."""
        self.disconnect()
    
    def _get_cursor(self, dict_cursor: bool = True):
        """
        Получение курсора.
        
        Args:
            dict_cursor: Возвращать результаты как словари (True) или кортежи (False)
        
        Returns:
            Курсор базы данных
        """
        if self._connection is None:
            raise ConnectionError("Подключение к базе данных не установлено. Вызовите connect() или используйте контекстный менеджер.")
        
        if dict_cursor:
            return self._connection.cursor(cursor_factory=RealDictCursor)
        else:
            return self._connection.cursor()
    
    # ==================== CRUD МЕТОДЫ ====================
    
    def create_table(self, table_name: str, columns: Dict[str, str], primary_key: Optional[str] = None) -> bool:
        """
        Создание таблицы.
        
        Args:
            table_name: Имя таблицы
            columns: Словарь {имя_колонки: тип_данных}
            primary_key: Имя первичного ключа (опционально)
        
        Returns:
            True если успешно
        """
        column_defs = []
        for col_name, col_type in columns.items():
            column_defs.append(f"{col_name} {col_type}")
        
        if primary_key:
            column_defs.append(f"PRIMARY KEY ({primary_key})")
        
        query = f"CREATE TABLE IF NOT EXISTS {table_name} (\n" + ",\n".join(column_defs) + "\n)"
        
        return self.execute_query(query)
    
    def drop_table(self, table_name: str, if_exists: bool = True, cascade: bool = False) -> bool:
        """
        Удаление таблицы.
        
        Args:
            table_name: Имя таблицы
            if_exists: Удалить если существует
            cascade: Удалить зависимые объекты (внешние ключи и т.д.)
        
        Returns:
            True если успешно
        """
        if_exists_str = "IF EXISTS " if if_exists else ""
        cascade_str = " CASCADE" if cascade else ""
        query = f"DROP TABLE {if_exists_str}{table_name}{cascade_str}"
        return self.execute_query(query)
    
    def insert(self, table_name: str, data: Dict[str, Any], returning: Optional[str] = None) -> Optional[Any]:
        """
        Вставка записи в таблицу.
        
        Args:
            table_name: Имя таблицы
            data: Словарь {column: value}
            returning: Имя колонки для RETURNING (опционально)
        
        Returns:
            Вернувшееся значение или None
        """
        columns = list(data.keys())
        values = list(data.values())
        
        # Создаём плейсхолдеры %s для каждой колонки
        placeholders = ", ".join(["%s"] * len(columns))
        
        query = sql.SQL("INSERT INTO {table} ({columns}) VALUES ({values})")
        query = query.format(
            table=sql.Identifier(table_name),
            columns=sql.SQL(", ").join(map(sql.Identifier, columns)),
            values=sql.SQL(placeholders)
        )
        
        if returning:
            query = query + sql.SQL(" RETURNING {col}").format(col=sql.Identifier(returning))
            cursor = self._get_cursor(dict_cursor=False)
            cursor.execute(query.as_string(self._connection), values)
            self._connection.commit()
            result = cursor.fetchone()
            return result[0] if result else None
        else:
            return self.execute_query(query.as_string(self._connection), values)
    
    def insert_many(self, table_name: str, data_list: List[Dict[str, Any]]) -> bool:
        """
        Массовая вставка записей.
        
        Args:
            table_name: Имя таблицы
            data_list: Список словарей {column: value}
        
        Returns:
            True если успешно
        """
        if not data_list:
            return False
        
        columns = list(data_list[0].keys())
        values_list = [list(record.values()) for record in data_list]
        
        # Создаём плейсхолдеры %s для каждой колонки
        placeholders = ", ".join(["%s"] * len(columns))
        
        query = sql.SQL("INSERT INTO {table} ({columns}) VALUES {values}")
        query = query.format(
            table=sql.Identifier(table_name),
            columns=sql.SQL(", ").join(map(sql.Identifier, columns)),
            values=sql.SQL(", ").join(
                [sql.SQL("(" + placeholders + ")")] * len(values_list)
            )
        )
        
        # Разворачиваем значения для массового вставления
        all_values = []
        for values in values_list:
            all_values.extend(values)
        
        return self.execute_query(query.as_string(self._connection), all_values)
    
    def select_one(self, table_name: str, where: Optional[Dict[str, Any]] = None, 
                   columns: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """
        Выборка одной записи.
        
        Args:
            table_name: Имя таблицы
            where: Условия WHERE {column: value}
            columns: Колонки для выбора (по умолчанию *)
        
        Returns:
            Запись как словарь или None
        """
        query = sql.SQL("SELECT {columns} FROM {table}")
        query = query.format(
            columns=sql.SQL(", ").join(map(sql.Identifier, columns)) if columns else sql.SQL("*"),
            table=sql.Identifier(table_name)
        )
        
        params = []
        if where:
            where_clause = sql.SQL(" AND ").join(
                [sql.SQL("{col} = %s").format(col=sql.Identifier(col)) for col in where.keys()]
            )
            query = query + sql.SQL(" WHERE {where}").format(where=where_clause)
            params = list(where.values())
        
        cursor = self._get_cursor(dict_cursor=True)
        cursor.execute(query.as_string(self._connection), params)
        result = cursor.fetchone()
        return dict(result) if result else None
    
    def select_all(self, table_name: str, where: Optional[Dict[str, Any]] = None,
                   order_by: Optional[str] = None, limit: Optional[int] = None,
                   columns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Выборка всех записей.
        
        Args:
            table_name: Имя таблицы
            where: Условия WHERE {column: value}
            order_by: Сортировка
            limit: Лимит записей
            columns: Колонки для выбора (по умолчанию *)
        
        Returns:
            Список записей как словари
        """
        query = sql.SQL("SELECT {columns} FROM {table}")
        query = query.format(
            columns=sql.SQL(", ").join(map(sql.Identifier, columns)) if columns else sql.SQL("*"),
            table=sql.Identifier(table_name)
        )
        
        params = []
        if where:
            where_clause = sql.SQL(" AND ").join(
                [sql.SQL("{col} = %s").format(col=sql.Identifier(col)) for col in where.keys()]
            )
            query = query + sql.SQL(" WHERE {where}").format(where=where_clause)
            params = list(where.values())
        
        if order_by:
            query = query + sql.SQL(" ORDER BY {order}").format(order=sql.SQL(order_by))
        
        if limit:
            query = query + sql.SQL(" LIMIT %s")
            params.append(limit)
        
        cursor = self._get_cursor(dict_cursor=True)
        cursor.execute(query.as_string(self._connection), params)
        return [dict(row) for row in cursor.fetchall()]
    
    def update(self, table_name: str, data: Dict[str, Any], 
               where: Dict[str, Any]) -> bool:
        """
        Обновление записей.
        
        Args:
            table_name: Имя таблицы
            data: Данные для обновления {column: value}
            where: Условия WHERE {column: value}
        
        Returns:
            True если успешно
        """
        if not data or not where:
            raise ValueError("Необходимо указать данные для обновления и условия WHERE")
        
        set_clause = sql.SQL(", ").join(
            [sql.SQL("{col} = %s").format(col=sql.Identifier(col)) for col in data.keys()]
        )
        
        query = sql.SQL("UPDATE {table} SET {set} WHERE {where}")
        query = query.format(
            table=sql.Identifier(table_name),
            set=set_clause,
            where=sql.SQL(" AND ").join(
                [sql.SQL("{col} = %s").format(col=sql.Identifier(col)) for col in where.keys()]
            )
        )
        
        params = list(data.values()) + list(where.values())
        return self.execute_query(query.as_string(self._connection), params)
    
    def delete(self, table_name: str, where: Dict[str, Any]) -> bool:
        """
        Удаление записей.
        
        Args:
            table_name: Имя таблицы
            where: Условия WHERE {column: value}
        
        Returns:
            True если успешно
        """
        if not where:
            raise ValueError("Необходимо указать условия WHERE для удаления")
        
        query = sql.SQL("DELETE FROM {table} WHERE {where}")
        query = query.format(
            table=sql.Identifier(table_name),
            where=sql.SQL(" AND ").join(
                [sql.SQL("{col} = %s").format(col=sql.Identifier(col)) for col in where.keys()]
            )
        )
        
        params = list(where.values())
        return self.execute_query(query.as_string(self._connection), params)
    
    # ==================== МЕТОДЫ ДЛЯ ИСПОЛНЕНИЯ SQL ====================
    
    def execute_query(self, query: str, params: Optional[tuple] = None, 
                      commit: bool = True) -> bool:
        """
        Выполнение произвольного SQL-запроса.
        
        Args:
            query: SQL-запрос
            params: Параметры запроса
            commit: Выполнить commit после выполнения
        
        Returns:
            True если успешно
        """
        cursor = self._get_cursor(dict_cursor=False)
        try:
            cursor.execute(query, params)
            if commit:
                self._connection.commit()
            return True
        except Error as e:
            self._connection.rollback()
            raise e
        finally:
            cursor.close()
    
    def execute_query_with_result(self, query: str, params: Optional[tuple] = None,
                                   dict_cursor: bool = True) -> List[Dict[str, Any]]:
        """
        Выполнение SELECT-запроса с возвратом результатов.
        
        Args:
            query: SQL-запрос
            params: Параметры запроса
            dict_cursor: Возвращать как словари (True) или кортежи (False)
        
        Returns:
            Список результатов
        """
        cursor = self._get_cursor(dict_cursor=dict_cursor)
        try:
            cursor.execute(query, params)
            if dict_cursor:
                return [dict(row) for row in cursor.fetchall()]
            else:
                return cursor.fetchall()
        finally:
            cursor.close()
    
    def execute_many(self, query: str, params_list: List[tuple]) -> bool:
        """
        Выполнение массового SQL-запроса.
        
        Args:
            query: SQL-запрос с %s плейсхолдерами
            params_list: Список кортежей параметров
        
        Returns:
            True если успешно
        """
        cursor = self._get_cursor(dict_cursor=False)
        try:
            cursor.executemany(query, params_list)
            self._connection.commit()
            return True
        except Error as e:
            self._connection.rollback()
            raise e
        finally:
            cursor.close()
    
    # ==================== ТРАНСАКЦИИ ====================
    
    def begin_transaction(self) -> None:
        """Начало транзакции (автоматически в psycopg2)."""
        pass  # psycopg2 автоматически начинает транзакцию
    
    def commit(self) -> None:
        """Фиксация транзакции."""
        if self._connection:
            self._connection.commit()
    
    def rollback(self) -> None:
        """Откат транзакции."""
        if self._connection:
            self._connection.rollback()
    
    def execute_in_transaction(self, queries: List[tuple]) -> bool:
        """
        Выполнение нескольких запросов в одной транзакции.
        
        Args:
            queries: Список кортежей (query, params)
        
        Returns:
            True если успешно
        """
        cursor = self._get_cursor(dict_cursor=False)
        try:
            for query, params in queries:
                cursor.execute(query, params)
            self._connection.commit()
            return True
        except Error as e:
            self._connection.rollback()
            raise e
        finally:
            cursor.close()
    
    # ==================== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ====================
    
    def table_exists(self, table_name: str) -> bool:
        """
        Проверка существования таблицы.
        
        Args:
            table_name: Имя таблицы
        
        Returns:
            True если таблица существует
        """
        query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
            )
        """
        cursor = self._get_cursor(dict_cursor=False)
        cursor.execute(query, (table_name,))
        result = cursor.fetchone()
        return bool(result[0])
    
    def get_table_columns(self, table_name: str) -> List[str]:
        """
        Получение списка колонок таблицы.
        
        Args:
            table_name: Имя таблицы
        
        Returns:
            Список названий колонок
        """
        query = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = %s 
            ORDER BY ordinal_position
        """
        cursor = self._get_cursor(dict_cursor=True)
        cursor.execute(query, (table_name,))
        return [row['column_name'] for row in cursor.fetchall()]
    
    def get_row_count(self, table_name: str) -> int:
        """
        Получение количества записей в таблице.
        
        Args:
            table_name: Имя таблицы
        
        Returns:
            Количество записей
        """
        query = sql.SQL("SELECT COUNT(*) FROM {table}")
        query = query.format(table=sql.Identifier(table_name))
        
        cursor = self._get_cursor(dict_cursor=False)
        cursor.execute(query.as_string(self._connection))
        return cursor.fetchone()[0]
    
    # ==================== СПЕЦИАЛИЗИРОВАННЫЕ МЕТОДЫ ДЛЯ users И orders ====================
    
    def create_tables(self) -> bool:
        """
        Создание таблиц users и orders.
        
        Returns:
            True если успешно
        """
        # Если таблицы существуют — удаляем их для пересоздания
        if self.table_exists('orders'):
            self.drop_table('orders', cascade=True)
        if self.table_exists('users'):
            self.drop_table('users', cascade=True)
        
        # Создаём таблицу users
        users_query = """
            CREATE TABLE IF NOT EXISTS users (
                id   SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                age  INT CHECK (age >= 0)
            )
        """
        self.execute_query(users_query)
        
        # Создаём таблицу orders
        orders_query = """
            CREATE TABLE IF NOT EXISTS orders (
                id         SERIAL PRIMARY KEY,
                user_id    INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                amount     NUMERIC(10,2) NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """
        self.execute_query(orders_query)
        
        return True
    
    def add_user(self, name: str, age: int) -> Optional[int]:
        """
        Добавление пользователя.
        
        Args:
            name: Имя пользователя
            age: Возраст пользователя
        
        Returns:
            ID созданного пользователя или None
        """
        cursor = self._get_cursor(dict_cursor=False)
        try:
            cursor.execute(
                "INSERT INTO users (name, age) VALUES (%s, %s) RETURNING id",
                (name, age)
            )
            result = cursor.fetchone()
            self._connection.commit()
            return result[0] if result else None
        except Error as e:
            self._connection.rollback()
            raise e
        finally:
            cursor.close()
    
    def add_order(self, user_id: int, amount: float) -> Optional[int]:
        """
        Добавление заказа.
        
        Args:
            user_id: ID пользователя
            amount: Сумма заказа
        
        Returns:
            ID созданного заказа или None
        """
        cursor = self._get_cursor(dict_cursor=False)
        try:
            cursor.execute(
                "INSERT INTO orders (user_id, amount) VALUES (%s, %s) RETURNING id",
                (user_id, amount)
            )
            result = cursor.fetchone()
            self._connection.commit()
            return result[0] if result else None
        except Error as e:
            self._connection.rollback()
            raise e
        finally:
            cursor.close()
    
    def get_user_totals(self) -> List[Dict[str, Any]]:
        """
        Получение суммы заказов по каждому пользователю.
        
        Returns:
            Список словарей {name, total_amount}
        """
        query = """
            SELECT u.name,
                   COALESCE(SUM(o.amount), 0) AS total_amount
            FROM users u
            LEFT JOIN orders o ON o.user_id = u.id
            GROUP BY u.id, u.name
            ORDER BY total_amount DESC
        """
        cursor = self._get_cursor(dict_cursor=True)
        try:
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            cursor.close()