from postgres_driver import PostgreSQLDriver


def main():
    """Основная функция - демонстрация работы с драйвером PostgreSQL"""
    
    # Использование через контекстный менеджер
    with PostgreSQLDriver() as db:
        # Проверка успешного подключения
        print("✓ Успешно подключено к PostgreSQL!")
        
        # Получаем версию PostgreSQL
        result = db.execute_query_with_result("SELECT version();")
        print(f"Версия базы данных: {result[0]['version']}")
        
        # Пример использования CRUD-методов:
        # 1. Проверка существования таблицы
        if db.table_exists('users'):
            print("✓ Таблица 'users' существует")
            
            # 2. Выборка всех записей
            users = db.select_all('users')
            print(f"Найдено пользователей: {len(users)}")
            
            # 3. Выборка одной записи
            user = db.select_one('users', where={'id': 1})
            if user:
                print(f"Пользователь ID=1: {user}")
            
            # 4. Вставка новой записи
            # new_user_id = db.insert('users', {'name': 'Test User', 'email': 'test@example.com'}, returning='id')
            # print(f"Создан пользователь с ID: {new_user_id}")
            
            # 5. Обновление записи
            # db.update('users', {'name': 'Updated Name'}, where={'id': 1})
            
            # 6. Удаление записи
            # db.delete('users', where={'id': 1})
        else:
            print("Таблица 'users' не найдена")
        
        # Пример создания таблицы
        # db.create_table('users', {
        #     'id': 'SERIAL PRIMARY KEY',
        #     'name': 'VARCHAR(100) NOT NULL',
        #     'email': 'VARCHAR(100) UNIQUE',
        #     'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
        # })
        
        print("✓ Работа с базой данных завершена")


if __name__ == "__main__":
    main()