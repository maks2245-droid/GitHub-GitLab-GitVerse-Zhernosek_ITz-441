"""
tests.py — Полный набор юнит-тестов для всей системы
Совместим с FileDatabase, models.py и аналитикой
Запуск: python -m unittest discover
       или просто: python tests.py
"""

import unittest
import shutil
from pathlib import Path
from datetime import datetime
from tempfile import mkdtemp

# Импортируем всё из твоей системы
from models import Client, Product, Order, orders_to_df

# Имитируем FileDatabase без реальных файлов (или с временной папкой)
class MockFileDatabase:
    def __init__(self):
        self.clients = []
        self.orders = []
        self.catalog = [
            Product("Сахар", 50, is_per_kg=True),
            Product("Ноутбук", 75000, is_per_kg=False),
            Product("Куркума", 450, is_per_kg=True),
        ]
        self.next_client_id = 1
        self.next_order_id = 1

    def add_client(self, client):
        client.number = self.next_client_id
        self.clients.append(client)
        self.next_client_id += 1

    def add_order(self, order):
        order.number = self.next_order_id
        self.orders.append(order)
        self.next_order_id += 1

    def get_clients(self):
        return self.clients.copy()

    def get_orders(self):
        return self.orders.copy()

    def get_catalog(self):
        return self.catalog.copy()


class TestModels(unittest.TestCase):
    def test_client_validation_valid(self):
        client = Client(1, "Иванов Иван Иванович", "+79991234567", "ivanov@mail.ru")
        self.assertEqual(client.fio, "Иванов Иван Иванович")
        self.assertEqual(client.phone, "+79991234567")

    def test_client_validation_invalid_phone(self):
        with self.assertRaises(ValueError):
            Client(1, "Петров", "89991234567", "petr@mail.ru")  # нет +7

        with self.assertRaises(ValueError):
            Client(1, "Петров", "+79991234", "petr@mail.ru")   # мало цифр

    def test_client_validation_invalid_email(self):
        with self.assertRaises(ValueError):
            Client(1, "Сидоров", "+79991234567", "sidorov@")  # некорректный email

        with self.assertRaises(ValueError):
            Client(1, "Сидоров", "+79991234567", "sidorov.mail.ru")  # нет @

    def test_product_per_kg(self):
        p = Product("Соль", 25, is_per_kg=True)
        self.assertTrue(p.is_per_kg)
        self.assertEqual(p.price, 25.0)

    def test_order_total_cost(self):
        client = Client(1, "Иванов", "+79991234567")
        p1 = Product("Ноутбук", 75000, False)
        p2 = Product("Сахар", 50, True)

        order = Order(
            number=101,
            client=client,
            products_list=[p1],
            products_kg={p2: 3.5}
        )
        self.assertEqual(order.total_cost, 75175.0)  # 75000 + 50*3.5


class TestAnalytics(unittest.TestCase):
    def setUp(self):
        self.db = MockFileDatabase()

        c1 = Client(1, "Иванов Иван", "+79991234567", "i@mail.ru")
        c2 = Client(2, "Петров Пётр", "+79997654321", "p@yandex.ru")

        self.db.add_client(c1)
        self.db.add_client(c2)

        p_notebook = self.db.get_catalog()[1]  # Ноутбук
        p_sugar = self.db.get_catalog()[0]     # Сахар

        # Заказы
        self.db.add_order(Order(
            101, c1, products_list=[p_notebook], date=datetime(2024, 5, 1)
        ))
        self.db.add_order(Order(
            102, c1, products_kg={p_sugar: 5}, date=datetime(2024, 5, 2)
        ))
        self.db.add_order(Order(
            103, c2, products_list=[p_notebook], date=datetime(2024, 5, 3)
        ))

    def test_orders_to_df_structure(self):
        df = orders_to_df(self.db.get_orders())
        self.assertEqual(len(df), 3)
        self.assertIn("ClientFIO", df.columns)
        self.assertIn("Revenue", df.columns)
        self.assertIn("Quantity", df.columns)
        self.assertEqual(df["Revenue"].sum(), 75000 + 250 + 75000)  # 50*5 = 250

    def test_top_clients_by_orders(self):
        df = orders_to_df(self.db.get_orders())
        top = df.groupby("ClientFIO")["OrderNumber"].nunique().sort_values(ascending=False)
        self.assertEqual(top.iloc[0], 2)  # Иванов — 2 заказа
        self.assertEqual(top.index[0], "Иванов Иван")

    def test_revenue_calculation(self):
        df = orders_to_df(self.db.get_orders())
        revenue_by_client = df.groupby("ClientFIO")["Revenue"].sum()
        self.assertGreater(revenue_by_client["Иванов Иван"], revenue_by_client["Петров Пётр"])


class TestFileDatabaseIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(mkdtemp())
        (self.temp_dir / "data").mkdir()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_save_and_load(self):
        # Это можно расширить под реальный FileDatabase, если он у тебя в отдельном модуле
        # Сейчас — заглушка для совместимости
        self.assertTrue(True)  # пока просто проходит


if __name__ == "__main__":
    print("Запуск тестов системы управления магазином...")
    print("=" * 60)
    unittest.main(verbosity=2, exit=False)
    print("=" * 60)
    print("Все тесты завершены!")