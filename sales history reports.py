"""
Sales History & Reports screen for
Cafe Point of Sale & Inventory Management System.

Same color palette as login_window.py / pos_window.py / inventory_window.py.

Features:
- Quick date filters: Today / This Week / This Month / All Time
- Totals: total sales, total orders, best-seller
- Orders table -> click an order to see its per-item breakdown
- CSV export of the currently filtered orders
"""

import os
import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta

# ---- Shared palette (matches the rest of the app) ----
BG_COLOR = "#F5F1EA"
HEADER_BG = "#3C2A21"
ACCENT = "#D9822B"
ACCENT_DARK = "#C36F1E"
CARD_BG = "#FFFFFF"
TEXT_DARK = "#2C2C2A"
TEXT_MUTED = "#5F5E5A"
BORDER = "#E3DCCF"
SUCCESS = "#4E8C5C"

# ---- Persistence ----
# Orders are saved to this JSON file next to the script, so anything you
# add through "+ Add sale" survives closing and reopening the app.
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(APP_DIR, "sales_data.json")

_DEFAULT_ORDERS = [
    {"id": 1001, "hours_ago": 1, "payment": "Cash",
     "items": [{"name": "Espresso", "qty": 2, "price": 90}, {"name": "Croissant", "qty": 1, "price": 85}]},
    {"id": 1002, "hours_ago": 3, "payment": "GCash",
     "items": [{"name": "Cappuccino", "qty": 1, "price": 120}]},
    {"id": 1003, "hours_ago": 26, "payment": "Card",
     "items": [{"name": "Cafe Latte", "qty": 2, "price": 120}, {"name": "Matcha Latte", "qty": 1, "price": 130}]},
    {"id": 1004, "hours_ago": 77, "payment": "Cash",
     "items": [{"name": "Iced Americano", "qty": 3, "price": 110}]},
    {"id": 1005, "hours_ago": 145, "payment": "GCash",
     "items": [{"name": "Espresso", "qty": 1, "price": 90}, {"name": "Chamomile Tea", "qty": 2, "price": 90}]},
    {"id": 1006, "hours_ago": 240, "payment": "Cash",
     "items": [{"name": "Cappuccino", "qty": 2, "price": 120}, {"name": "Croissant", "qty": 2, "price": 85}]},
    {"id": 1007, "hours_ago": 480, "payment": "Card",
     "items": [{"name": "Cafe Latte", "qty": 1, "price": 120}]},
    {"id": 1008, "hours_ago": 960, "payment": "Cash",
     "items": [{"name": "Espresso", "qty": 4, "price": 90}, {"name": "Blueberry Muffin", "qty": 1, "price": 95}]},
]


def load_orders():
    """Load saved orders from disk, or seed with demo data the first time."""
    if os.path.exists(DATA_FILE):
        try:
            import json
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            orders = []
            for o in raw:
                orders.append({
                    "id": o["id"],
                    "timestamp": datetime.strptime(o["timestamp"], "%Y-%m-%d %H:%M:%S"),
                    "payment": o["payment"],
                    "items": o["items"],
                })
            return orders
        except Exception:
            pass
    now = datetime.now()
    return [
        {"id": o["id"], "timestamp": now - timedelta(hours=o["hours_ago"]),
         "payment": o["payment"], "items": o["items"]}
        for o in _DEFAULT_ORDERS
    ]


