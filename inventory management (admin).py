"""
Inventory Management screen (Admin) for
Cafe Point of Sale & Inventory Management System.

Same color palette as login_window.py / pos_window.py, now with
product photos: pick an image when adding/editing a product, see a
thumbnail in the table and a preview in the form.

Requires Pillow for image resizing:
    pip install pillow
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# ---- Shared palette (matches login_window.py / pos_window.py) ----
BG_COLOR = "#F5F1EA"
HEADER_BG = "#3C2A21"
ACCENT = "#D9822B"
ACCENT_DARK = "#C36F1E"
CARD_BG = "#FFFFFF"
TEXT_DARK = "#2C2C2A"
TEXT_MUTED = "#5F5E5A"
BORDER = "#E3DCCF"
DANGER = "#B23B3B"

LOW_STOCK_THRESHOLD = 5
THUMB_SIZE = (36, 36)      # shown in the table
PREVIEW_SIZE = (140, 140)  # shown in the add/edit form

# ---- Demo data — replace with real reads/writes via database.py ----
# "image" holds a file path on disk, or None if no photo was set yet.
PRODUCTS = [
    {"id": 1, "name": "Espresso", "category": "Coffee", "price": 90, "stock": 32, "active": True, "image": None},
    {"id": 2, "name": "Cappuccino", "category": "Coffee", "price": 120, "stock": 20, "active": True, "image": None},
    {"id": 3, "name": "Cafe Latte", "category": "Coffee", "price": 120, "stock": 18, "active": True, "image": None},
    {"id": 4, "name": "Iced Americano", "category": "Coffee", "price": 110, "stock": 25, "active": True, "image": None},
    {"id": 5, "name": "Matcha Latte", "category": "Tea", "price": 130, "stock": 4, "active": True, "image": None},
    {"id": 6, "name": "Chamomile Tea", "category": "Tea", "price": 90, "stock": 15, "active": True, "image": None},
    {"id": 7, "name": "Croissant", "category": "Pastry", "price": 85, "stock": 10, "active": True, "image": None},
    {"id": 8, "name": "Blueberry Muffin", "category": "Pastry", "price": 95, "stock": 0, "active": True, "image": None},
]
RESTOCK_LOG = []
_next_id = max(p["id"] for p in PRODUCTS) + 1


class InventoryWindow(tk.Tk):
    def __init__(self, user="admin", role="Admin"):
        super().__init__()
        self.title("Inventory Management — Cafe POS & Inventory Management System")
        self.geometry("1080x660")
        self.minsize(960, 580)
        self.configure(bg=BG_COLOR)

        self.user = user
        self.role = role
        self.selected_id = None

        # Keep references to PhotoImage objects — tkinter drops images
        # that have no live Python reference, even mid-display.
        self._thumb_cache = {}

        if not PIL_AVAILABLE:
            self.after(300, lambda: messagebox.showwarning(
                "Pillow not installed",
                "Product photos need the Pillow library.\n\n"
                "Install it with:\n    pip install pillow\n\n"
                "The screen will still work, but images won't load until then.",
            ))

        self._setup_styles()
        self._build_header()
        self._build_toolbar()
        self._build_table()
        self._build_statusbar()
        self._refresh_table()

    # ---------------- ttk styling ----------------
    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Inv.Treeview", background=CARD_BG, fieldbackground=CARD_BG,
            foreground=TEXT_DARK, rowheight=44, borderwidth=0, font=("Segoe UI", 10),
        )
        style.configure(
            "Inv.Treeview.Heading", background=HEADER_BG, foreground="white",
            font=("Segoe UI", 10, "bold"), relief="flat",
        )
        style.map(
            "Inv.Treeview",
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

    # ---------------- Toolbar ----------------
    def _build_toolbar(self):
        bar = tk.Frame(self, bg=BG_COLOR)
        bar.pack(fill="x", padx=20, pady=(16, 8))

        title_box = tk.Frame(bar, bg=BG_COLOR)
        title_box.pack(side="left")
        tk.Label(title_box, text="Inventory", font=("Segoe UI", 16, "bold"),
                  bg=BG_COLOR, fg=TEXT_DARK).pack(anchor="w")
        tk.Label(title_box, text="Manage products, photos, and stock levels",
                  font=("Segoe UI", 9), bg=BG_COLOR, fg=TEXT_MUTED).pack(anchor="w")

        actions = tk.Frame(bar, bg=BG_COLOR)
        actions.pack(side="right")

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self._refresh_table())
        search_entry = ttk.Entry(actions, textvariable=self.search_var, width=22)
        search_entry.pack(side="left", padx=(0, 10), ipady=3)
        self._add_placeholder(search_entry, "Search products\u2026")

        self._make_button(actions, "+ Add product", self._open_add_dialog, primary=True).pack(side="left", padx=(0, 8))
        self._make_button(actions, "Edit", self._open_edit_dialog).pack(side="left", padx=(0, 8))
        self._make_button(actions, "Restock", self._open_restock_dialog).pack(side="left", padx=(0, 8))
        self._make_button(actions, "Delete", self._soft_delete, danger=True).pack(side="left")

    def _make_button(self, parent, text, command, primary=False, danger=False):
        if danger:
            bg, active, fg = "#FBEAEA", "#F3D3D3", DANGER
        elif primary:
            bg, active, fg = ACCENT, ACCENT_DARK, "white"
        else:
            bg, active, fg = CARD_BG, BORDER, TEXT_DARK
        return tk.Button(
            parent, text=text, font=("Segoe UI", 9, "bold" if primary else "normal"),
            bg=bg, fg=fg, relief="flat", padx=14, pady=6,
            activebackground=active, activeforeground=fg,
            highlightbackground=BORDER, highlightthickness=0 if primary or danger else 1,
            command=command,
        )

    @staticmethod
    def _add_placeholder(entry, text):
        entry.insert(0, text)
        entry.configure(foreground=TEXT_MUTED)

        def on_focus_in(_):
            if entry.get() == text:
                entry.delete(0, tk.END)
                entry.configure(foreground=TEXT_DARK)

        def on_focus_out(_):
            if not entry.get():
                entry.insert(0, text)
                entry.configure(foreground=TEXT_MUTED)

        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

    # ---------------- Image helpers ----------------
    def _make_placeholder(self, size):
        w, h = size
        img = tk.PhotoImage(width=w, height=h)
        img.put(BORDER, to=(0, 0, w, h))
        return img

    def _load_thumb(self, path, size):
        """Load + resize an image file. Falls back to a placeholder if
        Pillow isn't installed, no path is set, or the file fails to load."""
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

    # ---------------- Table ----------------
    def _build_table(self):
        wrap = tk.Frame(self, bg=CARD_BG, highlightbackground=BORDER, highlightthickness=1)
        wrap.pack(fill="both", expand=True, padx=20, pady=(0, 8))

        columns = ("name", "category", "price", "stock", "status")
        # show="tree headings" so column #0 can hold the product photo
        self.tree = ttk.Treeview(
            wrap, columns=columns, show="tree headings",
            style="Inv.Treeview", selectmode="browse",
        )
        self.tree.heading("#0", text="Photo")
        self.tree.column("#0", width=64, anchor="center", stretch=False)

        headings = {"name": "Product", "category": "Category", "price": "Price",
                     "stock": "Stock", "status": "Status"}
        widths = {"name": 240, "category": 130, "price": 90, "stock": 90, "status": 150}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col],
                              anchor="w" if col in ("name", "category", "status") else "center")

        self.tree.tag_configure("out", foreground=DANGER)
        self.tree.tag_configure("low", foreground=ACCENT_DARK)
        self.tree.tag_configure("ok", foreground=TEXT_DARK)

        scrollbar = ttk.Scrollbar(wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", lambda e: self._open_edit_dialog())

    def _on_select(self, _event=None):
        sel = self.tree.selection()
        self.selected_id = int(sel[0]) if sel else None

    # ---------------- Status bar ----------------
    def _build_statusbar(self):
        bar = tk.Frame(self, bg=BG_COLOR)
        bar.pack(fill="x", padx=20, pady=(0, 16))
        self.status_label = tk.Label(bar, text="", font=("Segoe UI", 9), bg=BG_COLOR, fg=TEXT_MUTED)
        self.status_label.pack(side="left")

    # ---------------- Data refresh ----------------
    def _refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        self._thumb_cache.clear()  # drop old PhotoImage refs for removed rows

        query = self.search_var.get().strip().lower()
        if query == "search products\u2026":
            query = ""

        visible = [p for p in PRODUCTS if p["active"] and query in p["name"].lower()]
        low, out = 0, 0
        for p in sorted(visible, key=lambda x: x["name"]):
            if p["stock"] <= 0:
                status, tag = "Out of stock", "out"
                out += 1
            elif p["stock"] <= LOW_STOCK_THRESHOLD:
                status, tag = "Low stock", "low"
                low += 1
            else:
                status, tag = "In stock", "ok"

            thumb = self._load_thumb(p.get("image"), THUMB_SIZE)
            self._thumb_cache[p["id"]] = thumb  # keep alive

            self.tree.insert(
                "", "end", iid=str(p["id"]), tags=(tag,), image=thumb,
                values=(p["name"], p["category"], f"PHP {p['price']:.2f}", p["stock"], status),
            )

        self.status_label.configure(
            text=f"{len(visible)} product(s)   \u00b7   {low} low stock   \u00b7   {out} out of stock"
        )

    def _get_selected_product(self):
        if self.selected_id is None:
            messagebox.showwarning("No selection", "Select a product from the table first.")
            return None
        return next((p for p in PRODUCTS if p["id"] == self.selected_id), None)

    # ---------------- Add / Edit dialog ----------------
    def _open_add_dialog(self):
        self._product_form_dialog(title="Add product")

    def _open_edit_dialog(self):
        product = self._get_selected_product()
        if product:
            self._product_form_dialog(title="Edit product", product=product)

    def _product_form_dialog(self, title, product=None):
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.configure(bg=CARD_BG)
        dialog.geometry("560x430")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        tk.Label(dialog, text=title, font=("Segoe UI", 13, "bold"),
                  bg=CARD_BG, fg=TEXT_DARK).pack(anchor="w", padx=24, pady=(20, 4))
        tk.Label(dialog, text="Product details", font=("Segoe UI", 9),
                  bg=CARD_BG, fg=TEXT_MUTED).pack(anchor="w", padx=24, pady=(0, 12))

        body = tk.Frame(dialog, bg=CARD_BG)
        body.pack(fill="both", expand=True, padx=24)

        # ---- Left: photo picker ----
        photo_col = tk.Frame(body, bg=CARD_BG)
        photo_col.pack(side="left", padx=(0, 24))

        current_image_path = {"path": product.get("image") if product else None}
        preview_label = tk.Label(
            photo_col, bg=BG_COLOR, width=PREVIEW_SIZE[0], height=PREVIEW_SIZE[1],
            highlightbackground=BORDER, highlightthickness=1,
        )
        preview_label.pack()

        def refresh_preview():
            img = self._load_thumb(current_image_path["path"], PREVIEW_SIZE)
            preview_label.configure(image=img)
            preview_label.image = img  # keep reference

        refresh_preview()

        def choose_image():
            path = filedialog.askopenfilename(
                title="Choose product photo",
                filetypes=[("Image files", "*.png *.jpg *.jpeg *.webp *.gif *.bmp")],
            )
            if path:
                current_image_path["path"] = path
                refresh_preview()

        def clear_image():
            current_image_path["path"] = None
            refresh_preview()

        btns = tk.Frame(photo_col, bg=CARD_BG)
        btns.pack(pady=(8, 0))
        tk.Button(btns, text="Choose image\u2026", font=("Segoe UI", 8), bg=ACCENT, fg="white",
                  relief="flat", padx=8, pady=4, activebackground=ACCENT_DARK,
                  activeforeground="white", command=choose_image).pack(side="left", padx=(0, 6))
        tk.Button(btns, text="Clear", font=("Segoe UI", 8), bg=CARD_BG, fg=TEXT_MUTED,
                  relief="flat", highlightbackground=BORDER, highlightthickness=1,
                  padx=8, pady=4, command=clear_image).pack(side="left")

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

        name_entry = labeled_entry("Name", product["name"] if product else "")
        category_entry = labeled_entry("Category", product["category"] if product else "")
        price_entry = labeled_entry("Price (PHP)", str(product["price"]) if product else "")
        stock_entry = labeled_entry("Starting stock", str(product["stock"]) if product else "0")
        if product:
            stock_entry.configure(state="disabled")
            tk.Label(form_col, text="Use \u201cRestock\u201d to change stock.", font=("Segoe UI", 8),
                      bg=CARD_BG, fg=TEXT_MUTED).pack(anchor="w")

        def save():
            name = name_entry.get().strip()
            category = category_entry.get().strip()
            try:
                price = float(price_entry.get())
                stock = int(stock_entry.get()) if not product else product["stock"]
            except ValueError:
                messagebox.showerror("Invalid input", "Price and stock must be numbers.")
                return
            if not name or not category:
                messagebox.showerror("Invalid input", "Name and category are required.")
                return

            global _next_id
            if product:
                product.update(name=name, category=category, price=price,
                                image=current_image_path["path"])
            else:
                PRODUCTS.append({
                    "id": _next_id, "name": name, "category": category, "price": price,
                    "stock": stock, "active": True, "image": current_image_path["path"],
                })
                _next_id += 1

            self._refresh_table()
            dialog.destroy()

        btn_row = tk.Frame(dialog, bg=CARD_BG)
        btn_row.pack(fill="x", padx=24, pady=(14, 20))
        tk.Button(btn_row, text="Cancel", font=("Segoe UI", 9), bg=CARD_BG, fg=TEXT_DARK,
                  relief="flat", highlightbackground=BORDER, highlightthickness=1,
                  padx=14, pady=6, command=dialog.destroy).pack(side="left")
        tk.Button(btn_row, text="Save", font=("Segoe UI", 9, "bold"), bg=ACCENT, fg="white",
                  relief="flat", padx=18, pady=6, activebackground=ACCENT_DARK,
                  activeforeground="white", command=save).pack(side="right")

    # ---------------- Restock ----------------
    def _open_restock_dialog(self):
        product = self._get_selected_product()
        if not product:
            return

        dialog = tk.Toplevel(self)
        dialog.title("Restock product")
        dialog.configure(bg=CARD_BG)
        dialog.geometry("320x260")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        tk.Label(dialog, text="Restock", font=("Segoe UI", 13, "bold"),
                  bg=CARD_BG, fg=TEXT_DARK).pack(anchor="w", padx=24, pady=(20, 2))
        tk.Label(dialog, text=product["name"], font=("Segoe UI", 10),
                  bg=CARD_BG, fg=TEXT_MUTED).pack(anchor="w", padx=24, pady=(0, 16))
        tk.Label(dialog, text=f"Current stock: {product['stock']}", font=("Segoe UI", 9),
                  bg=CARD_BG, fg=TEXT_MUTED).pack(anchor="w", padx=24)

        tk.Label(dialog, text="Quantity to add", font=("Segoe UI", 9),
                  bg=CARD_BG, fg=TEXT_MUTED).pack(anchor="w", padx=24, pady=(10, 2))
        qty_entry = ttk.Entry(dialog, width=20)
        qty_entry.pack(padx=24, ipady=3)
        qty_entry.focus_set()

        def save():
            try:
                qty = int(qty_entry.get())
                if qty <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid input", "Enter a whole number greater than 0.")
                return

            product["stock"] += qty
            RESTOCK_LOG.append({
                "product": product["name"], "qty": qty,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            })
            self._refresh_table()
            messagebox.showinfo("Restocked", f"Added {qty} to {product['name']}.\nNew stock: {product['stock']}")
            dialog.destroy()

        btn_row = tk.Frame(dialog, bg=CARD_BG)
        btn_row.pack(fill="x", padx=24, pady=(20, 0))
        tk.Button(btn_row, text="Cancel", font=("Segoe UI", 9), bg=CARD_BG, fg=TEXT_DARK,
                  relief="flat", highlightbackground=BORDER, highlightthickness=1,
                  padx=14, pady=6, command=dialog.destroy).pack(side="left")
        tk.Button(btn_row, text="Confirm restock", font=("Segoe UI", 9, "bold"), bg=ACCENT,
                  fg="white", relief="flat", padx=14, pady=6, activebackground=ACCENT_DARK,
                  activeforeground="white", command=save).pack(side="right")

    # ---------------- Soft-delete ----------------
    def _soft_delete(self):
        product = self._get_selected_product()
        if not product:
            return
        confirm = messagebox.askyesno(
            "Remove product",
            f"Remove \u201c{product['name']}\u201d from the active menu?\n"
            "It will be hidden from the list but kept in records.",
        )
        if confirm:
            product["active"] = False
            self.selected_id = None
            self._refresh_table()


if __name__ == "__main__":
    app = InventoryWindow(user="admin", role="Admin")
    app.mainloop()
