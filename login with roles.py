"""
Login screen for Cafe Point of Sale & Inventory Management System.
Header: logo on the left, app name to its right.
"""

import tkinter as tk
from tkinter import ttk, messagebox

BG_COLOR = "#F5F1EA"
HEADER_BG = "#3C2A21"
ACCENT = "#D9822B"
CARD_BG = "#FFFFFF"
TEXT_DARK = "#2C2C2A"
TEXT_MUTED = "#5F5E5A"

# Demo credentials — replace with a real check against database.py
USERS = {
    "admin": {"password": "admin123", "role": "Admin"},
    "cashier": {"password": "cashier123", "role": "Cashier"},
}


class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cafe POS & Inventory Management System")
        self.geometry("420x520")
        self.resizable(False, False)
        self.configure(bg=BG_COLOR)

        self._build_header()
        self._build_login_card()

    # ---------- Header: logo (left) + app name (right of logo) ----------
    def _build_header(self):
        header = tk.Frame(self, bg=HEADER_BG, height=90)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        inner = tk.Frame(header, bg=HEADER_BG)
        inner.pack(expand=True)

        # Logo: a small canvas "badge" with a coffee-cup icon drawn on it.
        logo_canvas = tk.Canvas(
            inner, width=48, height=48, bg=HEADER_BG, highlightthickness=0
        )
        logo_canvas.grid(row=0, column=0, rowspan=2, padx=(0, 12))
        logo_canvas.create_oval(0, 0, 48, 48, fill=ACCENT, outline="")
        # simple cup shape
        logo_canvas.create_rectangle(14, 18, 30, 32, fill="white", outline="")
        logo_canvas.create_arc(
            26, 20, 36, 30, start=-90, extent=180, style="arc", outline="white", width=2
        )
        logo_canvas.create_line(14, 15, 30, 15, fill="white", width=2)

        # App name, split into two lines, to the right of the logo
        name_frame = tk.Frame(inner, bg=HEADER_BG)
        name_frame.grid(row=0, column=1, sticky="w")

        tk.Label(
            name_frame,
            text="Cafe Point of Sale",
            font=("Segoe UI", 14, "bold"),
            bg=HEADER_BG,
            fg="white",
            anchor="w",
        ).pack(anchor="w")

        tk.Label(
            name_frame,
            text="& Inventory Management System",
            font=("Segoe UI", 9),
            bg=HEADER_BG,
            fg="#D8CFC3",
            anchor="w",
        ).pack(anchor="w")

    # ---------- Login card ----------
    def _build_login_card(self):
        card = tk.Frame(self, bg=CARD_BG, bd=0)
        card.place(relx=0.5, rely=0.62, anchor="center", width=340, height=300)

        tk.Label(
            card, text="Sign in", font=("Segoe UI", 14, "bold"), bg=CARD_BG, fg=TEXT_DARK
        ).pack(pady=(24, 2))
        tk.Label(
            card,
            text="Enter your username and password.",
            font=("Segoe UI", 9),
            bg=CARD_BG,
            fg=TEXT_MUTED,
        ).pack(pady=(0, 18))

        tk.Label(
            card, text="Username", font=("Segoe UI", 9), bg=CARD_BG, fg=TEXT_MUTED
        ).pack(anchor="w", padx=30)
        self.username_entry = ttk.Entry(card, width=32)
        self.username_entry.pack(padx=30, pady=(2, 12))

        tk.Label(
            card, text="Password", font=("Segoe UI", 9), bg=CARD_BG, fg=TEXT_MUTED
        ).pack(anchor="w", padx=30)
        self.password_entry = ttk.Entry(card, width=32, show="*")
        self.password_entry.pack(padx=30, pady=(2, 20))

        login_btn = tk.Button(
            card,
            text="Sign in",
            font=("Segoe UI", 10, "bold"),
            bg=ACCENT,
            fg="white",
            activebackground="#C36F1E",
            activeforeground="white",
            relief="flat",
            width=28,
            pady=6,
            command=self._handle_login,
        )
        login_btn.pack(pady=(0, 6))

        self.password_entry.bind("<Return>", lambda e: self._handle_login())

    def _handle_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        user = USERS.get(username)
        if not user or user["password"] != password:
            messagebox.showerror("Login failed", "Incorrect username or password.")
            return

        messagebox.showinfo(
            "Welcome", f"Logged in as {username} ({user['role']})"
        )
        # TODO: open the main app window / dashboard here, passing user['role']


if __name__ == "__main__":
    app = LoginWindow()
    app.mainloop()
