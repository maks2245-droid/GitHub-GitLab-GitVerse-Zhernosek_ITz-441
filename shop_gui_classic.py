"""
Менеджер интернет-магазина (v2)
Полностью совместим с предыдущим аналитическим кодом (классы Client/Product/Order)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from typing import List
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns

# Настраиваем стиль и шрифты для красивых графиков
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False
sns.set_style("whitegrid")


# === Классы из предыдущего кода (для полной совместимости) ===
class Product:
    def __init__(self, name: str, price: float):
        self.name = name
        self.price = price

    def to_dict(self):
        return {"name": self.name, "price": self.price}

    @classmethod
    def from_dict(cls, data):
        return cls(data["name"], data["price"])


class Client:
    def __init__(self, number: int, fio: str, email: str = "", phone: str = ""):
        self.number = number
        self.fio = fio
        self.email = email
        self.phone = phone

    def to_dict(self):
        return {"number": self.number, "fio": self.fio, "email": self.email, "phone": self.phone}

    @classmethod
    def from_dict(cls, data):
        return cls(data["number"], data["fio"], data.get("email", ""), data.get("phone", ""))


class Order:
    def __init__(self, number: int, client: Client, products: List[Product], date: datetime = None):
        self.number = number
        self.client = client
        self.products = products
        self.date = date or datetime.now()

    def to_dict(self):
        return {
            "number": self.number,
            "client_number": self.client.number,
            "products": [p.to_dict() for p in self.products],
            "date": self.date.isoformat()
        }

    @classmethod
    def from_dict(cls, data, clients_dict):
        client = clients_dict[data["client_number"]]
        products = [Product.from_dict(p) for p in data["products"]]
        date = datetime.fromisoformat(data["date"])
        return cls(data["number"], client, products, date)


# === Глобальные списки ===
clients: List[Client] = []
orders: List[Order] = []
next_client_id = 1
next_order_id = 1


# === Конвертация в DataFrame (из предыдущего кода) ===
def orders_to_df():
    import pandas as pd
    data = []
    for order in orders:
        for product in order.products:
            data.append({
                'OrderNumber': order.number,
                'ClientNumber': order.client.number,
                'ClientFIO': order.client.fio,
                'ProductName': product.name,
                'ProductPrice': product.price,
                'OrderDate': order.date.date()
            })
    return pd.DataFrame(data)


# === Функции GUI ===
def refresh_clients():
    for row in tree_clients.get_children():
        tree_clients.delete(row)
    for c in clients:
        tree_clients.insert("", "end", values=(c.number, c.fio, c.email, c.phone))


def refresh_orders():
    for row in tree_orders.get_children():
        tree_orders.delete(row)
    for o in orders:
        products_str = ", ".join([f"{p.name} ×1" for p in o.products])  # можно расширить на qty
        total = sum(p.price for p in o.products)
        tree_orders.insert("", "end", values=(
            o.number, o.client.fio, f"{o.date.strftime('%d.%m.%Y')}", len(o.products), f"{total:,.0f} ₽", products_str
        ))


def add_client():
    global next_client_id
    fio = entry_fio.get().strip()
    email = entry_email.get().strip()
    phone = entry_phone.get().strip()
    if not fio:
        messagebox.showwarning("Ошибка", "ФИО обязательно!")
        return
    client = Client(next_client_id, fio, email, phone)
    clients.append(client)
    next_client_id += 1
    refresh_clients()
    entry_fio.delete(0, tk.END)
    entry_email.delete(0, tk.END)
    entry_phone.delete(0, tk.END)


def add_order():
    global next_order_id
    try:
        client_num = int(entry_client_id.get())
        client = next(c for c in clients if c.number == client_num)
    except StopIteration:
        messagebox.showerror("Ошибка", "Клиент не найден")
        return
    except ValueError:
        messagebox.showerror("Ошибка", "ID клиента — число")
        return

    products_text = entry_products.get().strip()
    if not products_text:
        messagebox.showerror("Ошибка", "Укажите товары")
        return

    products = []
    for part in products_text.split(";"):
        part = part.strip()
        if not part: continue
        try:
            name_price = part.split(",")
            if len(name_price) == 1:
                name, price = part.strip(), 1000.0
            else:
                name = ",".join(name_price[:-1]).strip()
                price = float(name_price[-1])
            products.append(Product(name, price))
        except:
            messagebox.showerror("Ошибка", f"Неверный формат товара: {part}\nОжидается: Название, цена")
            return

    order = Order(next_order_id, client, products)
    orders.append(order)
    next_order_id += 1
    refresh_orders()
    entry_client_id.delete(0, tk.END)
    entry_products.delete(0, tk.END)


# === Аналитика ===
def show_full_analysis():
    if not orders:
        messagebox.showinfo("Аналитика", "Нет заказов для анализа")
        return

    df = orders_to_df()

    win = tk.Toplevel(root)
    win.title("Аналитика продаж")
    win.geometry("1000x700")

    notebook = ttk.Notebook(win)
    notebook.pack(fill="both", expand=True)

    # Вкладка: Топ клиентов
    frame1 = ttk.Frame(notebook)
    notebook.add(frame1, text="Топ клиентов")

    top_by_orders = df.groupby(['ClientNumber', 'ClientFIO'])['OrderNumber'].nunique().sort_values(ascending=False).head(10)
    top_by_revenue = df.groupby(['ClientNumber', 'ClientFIO'])['ProductPrice'].sum().sort_values(ascending=False).head(10)

    text = tk.Text(frame1, font=("Consolas", 11))
    text.pack(fill="both", expand=True, padx=10, pady=10)
    text.insert("end", "ТОП КЛИЕНТОВ ПО КОЛИЧЕСТВУ ЗАКАЗОВ:\n")
    text.insert("end", top_by_orders.to_string() + "\n\n")
    text.insert("end", "ТОП КЛИЕНТОВ ПО ВЫРУЧКЕ:\n")
    text.insert("end", top_by_revenue.apply(lambda x: f"{x:,.0f} ₽").to_string())

    # Вкладка: Динамика заказов
    frame2 = ttk.Frame(notebook)
    notebook.add(frame2, text="Динамика заказов")

    fig = plt.Figure(figsize=(10, 5), dpi=100)
    ax = fig.add_subplot(111)
    daily = df.groupby('OrderDate')['OrderNumber'].nunique()
    daily.plot(ax=ax, marker='o', linewidth=2.5, color='#2E86AB')
    ax.set_title('Динамика количества заказов по дням', fontsize=14, fontweight='bold')
    ax.set_xlabel('Дата')
    ax.set_ylabel('Заказов в день')
    ax.grid(True, alpha=0.3)

    canvas = FigureCanvasTkAgg(fig, frame2)
    canvas.get_tk_widget().pack(fill="both", expand=True)
    canvas.draw()

    # Вкладка: Топ товаров
    frame3 = ttk.Frame(notebook)
    notebook.add(frame3, text="Топ товаров")

    fig2 = plt.Figure(figsize=(10, 5), dpi=100)
    ax2 = fig2.add_subplot(111)
    top_prod = df.groupby('ProductName')['ProductPrice'].sum().sort_values(ascending=False).head(10)
    top_prod.plot(kind='barh', ax=ax2, color='#A23B72')
    ax2.set_title('Топ товаров по выручке', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Выручка, ₽')

    canvas2 = FigureCanvasTkAgg(fig2, frame3)
    canvas2.get_tk_widget().pack(fill="both", expand=True)
    canvas2.draw()


# === Импорт/Экспорт ===
def export_json():
    if not clients and not orders:
        messagebox.showinfo("Экспорт", "Нет данных для экспорта")
        return
    file = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
    if file:
        data = {
            "clients": [c.to_dict() for c in clients],
            "orders": [o.to_dict() for o in orders]
        }
        with open(file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        messagebox.showinfo("Успех", "Данные экспортированы!")

def import_json():
    global clients, orders, next_client_id, next_order_id
    file = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
    if not file: return
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        clients = [Client.from_dict(c) for c in data.get("clients", [])]
        clients_dict = {c.number: c for c in clients}
        orders = [Order.from_dict(o, clients_dict) for o in data.get("orders", [])]

        next_client_id = max((c.number for c in clients), default=0) + 1
        next_order_id = max((o.number for o in orders), default=0) + 1

        refresh_clients()
        refresh_orders()
        messagebox.showinfo("Успех", "Данные импортированы!")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось импортировать:\n{e}")


# === GUI ===
root = tk.Tk()
root.title("Менеджер интернет-магазина (Pro)")
root.geometry("1100x650")
root.state('zoomed')  # на весь экран (Windows)

notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True)

# Вкладка: Клиенты
tab_clients = ttk.Frame(notebook)
notebook.add(tab_clients, text="Клиенты")

tree_clients = ttk.Treeview(tab_clients, columns=("id", "fio", "email", "phone"), show="headings", height=15)
tree_clients.heading("id", text="ID")
tree_clients.heading("fio", text="ФИО")
tree_clients.heading("email", text="Email")
tree_clients.heading("phone", text="Телефон")
tree_clients.column("id", width=50)
tree_clients.column("fio", width=250)
tree_clients.pack(fill="both", expand=True, padx=10, pady=10)

form_c = ttk.LabelFrame(tab_clients, text="Добавить клиента")
form_c.pack(padx=10, pady=10, fill="x")

ttk.Label(form_c, text="ФИО:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
entry_fio = ttk.Entry(form_c, width=40)
entry_fio.grid(row=0, column=1, padx=5, pady=5)

ttk.Label(form_c, text="Email:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
entry_email = ttk.Entry(form_c, width=40)
entry_email.grid(row=1, column=1, padx=5, pady=5)

ttk.Label(form_c, text="Телефон:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
entry_phone = ttk.Entry(form_c, width=40)
entry_phone.grid(row=2, column=1, padx=5, pady=5)

ttk.Button(form_c, text="Добавить клиента", command=add_client).grid(row=3, column=0, columnspan=2, pady=10)

# Вкладка: Заказы
tab_orders = ttk.Frame(notebook)
notebook.add(tab_orders, text="Заказы")

tree_orders = ttk.Treeview(tab_orders, columns=("id", "client", "date", "items", "sum", "products"), show="headings")
for col, text in [("id", "№"), ("client", "Клиент"), ("date", "Дата"), ("items", "Тов."), ("sum", "Сумма"), ("products", "Товары")]:
    tree_orders.heading(col, text=text)
tree_orders.column("id", width=50)
tree_orders.column("sum", width=100)
tree_orders.pack(fill="both", expand=True, padx=10, pady=10)

form_o = ttk.LabelFrame(tab_orders, text="Новый заказ")
form_o.pack(padx=10, pady=10, fill="x")

ttk.Label(form_o, text="ID клиента:").grid(row=0, column=0, sticky="w", padx=5)
entry_client_id = ttk.Entry(form_o, width=15)
entry_client_id.grid(row=0, column=1, padx=5)

ttk.Label(form_o, text="Товары (Название, цена; Название2, 2500):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
entry_products = ttk.Entry(form_o, width=80)
entry_products.grid(row=1, column=1, padx=5, pady=5)
entry_products.insert(0, "Ноутбук, 75000; Мышь, 2500")

ttk.Button(form_o, text="Добавить заказ", command=add_order).grid(row=2, column=0, columnspan=2, pady=10)

# Вкладка: Аналитика
tab_analytics = ttk.Frame(notebook)
notebook.add(tab_analytics, text="Аналитика")

ttk.Button(tab_analytics, text="ПОЛНЫЙ АНАЛИЗ ПРОДАЖ", command=show_full_analysis,
           style="Accent.TButton").pack(pady=50)

ttk.Label(tab_analytics, text="Нажмите кнопку выше, чтобы увидеть:\n"
                             "• Топ клиентов\n"
                             "• Динамику заказов\n"
                             "• Топ товаров по выручке", justify="center", font=("Arial", 12)).pack(pady=20)

# Меню
menu = tk.Menu(root)
root.config(menu=menu)
file_menu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Файл", menu=file_menu)
file_menu.add_command(label="Импорт из JSON", command=import_json)
file_menu.add_command(label="Экспорт в JSON", command=export_json)
file_menu.add_separator()
file_menu.add_command(label="Выход", command=root.quit)

# Стиль
style = ttk.Style()
style.theme_use('clam')
style.configure("Accent.TButton", foreground="white", background="#2E86AB", font=("Arial", 11, "bold"))

root.mainloop()