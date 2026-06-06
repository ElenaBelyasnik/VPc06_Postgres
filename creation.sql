-- =============================================
-- Скрипт создания базы данных и пользователя
-- =============================================

-- Создание пользователя (если не существует)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'user') THEN
        CREATE USER "user" WITH PASSWORD '111';
        RAISE NOTICE 'Пользователь "user" создан';
    ELSE
        RAISE NOTICE 'Пользователь "user" уже существует';
    END IF;
END
$$;

-- Создание базы данных (если не существует)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_database WHERE datname = 'test') THEN
        CREATE DATABASE test OWNER "user";
        RAISE NOTICE 'База данных "test" создана';
    ELSE
        RAISE NOTICE 'База данных "test" уже существует';
    END IF;
END
$$;

-- Подключение к базе данных test
\c test

-- Назначение прав пользователю
GRANT ALL PRIVILEGES ON DATABASE test TO "user";

-- Создание таблиц
CREATE TABLE IF NOT EXISTS users (
    id   SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    age  INT CHECK (age >= 0)
);

CREATE TABLE IF NOT EXISTS orders (
    id         SERIAL PRIMARY KEY,
    user_id    INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount     NUMERIC(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Назначение прав на таблицы пользователю
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "user";
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "user";

-- Изменение владельца таблиц (опционально)
ALTER TABLE users OWNER TO "user";
ALTER TABLE orders OWNER TO "user";

\echo '=== Создание завершено ==='