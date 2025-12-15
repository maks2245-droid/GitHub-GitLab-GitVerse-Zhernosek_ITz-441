"""
Анализ заказов: преобразование в DataFrame, топ клиентов, динамика заказов и выручка.
Поддерживает русский язык в графиках.
"""

import pandas as pd
from datetime import datetime
from typing import List
import matplotlib.pyplot as plt
import seaborn as sns

# Настраиваем русские шрифты для графиков
plt.rcParams['font.family'] = 'DejaVu Sans'  # или 'Arial', если есть
plt.rcParams['axes.unicode_minus'] = False

class Product:
    def __init__(self, name: str, price: float):
        self.name = name
        self.price = price

class Client:
    def __init__(self, number: int, fio: str):
        self.number = number
        self.fio = fio

class Order:
    def __init__(self, number: int, client: Client, products: List[Product], date: datetime):
        self.number = number
        self.client = client
        self.products = products
        self.date = date

def orders_to_df(orders: List[Order]) -> pd.DataFrame:
    """Преобразует список заказов в плоский DataFrame (по одной строке на товар в заказе)"""
    data = []
    for order in orders:
        for product in order.products:
            data.append({
                'OrderNumber': order.number,
                'ClientNumber': order.client.number,
                'ClientFIO': order.client.fio,
                'ProductName': product.name,
                'ProductPrice': product.price,
                'OrderDate': order.date.date()  # оставляем только дату без времени
            })
    return pd.DataFrame(data)

def top_clients_by_orders(orders: List[Order], top: int = 5) -> pd.Series:
    """Топ клиентов по количеству уникальных заказов"""
    df = orders_to_df(orders)
    if df.empty:
        print("Нет данных для анализа клиентов.")
        return pd.Series()

    top_clients = (
        df.groupby(['ClientNumber', 'ClientFIO'])['OrderNumber']
        .nunique()
        .sort_values(ascending=False)
        .head(top)
    )
    
    print(f"\nТоп-{top} клиентов по количеству заказов:")
    print(top_clients.to_string())
    return top_clients

def top_clients_by_revenue(orders: List[Order], top: int = 5) -> pd.Series:
    """Топ клиентов по выручке"""
    df = orders_to_df(orders)
    if df.empty:
        print("Нет данных для анализа выручки.")
        return pd.Series()

    df['Revenue'] = df['ProductPrice']  # цена уже за единицу, а в заказе может быть несколько товаров
    revenue = df.groupby(['ClientNumber', 'ClientFIO'])['Revenue'].sum().sort_values(ascending=False).head(top)
    
    print(f"\nТоп-{top} клиентов по выручке:")
    print(revenue.apply(lambda x: f"{x:,.2f} ₽").to_string())
    return revenue

def top_products_by_revenue(orders: List[Order], top: int = 5) -> pd.Series:
    """Топ товаров по выручке"""
    df = orders_to_df(orders)
    if df.empty:
        return pd.Series()

    top_prod = df.groupby('ProductName')['ProductPrice'].sum().sort_values(ascending=False).head(top)
    
    print(f"\nТоп-{top} товаров по выручке:")
    print(top_prod.apply(lambda x: f"{x:,.2f} ₽").to_string())
    return top_prod

def order_dynamics(orders: List[Order]) -> pd.Series:
    """График динамики количества заказов по дням"""
    df = orders_to_df(orders)
    if df.empty:
        print("Нет данных для построения графика динамики.")
        return pd.Series()

    daily_orders = df.groupby('OrderDate')['OrderNumber'].nunique()
    
    plt.figure(figsize=(12, 6))
    daily_orders.plot(kind='line', marker='o', linewidth=2, markersize=8, color='#2E86AB')
    plt.title('Динамика количества заказов по дням', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Дата', fontsize=12)
    plt.ylabel('Количество заказов', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()
    
    return daily_orders

def run_full_analysis(orders: List[Order]):
    """Запуск полного анализа одним вызовом"""
    print("═" * 60)
    print("АНАЛИЗ ЗАКАЗОВ".center(60))
    print("═" * 60)
    
    df = orders_to_df(orders)
    print("\nОбщий вид данных:")
    print(df)
    
    top_clients_by_orders(orders)
    top_clients_by_revenue(orders)
    top_products_by_revenue(orders)
    order_dynamics(orders)
    
    print("\nГотово!")

# ───────────────────── Тестовые данные ─────────────────────
if __name__ == "__main__":
    client1 = Client(1, "Иванов Иван Иванович")
    client2 = Client(2, "Петров Пётр Петрович")
    client3 = Client(3, "Сидорова Анна Сергеевна")

    product1 = Product("Ноутбук Xiaomi", 75_000)
    product2 = Product("Мышь Logitech", 3_500)
    product3 = Product("Клавиатура Keychron", 12_000)
    product4 = Product("Монитор 27\" Dell", 28_000)

    orders = [
        Order(101, client1, [product1, product2], datetime(2024, 5, 1)),
        Order(102, client1, [product3], datetime(2024, 5, 2)),
        Order(103, client2, [product4, product2], datetime(2024, 5, 1)),
        Order(104, client3, [product1], datetime(2024, 5, 3)),
        Order(105, client1, [product2, product4], datetime(2024, 5, 10)),
        Order(106, client2, [product3, product3], datetime(2024, 5, 15)),
    ]

    # Запуск полного анализа
    run_full_analysis(orders)