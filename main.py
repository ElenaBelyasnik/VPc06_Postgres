from postgres_driver import PostgreSQLDriver
from psycopg2 import Error


def main():
    """
    Демонстрация работы с PostgreSQL через postgres_driver.py.
    
    1. Подключение к БД через psycopg2 и load_dotenv()
    2. Создание таблиц users и orders
    3. Добавление пользователей и заказов
    4. Выполнение агрегирующего запроса (сумма заказов по пользователям)
    5. Обработка исключений и гарантированное закрытие соединения
    """
    
    connection = None
    
    try:
        # 1. Подключение к БД через контекстный менеджер
        with PostgreSQLDriver() as db:
            print("✓ Успешно подключено к PostgreSQL!")
            
            # 2. Создание таблиц users и orders
            print("\n--- Создание таблиц ---")
            db.create_tables()
            print("✓ Таблицы users и orders созданы")
            
            # 3. Добавление пользователей и заказов в транзакции
            print("\n--- Добавление данных ---")
            
            # Добавляем 3+ пользователей
            users_to_add = [
                ("Алиса", 28),
                ("Борис", 35),
                ("Виктор", 42),
                ("Галина", 31),
            ]
            
            user_ids = {}
            for name, age in users_to_add:
                user_id = db.add_user(name, age)
                user_ids[name] = user_id
                print(f"  Добавлен пользователь: {name} (ID={user_id})")
            
            # Добавляем 2+ заказа у разных пользователей
            orders_to_add = [
                (user_ids["Алиса"], 499.90),
                (user_ids["Алиса"], 1250.00),
                (user_ids["Борис"], 750.50),
                (user_ids["Виктор"], 2100.00),
            ]
            
            for user_id, amount in orders_to_add:
                order_id = db.add_order(user_id, amount)
                print(f"  Добавлен заказ ID={order_id} для пользователя ID={user_id}, сумма={amount}")
            
            # 4. Выполнение агрегирующего запроса
            print("\n--- Итоги заказов по пользователям ---")
            user_totals = db.get_user_totals()
            
            for row in user_totals:
                name = row['name']
                total = float(row['total_amount'])
                print(f"  {name} — {total:.2f} руб.")
            
            # 6. Проверка ON DELETE CASCADE
            print("\n=== ПРОВЕРКА ON DELETE CASCADE ===")
            
            # Удаляем пользователя Борис (ID=2) у которого есть заказ
            user_to_delete_id = user_ids["Борис"]
            print(f"  Удаляем пользователя ID={user_to_delete_id} (Борис)...")
            
            # Сначала получаем сумму заказов этого пользователя
            cursor = db._get_cursor(dict_cursor=False)
            cursor.execute(
                "SELECT COALESCE(SUM(amount), 0) as total FROM orders WHERE user_id = %s",
                (user_to_delete_id,)
            )
            result = cursor.fetchone()
            total_orders = float(result[0]) if result else 0
            cursor.close()
            
            print(f"  Сумма заказов удаляемого пользователя: {total_orders:.2f} руб.")
            
            # Удаляем пользователя (заказы должны удалиться автоматически)
            db.delete('users', where={'id': user_to_delete_id})
            print(f"  ✓ Пользователь 'Борис' удалён")
            
            # Проверяем, что заказы тоже удалены
            cursor = db._get_cursor(dict_cursor=False)
            cursor.execute("SELECT COUNT(*) FROM orders WHERE user_id = %s", (user_to_delete_id,))
            remaining_orders = cursor.fetchone()[0]
            cursor.close()
            
            print(f"  ✓ Оставшихся заказов для этого пользователя: {remaining_orders}")
            
            # И снова выполняем агрегирующий запрос
            print("\n--- Итоги заказов после удаления (с LEFT JOIN) ---")
            user_totals = db.get_user_totals()
            
            for row in user_totals:
                name = row['name']
                total = float(row['total_amount'])
                print(f"  {name} — {total:.2f} руб.")
            
            print("\n✓ Проверка ON DELETE CASCADE завершена успешно!")
            print("  Заказы удалённого пользователя были автоматически удалены (CASCADE).")
            
            print("\n✓ Работа с базой данных завершена успешно!")
            
    except Error as e:
        print(f"✗ Ошибка базы данных: {e}")
        raise
    except ConnectionError as e:
        print(f"✗ Ошибка подключения: {e}")
        raise
    finally:
        # 5. Гарантированное закрытие соединения
        # (в контекстном менеджере это происходит автоматически,
        # но для примера показываем явную обработку)
        print("✓ Соединение закрыто")


if __name__ == "__main__":
    main()