"""
Point of Sale screen for Cafe Point of Sale & Inventory Management System.
Same color palette as the login screen: search + category browsing on the
left, cart + checkout on the right.

Now with:
- Product photos (thumbnails on each product card)
- "+ Add product" right from the POS screen
- Shares the same data file as inventory_window.py (inventory_data.json)
  so products, stock, and photos stay in sync between the two screens.

Requires Pillow for image resizing:
    pip install pillow
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# ---- Shared palette (matches login_window.py / inventory_window.py) ----
BG_COLOR = "#F5F1EA"
HEADER_BG = "#3C2A21"
ACCENT = "#D9822B"
ACCENT_DARK = "#C36F1E"
CARD_BG = "#FFFFFF"
TEXT_DARK = "#2C2C2A"
TEXT_MUTED = "#5F5E5A"
BORDER = "#E3DCCF"
DANGER = "#B23B3B"

CARD_THUMB_SIZE = (110, 90)   # product photo on each grid card
PREVIEW_SIZE = (140, 140)     # photo preview in the add-product form

# ---- Shared persistence with inventory_window.py ----
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(APP_DIR, "inventory_data.json")
IMAGES_DIR = os.path.join(APP_DIR, "product_images")

_DEFAULT_PRODUCTS = [
    {"id": 1, "name": "Espresso", "category": "Coffee", "price": 90, "stock": 32, "active": True, "image": None},
    {"id": 2, "name": "Cappuccino", "category": "Coffee", "price": 120, "stock": 20, "active": True, "image": None},
    {"id": 3, "name": "Cafe Latte", "category": "Coffee", "price": 120, "stock": 18, "active": True, "image": None},
    {"id": 4, "name": "Iced Americano", "category": "Coffee", "price": 110, "stock": 25, "active": True, "image": None},
    {"id": 5, "name": "Matcha Latte", "category": "Tea", "price": 130, "stock": 4, "active": True, "image": None},
    {"id": 6, "name": "Chamomile Tea", "category": "Tea", "price": 90, "stock": 15, "active": True, "image": None},
    {"id": 7, "name": "Croissant", "category": "Pastry", "price": 85, "stock": 10, "active": True, "image": None},
    {"id": 8, "name": "Blueberry Muffin", "category": "Pastry", "price": 95, "stock": 0, "active": True, "image": None},
]


def load_products():
    if os.path.exists(DATA_FILE):
        try:
            import json
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("products", [])
        except Exception:
            pass
    return [dict(p) for p in _DEFAULT_PRODUCTS]


def save_products():
    import json
    os.makedirs(IMAGES_DIR, exist_ok=True)
    try:
        # Preserve any restock_log already in the file (written by
        # inventory_window.py) instead of clobbering it.
        existing_log = []
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    existing_log = json.load(f).get("restock_log", [])
            except Exception:
                pass
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"products": PRODUCTS, "restock_log": existing_log}, f, indent=2)
    except Exception as exc:
        print(f"Could not save product data: {exc}")


def import_image(source_path):
    """Copy a chosen photo into product_images/ so it keeps working even
    if the original file is moved."""
    if not source_path:
        return None
    import shutil, uuid
    os.makedirs(IMAGES_DIR, exist_ok=True)
    ext = os.path.splitext(source_path)[1]
    dest_path = os.path.join(IMAGES_DIR, f"{uuid.uuid4().hex}{ext}")
    try:
        shutil.copy2(source_path, dest_path)
        return dest_path
    except Exception:
        return source_path


PRODUCTS = load_products()
_next_id = (max((p["id"] for p in PRODUCTS), default=0) + 1)


class POSWindow(tk.Tk):
    def __init__(self, user="admin", role="Admin"):
        super().__init__()
        self.title("Cafe POS & Inventory Management System")
        self.geometry("1020x640")
        self.minsize(920, 580)
        self.configure(bg=BG_COLOR)

        self.user = user
        self.role = role
        self.cart = []  # list of dicts: name, price, qty
        self.active_category = "All"
        self.payment_var = tk.StringVar(value="Cash")
        self._thumb_cache = {}  # keep PhotoImage refs alive

        self._build_header()
        self._build_body()
        self._refresh_products()
        self._refresh_cart()

    # ---------------- Image helpers ----------------
    def _make_placeholder(self, size):
        w, h = size
        img = tk.PhotoImage(width=w, height=h)
        img.put(BORDER, to=(0, 0, w, h))
        return img

    def _load_thumb(self, path, size):
        if not path or not PIL_AVAILABLE or not os.path.exists(path):
            return self._make_placeholder(size)
        try:
            with Image.open(path) as im:
                im = im.convert("RGB")
                im.thumbnail(size)
                canvas = Image.new("RGB", size, "#FFFFFF")
                offset = ((size[0] - im.width) // 2, (size[1] - im.height) // 2)
                canvas.paste(im, offset)
                return ImageTk.PhotoImage(canvas)
        except Exception:
            return self._make_placeholder(size)

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
                  activeforeground="white", command=self._logout).pack(side="left")

    # ---------------- Body: products (left) + cart (right) ----------------
    def _build_body(self):
        body = tk.Frame(self, bg=BG_COLOR)
        body.pack(fill="both", expand=True, padx=16, pady=16)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        # ---- Left: search, categories, product grid ----
        left = tk.Frame(body, bg=BG_COLOR)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 16))

        top_row = tk.Frame(left, bg=BG_COLOR)
        top_row.pack(fill="x", pady=(0, 10))

        search_frame = tk.Frame(top_row, bg=BG_COLOR)
        search_frame.pack(side="left", fill="x", expand=True)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self._refresh_products())
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(fill="x", ipady=4)
        tk.Label(search_frame, text="Search products", font=("Segoe UI", 8),
                  bg=BG_COLOR, fg=TEXT_MUTED).pack(anchor="w", pady=(2, 0))

        if self.role == "Admin":
            tk.Button(
                top_row, text="+ Add product", font=("Segoe UI", 9, "bold"), bg=ACCENT, fg="white",
                relief="flat", padx=12, pady=6, activebackground=ACCENT_DARK,
                activeforeground="white", command=self._open_add_product_dialog,
            ).pack(side="left", padx=(10, 0))

        cat_frame = tk.Frame(left, bg=BG_COLOR)
        cat_frame.pack(fill="x", pady=(6, 10))
        self.cat_frame = cat_frame
        self.cat_buttons = {}
        self._rebuild_category_buttons()

        # Scrollable product grid
        grid_container = tk.Frame(left, bg=CARD_BG, bd=0, highlightbackground=BORDER,
                                    highlightthickness=1)
        grid_container.pack(fill="both", expand=True)
        canvas = tk.Canvas(grid_container, bg=CARD_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(grid_container, orient="vertical", command=canvas.yview)
        self.product_grid = tk.Frame(canvas, bg=CARD_BG)
        self.product_grid.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.product_grid, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # ---- Right: cart + checkout ----
        right = tk.Frame(body, bg=CARD_BG, highlightbackground=BORDER, highlightthickness=1)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        tk.Label(right, text="Current order", font=("Segoe UI", 12, "bold"),
                  bg=CARD_BG, fg=TEXT_DARK).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 8))

        self.cart_list = tk.Frame(right, bg=CARD_BG)
        self.cart_list.grid(row=1, column=0, sticky="nsew", padx=16)

        bottom = tk.Frame(right, bg=CARD_BG)
        bottom.grid(row=2, column=0, sticky="ew", padx=16, pady=12)

        self.total_label = tk.Label(bottom, text="Total: PHP 0.00", font=("Segoe UI", 13, "bold"),
                                      bg=CARD_BG, fg=TEXT_DARK)
        self.total_label.pack(anchor="w", pady=(0, 10))

        tk.Label(bottom, text="Payment method", font=("Segoe UI", 9),
                  bg=CARD_BG, fg=TEXT_MUTED).pack(anchor="w")
        pay_frame = tk.Frame(bottom, bg=CARD_BG)
        pay_frame.pack(fill="x", pady=(4, 12))
        for method in ("Cash", "GCash", "Card"):
            tk.Radiobutton(
                pay_frame, text=method, variable=self.payment_var, value=method,
                bg=CARD_BG, fg=TEXT_DARK, selectcolor=CARD_BG,
                activebackground=CARD_BG, font=("Segoe UI", 9),
            ).pack(side="left", padx=(0, 12))

        tk.Button(
            bottom, text="Checkout", font=("Segoe UI", 10, "bold"), bg=ACCENT, fg="white",
            relief="flat", pady=8, activebackground=ACCENT_DARK, activeforeground="white",
            command=self._checkout,
        ).pack(fill="x")

    # ---------------- Category buttons ----------------
    def _rebuild_category_buttons(self):
        for widget in self.cat_frame.winfo_children():
            widget.destroy()
        self.cat_buttons = {}
        categories = ["All"] + sorted({p["category"] for p in PRODUCTS if p.get("active", True)})
        for cat in categories:
            btn = tk.Button(
                self.cat_frame, text=cat, font=("Segoe UI", 9), relief="flat",
                padx=12, pady=5, command=lambda c=cat: self._select_category(c),
            )
            btn.pack(side="left", padx=(0, 6))
            self.cat_buttons[cat] = btn
        if self.active_category not in self.cat_buttons:
            self.active_category = "All"
        self._style_category_buttons()

    def _style_category_buttons(self):
        for cat, btn in self.cat_buttons.items():
            if cat == self.active_category:
                btn.configure(bg=ACCENT, fg="white", activebackground=ACCENT_DARK)
            else:
                btn.configure(bg=BG_COLOR, fg=TEXT_DARK, activebackground=BORDER)

    def _select_category(self, cat):
        self.active_category = cat
        self._style_category_buttons()
        self._refresh_products()

    # ---------------- Product grid ----------------
    def _refresh_products(self):
        for widget in self.product_grid.winfo_children():
            widget.destroy()
        self._thumb_cache.clear()

        query = self.search_var.get().strip().lower()
        items = [
            p for p in PRODUCTS
            if p.get("active", True)
            and (self.active_category == "All" or p["category"] == self.active_category)
            and query in p["name"].lower()
        ]

        cols = 3
        for i, p in enumerate(items):
            row, col = divmod(i, cols)
            card = tk.Frame(self.product_grid, bg=BG_COLOR, width=160, height=190,
                              highlightbackground=BORDER, highlightthickness=1)
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
            card.grid_propagate(False)

            thumb = self._load_thumb(p.get("image"), CARD_THUMB_SIZE)
            self._thumb_cache[p["id"]] = thumb
            tk.Label(card, image=thumb, bg=BG_COLOR).pack(pady=(8, 4))

            tk.Label(card, text=p["name"], font=("Segoe UI", 10, "bold"),
                      bg=BG_COLOR, fg=TEXT_DARK, wraplength=140).pack()
            tk.Label(card, text=f"PHP {p['price']:.2f}", font=("Segoe UI", 9),
                      bg=BG_COLOR, fg=TEXT_MUTED).pack()

            if p["stock"] <= 0:
                tk.Label(card, text="Out of stock", font=("Segoe UI", 8),
                          bg=BG_COLOR, fg=DANGER).pack(pady=(4, 0))
            else:
                if p["stock"] <= 5:
                    tk.Label(card, text=f"Low stock ({p['stock']})", font=("Segoe UI", 8),
                              bg=BG_COLOR, fg=ACCENT_DARK).pack(pady=(2, 0))
                tk.Button(
                    card, text="Add to cart", font=("Segoe UI", 8), bg=ACCENT, fg="white",
                    relief="flat", command=lambda prod=p: self._add_to_cart(prod),
                ).pack(pady=(4, 0))

    # ---------------- Add product (from POS) ----------------
    def _open_add_product_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Add product")
        dialog.configure(bg=CARD_BG)
        dialog.geometry("560x430")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        tk.Label(dialog, text="Add product", font=("Segoe UI", 13, "bold"),
                  bg=CARD_BG, fg=TEXT_DARK).pack(anchor="w", padx=24, pady=(20, 4))
        tk.Label(dialog, text="Add a new item to the menu", font=("Segoe UI", 9),
                  bg=CARD_BG, fg=TEXT_MUTED).pack(anchor="w", padx=24, pady=(0, 12))

        body = tk.Frame(dialog, bg=CARD_BG)
        body.pack(fill="both", expand=True, padx=24)

        # ---- Left: photo picker ----
        photo_col = tk.Frame(body, bg=CARD_BG)
        photo_col.pack(side="left", padx=(0, 24))

        chosen_image = {"path": None}
        preview_label = tk.Label(
            photo_col, bg=BG_COLOR, width=PREVIEW_SIZE[0], height=PREVIEW_SIZE[1],
            highlightbackground=BORDER, highlightthickness=1,
        )
        preview_label.pack()

        def refresh_preview():
            img = self._load_thumb(chosen_image["path"], PREVIEW_SIZE)
            preview_label.configure(image=img)
            preview_label.image = img

        refresh_preview()

        def choose_image():
            path = filedialog.askopenfilename(
                title="Choose product photo",
                filetypes=[("Image files", "*.png *.jpg *.jpeg *.webp *.gif *.bmp")],
            )
            if path:
                chosen_image["path"] = path
                refresh_preview()

        btns = tk.Frame(photo_col, bg=CARD_BG)
        btns.pack(pady=(8, 0))
        tk.Button(btns, text="Choose image\u2026", font=("Segoe UI", 8), bg=ACCENT, fg="white",
                  relief="flat", padx=8, pady=4, activebackground=ACCENT_DARK,
                  activeforeground="white", command=choose_image).pack(side="left", padx=(0, 6))
        tk.Button(btns, text="Clear", font=("Segoe UI", 8), bg=CARD_BG, fg=TEXT_MUTED,
                  relief="flat", highlightbackground=BORDER, highlightthickness=1,
                  padx=8, pady=4, command=lambda: (chosen_image.update(path=None), refresh_preview())
                  ).pack(side="left")

        if not PIL_AVAILABLE:
            tk.Label(photo_col, text="Install Pillow to preview photos\n(pip install pillow)",
                      font=("Segoe UI", 7), bg=CARD_BG, fg=DANGER, justify="left").pack(pady=(6, 0))

        # ---- Right: fields ----
        form_col = tk.Frame(body, bg=CARD_BG)
        form_col.pack(side="left", fill="both", expand=True)

        def labeled_entry(label_text, initial=""):
            tk.Label(form_col, text=label_text, font=("Segoe UI", 9),
                      bg=CARD_BG, fg=TEXT_MUTED).pack(anchor="w")
            entry = ttk.Entry(form_col, width=30)
            entry.pack(anchor="w", pady=(2, 12), ipady=3)
            entry.insert(0, initial)
            return entry

        name_entry = labeled_entry("Name")
        category_entry = labeled_entry("Category")
        price_entry = labeled_entry("Price (PHP)")
        stock_entry = labeled_entry("Starting stock", "0")

        def save():
            name = name_entry.get().strip()
            category = category_entry.get().strip()
            try:
                price = float(price_entry.get())
                stock = int(stock_entry.get())
            except ValueError:
                messagebox.showerror("Invalid input", "Price and stock must be numbers.")
                return
            if not name or not category:
                messagebox.showerror("Invalid input", "Name and category are required.")
                return

            global _next_id
            stored_image = import_image(chosen_image["path"]) if chosen_image["path"] else None
            PRODUCTS.append({
                "id": _next_id, "name": name, "category": category, "price": price,
                "stock": stock, "active": True, "image": stored_image,
            })
            _next_id += 1
            save_products()
            self._rebuild_category_buttons()
            self._refresh_products()
            dialog.destroy()

        btn_row = tk.Frame(dialog, bg=CARD_BG)
        btn_row.pack(fill="x", padx=24, pady=(14, 20))
        tk.Button(btn_row, text="Cancel", font=("Segoe UI", 9), bg=CARD_BG, fg=TEXT_DARK,
                  relief="flat", highlightbackground=BORDER, highlightthickness=1,
                  padx=14, pady=6, command=dialog.destroy).pack(side="left")
        tk.Button(btn_row, text="Save product", font=("Segoe UI", 9, "bold"), bg=ACCENT, fg="white",
                  relief="flat", padx=18, pady=6, activebackground=ACCENT_DARK,
                  activeforeground="white", command=save).pack(side="right")

    # ---------------- Cart logic ----------------
    def _add_to_cart(self, product):
        for line in self.cart:
            if line["name"] == product["name"]:
                line["qty"] += 1
                self._refresh_cart()
                return
        self.cart.append({"name": product["name"], "price": product["price"], "qty": 1})
        self._refresh_cart()

    def _remove_from_cart(self, name):
        self.cart = [line for line in self.cart if line["name"] != name]
        self._refresh_cart()

    def _refresh_cart(self):
        for widget in self.cart_list.winfo_children():
            widget.destroy()

        if not self.cart:
            tk.Label(self.cart_list, text="No items yet.", font=("Segoe UI", 9),
                      bg=CARD_BG, fg=TEXT_MUTED).pack(anchor="w", pady=8)

        total = 0
        for line in self.cart:
            row = tk.Frame(self.cart_list, bg=CARD_BG)
            row.pack(fill="x", pady=4)
            tk.Label(row, text=f"{line['qty']}x {line['name']}", font=("Segoe UI", 9),
                      bg=CARD_BG, fg=TEXT_DARK).pack(side="left")
            subtotal = line["price"] * line["qty"]
            total += subtotal
            tk.Label(row, text=f"PHP {subtotal:.2f}", font=("Segoe UI", 9),
                      bg=CARD_BG, fg=TEXT_MUTED).pack(side="right")
            tk.Button(row, text="x", font=("Segoe UI", 8), bg=CARD_BG, fg=DANGER,
                       relief="flat", bd=0, command=lambda n=line["name"]: self._remove_from_cart(n)
                       ).pack(side="right", padx=6)

        self.total_label.configure(text=f"Total: PHP {total:.2f}")

    def _checkout(self):
        if not self.cart:
            messagebox.showwarning("Empty cart", "Add at least one item before checking out.")
            return
        total = sum(line["price"] * line["qty"] for line in self.cart)
        method = self.payment_var.get()

        # Deduct stock for each item sold
        for line in self.cart:
            product = next((p for p in PRODUCTS if p["name"] == line["name"]), None)
            if product:
                product["stock"] = max(0, product["stock"] - line["qty"])
        save_products()

        messagebox.showinfo(
            "Order complete",
            f"Paid PHP {total:.2f} via {method}.\nReceipt and sales record would be saved here.",
        )
        self.cart = []
        self._refresh_cart()
        self._refresh_products()

    def _logout(self):
        self.destroy()


if __name__ == "__main__":
    print("Bago mag-open ang window...")
    app = POSWindow(user="admin", role="Admin")
    print("Nagawa na ang window object, tatakbo na ang mainloop...")
    app.mainloop()
    print("Nag-close na ang window.")
