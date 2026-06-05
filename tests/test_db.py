import psycopg2
from psycopg2 import Error
from dotenv import load_dotenv
import os
from pathlib import Path

# Находим путь к корню проекта и загружаем .env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def get_db_connection():
    """Получение подключения к PostgreSQL из переменных окружения"""
    return psycopg2.connect(
        host=os.getenv("HOST"),
        port=int(os.getenv("PORT", 5432)),
        database=os.getenv("NAME"),
        user=os.getenv("USER"),
        password=os.getenv("PASSWORD")
    )


def test_postgres_connection():
    """Тестовое подключение к PostgreSQL"""
    
    connection = None
    
    try:
        # Подключение через функцию с переменными окружения
        connection = get_db_connection()
        
        # Проверка успешного подключения
        if connection:
            print("✓ Успешно подключено к PostgreSQL!")
            
            # Создаём курсор для выполнения SQL-запросов
            cursor = connection.cursor()
            
            # Получаем версию PostgreSQL
            cursor.execute("SELECT version();")
            record = cursor.fetchone()
            print(f"Версия базы данных: {record[0]}")
            
            cursor.close()
            return True
            
    except Error as e:
        print(f"✗ Ошибка при подключении к PostgreSQL: {e}")
        return False
        
    finally:
        if connection:
            connection.close()
            print("✓ Соединение закрыто")


if __name__ == "__main__":
    test_postgres_connection()
