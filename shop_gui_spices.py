"""
Менеджер заказов специй (по весу в кг)
Полностью совместим с FileDatabase, аналитикой и предыдущими GUI
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from typing import Dict
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd

# === Классы (обновлённые, совместимые с FileDatabase) ===
class Product:
    def __init__(self, name: str, price_per_kg: float):
        self.name = name
        self.price_per_kg = price_per_kg

    def to_dict(self): return {"name": self.name, "price_per_kg": self.price_per_kg}
    @classmethod
    def from_dict(cls, d): return cls(d["name"], d["price_per_kg"])


class Client:
    def __init__(self, number: int, fio: str, phone: str = "", email: str = ""):
        self.number = number
        self.fio = fio
        self.phone = phone
        self.email = email

    def to_dict(self): return {"number": self.number, "fio": self.fio, "phone": self.phone, "email": self.email}
    @classmethod
    def from_dict(cls, d): return cls(d["number"], d["fio"], d.get("phone", ""), d.get("email", ""))


class Order:
    def __init__(self, number: int, client: Client, products_kg: Dict[Product, float], date=None):
        self.number = number
        self.client = client
        self.products_kg = products_kg  # {Product: кг}
        self.date = date or datetime.now()

    def total_sum(self):
        return sum(p.price_per_kg * kg for p, kg in self.products_kg.items())

    def to_dict(self):
        return {
            "number": self.number,
            "client_number": self.client.number,
            "products_kg": {p.name: kg for p, kg in self.products_kg.items()},
            "date": self.date.isoformat()
        }

    @classmethod
    def from_dict(cls, data, clients_map, products_catalog):
        client = clients_map[data["client_number"]]
        products_kg = {}
        for name, kg in data["products_kg"].items():
            product = next(p for p in products_catalog if p.name == name)
            products_kg[product] = kg
        date = datetime.fromisoformat(data["date"])
        return cls(data["number"], client, products_kg, date)


# === FileDatabase (упрощённая версия только для этого модуля) ===
from pathlib import Path
import json

class FileDatabase:
    def __init__(self, folder="spice_data"):
        self.folder = Path(folder)
        self.folder.mkdir(exist_ok=True)
        self.clients_file = self.folder / "clients.json"
        self.orders_file = self.folder / "orders.json"
        self.catalog_file = self.folder / "catalog.json"

        self.catalog = self._load_catalog()
        self.clients = self._load_clients()
        self.orders = self._load_orders()

        self.next_client_id = max((c.number for c in self.clients), default=0) + 1
        self.next_order_id = max((o.number for o in self.orders), default=0) + 1

    def _load_catalog(self):
        if self.catalog_file.exists():
            with open(self.catalog_file, "r", encoding="utf-8") as f:
                return [Product.from_dict(p) for p in json.load(f)]
        # По умолчанию — специи
        default = [
            Product("Сахар", 50), Product("Соль", 20), Product("Перец чёрный молотый", 300),
            Product("Куркума", 450), Product("Паприка сладкая", 280), Product("Корица молотая", 600)
        ]
        self._save_catalog(default)
        return default

    def _save_catalog(self, catalog=None):
        data = [p.to_dict() for p in (catalog or self.catalog)]
        with open(self.catalog_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def _load_clients(self): return self._load_json(self.clients_file, [])
    def _load_orders(self):
        if not self.clients: return []
        clients_map = {c.number: c for c in self.clients}
        data = self._load_json(self.orders_file, [])
        return [Order.from_dict(o, clients_map, self.catalog) for o in data]

    def _load_json(self, file, default):
        if not file.exists(): return default
        try:
            with open(file, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return default

    def save(self):
        with open(self.clients_file, "w", encoding="utf-8") as f:
            json.dump([c.to_dict() for c in self.clients], f, ensure_ascii=False, indent=4)
        with open(self.orders_file, "w", encoding="utf-8") as f:
            json.dump([o.to_dict() for o in self.orders], f, ensure_ascii=False, indent=4)


# === Основное приложение ===
class SpiceShopApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Менеджер заказов специй (по весу)")
        self.geometry("1100x750")
        self.db = FileDatabase()

        self.style = ttk.Style()
        self.style.theme_use('clam')

        self.create_widgets()
        self.refresh_all()

    def create_widgets(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)

        self.tab_clients = ttk.Frame(nb)
        self.tab_orders = ttk.Frame(nb)
        self.tab_analysis = ttk.Frame(nb)

        nb.add(self.tab_clients, text="Клиенты")
        nb.add(self.tab_orders, text="Заказы")
        nb.add(self.tab_analysis, text="Аналитика")

        self.setup_clients_tab()
        self.setup_orders_tab()
        self.setup_analysis_tab()

        # Меню
        menu = tk.Menu(self)
        self.config(menu=menu)
        file_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Экспорт заказов в CSV", command=self.export_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.quit)

    def setup_clients_tab(self):
        frame = ttk.LabelFrame(self.tab_clients, text="Добавить клиента")
        frame.pack(padx=10, pady=10, fill="x")

        ttk.Label(frame, text="ФИО:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.entry_fio = ttk.Entry(frame, width=40)
        self.entry_fio.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Телефон:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.entry_phone = ttk.Entry(frame, width=40)
        self.entry_phone.grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(frame, text="Добавить клиента", command=self.add_client).grid(row=2, column=0, columnspan=2, pady=10)

        self.list_clients = tk.Listbox(self.tab_clients, height=15)
        self.list_clients.pack(fill="both", expand=True, padx=10, pady=10)

    def add_client(self):
        fio = self.entry_fio.get().strip()
        phone = self.entry_phone.get().strip()
        if not fio:
            messagebox.showwarning("Ошибка", "Введите ФИО")
            return
        client = Client(self.db.next_client_id, fio, phone)
        self.db.clients.append(client)
        self.db.next_client_id += 1
        self.db.save()
        self.refresh_clients()
        self.entry_fio.delete(0, tk.END)
        self.entry_phone.delete(0, tk.END)

    def refresh_clients(self):
        self.list_clients.delete(0, tk.END)
        for c in self.db.clients:
            self.list_clients.insert(tk.END, f"{c.number}: {c.fio} | {c.phone or '—'}")

    def setup_orders_tab(self):
        top = ttk.Frame(self.tab_orders)
        top.pack(fill="x", padx=10, pady=10)

        ttk.Label(top, text="Клиент ID:").pack(side="left")
        self.entry_client_id = ttk.Entry(top, width=10)
        self.entry_client_id.pack(side="left", padx=5)

        ttk.Button(top, text="Новый заказ", command=self.open_order_window).pack(side="right")

        self.tree_orders = ttk.Treeview(self.tab_orders, columns=("date", "client", "items", "sum"), show="headings")
        self.tree_orders.heading("date", text="Дата")
        self.tree_orders.heading("client", text="Клиент")
        self.tree_orders.heading("items", text="Товары")
        self.tree_orders.heading("sum", text="Сумма")
        self.tree_orders.pack(fill="both", expand=True, padx=10, pady=10)

    def open_order_window(self):
        win = tk.Toplevel(self)
        win.title("Новый заказ")
        win.geometry("500x600")

        client_id = self.entry_client_id.get().strip()
        if not client_id.isdigit() or not any(c.number == int(client_id) for c in self.db.clients):
            messagebox.showerror("Ошибка", "Введите корректный ID клиента")
            return
        client = next(c for c in self.db.clients if c.number == int(client_id))

        ttk.Label(win, text=f"Заказ для: {client.fio}", font=("Arial", 12, "bold")).pack(pady=10)

        vars_dict = {}
        for product in self.db.catalog:
            frame = ttk.Frame(win)
            frame.pack(fill="x", padx=20, pady=2)
            var = tk.BooleanVar()
            vars_dict[product] = var
            ttk.Checkbutton(frame, text=f"{product.name} — {product.price_per_kg} ₽/кг", variable=var).pack(side="left")
            qty = tk.StringVar(value="0")
            ttk.Entry(frame, textvariable=qty, width=8).pack(side="right")
            ttk.Label(frame, text="кг").pack(side="right")
            frame.qty_var = qty

        def save_order():
            products_kg = {}
            for p, var in vars_dict.items():
                if var.get():
                    try:
                        kg = float(frame.qty_var.get())
                        if kg > 0:
                            products_kg[p] = kg
                    except:
                        pass
            if not products_kg:
                messagebox.showwarning("Ошибка", "Выберите товары и укажите вес")
                return
            order = Order(self.db.next_order_id, client, products_kg)
            self.db.orders.append(order)
            self.db.next_order_id += 1
            self.db.save()
            self.refresh_orders()
            win.destroy()
            messagebox.showinfo("Успех", f"Заказ #{order.number} создан!")

        ttk.Button(win, text="Сохранить заказ", command=save_order).pack(pady=20)

    def refresh_orders(self):
        for i in self.tree_orders.get_children():
            self.tree_orders.delete(i)
        for o in sorted(self.db.orders, key=lambda x: x.date, reverse=True):
            items = ", ".join([f"{p.name} {kg}кг" for p, kg in o.products_kg.items()])
            self.tree_orders.insert("", "end", values=(
                o.date.strftime("%d.%m %H:%M"),
                o.client.fio,
                items,
                f"{o.total_sum():,.0f} ₽"
            ))

    def setup_analysis_tab(self):
        btn = ttk.Button(self.tab_analysis, text="ОБНОВИТЬ АНАЛИТИКУ", command=self.show_analysis)
        btn.pack(pady=20)
        self.analysis_canvas_frame = ttk.Frame(self.tab_analysis)
        self.analysis_canvas_frame.pack(fill="both", expand=True)

    def show_analysis(self):
        for widget in self.analysis_canvas_frame.winfo_children():
            widget.destroy()

        if not self.db.orders:
            ttk.Label(self.analysis_canvas_frame, text="Нет заказов для анализа").pack(pady=20)
            return

        df = self.orders_to_df()
        fig = plt.Figure(figsize=(12, 8), dpi=100)
        gs = fig.add_gridspec(2, 2)

        # Динамика заказов
        ax1 = fig.add_subplot(gs[0, :])
        daily = df.groupby(df['OrderDate'].dt.date)['OrderNumber'].nunique()
        daily.plot(ax=ax1, marker='o', linewidth=2, color='#2E86AB')
        ax1.set_title('Динамика заказов по дням', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)

        # Топ клиентов
        ax2 = fig.add_subplot(gs[1, 0])
        top_clients = df.groupby(['ClientFIO'])['OrderNumber'].nunique().sort_values(ascending=False).head(8)
        top_clients.plot(kind='barh', ax=ax2, color='#A23B72')
        ax2.set_title('Топ клиентов по количеству заказов')

        # Топ специй
        ax3 = fig.add_subplot(gs[1, 1])
        top_spices = df.groupby('ProductName')['Quantity'].sum().sort_values(ascending=False).head(8)
        top_spices.plot(kind='barh', ax=ax3, color='#F18F01')
        ax3.set_title('Топ специй по весу (кг)')

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, self.analysis_canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def orders_to_df(self):
        data = []
        for order in self.db.orders:
            for product, kg in order.products_kg.items():
                data.append({
                    'OrderNumber': order.number,
                    'ClientNumber': order.client.number,
                    'ClientFIO': order.client.fio,
                    'ProductName': product.name,
                    'PricePerKg': product.price_per_kg,
                    'Quantity': kg,
                    'Revenue': product.price_per_kg * kg,
                    'OrderDate': order.date
                })
        return pd.DataFrame(data)

    def export_csv(self):
        file = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if file:
            self.orders_to_df().to_csv(file, index=False, encoding="utf-8-sig")
            messagebox.showinfo("Успех", "Экспорт завершён!")

    def refresh_all(self):
        self.refresh_clients()
        self.refresh_orders()


if __name__ == "__main__":
    app = SpiceShopApp()
    app.mainloop()