"""
Staff Management screen (Admin) for
Cafe Point of Sale & Inventory Management System.

Same color palette as login_window.py / pos_window.py / inventory_window.py /
reports_window.py.

Features:
- Create cashier / admin accounts
- Reset a staff member's password
- Deactivate / reactivate accounts (soft-delete — account is kept, just
  blocked from logging in)
"""

import os
import hashlib
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

# ---- Shared palette (matches the rest of the app) ----
BG_COLOR = "#F5F1EA"
HEADER_BG = "#3C2A21"
ACCENT = "#D9822B"
ACCENT_DARK = "#C36F1E"
CARD_BG = "#FFFFFF"
TEXT_DARK = "#2C2C2A"
TEXT_MUTED = "#5F5E5A"
BORDER = "#E3DCCF"
DANGER = "#B23B3B"
SUCCESS = "#4E8C5C"

# ---- Persistence ----
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(APP_DIR, "staff_data.json")

_DEFAULT_STAFF = [
    {"id": 1, "username": "admin", "password_hash": None, "role": "Admin", "active": True},
    {"id": 2, "username": "cashier", "password_hash": None, "role": "Cashier", "active": True},
]


def hash_password(raw):
    """Simple SHA-256 hash so plaintext passwords are never stored.
    Swap this for your project's real auth/hashing (e.g. via database.py)
    if it already has one."""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def load_staff():
    if os.path.exists(DATA_FILE):
        try:
            import json
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    seeded = []
    for s in _DEFAULT_STAFF:
        s = dict(s)
        default_pw = "admin123" if s["username"] == "admin" else "cashier123"
        s["password_hash"] = hash_password(default_pw)
        seeded.append(s)
    return seeded


def save_staff():
    import json
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(STAFF, f, indent=2)
    except Exception as exc:
        print(f"Could not save staff data: {exc}")


STAFF = load_staff()
_next_id = (max((s["id"] for s in STAFF), default=0) + 1)


