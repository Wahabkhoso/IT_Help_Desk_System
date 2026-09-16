"""
sidebar.py
Shared sidebar navigation component used by admin, employee, and staff
dashboards to keep a consistent professional layout.
"""

import tkinter as tk
from utils import theme


class Sidebar(tk.Frame):
    def __init__(self, master, title, subtitle, nav_items, on_select, on_logout):
        """
        nav_items: list of (key, label) tuples
        on_select: callback(key)
        """
        super().__init__(master, bg=theme.PRIMARY, width=220)
        self.pack_propagate(False)
        self.on_select = on_select
        self.buttons = {}

        header = tk.Frame(self, bg=theme.PRIMARY_DARK, height=90)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text=title, font=theme.FONT_SUBTITLE, bg=theme.PRIMARY_DARK,
                 fg="white").pack(anchor="w", padx=18, pady=(18, 0))
        tk.Label(header, text=subtitle, font=theme.FONT_SMALL, bg=theme.PRIMARY_DARK,
                 fg=theme.SIDEBAR_TEXT).pack(anchor="w", padx=18)

        nav_frame = tk.Frame(self, bg=theme.PRIMARY)
        nav_frame.pack(fill="both", expand=True, pady=10)

        for key, label in nav_items:
            btn = tk.Button(
                nav_frame, text=label, anchor="w", bg=theme.PRIMARY, fg=theme.SIDEBAR_TEXT,
                font=theme.FONT_SIDEBAR, relief="flat", bd=0, padx=20, pady=12,
                activebackground=theme.SIDEBAR_HOVER, activeforeground="white",
                cursor="hand2", command=lambda k=key: self._select(k)
            )
            btn.pack(fill="x")
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=theme.SIDEBAR_HOVER)
                      if b["bg"] != theme.ACCENT else None)
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=theme.PRIMARY)
                      if b["bg"] != theme.ACCENT else None)
            self.buttons[key] = btn

        logout_btn = tk.Button(
            self, text="Log Out", anchor="w", bg=theme.PRIMARY_DARK, fg="white",
            font=theme.FONT_SIDEBAR, relief="flat", bd=0, padx=20, pady=14,
            activebackground=theme.DANGER, activeforeground="white",
            cursor="hand2", command=on_logout
        )
        logout_btn.pack(fill="x", side="bottom")

    def _select(self, key):
        for k, btn in self.buttons.items():
            btn.config(bg=theme.ACCENT if k == key else theme.PRIMARY)
        self.on_select(key)
