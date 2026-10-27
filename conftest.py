import sqlite3
import os
import pytest
import pandas as pd

DB_PATH = os.environ.get(
    "DB_PATH",
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "cryptogamer-ecommerce",
        "backend",
        "prisma",
        "dev.db",
    ),
)


@pytest.fixture(scope="session")
def db():
    """Conexión SQLite compartida para toda la sesión de tests."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture(scope="session")
def df_products(db):
    return pd.read_sql_query("SELECT * FROM products", db)


@pytest.fixture(scope="session")
def df_users(db):
    return pd.read_sql_query("SELECT * FROM users", db)


@pytest.fixture(scope="session")
def df_orders(db):
    return pd.read_sql_query("SELECT * FROM orders", db)


@pytest.fixture(scope="session")
def df_order_items(db):
    return pd.read_sql_query("SELECT * FROM order_items", db)


@pytest.fixture(scope="session")
def df_categories(db):
    return pd.read_sql_query("SELECT * FROM categories", db)