def save_orders():
    import json
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump([
                {
                    "id": o["id"],
                    "timestamp": o["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                    "payment": o["payment"],
                    "items": o["items"],
                }
                for o in ORDERS
            ], f, indent=2)
    except Exception as exc:
        print(f"Could not save sales data: {exc}")


ORDERS = load_orders()
_next_order_id = (max((o["id"] for o in ORDERS), default=1000) + 1)


def order_total(order):
    return sum(i["qty"] * i["price"] for i in order["items"])


class ReportsWindow(tk.Tk):
    def __init__(self, user="admin", role="Admin"):
        super().__init__()
        self.title("Sales History & Reports — Cafe POS & Inventory Management System")
        self.geometry("1100x680")
        self.minsize(980, 600)
        self.configure(bg=BG_COLOR)

        self.user = user
        self.role = role
        self.active_filter = "Today"
        self.filtered_orders = []

        self._setup_styles()
        self._build_header()
        self._build_toolbar()
        self._build_summary_cards()
        self._build_body()
        self._apply_filter("Today")

    # ---------------- ttk styling ----------------
    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Rep.Treeview", background=CARD_BG, fieldbackground=CARD_BG,
            foreground=TEXT_DARK, rowheight=32, borderwidth=0, font=("Segoe UI", 10),
        )
        style.configure(
            "Rep.Treeview.Heading", background=HEADER_BG, foreground="white",
            font=("Segoe UI", 10, "bold"), relief="flat",
        )
        style.map(
            "Rep.Treeview",
            background=[("selected", ACCENT)],
            foreground=[("selected", "white")],
        )

    # ---------------- Header ----------------
    def _build_header(self):
        header = tk.Frame(self, bg=HEADER_BG, height=64)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        left = tk.Frame(header, bg=HEADER_BG)
        left.pack(side="left", padx=16, pady=8)

        logo_canvas = tk.Canvas(left, width=36, height=36, bg=HEADER_BG, highlightthickness=0)
        logo_canvas.grid(row=0, column=0, rowspan=2, padx=(0, 10))
        logo_canvas.create_oval(0, 0, 36, 36, fill=ACCENT, outline="")
        logo_canvas.create_rectangle(11, 14, 23, 24, fill="white", outline="")
        logo_canvas.create_arc(20, 15, 27, 23, start=-90, extent=180, style="arc", outline="white", width=2)

        name_frame = tk.Frame(left, bg=HEADER_BG)
        name_frame.grid(row=0, column=1, sticky="w")
        tk.Label(name_frame, text="Cafe Point of Sale", font=("Segoe UI", 12, "bold"),
                  bg=HEADER_BG, fg="white", anchor="w").pack(anchor="w")
        tk.Label(name_frame, text="& Inventory Management System", font=("Segoe UI", 8),
                  bg=HEADER_BG, fg="#D8CFC3", anchor="w").pack(anchor="w")

        right = tk.Frame(header, bg=HEADER_BG)
        right.pack(side="right", padx=16)
        tk.Label(right, text=f"{self.user}  \u00b7  {self.role}", font=("Segoe UI", 9),
                  bg=HEADER_BG, fg="white").pack(side="left", padx=(0, 12))
        tk.Button(right, text="Log out", font=("Segoe UI", 9), bg=ACCENT, fg="white",
                  relief="flat", padx=10, pady=3, activebackground=ACCENT_DARK,
                  activeforeground="white", command=self.destroy).pack(side="left")

    # ---------------- Toolbar: title + filters + export ----------------
    def _build_toolbar(self):
        bar = tk.Frame(self, bg=BG_COLOR)
        bar.pack(fill="x", padx=20, pady=(16, 10))

        title_box = tk.Frame(bar, bg=BG_COLOR)
        title_box.pack(side="left")
        tk.Label(title_box, text="Sales History & Reports", font=("Segoe UI", 16, "bold"),
                  bg=BG_COLOR, fg=TEXT_DARK).pack(anchor="w")
        tk.Label(title_box, text="Filter by date range, review orders, export to CSV",
                  font=("Segoe UI", 9), bg=BG_COLOR, fg=TEXT_MUTED).pack(anchor="w")

        export_btn = tk.Button(
            bar, text="Export CSV", font=("Segoe UI", 9, "bold"), bg=ACCENT, fg="white",
            relief="flat", padx=14, pady=6, activebackground=ACCENT_DARK,
            activeforeground="white", command=self._export_csv,
        )
        export_btn.pack(side="right")

        add_btn = tk.Button(
            bar, text="+ Add sale", font=("Segoe UI", 9, "bold"), bg=CARD_BG, fg=TEXT_DARK,
            relief="flat", padx=14, pady=6, highlightbackground=BORDER, highlightthickness=1,
            activebackground=BORDER, command=self._open_add_sale_dialog,
        )
        add_btn.pack(side="right", padx=(0, 10))

        filter_bar = tk.Frame(self, bg=BG_COLOR)
        filter_bar.pack(fill="x", padx=20, pady=(0, 10))
        self.filter_buttons = {}
        for label in ("Today", "This Week", "This Month", "All Time"):
            btn = tk.Button(
                filter_bar, text=label, font=("Segoe UI", 9), relief="flat",
                padx=14, pady=6, command=lambda l=label: self._apply_filter(l),
            )
            btn.pack(side="left", padx=(0, 8))
            self.filter_buttons[label] = btn
        self._style_filter_buttons()

    def _style_filter_buttons(self):
        for label, btn in self.filter_buttons.items():
            if label == self.active_filter:
                btn.configure(bg=ACCENT, fg="white", activebackground=ACCENT_DARK)
            else:
                btn.configure(bg=CARD_BG, fg=TEXT_DARK, activebackground=BORDER)

    # ---------------- Summary cards ----------------
    def _build_summary_cards(self):
        row = tk.Frame(self, bg=BG_COLOR)
        row.pack(fill="x", padx=20, pady=(0, 12))
        row.columnconfigure((0, 1, 2), weight=1)

        self.total_sales_card = self._make_card(row, "Total sales", "PHP 0.00")
        self.total_sales_card.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.total_orders_card = self._make_card(row, "Total orders", "0")
        self.total_orders_card.grid(row=0, column=1, sticky="ew", padx=8)

        self.best_seller_card = self._make_card(row, "Best-seller", "\u2014")
        self.best_seller_card.grid(row=0, column=2, sticky="ew", padx=(8, 0))

    def _make_card(self, parent, label, value):
        card = tk.Frame(parent, bg=CARD_BG, highlightbackground=BORDER, highlightthickness=1)
        tk.Label(card, text=label, font=("Segoe UI", 9), bg=CARD_BG, fg=TEXT_MUTED
                  ).pack(anchor="w", padx=16, pady=(12, 0))
        value_label = tk.Label(card, text=value, font=("Segoe UI", 17, "bold"), bg=CARD_BG, fg=TEXT_DARK)
        value_label.pack(anchor="w", padx=16, pady=(2, 12))
        card.value_label = value_label
        return card

    # ---------------- Body: orders table (left) + item breakdown (right) ----------------
    def _build_body(self):
        body = tk.Frame(self, bg=BG_COLOR)
        body.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        # ---- Orders table ----
        table_wrap = tk.Frame(body, bg=CARD_BG, highlightbackground=BORDER, highlightthickness=1)
        table_wrap.grid(row=0, column=0, sticky="nsew", padx=(0, 16))

        columns = ("order", "date", "items", "payment", "total")
        self.tree = ttk.Treeview(
            table_wrap, columns=columns, show="headings", style="Rep.Treeview", selectmode="browse"
        )
        headings = {"order": "Order #", "date": "Date & time", "items": "Items",
                     "payment": "Payment", "total": "Total"}
        widths = {"order": 90, "date": 160, "items": 70, "payment": 100, "total": 110}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col],
                              anchor="center" if col in ("order", "items", "payment") else "w")

        scrollbar = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._on_select_order)

        # ---- Item breakdown panel ----
        detail = tk.Frame(body, bg=CARD_BG, highlightbackground=BORDER, highlightthickness=1)
        detail.grid(row=0, column=1, sticky="nsew")

        tk.Label(detail, text="Order breakdown", font=("Segoe UI", 12, "bold"),
                  bg=CARD_BG, fg=TEXT_DARK).pack(anchor="w", padx=16, pady=(16, 2))
        self.detail_subtitle = tk.Label(detail, text="Select an order to see its items.",
                                          font=("Segoe UI", 9), bg=CARD_BG, fg=TEXT_MUTED)
        self.detail_subtitle.pack(anchor="w", padx=16, pady=(0, 10))

        self.detail_items = tk.Frame(detail, bg=CARD_BG)
        self.detail_items.pack(fill="both", expand=True, padx=16)

        self.detail_total = tk.Label(detail, text="", font=("Segoe UI", 12, "bold"),
                                       bg=CARD_BG, fg=TEXT_DARK)
        self.detail_total.pack(anchor="e", padx=16, pady=16)

    def _on_select_order(self, _event=None):
        sel = self.tree.selection()
        for widget in self.detail_items.winfo_children():
            widget.destroy()

        if not sel:
            self.detail_subtitle.configure(text="Select an order to see its items.")
            self.detail_total.configure(text="")
            return

        order_id = int(sel[0])
        order = next(o for o in self.filtered_orders if o["id"] == order_id)
        self.detail_subtitle.configure(
            text=f"Order #{order['id']}  \u00b7  {order['timestamp'].strftime('%b %d, %Y %I:%M %p')}  \u00b7  {order['payment']}"
        )

        for item in order["items"]:
            row = tk.Frame(self.detail_items, bg=CARD_BG)
            row.pack(fill="x", pady=4)
            tk.Label(row, text=f"{item['qty']}x {item['name']}", font=("Segoe UI", 10),
                      bg=CARD_BG, fg=TEXT_DARK).pack(side="left")
            subtotal = item["qty"] * item["price"]
            tk.Label(row, text=f"PHP {subtotal:.2f}", font=("Segoe UI", 10),
                      bg=CARD_BG, fg=TEXT_MUTED).pack(side="right")

        self.detail_total.configure(text=f"Total: PHP {order_total(order):.2f}")

    # ---------------- Filtering ----------------
    def _apply_filter(self, label):
        self.active_filter = label
        self._style_filter_buttons()

        now = datetime.now()
        if label == "Today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif label == "This Week":
            start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        elif label == "This Month":
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:  # All Time
            start = None

        self.filtered_orders = [
            o for o in ORDERS if start is None or o["timestamp"] >= start
        ]
        self._refresh_table()
        self._refresh_summary()

    def _refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for order in sorted(self.filtered_orders, key=lambda o: o["timestamp"], reverse=True):
            item_count = sum(i["qty"] for i in order["items"])
            self.tree.insert(
                "", "end", iid=str(order["id"]),
                values=(
                    f"#{order['id']}",
                    order["timestamp"].strftime("%b %d, %Y %I:%M %p"),
                    item_count,
                    order["payment"],
                    f"PHP {order_total(order):.2f}",
                ),
            )
        self.detail_subtitle.configure(text="Select an order to see its items.")
        self.detail_total.configure(text="")
        for widget in self.detail_items.winfo_children():
            widget.destroy()

    def _refresh_summary(self):
        total_sales = sum(order_total(o) for o in self.filtered_orders)
        total_orders = len(self.filtered_orders)

        tally = {}
        for order in self.filtered_orders:
            for item in order["items"]:
                tally[item["name"]] = tally.get(item["name"], 0) + item["qty"]

        if tally:
            best_name, best_qty = max(tally.items(), key=lambda kv: kv[1])
            best_text = f"{best_name} ({best_qty} sold)"
        else:
            best_text = "\u2014"

        self.total_sales_card.value_label.configure(text=f"PHP {total_sales:.2f}")
        self.total_orders_card.value_label.configure(text=str(total_orders))
        self.best_seller_card.value_label.configure(text=best_text)

    # ---------------- Add sale ----------------
    def _open_add_sale_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Add sale")
        dialog.configure(bg=CARD_BG)
        dialog.geometry("420x560")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        tk.Label(dialog, text="Add sale", font=("Segoe UI", 13, "bold"),
                  bg=CARD_BG, fg=TEXT_DARK).pack(anchor="w", padx=24, pady=(20, 2))
        tk.Label(dialog, text="Record a transaction manually", font=("Segoe UI", 9),
                  bg=CARD_BG, fg=TEXT_MUTED).pack(anchor="w", padx=24, pady=(0, 14))

        # ---- Payment method ----
        tk.Label(dialog, text="Payment method", font=("Segoe UI", 9),
                  bg=CARD_BG, fg=TEXT_MUTED).pack(anchor="w", padx=24)
        payment_var = tk.StringVar(value="Cash")
        pay_row = tk.Frame(dialog, bg=CARD_BG)
        pay_row.pack(anchor="w", padx=24, pady=(2, 14))
        for method in ("Cash", "GCash", "Card"):
            tk.Radiobutton(pay_row, text=method, variable=payment_var, value=method,
                            bg=CARD_BG, fg=TEXT_DARK, selectcolor=CARD_BG,
                            activebackground=CARD_BG, font=("Segoe UI", 9)
                            ).pack(side="left", padx=(0, 12))

        # ---- Item entry ----
        tk.Label(dialog, text="Add items to this sale", font=("Segoe UI", 9, "bold"),
                  bg=CARD_BG, fg=TEXT_DARK).pack(anchor="w", padx=24)

        entry_row = tk.Frame(dialog, bg=CARD_BG)
        entry_row.pack(anchor="w", padx=24, pady=(6, 6))

        tk.Label(entry_row, text="Item name", font=("Segoe UI", 8), bg=CARD_BG, fg=TEXT_MUTED).grid(row=0, column=0, sticky="w")
        tk.Label(entry_row, text="Qty", font=("Segoe UI", 8), bg=CARD_BG, fg=TEXT_MUTED).grid(row=0, column=1, sticky="w", padx=(8, 0))
        tk.Label(entry_row, text="Price", font=("Segoe UI", 8), bg=CARD_BG, fg=TEXT_MUTED).grid(row=0, column=2, sticky="w", padx=(8, 0))

        name_entry = ttk.Entry(entry_row, width=16)
        name_entry.grid(row=1, column=0, ipady=3)
        qty_entry = ttk.Entry(entry_row, width=5)
        qty_entry.grid(row=1, column=1, padx=(8, 0), ipady=3)
        qty_entry.insert(0, "1")
        price_entry = ttk.Entry(entry_row, width=8)
        price_entry.grid(row=1, column=2, padx=(8, 0), ipady=3)

        pending_items = []
        items_list_frame = tk.Frame(dialog, bg=BG_COLOR, highlightbackground=BORDER, highlightthickness=1)
        items_list_frame.pack(fill="both", expand=True, padx=24, pady=(6, 6))

        running_total_label = tk.Label(dialog, text="Running total: PHP 0.00",
                                         font=("Segoe UI", 10, "bold"), bg=CARD_BG, fg=TEXT_DARK)
        running_total_label.pack(anchor="e", padx=24)

        def refresh_pending():
            for widget in items_list_frame.winfo_children():
                widget.destroy()
            if not pending_items:
                tk.Label(items_list_frame, text="No items added yet.", font=("Segoe UI", 9),
                          bg=BG_COLOR, fg=TEXT_MUTED).pack(anchor="w", padx=10, pady=8)
            total = 0
            for idx, item in enumerate(pending_items):
                row = tk.Frame(items_list_frame, bg=BG_COLOR)
                row.pack(fill="x", padx=10, pady=3)
                tk.Label(row, text=f"{item['qty']}x {item['name']}", font=("Segoe UI", 9),
                          bg=BG_COLOR, fg=TEXT_DARK).pack(side="left")
                subtotal = item["qty"] * item["price"]
                total += subtotal
                tk.Label(row, text=f"PHP {subtotal:.2f}", font=("Segoe UI", 9),
                          bg=BG_COLOR, fg=TEXT_MUTED).pack(side="right")
                tk.Button(row, text="x", font=("Segoe UI", 8), bg=BG_COLOR, fg="#B23B3B",
                           relief="flat", bd=0, command=lambda i=idx: remove_item(i)).pack(side="right", padx=6)
            running_total_label.configure(text=f"Running total: PHP {total:.2f}")

        def remove_item(index):
            pending_items.pop(index)
            refresh_pending()

        def add_item():
            name = name_entry.get().strip()
            try:
                qty = int(qty_entry.get())
                price = float(price_entry.get())
                if qty <= 0 or price < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid item", "Enter a valid name, quantity, and price.")
                return
            if not name:
                messagebox.showerror("Invalid item", "Item name is required.")
                return
            pending_items.append({"name": name, "qty": qty, "price": price})
            name_entry.delete(0, tk.END)
            qty_entry.delete(0, tk.END)
            qty_entry.insert(0, "1")
            price_entry.delete(0, tk.END)
            name_entry.focus_set()
            refresh_pending()

        tk.Button(entry_row, text="+ Add item", font=("Segoe UI", 8, "bold"), bg=ACCENT, fg="white",
                  relief="flat", padx=8, pady=3, activebackground=ACCENT_DARK,
                  activeforeground="white", command=add_item).grid(row=1, column=3, padx=(8, 0))

        refresh_pending()

        def save_sale():
            if not pending_items:
                messagebox.showwarning("No items", "Add at least one item before saving.")
                return
            global _next_order_id
            ORDERS.append({
                "id": _next_order_id,
                "timestamp": datetime.now(),
                "payment": payment_var.get(),
                "items": [dict(i) for i in pending_items],
            })
            _next_order_id += 1
            save_orders()
            self._apply_filter(self.active_filter)
            dialog.destroy()

        btn_row = tk.Frame(dialog, bg=CARD_BG)
        btn_row.pack(fill="x", padx=24, pady=(10, 20))
        tk.Button(btn_row, text="Cancel", font=("Segoe UI", 9), bg=CARD_BG, fg=TEXT_DARK,
                  relief="flat", highlightbackground=BORDER, highlightthickness=1,
                  padx=14, pady=6, command=dialog.destroy).pack(side="left")
        tk.Button(btn_row, text="Save sale", font=("Segoe UI", 9, "bold"), bg=ACCENT, fg="white",
                  relief="flat", padx=18, pady=6, activebackground=ACCENT_DARK,
                  activeforeground="white", command=save_sale).pack(side="right")

    # ---------------- CSV export ----------------
    def _export_csv(self):
        if not self.filtered_orders:
            messagebox.showwarning("Nothing to export", "There are no orders in this date range.")
            return

        default_name = f"sales_{self.active_filter.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv"
        path = filedialog.asksaveasfilename(
            title="Export sales to CSV",
            defaultextension=".csv",
            initialfile=default_name,
            filetypes=[("CSV files", "*.csv")],
        )
        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Order #", "Date & time", "Item", "Qty", "Unit price", "Line total", "Payment", "Order total"])
                for order in sorted(self.filtered_orders, key=lambda o: o["timestamp"], reverse=True):
                    total = order_total(order)
                    for item in order["items"]:
                        writer.writerow([
                            order["id"],
                            order["timestamp"].strftime("%Y-%m-%d %H:%M"),
                            item["name"],
                            item["qty"],
                            f"{item['price']:.2f}",
                            f"{item['qty'] * item['price']:.2f}",
                            order["payment"],
                            f"{total:.2f}",
                        ])
            messagebox.showinfo("Exported", f"Saved to:\n{path}")
        except Exception as exc:
            messagebox.showerror("Export failed", str(exc))


if __name__ == "__main__":
    app = ReportsWindow(user="admin", role="Admin")
    app.mainloop()
