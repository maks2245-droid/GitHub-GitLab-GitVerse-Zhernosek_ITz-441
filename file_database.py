"""
Модуль работы с данными — БЕЗ SQLite!
Полностью совместим с GUI и аналитикой из предыдущих версий.
Поддерживает JSON (основной) и CSV (экспорт/импорт).
Автоматически сохраняет данные при каждом изменении.
"""

import json
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from models import Client, Product, Order  # ← те же классы, что и везде


class FileDatabase:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.clients_file = self.data_dir / "clients.json"
        self.orders_file = self.data_dir / "orders.json"
        
        # Автозагрузка при старте
        self.clients: List[Client] = self._load_clients()
        self.orders: List[Order] = self._load_orders()
        
        # Для генерации ID
        self.next_client_id = max((c.number for c in self.clients), default=0) + 1
        self.next_order_id = max((o.number for o in self.orders), default=0) + 1

    # ==================== Внутренние методы загрузки ====================
    def _load_clients(self) -> List[Client]:
        if not self.clients_file.exists():
            return []
        try:
            with open(self.clients_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [Client.from_dict(c) for c in data]
        except Exception as e:
            print(f"Ошибка загрузки клиентов: {e}")
            return []

    def _load_orders(self) -> List[Order]:
        if not self.orders_file.exists() or not self.clients:
            return []
        try:
            with open(self.orders_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            clients_map = {c.number: c for c in self.clients}
            return [Order.from_dict(o, clients_map) for o in data]
        except Exception as e:
            print(f"Ошибка загрузки заказов: {e}")
            return []

    # ==================== Сохранение ====================
    def _save_clients(self):
        data = [c.to_dict() for c in self.clients]
        with open(self.clients_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def _save_orders(self):
        data = [o.to_dict() for o in self.orders]
        with open(self.orders_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    # ==================== Клиенты ====================
    def add_client(self, client: Client):
        self.clients.append(client)
        self.next_client_id = max(self.next_client_id, client.number + 1)
        self._save_clients()

    def get_clients(self) -> List[Client]:
        return self.clients.copy()

    def find_client_by_id(self, client_id: int) -> Optional[Client]:
        return next((c for c in self.clients if c.number == client_id), None)

    # ==================== Заказы ====================
    def add_order(self, order: Order):
        self.orders.append(order)
        self.next_order_id = max(self.next_order_id, order.number + 1)
        self._save_orders()

    def get_orders(self) -> List[Order]:
        return self.orders.copy()

    def get_next_client_id(self) -> int:
        return self.next_client_id

    def get_next_order_id(self) -> int:
        return self.next_order_id

    # ==================== Экспорт в CSV (для отчётов) ====================
    def export_to_csv(self, filepath: str):
        import pandas as pd
        df = self.orders_to_df()
        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        print(f"Экспорт в CSV: {filepath}")

    def orders_to_df(self):
        import pandas as pd
        data = []
        for order in self.orders:
            for product in order.products:
                data.append({
                    "OrderNumber": order.number,
                    "ClientID": order.client.number,
                    "ClientFIO": order.client.fio,
                    "ProductName": product.name,
                    "ProductPrice": product.price,
                    "OrderDate": order.date.strftime("%Y-%m-%d")
                })
        return pd.DataFrame(data)

    # ==================== Импорт из старого JSON (если нужно) ====================
    def import_from_old_json(self, clients_path: str, orders_path: str):
        # Для миграции со старых версий
        pass  # можно реализовать при необходимости