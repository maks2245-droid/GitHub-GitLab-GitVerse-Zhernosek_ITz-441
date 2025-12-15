"""
test_models.py — Полные юнит-тесты для models.py
Покрывает валидацию, расчёты, сериализацию и совместимость с FileDatabase
Запуск: python test_models.py
"""

import unittest
from datetime import datetime
from models import Client, Product, Order, orders_to_df


class TestClientValidation(unittest.TestCase):
    def test_valid_client(self):
        """Корректные данные должны проходить валидацию"""
        client = Client(
            number=1,
            fio="Иванов Иван Иванович",
            phone="+79991234567",
            email="ivanov@example.com"
        )
        self.assertEqual(client.number, 1)
        self.assertEqual(client.fio, "Иванов Иван Иванович")
        self.assertEqual(client.phone, "+79991234567")
        self.assertEqual(client.email, "ivanov@example.com")

    def test_invalid_phone_variants(self):
        """Все некорректные телефоны должны падать"""
        invalid_phones = [
            "89991234567",           # нет +
            "+7999123456",           # мало цифр
            "+799912345678",         # много цифр
            "79991234567",           # нет +7
            "+7 999 123 45 67",      # пробелы
            "+375291234567",         # белорусский код
            "12345",                 # короткий
            "",                      # пустой (разрешено, если не обязателен)
            None,                    # None
        ]

        for phone in invalid_phones:
            if phone == "":  # пустая строка — допустимо
                Client(1, "Тест", phone="", email="test@mail.ru")
                continue
            with self.subTest(phone=phone):
                with self.assertRaises(ValueError) as cm:
                    Client(1, "Тест", phone=phone, email="test@mail.ru")
                self.assertIn("телефон", str(cm.exception).lower())

    def test_invalid_email_variants(self):
        """Все некорректные email должны падать"""
        invalid_emails = [
            "test", "test@", "@mail.ru", "test@mail", "test@mail..ru",
            "test@ mail.ru", "тест@почта.рф", "user@.com", "user@@mail.ru",
            "user.name@mail..com", "user@mail.r", ""
        ]

        for email in invalid_emails:
            with self.subTest(email=email):
                if email == "":  # пустой — разрешено
                    Client(1, "Тест", "+79991234567", email="")
                    continue
                with self.assertRaises(ValueError) as cm:
                    Client(1, "Тест", "+79991234567", email=email)
                self.assertIn("email", str(cm.exception).lower())

    def test_empty_contact_fields_allowed(self):
        """Поля phone и email могут быть пустыми — это нормально"""
        client = Client(1, "Петров Пётр", phone="", email="")
        self.assertEqual(client.phone, "")
        self.assertEqual(client.email, "")


class TestProduct(unittest.TestCase):
    def test_piece_product(self):
        p = Product("Ноутбук Dell", 85000, is_per_kg=False)
        self.assertFalse(p.is_per_kg)
        self.assertEqual(p.price, 85000.0)

    def test_weight_product(self):
        p = Product("Куркума молотая", 450, is_per_kg=True)
        self.assertTrue(p.is_per_kg)
        self.assertEqual(p.price, 450.0)


class TestOrderCalculations(unittest.TestCase):
    def setUp(self):
        self.client = Client(1, "Сидоров", "+79991234567", "sidorov@mail.ru")
        self.p1 = Product("Монитор 27\"", 28000, is_per_kg=False)
        self.p2 = Product("Сахар", 55, is_per_kg=True)
        self.p3 = Product("Кофе молотый", 890, is_per_kg=True)

    def test_only_piece_goods(self):
        order = Order(101, self.client, products_list=[self.p1, self.p1])
        self.assertEqual(order.total_cost, 56000.0)

    def test_only_weight_goods(self):
        order = Order(102, self.client, products_kg={self.p2: 3.0, self.p3: 0.5})
        self.assertEqual(order.total_cost, 55 * 3 + 890 * 0.5)  # 165 + 445 = 610

    def test_mixed_goods(self):
        order = Order(
            103,
            self.client,
            products_list=[self.p1],
            products_kg={self.p2: 2.5, self.p3: 1.0}
        )
        expected = 28000 + (55 * 2.5) + (890 * 1.0)
        self.assertEqual(order.total_cost, expected)

    def test_rounding(self):
        order = Order(104, self.client, products_kg={self.p2: 1.234})
        self.assertAlmostEqual(order.total_cost, 67.87, places=2)


class TestSerialization(unittest.TestCase):
    def test_client_serialization(self):
        c = Client(5, "Козлов А.В.", "+79995554433", "kozlov@company.ru")
        data = c.to_dict()
        self.assertEqual(data["fio"], "Козлов А.В.")
        restored = Client.from_dict(data)
        self.assertEqual(restored.fio, c.fio)
        self.assertEqual(restored.phone, c.phone)

    def test_order_serialization_full_cycle(self):
        client = Client(1, "Тестов Т.Т.", "+79990001122")
        catalog = [
            Product("Рис", 80, True),
            Product("Чайник", 3500, False)
        ]
        name_to_prod = {p.name: p for p in catalog}

        order = Order(
            999,
            client,
            products_list=[catalog[1]],
            products_kg={catalog[0]: 5.5},
            date=datetime(2025, 4, 5)
        )

        data = order.to_dict()
        clients_map = {client.number: client}

        restored = Order.from_dict(data, clients_map, catalog)

        self.assertEqual(restored.number, 999)
        self.assertEqual(restored.total_cost, order.total_cost)
        self.assertEqual(len(restored.products_list), 1)
        self.assertAlmostEqual(restored.products_kg[catalog[0]], 5.5)


class TestOrdersToDataFrame(unittest.TestCase):
    def setUp(self):
        self.client = Client(1, "Иванов")
        self.p_piece = Product("Мышь", 1500, False)
        self.p_weight = Product("Перец", 320, True)
        self.orders = [
            Order(1, self.client, products_list=[self.p_piece]),
            Order(2, self.client, products_kg={self.p_weight: 0.25})
        ]

    def test_df_structure_and_values(self):
        df = orders_to_df(self.orders)
        self.assertEqual(len(df), 2)
        self.assertEqual(set(df.columns),
                         {"OrderNumber", "ClientNumber", "ClientFIO", "ProductName",
                          "Price", "Quantity", "Revenue", "IsPerKg", "OrderDate"})

        row1 = df.iloc[0]
        self.assertEqual(row1["ProductName"], "Мышь")
        self.assertEqual(row1["Quantity"], 1)
        self.assertEqual(row1["Revenue"], 1500)
        self.assertFalse(row1["IsPerKg"])

        row2 = df.iloc[1]
        self.assertEqual(row2["ProductName"], "Перец")
        self.assertEqual(row2["Quantity"], 0.25)
        self.assertEqual(row2["Revenue"], 80.0)
        self.assertTrue(row2["IsPerKg"])


if __name__ == "__main__":
    print("Запуск юнит-тестов для моделей данных...")
    print("═" * 65)
    unittest.main(verbosity=2, exit=False)
    print("═" * 65)
    print("Все тесты моделей завершены успешно!")