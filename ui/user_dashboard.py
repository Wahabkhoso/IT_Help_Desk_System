"""
user_dashboard.py
Employee-facing interface: submit new tickets, view/track their own tickets,
and close resolved tickets.
"""

import tkinter as tk
from tkinter import ttk

from services.ticket_service import TicketService
from utils.validators import ValidationError
from utils import theme
from ui.sidebar import Sidebar
from ui.widgets import (
    PrimaryButton, SecondaryButton, Card, TopBar, styled_treeview, row_tags,
    show_error, show_success, confirm
)
from ui.admin_dashboard import TicketDetailView

NAV_ITEMS = [
    ("my_tickets", "🎫  My Tickets"),
    ("new_ticket", "➕  New Ticket"),
]


class UserDashboard(tk.Frame):
    def __init__(self, master, user, on_logout):
        super().__init__(master, bg=theme.BG_LIGHT)
        self.user = user
        self.on_logout = on_logout
        self.ticket_service = TicketService()

        self.sidebar = Sidebar(self, "IT Help Desk", f"Employee · {user.full_name}",
                                NAV_ITEMS, self.show_view, on_logout)
        self.sidebar.pack(side="left", fill="y")

        right_panel = tk.Frame(self, bg=theme.BG_LIGHT)
        right_panel.pack(side="left", fill="both", expand=True)

        TopBar(right_panel, user, "Employee").pack(fill="x")

        self.content = tk.Frame(right_panel, bg=theme.BG_LIGHT)
        self.content.pack(side="top", fill="both", expand=True)

        self.show_view("my_tickets")

    def clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    def show_view(self, key):
        self.clear_content()
        if key == "my_tickets":
            self.build_my_tickets_view()
        elif key == "new_ticket":
            self.build_new_ticket_view()

    def page_header(self, title, subtitle=""):
        header = tk.Frame(self.content, bg=theme.BG_LIGHT)
        header.pack(fill="x", padx=30, pady=(24, 10))
        tk.Label(header, text=title, font=theme.FONT_TITLE, bg=theme.BG_LIGHT,
                 fg=theme.TEXT_DARK).pack(anchor="w")
        if subtitle:
            tk.Label(header, text=subtitle, font=theme.FONT_BODY, bg=theme.BG_LIGHT,
                     fg=theme.TEXT_MUTED).pack(anchor="w")

    # ==================================================================
    def build_my_tickets_view(self):
        self.page_header("My Tickets", "Track the status of your submitted tickets")

        filter_bar = tk.Frame(self.content, bg=theme.BG_LIGHT)
        filter_bar.pack(fill="x", padx=30)
        status_combo = ttk.Combobox(filter_bar, values=["All", "New", "Assigned", "In Progress",
                                                          "Resolved", "Closed", "Reopened"],
                                     state="readonly", width=14)
        status_combo.set("All")
        status_combo.pack(side="left")

        def do_filter():
            status = None if status_combo.get() == "All" else status_combo.get()
            rows = self.ticket_service.search_tickets(for_user_id=self.user.user_id, status=status)
            self._populate(rows)

        PrimaryButton(filter_bar, "Filter", command=do_filter).pack(side="left", padx=8)

        table_card = Card(self.content)
        table_card.pack(fill="both", expand=True, padx=30, pady=16)
        columns = ("id", "title", "category", "priority", "status", "staff", "created")
        headings = ("ID", "Title", "Category", "Priority", "Status", "Assigned Staff", "Created")
        widths = {"id": 40, "title": 200, "category": 100, "priority": 80,
                  "status": 100, "staff": 130, "created": 130}
        frame, tree = styled_treeview(table_card, columns, headings, widths)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree = tree

        actions = tk.Frame(table_card, bg=theme.CARD_BG)
        actions.pack(fill="x", padx=10, pady=(0, 10))
        PrimaryButton(actions, "View Details", command=self._open_detail).pack(side="left")
        SecondaryButton(actions, "Close Resolved Ticket", command=self._close_ticket).pack(side="left", padx=8)

        rows = self.ticket_service.search_tickets(for_user_id=self.user.user_id)
        self._populate(rows)

    def _populate(self, rows):
        self.tree.delete(*self.tree.get_children())
        for r in rows:
            self.tree.insert("", "end", iid=str(r["ticket_id"]), values=(
                r["ticket_id"], r["title"], r["category_name"], r["priority"],
                r["status"], r["staff_name"] or "Unassigned", str(r["created_at"])[:16]
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
        self.clear_content()
        detail = TicketDetailView(self.content, ticket_id, self.user, admin_mode=False,
                                   staff_mode=False, on_back=lambda: self.show_view("my_tickets"))
        detail.pack(fill="both", expand=True)

    def _close_ticket(self):
        sel = self.tree.selection()
        if not sel:
            show_error("Please select a ticket first.")
            return
        ticket_id = int(sel[0])
        ticket = self.ticket_service.get_ticket(ticket_id)
        if ticket.status != "Resolved":
            show_error("Only resolved tickets can be closed.")
            return
        if confirm("Close this ticket? You can reopen it later if needed."):
            self.ticket_service.close_ticket(ticket_id, self.user.user_id)
            show_success("Ticket closed.")
            self.build_my_tickets_view()

    # ==================================================================
    def build_new_ticket_view(self):
        self.page_header("Submit a New Ticket", "Describe your issue and we'll get it assigned")

        card = Card(self.content)
        card.pack(fill="both", expand=True, padx=30, pady=10)
        inner = tk.Frame(card, bg=theme.CARD_BG)
        inner.pack(padx=24, pady=24, fill="both", expand=True)

        tk.Label(inner, text="Title", font=theme.FONT_BODY_BOLD, bg=theme.CARD_BG).pack(anchor="w")
        title_entry = tk.Entry(inner, font=theme.FONT_BODY, width=60)
        title_entry.pack(anchor="w", pady=(2, 12), ipady=5)

        row = tk.Frame(inner, bg=theme.CARD_BG)
        row.pack(anchor="w", fill="x", pady=(0, 12))

        cat_frame = tk.Frame(row, bg=theme.CARD_BG)
        cat_frame.pack(side="left", padx=(0, 30))
        tk.Label(cat_frame, text="Category", font=theme.FONT_BODY_BOLD, bg=theme.CARD_BG).pack(anchor="w")
        categories = self.ticket_service.list_categories()
        cat_names = [c["name"] for c in categories]
        cat_combo = ttk.Combobox(cat_frame, values=cat_names, state="readonly", width=22)
        if cat_names:
            cat_combo.set(cat_names[0])
        cat_combo.pack(anchor="w", pady=(2, 0), ipady=3)

        pri_frame = tk.Frame(row, bg=theme.CARD_BG)
        pri_frame.pack(side="left")
        tk.Label(pri_frame, text="Priority", font=theme.FONT_BODY_BOLD, bg=theme.CARD_BG).pack(anchor="w")
        pri_combo = ttk.Combobox(pri_frame, values=["Low", "Medium", "High", "Critical"],
                                  state="readonly", width=15)
        pri_combo.set("Medium")
        pri_combo.pack(anchor="w", pady=(2, 0), ipady=3)

        tk.Label(inner, text="Description", font=theme.FONT_BODY_BOLD, bg=theme.CARD_BG).pack(anchor="w")
        desc_text = tk.Text(inner, font=theme.FONT_BODY, width=70, height=10, relief="solid", bd=1)
        desc_text.pack(anchor="w", pady=(2, 16))

        self.status_label = tk.Label(inner, text="", font=theme.FONT_SMALL, bg=theme.CARD_BG, fg=theme.SUCCESS)
        self.status_label.pack(anchor="w", pady=(0, 8))

        def submit():
            try:
                cat_id = next((c["category_id"] for c in categories if c["name"] == cat_combo.get()), None)
                if cat_id is None:
                    raise ValidationError("Please select a category.")
                self.ticket_service.create_ticket(
                    user_id=self.user.user_id,
                    category_id=cat_id,
                    title=title_entry.get(),
                    description=desc_text.get("1.0", "end").strip(),
                    priority=pri_combo.get(),
                )
                show_success("Your ticket has been submitted.")
                self.show_view("my_tickets")
            except ValidationError as e:
                show_error(str(e))

        PrimaryButton(inner, "Submit Ticket", command=submit).pack(anchor="w")