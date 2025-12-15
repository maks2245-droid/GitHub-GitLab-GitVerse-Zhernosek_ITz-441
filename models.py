"""
models.py — Универсальные модели данных
Полная совместимость с FileDatabase, GUI, аналитикой и всеми версиями
С валидацией, сериализацией и поддержкой продажи по весу (кг)
"""

import re
from datetime import datetime
from typing import List, Dict, Union, Any


class Client:
    """Клиент с жёсткой валидацией телефона и email"""
    phone_pattern = re.compile(r'^\+7\d{10}$')
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    def __init__(self, number: int, fio: str, phone: str = "", email: str = ""):
        self.number = int(number)
        self.fio = fio.strip()
        self.phone = phone.strip()
        self.email = email.strip().lower()
        self.validate()

    def validate(self):
        if self.phone and not self.phone_pattern.match(self.phone):
            raise ValueError(f"Неверный телефон: {self.phone}. Ожидается: +79991234567")
        if self.email and not self.email_pattern.match(self.email):
            raise ValueError(f"Неверный email: {self.email}")

    def to_dict(self) -> dict:
        return {
            "number": self.number,
            "fio": self.fio,
            "phone": self.phone,
            "email": self.email
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            number=data["number"],
            fio=data["fio"],
            phone=data.get("phone", ""),
            email=data.get("email", "")
        )

    def __repr__(self):
        return f"Client({self.number}: {self.fio})"


class Product:
    """Товар: может быть штучным или на вес (цена за кг или за штуку)"""
    def __init__(self, name: str, price: float, is_per_kg: bool = False):
        self.name = name.strip()
        self.price = float(price)
        self.is_per_kg = is_per_kg  # True — цена за кг, False — за штуку

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "price": self.price,
            "is_per_kg": self.is_per_kg
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            name=data["name"],
            price=data["price"],
            is_per_kg=data.get("is_per_kg", False)
        )

    def __repr__(self):
        unit = "₽/кг" if self.is_per_kg else "₽/шт"
        return f"Product({self.name}, {self.price} {unit})"


class Order:
    """
    Универсальный заказ:
    - products_list — для штучных товаров: [Product, Product, ...]
    - products_kg   — для весовых: {Product: кг}
    """
    def __init__(
        self,
        number: int,
        client: Client,
        products_list: List[Product] = None,
        products_kg: Dict[Product, float] = None,
        date: datetime = None
    ):
        self.number = int(number)
        self.client = client
        self.products_list = products_list or []
        self.products_kg = products_kg or {}
        self.date = date or datetime.now()

    @property
    def total_cost(self) -> float:
        """Общая стоимость заказа"""
        total = 0.0
        total += sum(p.price for p in self.products_list)
        total += sum(p.price * kg for p, kg in self.products_kg.items())
        return round(total, 2)

    def to_dict(self) -> dict:
        return {
            "number": self.number,
            "client_number": self.client.number,
            "products_list": [p.name for p in self.products_list],
            "products_kg": {p.name: kg for p, kg in self.products_kg.items()},
            "date": self.date.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict, clients_map: dict, products_catalog: List[Product]):
        client = clients_map[data["client_number"]]
        name_to_product = {p.name: p for p in products_catalog}

        products_list = []
        for name in data.get("products_list", []):
            if name in name_to_product:
                products_list.append(name_to_product[name])

        products_kg = {}
        for name, kg in data.get("products_kg", {}).items():
            if name in name_to_product and name_to_product[name].is_per_kg:
                products_kg[name_to_product[name]] = float(kg)

        date = datetime.fromisoformat(data["date"])
        return cls(data["number"], client, products_list, products_kg, date)

    def __repr__(self):
        items = len(self.products_list) + len(self.products_kg)
        return f"Order(#{self.number}, {self.client.fio}, {items} поз., {self.total_cost} ₽)"


# === Вспомогательная функция для аналитики (используется везде) ===
def orders_to_df(orders: List[Order]):
    """Конвертация списка заказов в pandas.DataFrame — единый стандарт"""
    import pandas as pd
    data = []
    for order in orders:
        # Штучные товары
        for product in order.products_list:
            data.append({
                "OrderNumber": order.number,
                "ClientNumber": order.client.number,
                "ClientFIO": order.client.fio,
                "ProductName": product.name,
                "Price": product.price,
                "Quantity": 1,
                "Revenue": product.price,
                "IsPerKg": False,
                "OrderDate": order.date.date()
            })
        # Весовые товары
        for product, kg in order.products_kg.items():
            data.append({
                "OrderNumber": order.number,
                "ClientNumber": order.client.number,
                "ClientFIO": order.client.fio,
                "ProductName": product.name,
                "Price": product.price,
                "Quantity": kg,
                "Revenue": product.price * kg,
                "IsPerKg": True,
                "OrderDate": order.date.date()
            })
    return pd.DataFrame(data)