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
        
        # ==================== СОЗДАНИЕ ТАБЛИЦ ====================
        
        # Создаём таблицу users (пересоздаём если существует)
        print("\n--- Создание таблицы users ---")
        if db.table_exists('users'):
            print("Таблица 'users' существует, удаляю...")
            db.drop_table('users', cascade=True)
        
        db.create_table('users', {
            'id': 'INTEGER NOT NULL',
            'name': 'TEXT',
            'age': 'REAL',
        }, primary_key='id')
        print("✓ Таблица 'users' создана")
        
        # Создаём таблицу orders (пересоздаём если существует)
        print("\n--- Создание таблицы orders ---")
        if db.table_exists('orders'):
            print("Таблица 'orders' существует, удаляю...")
            db.drop_table('orders')
        
        db.create_table('orders', {
            'id': 'INTEGER NOT NULL',
            'user_id': 'INTEGER NOT NULL',
            'product_name': 'TEXT',
            'quantity': 'INTEGER',
            'price': 'DECIMAL(10, 2)',
            'order_date': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
        }, primary_key='id')
        
        # Добавляем внешний ключ для связи one-to-many
        db.execute_query("""
            ALTER TABLE orders 
            ADD CONSTRAINT fk_orders_user 
            FOREIGN KEY (user_id) REFERENCES users(id)
        """)
        print("✓ Таблица 'orders' создана с внешним ключом к users")
        
        # ==================== ЗАПОЛНЕНИЕ ДАННЫМИ ====================
        
        # Тестовые данные для users (10 записей)
        print("\n--- Заполнение таблицы users ---")
        users_data = [
            {'id': 1, 'name': 'Иван Иванов', 'age': 25.0},
            {'id': 2, 'name': 'Мария Петрова', 'age': 30.0},
            {'id': 3, 'name': 'Алексей Сидоров', 'age': 35.0},
            {'id': 4, 'name': 'Елена Смирнова', 'age': 28.0},
            {'id': 5, 'name': 'Дмитрий Козлов', 'age': 42.0},
            {'id': 6, 'name': 'Ольга Новикова', 'age': 23.0},
            {'id': 7, 'name': 'Сергей Морозов', 'age': 38.0},
            {'id': 8, 'name': 'Анна Волкова', 'age': 31.0},
            {'id': 9, 'name': 'Павел Соколов', 'age': 27.0},
            {'id': 10, 'name': 'Татьяна Лебедева', 'age': 33.0},
        ]
        
        db.insert_many('users', users_data)
        print(f"✓ Вставлено {len(users_data)} пользователей")
        
        # Тестовые данные для orders (45 записей)
        print("\n--- Заполнение таблицы orders ---")
        products = [
            ('Ноутбук', 5, 75000.00),
            ('Смартфон', 10, 25000.00),
            ('Наушники', 3, 5000.00),
            ('Монитор', 2, 18000.00),
            ('Клавиатура', 4, 3500.00),
            ('Мышь', 6, 1500.00),
            ('Веб-камера', 2, 4500.00),
            ('Принтер', 1, 12000.00),
        ]
        
        orders_data = []
        order_id = 1
        
        # Генерируем заказы для разных пользователей
        import random
        import datetime
        
        base_date = datetime.datetime(2025, 1, 1)
        
        for _ in range(45):
            user_id = random.randint(1, 10)  # Случайный пользователь от 1 до 10
            product, quantity, price = random.choice(products)
            order_date = base_date + datetime.timedelta(days=random.randint(0, 365))
            
            orders_data.append({
                'id': order_id,
                'user_id': user_id,
                'product_name': product,
                'quantity': quantity,
                'price': price,
            })
            order_id += 1
        
        db.insert_many('orders', orders_data)
        print(f"✓ Вставлено {len(orders_data)} заказов")
        
        # ==================== ДЕМОНСТРАЦИЯ ВОЗМОЖНОСТЕЙ ====================
        
        print("\n--- Демонстрация CRUD-операций ---")
        
        # 1. Проверка существования таблиц
        print(f"\nТаблица 'users' существует: {db.table_exists('users')}")
        print(f"Таблица 'orders' существует: {db.table_exists('orders')}")
        
        # 2. Получение колонок таблиц
        print(f"\nКолонки 'users': {db.get_table_columns('users')}")
        print(f"Колонки 'orders': {db.get_table_columns('orders')}")
        
        # 3. Подсчёт записей
        print(f"\nКоличество пользователей: {db.get_row_count('users')}")
        print(f"Количество заказов: {db.get_row_count('orders')}")
        
        # 4. Выборка всех пользователей
        print("\n--- Все пользователи ---")
        users = db.select_all('users')
        for user in users:
            print(f"  ID={user['id']}, Имя={user['name']}, Возраст={user['age']}")
        
        # 5. Выборка заказов конкретного пользователя
        print("\n--- Заказы пользователя ID=3 ---")
        user_orders = db.select_all('orders', where={'user_id': 3})
        for order in user_orders:
            print(f"  Заказ ID={order['id']}: {order['product_name']} x{order['quantity']} = {order['price']} руб.")
        
        # 6. Обновление данных
        print("\n--- Обновление данных ---")
        db.update('users', data={'age': 26.0}, where={'id': 1})
        user = db.select_one('users', where={'id': 1})
        print(f"  Возраст пользователя ID=1 изменён на: {user['age']}")
        
        # 7. Вставка отдельной записи
        print("\n--- Вставка отдельной записи ---")
        new_user_id = db.insert('users', {'id': 11, 'name': 'Новый Пользователь', 'age': 40.0}, returning='id')
        print(f"  Создан пользователь с ID: {new_user_id}")
        
        # 8. Запрос с JOIN (через execute_query_with_result)
        print("\n--- Заказы с именами пользователей (JOIN) ---")
        join_query = """
            SELECT o.id as order_id, u.name as user_name, o.product_name, o.quantity, o.price
            FROM orders o
            JOIN users u ON o.user_id = u.id
            ORDER BY o.id
            LIMIT 10
        """
        join_results = db.execute_query_with_result(join_query)
        for row in join_results:
            print(f"  Заказ #{row['order_id']}: {row['user_name']} купил {row['product_name']}")
        
        # 9. Удаление записи
        print("\n--- Удаление записи ---")
        db.delete('users', where={'id': 11})
        print(f"  Удалён пользователь с ID=11")
        
        print("\n✓ Демонстрация завершена успешно!")


if __name__ == "__main__":
    main()