class StaffWindow(tk.Tk):
    def __init__(self, user="admin", role="Admin"):
        super().__init__()
        self.title("Staff Management — Cafe POS & Inventory Management System")
        self.geometry("880x600")
        self.minsize(780, 540)
        self.configure(bg=BG_COLOR)

        self.user = user
        self.role = role
        self.selected_id = None

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
            "Staff.Treeview", background=CARD_BG, fieldbackground=CARD_BG,
            foreground=TEXT_DARK, rowheight=34, borderwidth=0, font=("Segoe UI", 10),
        )
        style.configure(
            "Staff.Treeview.Heading", background=HEADER_BG, foreground="white",
            font=("Segoe UI", 10, "bold"), relief="flat",
        )
        style.map(
            "Staff.Treeview",
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
        tk.Label(title_box, text="Staff", font=("Segoe UI", 16, "bold"),
                  bg=BG_COLOR, fg=TEXT_DARK).pack(anchor="w")
        tk.Label(title_box, text="Manage cashier and admin accounts",
                  font=("Segoe UI", 9), bg=BG_COLOR, fg=TEXT_MUTED).pack(anchor="w")

        actions = tk.Frame(bar, bg=BG_COLOR)
        actions.pack(side="right")

        self._make_button(actions, "+ Add staff", self._open_add_dialog, primary=True).pack(side="left", padx=(0, 8))
        self._make_button(actions, "Reset password", self._open_reset_dialog).pack(side="left", padx=(0, 8))
        self.toggle_btn = self._make_button(actions, "Deactivate", self._toggle_active, danger=True)
        self.toggle_btn.pack(side="left")

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

    # ---------------- Table ----------------
    def _build_table(self):
        wrap = tk.Frame(self, bg=CARD_BG, highlightbackground=BORDER, highlightthickness=1)
        wrap.pack(fill="both", expand=True, padx=20, pady=(0, 8))

        columns = ("username", "role", "status")
        self.tree = ttk.Treeview(
            wrap, columns=columns, show="headings", style="Staff.Treeview", selectmode="browse"
        )
        headings = {"username": "Username", "role": "Role", "status": "Status"}
        widths = {"username": 260, "role": 160, "status": 160}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w" if col != "status" else "center")

        self.tree.tag_configure("active", foreground=SUCCESS)
        self.tree.tag_configure("inactive", foreground=DANGER)

        scrollbar = ttk.Scrollbar(wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _on_select(self, _event=None):
        sel = self.tree.selection()
        self.selected_id = int(sel[0]) if sel else None
        if self.selected_id is not None:
            staff = next(s for s in STAFF if s["id"] == self.selected_id)
            self.toggle_btn.configure(text="Deactivate" if staff["active"] else "Activate")

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

        active_count = 0
        for s in sorted(STAFF, key=lambda x: x["username"]):
            status = "Active" if s["active"] else "Deactivated"
            tag = "active" if s["active"] else "inactive"
            if s["active"]:
                active_count += 1
            self.tree.insert(
                "", "end", iid=str(s["id"]), tags=(tag,),
                values=(s["username"], s["role"], status),
            )

        self.status_label.configure(
            text=f"{len(STAFF)} account(s)   \u00b7   {active_count} active   \u00b7   {len(STAFF) - active_count} deactivated"
        )

    def _get_selected_staff(self):
        if self.selected_id is None:
            messagebox.showwarning("No selection", "Select a staff account from the table first.")
            return None
        return next((s for s in STAFF if s["id"] == self.selected_id), None)

    # ---------------- Add staff ----------------
    def _open_add_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Add staff account")
        dialog.configure(bg=CARD_BG)
        dialog.geometry("340x440")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        tk.Label(dialog, text="Add staff account", font=("Segoe UI", 13, "bold"),
                  bg=CARD_BG, fg=TEXT_DARK).pack(anchor="w", padx=24, pady=(20, 4))
        tk.Label(dialog, text="Create a cashier or admin login", font=("Segoe UI", 9),
                  bg=CARD_BG, fg=TEXT_MUTED).pack(anchor="w", padx=24, pady=(0, 16))

        def labeled_entry(label_text, show=None):
            tk.Label(dialog, text=label_text, font=("Segoe UI", 9),
                      bg=CARD_BG, fg=TEXT_MUTED).pack(anchor="w", padx=24)
            entry = ttk.Entry(dialog, width=32, show=show)
            entry.pack(padx=24, pady=(2, 12), ipady=3)
            return entry

        username_entry = labeled_entry("Username")
        password_entry = labeled_entry("Password", show="*")
        confirm_entry = labeled_entry("Confirm password", show="*")

        tk.Label(dialog, text="Role", font=("Segoe UI", 9),
                  bg=CARD_BG, fg=TEXT_MUTED).pack(anchor="w", padx=24)
        role_var = tk.StringVar(value="Cashier")
        role_row = tk.Frame(dialog, bg=CARD_BG)
        role_row.pack(anchor="w", padx=24, pady=(2, 12))
        for r in ("Cashier", "Admin"):
            tk.Radiobutton(role_row, text=r, variable=role_var, value=r,
                            bg=CARD_BG, fg=TEXT_DARK, selectcolor=CARD_BG,
                            activebackground=CARD_BG, font=("Segoe UI", 9)
                            ).pack(side="left", padx=(0, 12))

        def save():
            username = username_entry.get().strip()
            password = password_entry.get()
            confirm = confirm_entry.get()

            if not username or not password:
                messagebox.showerror("Invalid input", "Username and password are required.")
                return
            if any(s["username"].lower() == username.lower() for s in STAFF):
                messagebox.showerror("Username taken", "That username is already in use.")
                return
            if len(password) < 6:
                messagebox.showerror("Weak password", "Password must be at least 6 characters.")
                return
            if password != confirm:
                messagebox.showerror("Mismatch", "Passwords do not match.")
                return

            global _next_id
            STAFF.append({
                "id": _next_id, "username": username,
                "password_hash": hash_password(password),
                "role": role_var.get(), "active": True,
            })
            _next_id += 1
            save_staff()
            self._refresh_table()
            dialog.destroy()

        btn_row = tk.Frame(dialog, bg=CARD_BG)
        btn_row.pack(fill="x", padx=24, pady=(10, 20))
        tk.Button(btn_row, text="Cancel", font=("Segoe UI", 9), bg=CARD_BG, fg=TEXT_DARK,
                  relief="flat", highlightbackground=BORDER, highlightthickness=1,
                  padx=14, pady=6, command=dialog.destroy).pack(side="left")
        tk.Button(btn_row, text="Create account", font=("Segoe UI", 9, "bold"), bg=ACCENT, fg="white",
                  relief="flat", padx=18, pady=6, activebackground=ACCENT_DARK,
                  activeforeground="white", command=save).pack(side="right")

    # ---------------- Reset password ----------------
    def _open_reset_dialog(self):
        staff = self._get_selected_staff()
        if not staff:
            return

        dialog = tk.Toplevel(self)
        dialog.title("Reset password")
        dialog.configure(bg=CARD_BG)
        dialog.geometry("320x300")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        tk.Label(dialog, text="Reset password", font=("Segoe UI", 13, "bold"),
                  bg=CARD_BG, fg=TEXT_DARK).pack(anchor="w", padx=24, pady=(20, 2))
        tk.Label(dialog, text=f"for {staff['username']}", font=("Segoe UI", 10),
                  bg=CARD_BG, fg=TEXT_MUTED).pack(anchor="w", padx=24, pady=(0, 16))

        tk.Label(dialog, text="New password", font=("Segoe UI", 9),
                  bg=CARD_BG, fg=TEXT_MUTED).pack(anchor="w", padx=24)
        new_pw = ttk.Entry(dialog, width=28, show="*")
        new_pw.pack(padx=24, pady=(2, 10), ipady=3)

        tk.Label(dialog, text="Confirm new password", font=("Segoe UI", 9),
                  bg=CARD_BG, fg=TEXT_MUTED).pack(anchor="w", padx=24)
        confirm_pw = ttk.Entry(dialog, width=28, show="*")
        confirm_pw.pack(padx=24, pady=(2, 10), ipady=3)
        new_pw.focus_set()

        def save():
            pw = new_pw.get()
            confirm = confirm_pw.get()
            if len(pw) < 6:
                messagebox.showerror("Weak password", "Password must be at least 6 characters.")
                return
            if pw != confirm:
                messagebox.showerror("Mismatch", "Passwords do not match.")
                return
            staff["password_hash"] = hash_password(pw)
            save_staff()
            messagebox.showinfo("Password reset", f"Password updated for {staff['username']}.")
            dialog.destroy()

        btn_row = tk.Frame(dialog, bg=CARD_BG)
        btn_row.pack(fill="x", padx=24, pady=(10, 20))
        tk.Button(btn_row, text="Cancel", font=("Segoe UI", 9), bg=CARD_BG, fg=TEXT_DARK,
                  relief="flat", highlightbackground=BORDER, highlightthickness=1,
                  padx=14, pady=6, command=dialog.destroy).pack(side="left")
        tk.Button(btn_row, text="Save", font=("Segoe UI", 9, "bold"), bg=ACCENT, fg="white",
                  relief="flat", padx=18, pady=6, activebackground=ACCENT_DARK,
                  activeforeground="white", command=save).pack(side="right")

    # ---------------- Deactivate / reactivate ----------------
    def _toggle_active(self):
        staff = self._get_selected_staff()
        if not staff:
            return

        if staff["username"] == self.user and staff["active"]:
            messagebox.showwarning("Not allowed", "You can't deactivate the account you're currently using.")
            return

        if staff["active"]:
            confirm = messagebox.askyesno(
                "Deactivate account",
                f"Deactivate \u201c{staff['username']}\u201d? They won't be able to log in "
                "until the account is reactivated.",
            )
            if confirm:
                staff["active"] = False
        else:
            confirm = messagebox.askyesno(
                "Reactivate account", f"Reactivate \u201c{staff['username']}\u201d?"
            )
            if confirm:
                staff["active"] = True

        save_staff()
        self._refresh_table()
        self.toggle_btn.configure(text="Deactivate" if staff["active"] else "Activate")


if __name__ == "__main__":
    app = StaffWindow(user="admin", role="Admin")
    app.mainloop()
