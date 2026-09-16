"""
staff_dashboard.py
Support staff interface: view assigned tickets, filter by priority/status/category,
add notes, respond to users, and update ticket status.
"""

import tkinter as tk
from tkinter import ttk

from database.database import get_db
from services.ticket_service import TicketService
from utils import theme
from ui.sidebar import Sidebar
from ui.widgets import PrimaryButton, Card, StatCard, TopBar, styled_treeview, row_tags, show_error
from ui.admin_dashboard import TicketDetailView

NAV_ITEMS = [
    ("assigned", "🎫  Assigned to Me"),
    ("pending", "⏳  Pending"),
    ("completed", "✅  Completed"),
]


class StaffDashboard(tk.Frame):
    def __init__(self, master, user, on_logout):
        super().__init__(master, bg=theme.BG_LIGHT)
        self.user = user
        self.on_logout = on_logout
        self.ticket_service = TicketService()
        self.db = get_db()
        self.staff_id = self._resolve_staff_id()

        self.sidebar = Sidebar(self, "IT Help Desk", f"Support · {user.full_name}",
                                NAV_ITEMS, self.show_view, on_logout)
        self.sidebar.pack(side="left", fill="y")

        right_panel = tk.Frame(self, bg=theme.BG_LIGHT)
        right_panel.pack(side="left", fill="both", expand=True)

        TopBar(right_panel, user, "Support Staff").pack(fill="x")

        self.content = tk.Frame(right_panel, bg=theme.BG_LIGHT)
        self.content.pack(side="top", fill="both", expand=True)

        self.show_view("assigned")

    def _resolve_staff_id(self):
        row = self.db.fetchone(
            "SELECT staff_id FROM support_staff WHERE user_id = ?", (self.user.user_id,))
        return row["staff_id"] if row else None

    def clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    def show_view(self, key):
        self.current_view_key = key
        self.clear_content()
        if key == "assigned":
            self.build_assigned_view()
        elif key == "pending":
            self.build_filtered_view(statuses=["Assigned", "In Progress", "Reopened"], title="Pending Tickets")
        elif key == "completed":
            self.build_filtered_view(statuses=["Resolved", "Closed"], title="Completed Tickets")

    def page_header(self, title, subtitle=""):
        header = tk.Frame(self.content, bg=theme.BG_LIGHT)
        header.pack(fill="x", padx=30, pady=(24, 10))
        tk.Label(header, text=title, font=theme.FONT_TITLE, bg=theme.BG_LIGHT,
                 fg=theme.TEXT_DARK).pack(anchor="w")
        if subtitle:
            tk.Label(header, text=subtitle, font=theme.FONT_BODY, bg=theme.BG_LIGHT,
                     fg=theme.TEXT_MUTED).pack(anchor="w")

    # ==================================================================
    def build_assigned_view(self):
        self.page_header("Assigned to Me", "All tickets currently assigned to you")

        workload = self.ticket_service.get_staff_workload(self.staff_id) if self.staff_id else {"pending": 0, "completed": 0}
        cards_frame = tk.Frame(self.content, bg=theme.BG_LIGHT)
        cards_frame.pack(fill="x", padx=30)
        StatCard(cards_frame, "Pending Tickets", workload["pending"], color=theme.WARNING, icon="⏳").pack(side="left", padx=(0, 10))
        StatCard(cards_frame, "Completed Tickets", workload["completed"], color=theme.SUCCESS, icon="✅").pack(side="left")

        filter_bar = tk.Frame(self.content, bg=theme.BG_LIGHT)
        filter_bar.pack(fill="x", padx=30, pady=(16, 0))

        tk.Label(filter_bar, text="Priority", bg=theme.BG_LIGHT, font=theme.FONT_SMALL).pack(side="left")
        pri_combo = ttk.Combobox(filter_bar, values=["All", "Low", "Medium", "High", "Critical"],
                                  state="readonly", width=10)
        pri_combo.set("All")
        pri_combo.pack(side="left", padx=(4, 14))

        tk.Label(filter_bar, text="Status", bg=theme.BG_LIGHT, font=theme.FONT_SMALL).pack(side="left")
        status_combo = ttk.Combobox(filter_bar, values=["All", "Assigned", "In Progress", "Resolved",
                                                          "Closed", "Reopened"], state="readonly", width=12)
        status_combo.set("All")
        status_combo.pack(side="left", padx=(4, 14))

        categories = self.ticket_service.list_categories()
        cat_names = ["All"] + [c["name"] for c in categories]
        tk.Label(filter_bar, text="Category", bg=theme.BG_LIGHT, font=theme.FONT_SMALL).pack(side="left")
        cat_combo = ttk.Combobox(filter_bar, values=cat_names, state="readonly", width=14)
        cat_combo.set("All")
        cat_combo.pack(side="left", padx=(4, 14))

        table_card = Card(self.content)
        table_card.pack(fill="both", expand=True, padx=30, pady=16)
        columns = ("id", "title", "user", "category", "priority", "status", "created")
        headings = ("ID", "Title", "User", "Category", "Priority", "Status", "Created")
        widths = {"id": 40, "title": 200, "user": 110, "category": 100, "priority": 80, "status": 110, "created": 130}
        frame, tree = styled_treeview(table_card, columns, headings, widths)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree = tree

        def refresh():
            cat_id = None
            if cat_combo.get() != "All":
                cat_id = next(c["category_id"] for c in categories if c["name"] == cat_combo.get())
            rows = self.ticket_service.search_tickets(
                for_staff_id=self.staff_id,
                priority=None if pri_combo.get() == "All" else pri_combo.get(),
                status=None if status_combo.get() == "All" else status_combo.get(),
                category_id=cat_id,
            )
            self._populate(rows)

        PrimaryButton(filter_bar, "Apply", command=refresh).pack(side="left")

        actions = tk.Frame(table_card, bg=theme.CARD_BG)
        actions.pack(fill="x", padx=10, pady=(0, 10))
        PrimaryButton(actions, "Open Ticket", command=self._open_detail).pack(side="left")

        refresh()

    def build_filtered_view(self, statuses, title):
        self.page_header(title)
        table_card = Card(self.content)
        table_card.pack(fill="both", expand=True, padx=30, pady=16)
        columns = ("id", "title", "user", "category", "priority", "status", "created")
        headings = ("ID", "Title", "User", "Category", "Priority", "Status", "Created")
        widths = {"id": 40, "title": 200, "user": 110, "category": 100, "priority": 80, "status": 110, "created": 130}
        frame, tree = styled_treeview(table_card, columns, headings, widths)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree = tree

        actions = tk.Frame(table_card, bg=theme.CARD_BG)
        actions.pack(fill="x", padx=10, pady=(0, 10))
        PrimaryButton(actions, "Open Ticket", command=self._open_detail).pack(side="left")

        all_rows = []
        for s in statuses:
            all_rows.extend(self.ticket_service.search_tickets(for_staff_id=self.staff_id, status=s))
        self._populate(all_rows)

    def _populate(self, rows):
        self.tree.delete(*self.tree.get_children())
        for r in rows:
            self.tree.insert("", "end", iid=str(r["ticket_id"]), values=(
                r["ticket_id"], r["title"], r["user_name"], r["category_name"],
                r["priority"], r["status"], str(r["created_at"])[:16]
            ), tags=row_tags(priority=r["priority"], status=r["status"]))
        children = self.tree.get_children()
        if children:
            self.tree.selection_set(children[0])
            self.tree.focus(children[0])

    def _open_detail(self):
        sel = self.tree.selection()
        if not sel:
            show_error("Please select a ticket first.")
            return
        ticket_id = int(sel[0])
        return_view = getattr(self, "current_view_key", "assigned")
        self.clear_content()
        detail = TicketDetailView(self.content, ticket_id, self.user, admin_mode=False,
                                   staff_mode=True, on_back=lambda: self.show_view(return_view))
        detail.pack(fill="both", expand=True)