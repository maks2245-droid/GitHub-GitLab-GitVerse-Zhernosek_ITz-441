"""
Главный лаунчер системы управления магазинами
Запускает нужное приложение по выбору пользователя
Полностью совместим со всеми предыдущими модулями
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
from pathlib import Path

# Попытка импортировать все возможные приложения
apps = {}

try:
    from shop_gui_classic import ClassicShopApp as App1
    apps["classic"] = {
        "name": "Классический магазин (штучные товары)",
        "desc": "Ноутбуки, мыши, мониторы — продажа по штукам",
        "class": App1,
        "icon": "🛒"
    }
except ImportError:
    pass

try:
    from shop_gui_spices import SpiceShopApp as App2
    apps["spices"] = {
        "name": "Магазин специй (по весу)",
        "desc": "Сахар, соль, куркума — продажа на вес (кг)",
        "class": App2,
        "icon": "🌶️"
    }
except ImportError:
    pass

try:
    from gui_universal import UniversalShopApp as App3
    apps["universal"] = {
        "name": "Универсальный магазин (новая версия)",
        "desc": "Современный интерфейс • Аналитика • Импорт/экспорт",
        "class": App3,
        "icon": "✨"
    }
except ImportError:
    pass

# Если ничего не найдено — резервный вариант
if not apps:
    from tkinter import simpledialog
    print("Предупреждение: Не найдено ни одного GUI-модуля!")
    print("Помести этот файл в папку с хотя бы одним из: shop_gui_classic.py, shop_gui_spices.py, gui_universal.py")

class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Менеджер магазинов v3.0")
        self.geometry("700x500")
        self.resizable(False, False)
        self.configure(bg="#f0f0f0")

        # Заголовок
        header = tk.Label(
            self,
            text="Выберите тип магазина",
            font=("Segoe UI", 20, "bold"),
            bg="#f0f0f0",
            fg="#2c3e50"
        )
        header.pack(pady=30)

        subtitle = tk.Label(
            self,
            text="Одна система — разные магазины",
            font=("Segoe UI", 10),
            bg="#f0f0f0",
            fg="#7f8c8d"
        )
        subtitle.pack(pady=5)

        # Фрейм для кнопок
        frame = tk.Frame(self, bg="#f0f0f0")
        frame.pack(expand=True)

        if not apps:
            tk.Label(
                frame,
                text="Не найдено ни одного приложения!\n"
                     "Убедитесь, что рядом есть файлы:\n"
                     "• shop_gui_classic.py\n"
                     "• shop_gui_spices.py\n"
                     "• gui_universal.py",
                font=("Consolas", 11),
                bg="#f0f0f0",
                fg="red"
            ).pack(expand=True)
            tk.Button(frame, text="Закрыть", command=self.destroy, width=20).pack(pady=20)
            self.mainloop()
            return

        # Создаём красивые карточки
        for key, app in apps.items():
            card = tk.Frame(frame, relief="raised", borderwidth=2, bg="white", padx=20, pady=20)
            card.pack(pady=15, padx=50, fill="x")

            tk.Label(
                card,
                text=app["icon"],
                font=("Segoe UI", 40),
                bg="white"
            ).pack()

            tk.Label(
                card,
                text=app["name"],
                font=("Segoe UI", 14, "bold"),
                bg="white",
                fg="#2c3e50"
            ).pack(pady=5)

            tk.Label(
                card,
                text=app["desc"],
                font=("Segoe UI", 10),
                bg="white",
                fg="#7f8c8d",
                wraplength=500
            ).pack(pady=5)

            btn = tk.Button(
                card,
                text="Запустить",
                command=lambda a=app["class"]: self.launch(a),
                bg="#3498db",
                fg="white",
                font=("Segoe UI", 10, "bold"),
                relief="flat",
                padx=20,
                pady=8,
                cursor="hand2"
            )
            btn.pack(pady=10)
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg="#2980b9"))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(bg="#3498db"))

        # Нижняя часть
        footer = tk.Label(
            self,
            text=f"Найдено приложений: {len(apps)} • Данные хранятся в папках: data/, spice_data/",
            font=("Segoe UI", 9),
            bg="#f0f0f0",
            fg="#95a5a6"
        )
        footer.pack(side="bottom", pady=20)

    def launch(self, app_class):
        self.withdraw()  # скрываем лаунчер
        try:
            app = app_class()
            app.protocol("WM_DELETE_WINDOW", lambda: self.on_app_close(app))
            app.mainloop()
        except Exception as e:
            messagebox.showerror("Ошибка запуска", f"Не удалось запустить приложение:\n{e}")
            self.deiconify()

    def on_app_close(self, app):
        app.destroy()
        self.deiconify()  # возвращаем лаунчер


if __name__ == "__main__":
    # Создаём папки для данных (если их нет)
    Path("data").mkdir(exist_ok=True)
    Path("spice_data").mkdir(exist_ok=True)

    launcher = Launcher()
    launcher.mainloop()