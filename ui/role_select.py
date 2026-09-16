"""
role_select.py
The very first screen shown when the app opens. The person picks which
type of account they're logging in as (Employee / Support Staff / Admin)
before ever seeing a username/password field. This keeps the login form
simple and prevents the account list from being exposed to the person
before they've identified themselves.
"""

import tkinter as tk
from utils import theme


ROLES = [
    ("employee", "Employee", "Submit and track your own support tickets"),
    ("staff", "Support Staff", "Handle tickets assigned to you"),
    ("admin", "Admin", "Manage users, staff, and the full system"),
]


class RoleSelectScreen(tk.Frame):
    def __init__(self, master, on_role_selected):
        super().__init__(master, bg=theme.BG_LIGHT)
        self.on_role_selected = on_role_selected
        self._build_ui()

    def _build_ui(self):
        container = tk.Frame(self, bg=theme.BG_LIGHT)
        container.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(container, text="IT Help Desk", font=theme.FONT_TITLE,
                 bg=theme.BG_LIGHT, fg=theme.PRIMARY).pack()
        tk.Label(container, text="Please select how you'd like to log in",
                 font=theme.FONT_BODY, bg=theme.BG_LIGHT, fg=theme.TEXT_MUTED).pack(pady=(0, 28))

        cards_row = tk.Frame(container, bg=theme.BG_LIGHT)
        cards_row.pack()

        for key, label, desc in ROLES:
            self._build_role_card(cards_row, key, label, desc)

    def _build_role_card(self, parent, key, label, desc):
        card = tk.Frame(parent, bg=theme.CARD_BG, highlightbackground=theme.BORDER,
                         highlightthickness=1, width=200, height=180, cursor="hand2")
        card.pack(side="left", padx=12)
        card.pack_propagate(False)

        bar = tk.Frame(card, bg=theme.ACCENT, height=6)
        bar.pack(fill="x")

        inner = tk.Frame(card, bg=theme.CARD_BG)
        inner.pack(fill="both", expand=True, padx=16, pady=16)

        title_lbl = tk.Label(inner, text=label, font=theme.FONT_SUBTITLE,
                              bg=theme.CARD_BG, fg=theme.TEXT_DARK)
        title_lbl.pack(anchor="w", pady=(6, 6))

        desc_lbl = tk.Label(inner, text=desc, font=theme.FONT_SMALL, bg=theme.CARD_BG,
                             fg=theme.TEXT_MUTED, wraplength=160, justify="left")
        desc_lbl.pack(anchor="w")

        widgets = [card, bar, inner, title_lbl, desc_lbl]

        def select(event=None):
            self.on_role_selected(key)

        def on_enter(event=None):
            card.config(highlightbackground=theme.ACCENT, highlightthickness=2)

        def on_leave(event=None):
            card.config(highlightbackground=theme.BORDER, highlightthickness=1)

        for w in widgets:
            w.bind("<Button-1>", select)
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
