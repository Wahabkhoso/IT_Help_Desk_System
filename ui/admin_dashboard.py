"""
admin_dashboard.py
Full admin interface: dashboard stats + charts, user management, staff
management, ticket oversight/assignment, search & filters, and PDF reports.
"""

import tkinter as tk
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from services.auth_service import AuthService
from services.ticket_service import TicketService
from services.report_service import ReportService
from utils.validators import ValidationError
from utils import theme
from ui.sidebar import Sidebar
from ui.widgets import (
    PrimaryButton, SecondaryButton, DangerButton, Card, StatCard, TopBar,
    priority_badge, status_badge, styled_treeview, row_tags,
    show_error, show_success, confirm
)

NAV_ITEMS = [
    ("dashboard", "📊  Dashboard"),
    ("tickets", "🎫  All Tickets"),
    ("users", "👤  Manage Users"),
    ("staff", "🛠️  Manage Staff"),
    ("reports", "📄  Reports"),
    ("settings", "⚙️  Settings"),
]


class AdminDashboard(tk.Frame):
    def __init__(self, master, user, on_logout):
        super().__init__(master, bg=theme.BG_LIGHT)
        self.user = user
        self.on_logout = on_logout
        self.auth_service = AuthService()
        self.ticket_service = TicketService()
        self.report_service = ReportService()

        self.sidebar = Sidebar(self, "IT Help Desk", f"Admin · {user.full_name}",
                                NAV_ITEMS, self.show_view, on_logout)
        self.sidebar.pack(side="left", fill="y")

        right_panel = tk.Frame(self, bg=theme.BG_LIGHT)
        right_panel.pack(side="left", fill="both", expand=True)

        TopBar(right_panel, user, "System Administrator").pack(fill="x")

        self.content = tk.Frame(right_panel, bg=theme.BG_LIGHT)
        self.content.pack(side="top", fill="both", expand=True)

        self.show_view("dashboard")

    # ------------------------------------------------------------------
    def clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    def show_view(self, key):
        self.clear_content()
        {
            "dashboard": self.build_dashboard_view,
            "tickets": self.build_tickets_view,
            "users": self.build_users_view,
            "staff": self.build_staff_view,
            "reports": self.build_reports_view,
            "settings": self.build_settings_view,
        }[key]()

    def page_header(self, title, subtitle=""):
        header = tk.Frame(self.content, bg=theme.BG_LIGHT)
        header.pack(fill="x", padx=30, pady=(24, 10))
        tk.Label(header, text=title, font=theme.FONT_TITLE, bg=theme.BG_LIGHT,
                 fg=theme.TEXT_DARK).pack(anchor="w")
        if subtitle:
            tk.Label(header, text=subtitle, font=theme.FONT_BODY, bg=theme.BG_LIGHT,
                     fg=theme.TEXT_MUTED).pack(anchor="w")
        return header

    # ==================================================================
    # DASHBOARD VIEW
    # ==================================================================
    def build_dashboard_view(self):
        self.page_header("Dashboard", "Overview of the help desk system")
        stats = self.ticket_service.get_dashboard_stats()

        cards_frame = tk.Frame(self.content, bg=theme.BG_LIGHT)
        cards_frame.pack(fill="x", padx=30)
        cards = [
            ("Total Tickets", stats["total_tickets"], theme.ACCENT, "🎫"),
            ("New", stats["new_tickets"], theme.STATUS_COLORS["New"], "🆕"),
            ("In Progress", stats["in_progress_tickets"], theme.STATUS_COLORS["In Progress"], "⏳"),
            ("Resolved", stats["resolved_tickets"], theme.STATUS_COLORS["Resolved"], "✅"),
            ("Closed", stats["closed_tickets"], theme.STATUS_COLORS["Closed"], "🔒"),
            ("Critical (open)", stats["critical_tickets"], theme.DANGER, "⚠️"),
            ("Employees", stats["total_users"], theme.PRIMARY, "👥"),
            ("Support Staff", stats["total_staff"], theme.PRIMARY_DARK, "🛠️"),
        ]
        for i, (label, value, color, icon) in enumerate(cards):
            c = StatCard(cards_frame, label, value, color=color, icon=icon)
            c.grid(row=i // 4, column=i % 4, padx=8, pady=8, sticky="nsew")
        for col in range(4):
            cards_frame.grid_columnconfigure(col, weight=1)

        charts_frame = tk.Frame(self.content, bg=theme.BG_LIGHT)
        charts_frame.pack(fill="both", expand=True, padx=30, pady=(10, 20))
        self._build_charts(charts_frame)

    def _build_charts(self, parent):
        status_dist = self.ticket_service.get_status_distribution()
        priority_dist = self.ticket_service.get_priority_distribution()
        category_dist = self.ticket_service.get_category_distribution()

        fig = Figure(figsize=(11, 3.4), dpi=100)
        fig.patch.set_facecolor(theme.BG_LIGHT)

        ax1 = fig.add_subplot(131)
        if status_dist:
            ax1.bar(status_dist.keys(), status_dist.values(), color=theme.ACCENT)
        ax1.set_title("By Status", fontsize=10)
        ax1.tick_params(axis="x", labelrotation=35, labelsize=7)
        ax1.tick_params(axis="y", labelsize=7)

        ax2 = fig.add_subplot(132)
        if priority_dist:
            colors_list = [theme.PRIORITY_COLORS.get(k, theme.ACCENT) for k in priority_dist.keys()]
            ax2.pie(priority_dist.values(), labels=priority_dist.keys(), autopct="%1.0f%%",
                    colors=colors_list, textprops={"fontsize": 7})
        ax2.set_title("By Priority", fontsize=10)

        ax3 = fig.add_subplot(133)
        if category_dist:
            ax3.barh(list(category_dist.keys()), list(category_dist.values()), color=theme.PRIMARY)
        ax3.set_title("By Category", fontsize=10)
        ax3.tick_params(axis="both", labelsize=7)

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    # ==================================================================
    # TICKETS VIEW
    # ==================================================================
    def build_tickets_view(self):
        self.page_header("All Tickets", "Search, filter, assign, and manage tickets")

        filter_bar = Card(self.content)
        filter_bar.pack(fill="x", padx=30, pady=(0, 12))
        inner = tk.Frame(filter_bar, bg=theme.CARD_BG)
        inner.pack(fill="x", padx=14, pady=14)

        tk.Label(inner, text="Ticket ID", bg=theme.CARD_BG, font=theme.FONT_SMALL).grid(row=0, column=0, sticky="w")
        id_entry = tk.Entry(inner, width=8, font=theme.FONT_BODY)
        id_entry.grid(row=1, column=0, padx=(0, 10))

        tk.Label(inner, text="User", bg=theme.CARD_BG, font=theme.FONT_SMALL).grid(row=0, column=1, sticky="w")
        user_entry = tk.Entry(inner, width=14, font=theme.FONT_BODY)
        user_entry.grid(row=1, column=1, padx=(0, 10))

        categories = self.ticket_service.list_categories()
        cat_names = ["All"] + [c["name"] for c in categories]
        tk.Label(inner, text="Category", bg=theme.CARD_BG, font=theme.FONT_SMALL).grid(row=0, column=2, sticky="w")
        cat_combo = ttk.Combobox(inner, values=cat_names, state="readonly", width=13)
        cat_combo.set("All")
        cat_combo.grid(row=1, column=2, padx=(0, 10))

        tk.Label(inner, text="Priority", bg=theme.CARD_BG, font=theme.FONT_SMALL).grid(row=0, column=3, sticky="w")
        pri_combo = ttk.Combobox(inner, values=["All", "Low", "Medium", "High", "Critical"],
                                  state="readonly", width=10)
        pri_combo.set("All")
        pri_combo.grid(row=1, column=3, padx=(0, 10))

        tk.Label(inner, text="Status", bg=theme.CARD_BG, font=theme.FONT_SMALL).grid(row=0, column=4, sticky="w")
        status_combo = ttk.Combobox(inner, values=["All", "New", "Assigned", "In Progress",
                                                     "Resolved", "Closed", "Reopened"],
                                     state="readonly", width=12)
        status_combo.set("All")
        status_combo.grid(row=1, column=4, padx=(0, 10))

        def do_search():
            cat_id = None
            if cat_combo.get() != "All":
                cat_id = next(c["category_id"] for c in categories if c["name"] == cat_combo.get())
            rows = self.ticket_service.search_tickets(
                ticket_id=id_entry.get().strip() or None,
                user_keyword=user_entry.get().strip() or None,
                category_id=cat_id,
                priority=None if pri_combo.get() == "All" else pri_combo.get(),
                status=None if status_combo.get() == "All" else status_combo.get(),
            )
            self._populate_ticket_tree(rows)

        PrimaryButton(inner, "Search", command=do_search).grid(row=1, column=5, padx=(6, 0))
        SecondaryButton(inner, "Reset", command=lambda: self.show_view("tickets")).grid(row=1, column=6, padx=(6, 0))

        table_card = Card(self.content)
        table_card.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        columns = ("id", "title", "user", "category", "priority", "status", "staff", "created")
        headings = ("ID", "Title", "User", "Category", "Priority", "Status", "Staff", "Created")
        widths = {"id": 40, "title": 160, "user": 100, "category": 90,
                  "priority": 80, "status": 100, "staff": 100, "created": 130}
        frame, tree = styled_treeview(table_card, columns, headings, widths)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.ticket_tree = tree
        tree.bind("<Double-1>", lambda e: self._open_ticket_detail())

        actions = tk.Frame(table_card, bg=theme.CARD_BG)
        actions.pack(fill="x", padx=10, pady=(0, 10))
        PrimaryButton(actions, "Open Ticket", command=self._open_ticket_detail).pack(side="left")

        self._populate_ticket_tree(self.ticket_service.search_tickets())

    def _populate_ticket_tree(self, rows):
        self.ticket_tree.delete(*self.ticket_tree.get_children())
        for r in rows:
            self.ticket_tree.insert("", "end", iid=str(r["ticket_id"]), values=(
                r["ticket_id"], r["title"], r["user_name"], r["category_name"],
                r["priority"], r["status"], r["staff_name"] or "Unassigned",
                str(r["created_at"])[:16]
            ), tags=row_tags(priority=r["priority"], status=r["status"]))
        # Auto-select the first result so "Open Ticket" works immediately
        # after a search, without requiring an extra click on the row.
        children = self.ticket_tree.get_children()
        if children:
            self.ticket_tree.selection_set(children[0])
            self.ticket_tree.focus(children[0])

    def _open_ticket_detail(self):
        sel = self.ticket_tree.selection()
        if not sel:
            show_error("Please select a ticket first.")
            return
        ticket_id = int(sel[0])
        self.clear_content()
        detail = TicketDetailView(self.content, ticket_id, self.user, admin_mode=True,
                                   on_back=lambda: self.show_view("tickets"))
        detail.pack(fill="both", expand=True)

    # ==================================================================
    # USERS VIEW
    # ==================================================================
    def build_users_view(self):
        self.page_header("Manage Users", "Create, edit, and deactivate employee accounts")

        toolbar = tk.Frame(self.content, bg=theme.BG_LIGHT)
        toolbar.pack(fill="x", padx=30)
        search_entry = tk.Entry(toolbar, font=theme.FONT_BODY, width=26)
        search_entry.pack(side="left", ipady=5)
        PrimaryButton(toolbar, "Search", command=lambda: refresh()).pack(side="left", padx=8)
        PrimaryButton(toolbar, "+ New User", command=lambda: self._open_user_form()).pack(side="right")

        table_card = Card(self.content)
        table_card.pack(fill="both", expand=True, padx=30, pady=16)
        columns = ("id", "name", "username", "email", "role", "dept", "active")
        headings = ("ID", "Full Name", "Username", "Email", "Role", "Department", "Active")
        widths = {"id": 40, "name": 150, "username": 100, "email": 170,
                  "role": 80, "dept": 100, "active": 60}
        frame, tree = styled_treeview(table_card, columns, headings, widths)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.users_tree = tree

        def refresh():
            users = self.auth_service.search_users(search_entry.get().strip())
            tree.delete(*tree.get_children())
            for u in users:
                tree.insert("", "end", iid=str(u.user_id), values=(
                    u.user_id, u.full_name, u.username, u.email, u.role,
                    u.department or "-", "Yes" if u.is_active else "No"
                ))
            children = tree.get_children()
            if children:
                tree.selection_set(children[0])
                tree.focus(children[0])

        actions = tk.Frame(table_card, bg=theme.CARD_BG)
        actions.pack(fill="x", padx=10, pady=(0, 10))
        PrimaryButton(actions, "Edit", command=lambda: self._edit_selected_user()).pack(side="left")
        DangerButton(actions, "Delete", command=lambda: self._delete_selected_user(refresh)).pack(side="left", padx=8)

        refresh()

    def _open_user_form(self, existing_user=None):
        self.clear_content()
        view = UserFormView(self.content, self.auth_service, existing_user,
                             on_close=lambda: self.show_view("users"))
        view.pack(fill="both", expand=True)

    def _edit_selected_user(self):
        sel = self.users_tree.selection()
        if not sel:
            show_error("Please select a user.")
            return
        user = self.auth_service.get_user_by_id(int(sel[0]))
        self._open_user_form(existing_user=user)

    def _delete_selected_user(self, refresh_cb):
        sel = self.users_tree.selection()
        if not sel:
            show_error("Please select a user.")
            return
        if confirm("Delete this user? This cannot be undone."):
            self.auth_service.delete_user(int(sel[0]))
            show_success("User deleted.")
            refresh_cb()

    # ==================================================================
    # STAFF VIEW
    # ==================================================================
    def build_staff_view(self):
        self.page_header("Manage Support Staff", "Support staff accounts and workload")

        toolbar = tk.Frame(self.content, bg=theme.BG_LIGHT)
        toolbar.pack(fill="x", padx=30)
        PrimaryButton(toolbar, "+ New Staff Member",
                      command=lambda: self._open_staff_form()).pack(side="right")

        table_card = Card(self.content)
        table_card.pack(fill="both", expand=True, padx=30, pady=16)
        columns = ("id", "name", "username", "specialty", "pending", "completed")
        headings = ("Staff ID", "Name", "Username", "Specialty", "Pending", "Completed")
        widths = {"id": 60, "name": 160, "username": 120, "specialty": 140, "pending": 80, "completed": 90}
        frame, tree = styled_treeview(table_card, columns, headings, widths)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        staff_list = self.auth_service.list_staff()
        for s in staff_list:
            workload = self.ticket_service.get_staff_workload(s.staff_id)
            tree.insert("", "end", iid=str(s.staff_id), values=(
                s.staff_id, s.full_name, s.username, s.specialty or "General",
                workload["pending"], workload["completed"]
            ))

    def _open_staff_form(self):
        self.clear_content()
        view = UserFormView(self.content, self.auth_service, None,
                             on_close=lambda: self.show_view("staff"), force_role="staff")
        view.pack(fill="both", expand=True)

    # ==================================================================
    # REPORTS VIEW
    # ==================================================================
    def build_reports_view(self):
        self.page_header("Reports", "Generate professional PDF reports")

        card = Card(self.content)
        card.pack(fill="x", padx=30, pady=10)
        inner = tk.Frame(card, bg=theme.CARD_BG)
        inner.pack(padx=20, pady=20, fill="x")

        tk.Label(inner, text="Summary Statistics Report", font=theme.FONT_SUBTITLE,
                 bg=theme.CARD_BG, fg=theme.TEXT_DARK).pack(anchor="w")
        tk.Label(inner, text="Overall ticket counts, status/priority/category breakdowns.",
                 font=theme.FONT_SMALL, bg=theme.CARD_BG, fg=theme.TEXT_MUTED).pack(anchor="w", pady=(0, 10))
        PrimaryButton(inner, "Generate Summary PDF", command=self._generate_summary).pack(anchor="w")

        card2 = Card(self.content)
        card2.pack(fill="x", padx=30, pady=10)
        inner2 = tk.Frame(card2, bg=theme.CARD_BG)
        inner2.pack(padx=20, pady=20, fill="x")
        tk.Label(inner2, text="Full Ticket List Report", font=theme.FONT_SUBTITLE,
                 bg=theme.CARD_BG, fg=theme.TEXT_DARK).pack(anchor="w")
        tk.Label(inner2, text="Every ticket currently in the system, with status and assignment.",
                 font=theme.FONT_SMALL, bg=theme.CARD_BG, fg=theme.TEXT_MUTED).pack(anchor="w", pady=(0, 10))
        PrimaryButton(inner2, "Generate Ticket List PDF", command=self._generate_ticket_list).pack(anchor="w")

        self.report_status = tk.Label(self.content, text="", font=theme.FONT_SMALL,
                                       bg=theme.BG_LIGHT, fg=theme.SUCCESS)
        self.report_status.pack(padx=30, anchor="w")

    def _generate_summary(self):
        path = self.report_service.generate_summary_report()
        self.report_status.config(text=f"Saved: {path}")
        show_success(f"Summary report generated:\n{path}")

    def _generate_ticket_list(self):
        rows = self.ticket_service.search_tickets()
        path = self.report_service.generate_ticket_list_report(rows)
        self.report_status.config(text=f"Saved: {path}")
        show_success(f"Ticket list report generated:\n{path}")

    # ==================================================================
    # SETTINGS VIEW
    # ==================================================================
    def build_settings_view(self):
        self.page_header("Settings", "System and account settings")
        card = Card(self.content)
        card.pack(fill="x", padx=30, pady=10)
        inner = tk.Frame(card, bg=theme.CARD_BG)
        inner.pack(padx=20, pady=20, fill="x")

        tk.Label(inner, text="Change My Password", font=theme.FONT_SUBTITLE,
                 bg=theme.CARD_BG, fg=theme.TEXT_DARK).pack(anchor="w", pady=(0, 10))

        tk.Label(inner, text="New Password", bg=theme.CARD_BG, font=theme.FONT_BODY).pack(anchor="w")
        pwd_entry = tk.Entry(inner, show="•", font=theme.FONT_BODY, width=30)
        pwd_entry.pack(anchor="w", pady=(2, 10), ipady=4)

        def change_pwd():
            try:
                self.auth_service.reset_password(self.user.user_id, pwd_entry.get())
                show_success("Password updated.")
                pwd_entry.delete(0, "end")
            except ValidationError as e:
                show_error(str(e))

        PrimaryButton(inner, "Update Password", command=change_pwd).pack(anchor="w")

        card2 = Card(self.content)
        card2.pack(fill="x", padx=30, pady=10)
        inner2 = tk.Frame(card2, bg=theme.CARD_BG)
        inner2.pack(padx=20, pady=20, fill="x")
        tk.Label(inner2, text="System Info", font=theme.FONT_SUBTITLE,
                 bg=theme.CARD_BG, fg=theme.TEXT_DARK).pack(anchor="w", pady=(0, 8))
        info_text = ("IT Help Desk Ticket Management System\n"
                     "Version 1.0 · SQLite database · Built with Python & Tkinter")
        tk.Label(inner2, text=info_text, bg=theme.CARD_BG, fg=theme.TEXT_MUTED,
                 font=theme.FONT_SMALL, justify="left").pack(anchor="w")


# ======================================================================
# User Create/Edit Form — embedded full-page view (not a popup)
# ======================================================================
class UserFormView(tk.Frame):
    def __init__(self, parent, auth_service, existing_user=None, on_close=None, force_role=None):
        super().__init__(parent, bg=theme.BG_LIGHT)
        self.auth_service = auth_service
        self.existing_user = existing_user
        self.on_close = on_close
        self.force_role = force_role

        topbar = tk.Frame(self, bg=theme.PRIMARY)
        topbar.pack(fill="x")
        back_btn = tk.Button(
            topbar, text="← Back", command=self._go_back, bg=theme.PRIMARY_DARK, fg="white",
            font=theme.FONT_BODY_BOLD, relief="flat", bd=0, padx=14, pady=8, cursor="hand2",
            activebackground=theme.SIDEBAR_HOVER, activeforeground="white")
        back_btn.pack(side="left", padx=(16, 0), pady=14)
        tk.Label(topbar, text="Edit User" if existing_user else "New User", font=theme.FONT_SUBTITLE,
                 bg=theme.PRIMARY, fg="white").pack(side="left", padx=16)

        outer = tk.Frame(self, bg=theme.BG_LIGHT)
        outer.pack(fill="both", expand=True)

        card = Card(outer)
        card.pack(padx=30, pady=24, anchor="nw")
        pad = tk.Frame(card, bg=theme.CARD_BG)
        pad.pack(padx=28, pady=24)

        tk.Label(pad, text="Full Name", bg=theme.CARD_BG, font=theme.FONT_BODY_BOLD).pack(anchor="w")
        self.name_entry = tk.Entry(pad, font=theme.FONT_BODY, width=38)
        self.name_entry.pack(pady=(2, 10), ipady=4)

        tk.Label(pad, text="Email", bg=theme.CARD_BG, font=theme.FONT_BODY_BOLD).pack(anchor="w")
        self.email_entry = tk.Entry(pad, font=theme.FONT_BODY, width=38)
        self.email_entry.pack(pady=(2, 10), ipady=4)

        tk.Label(pad, text="Username", bg=theme.CARD_BG, font=theme.FONT_BODY_BOLD).pack(anchor="w")
        self.username_entry = tk.Entry(pad, font=theme.FONT_BODY, width=38)
        self.username_entry.pack(pady=(2, 10), ipady=4)

        # Password field — always shown; the admin sets it directly for
        # every role, including support staff.
        password_frame = tk.Frame(pad, bg=theme.CARD_BG)
        password_frame.pack(fill="x")
        tk.Label(
            password_frame,
            text="Password" + (" (leave blank to keep)" if existing_user else ""),
            bg=theme.CARD_BG, font=theme.FONT_BODY_BOLD).pack(anchor="w")
        self.password_entry = tk.Entry(password_frame, font=theme.FONT_BODY, width=38, show="•")
        self.password_entry.pack(pady=(2, 10), ipady=4)

        tk.Label(pad, text="Role", bg=theme.CARD_BG, font=theme.FONT_BODY_BOLD).pack(anchor="w")
        self.role_combo = ttk.Combobox(pad, values=["admin", "employee", "staff"],
                                        state="readonly" if not force_role else "disabled", width=35)
        self.role_combo.pack(pady=(2, 10), ipady=3)
        self.role_combo.set(force_role or "employee")

        tk.Label(pad, text="Department", bg=theme.CARD_BG, font=theme.FONT_BODY_BOLD).pack(anchor="w")
        self.dept_entry = tk.Entry(pad, font=theme.FONT_BODY, width=38)
        self.dept_entry.pack(pady=(2, 10), ipady=4)

        tk.Label(pad, text="Phone", bg=theme.CARD_BG, font=theme.FONT_BODY_BOLD).pack(anchor="w")
        self.phone_entry = tk.Entry(pad, font=theme.FONT_BODY, width=38)
        self.phone_entry.pack(pady=(2, 16), ipady=4)

        if existing_user:
            self.name_entry.insert(0, existing_user.full_name)
            self.email_entry.insert(0, existing_user.email)
            self.username_entry.insert(0, existing_user.username)
            self.username_entry.config(state="disabled")
            self.role_combo.set(existing_user.role)
            self.role_combo.config(state="disabled")
            self.dept_entry.insert(0, existing_user.department or "")
            self.phone_entry.insert(0, existing_user.phone or "")

        btn_row = tk.Frame(pad, bg=theme.CARD_BG)
        btn_row.pack(fill="x")
        PrimaryButton(btn_row, "Save", command=self._save).pack(side="left")
        SecondaryButton(btn_row, "Cancel", command=self._go_back).pack(side="left", padx=(8, 0))

    def _go_back(self):
        if self.on_close:
            self.on_close()

    def _save(self):
        try:
            if self.existing_user:
                self.auth_service.update_user(
                    self.existing_user.user_id,
                    full_name=self.name_entry.get(),
                    email=self.email_entry.get(),
                    department=self.dept_entry.get(),
                    phone=self.phone_entry.get(),
                )
                if self.password_entry.get():
                    self.auth_service.reset_password(self.existing_user.user_id, self.password_entry.get())
            else:
                self.auth_service.create_user(
                    full_name=self.name_entry.get(),
                    email=self.email_entry.get(),
                    username=self.username_entry.get(),
                    password=self.password_entry.get(),
                    role=self.role_combo.get(),
                    department=self.dept_entry.get(),
                    phone=self.phone_entry.get(),
                )

            show_success("User saved successfully.")
            if self.on_close:
                self.on_close()
        except ValidationError as e:
            show_error(str(e))


# ======================================================================
# Popup: Ticket Detail (shared across admin & staff dashboards)
# ======================================================================
class TicketDetailView(tk.Frame):
    """
    Full ticket detail — rendered as a normal page inside the dashboard's
    content area (not a separate popup window), with a "← Back" button to
    return to the underlying list. Shared across Admin, Employee, and Staff
    dashboards; which controls are shown depends on admin_mode/staff_mode.
    """

    def __init__(self, parent, ticket_id, current_user, admin_mode=False,
                 staff_mode=False, on_back=None):
        super().__init__(parent, bg=theme.BG_LIGHT)
        self.ticket_id = ticket_id
        self.current_user = current_user
        self.admin_mode = admin_mode
        self.staff_mode = staff_mode
        self.on_back = on_back
        self.ticket_service = TicketService()
        self.auth_service = AuthService()
        self.report_service = ReportService()

        self._build_ui()

    def _go_back(self):
        if self.on_back:
            self.on_back()

    def _build_ui(self):
        for w in self.winfo_children():
            w.destroy()

        t = self.ticket_service.get_ticket_detail(self.ticket_id)
        if t is None:
            tk.Label(self, text="Ticket not found.", bg=theme.BG_LIGHT).pack(padx=20, pady=20)
            return

        topbar = tk.Frame(self, bg=theme.PRIMARY)
        topbar.pack(fill="x")

        back_btn = tk.Button(
            topbar, text="← Back", command=self._go_back, bg=theme.PRIMARY_DARK, fg="white",
            font=theme.FONT_BODY_BOLD, relief="flat", bd=0, padx=14, pady=8, cursor="hand2",
            activebackground=theme.SIDEBAR_HOVER, activeforeground="white")
        back_btn.pack(side="left", padx=(16, 0), pady=14)

        header_text = tk.Frame(topbar, bg=theme.PRIMARY)
        header_text.pack(side="left", padx=16, pady=10)
        tk.Label(header_text, text=f"#{t['ticket_id']} — {t['title']}", font=theme.FONT_SUBTITLE,
                 bg=theme.PRIMARY, fg="white").pack(anchor="w")
        badges = tk.Frame(header_text, bg=theme.PRIMARY)
        badges.pack(anchor="w", pady=(4, 0))
        priority_badge(badges, t["priority"]).pack(side="left", padx=(0, 6))
        status_badge(badges, t["status"]).pack(side="left")

        # Scrollable body — the full-page ticket detail can be taller than
        # the visible window, so this keeps everything reachable.
        outer = tk.Frame(self, bg=theme.BG_LIGHT)
        outer.pack(fill="both", expand=True)
        canvas = tk.Canvas(outer, bg=theme.BG_LIGHT, highlightthickness=0)
        vsb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        body = tk.Frame(canvas, bg=theme.BG_LIGHT)
        body_window = canvas.create_window((0, 0), window=body, anchor="nw")

        def on_body_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        body.bind("<Configure>", on_body_configure)

        def on_canvas_configure(event):
            canvas.itemconfig(body_window, width=event.width)
        canvas.bind("<Configure>", on_canvas_configure)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        body_pad = tk.Frame(body, bg=theme.BG_LIGHT)
        body_pad.pack(fill="both", expand=True, padx=20, pady=16)
        body = body_pad  # reuse the name below unchanged

        info = tk.Frame(body, bg=theme.CARD_BG, highlightbackground=theme.BORDER, highlightthickness=1)
        info.pack(fill="x", pady=(0, 10))
        info_inner = tk.Frame(info, bg=theme.CARD_BG)
        info_inner.pack(fill="x", padx=14, pady=10)
        rows = [
            ("User", f"{t['user_name']} ({t['user_email']})"),
            ("Category", t["category_name"]),
            ("Assigned Staff", t["staff_name"] or "Unassigned"),
            ("Created", t["created_at"]),
            ("Last Updated", t["updated_at"]),
            ("Resolved", t["resolved_at"] or "-"),
        ]
        for i, (k, v) in enumerate(rows):
            tk.Label(info_inner, text=k + ":", font=theme.FONT_BODY_BOLD, bg=theme.CARD_BG,
                     fg=theme.TEXT_MUTED).grid(row=i, column=0, sticky="w", pady=2)
            tk.Label(info_inner, text=v, font=theme.FONT_BODY, bg=theme.CARD_BG,
                     fg=theme.TEXT_DARK).grid(row=i, column=1, sticky="w", padx=(8, 0), pady=2)

        desc_frame = tk.Frame(body, bg=theme.CARD_BG, highlightbackground=theme.BORDER, highlightthickness=1)
        desc_frame.pack(fill="x", pady=(0, 10))
        tk.Label(desc_frame, text="Description", font=theme.FONT_BODY_BOLD, bg=theme.CARD_BG,
                 fg=theme.TEXT_DARK).pack(anchor="w", padx=12, pady=(8, 0))
        tk.Label(desc_frame, text=t["description"], font=theme.FONT_BODY, bg=theme.CARD_BG,
                 fg=theme.TEXT_DARK, wraplength=580, justify="left").pack(anchor="w", padx=12, pady=(2, 10))

        if self.admin_mode or self.staff_mode:
            controls = tk.Frame(body, bg=theme.CARD_BG, highlightbackground=theme.BORDER, highlightthickness=1)
            controls.pack(fill="x", pady=(0, 10))
            cinner = tk.Frame(controls, bg=theme.CARD_BG)
            cinner.pack(fill="x", padx=12, pady=10)

            if self.admin_mode:
                tk.Label(cinner, text="Assign to:", bg=theme.CARD_BG, font=theme.FONT_SMALL).grid(row=0, column=0, sticky="w")
                staff_list = self.auth_service.list_staff()
                staff_map = {f"{s.full_name} ({s.specialty})": s.staff_id for s in staff_list}
                assign_combo = ttk.Combobox(cinner, values=list(staff_map.keys()), state="readonly", width=26)
                assign_combo.grid(row=1, column=0, padx=(0, 8))

                def do_assign():
                    if not assign_combo.get():
                        show_error("Select a staff member.")
                        return
                    self.ticket_service.assign_ticket(
                        self.ticket_id, staff_map[assign_combo.get()], self.current_user.user_id)
                    show_success("Ticket assigned.")
                    self._refresh()

                PrimaryButton(cinner, "Assign", command=do_assign).grid(row=1, column=1)

                tk.Label(cinner, text="Priority:", bg=theme.CARD_BG, font=theme.FONT_SMALL).grid(row=0, column=2, sticky="w", padx=(16, 0))
                pri_combo = ttk.Combobox(cinner, values=["Low", "Medium", "High", "Critical"],
                                          state="readonly", width=10)
                pri_combo.set(t["priority"])
                pri_combo.grid(row=1, column=2, padx=(16, 8))

                def do_priority():
                    self.ticket_service.update_priority(self.ticket_id, pri_combo.get(), self.current_user.user_id)
                    show_success("Priority updated.")
                    self._refresh()

                PrimaryButton(cinner, "Update", command=do_priority).grid(row=1, column=3)

            status_row = 2 if self.admin_mode else 0
            tk.Label(cinner, text="Status:", bg=theme.CARD_BG, font=theme.FONT_SMALL).grid(row=status_row, column=0, sticky="w", pady=(10, 0))
            status_combo = ttk.Combobox(cinner, values=["New", "Assigned", "In Progress", "Resolved", "Closed", "Reopened"],
                                         state="readonly", width=26)
            status_combo.set(t["status"])
            status_combo.grid(row=status_row + 1, column=0, padx=(0, 8))

            def do_status():
                self.ticket_service.update_status(self.ticket_id, status_combo.get(), self.current_user.user_id)
                show_success("Status updated.")
                self._refresh()

            PrimaryButton(cinner, "Update Status", command=do_status).grid(row=status_row + 1, column=1, pady=(10, 0))

            if self.admin_mode:
                SecondaryButton(cinner, "Export PDF", command=self._export_pdf).grid(row=status_row + 1, column=3, pady=(10, 0))

        comments_frame = tk.Frame(body, bg=theme.CARD_BG, highlightbackground=theme.BORDER, highlightthickness=1)
        comments_frame.pack(fill="both", expand=True)
        tk.Label(comments_frame, text="Comments / Troubleshooting Notes", font=theme.FONT_BODY_BOLD,
                 bg=theme.CARD_BG, fg=theme.TEXT_DARK).pack(anchor="w", padx=12, pady=(8, 4))

        comments_list = tk.Frame(comments_frame, bg=theme.CARD_BG)
        comments_list.pack(fill="both", expand=True, padx=12)
        comments = self.ticket_service.get_comments(self.ticket_id)
        for c in comments:
            row = tk.Frame(comments_list, bg=theme.BG_LIGHT)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=f"{c['author_name']} ({c['author_role']}) · {str(c['created_at'])[:16]}",
                     font=theme.FONT_SMALL, bg=theme.BG_LIGHT, fg=theme.TEXT_MUTED).pack(anchor="w", padx=8, pady=(4, 0))
            tk.Label(row, text=c["comment"], font=theme.FONT_BODY, bg=theme.BG_LIGHT,
                     fg=theme.TEXT_DARK, wraplength=560, justify="left").pack(anchor="w", padx=8, pady=(0, 4))

        add_row = tk.Frame(comments_frame, bg=theme.CARD_BG)
        add_row.pack(fill="x", padx=12, pady=10)
        self.comment_entry = tk.Entry(add_row, font=theme.FONT_BODY)
        self.comment_entry.pack(side="left", fill="x", expand=True, ipady=5)
        PrimaryButton(add_row, "Post", command=self._post_comment).pack(side="left", padx=(8, 0))

    def _post_comment(self):
        text = self.comment_entry.get().strip()
        if not text:
            return
        try:
            self.ticket_service.add_comment(self.ticket_id, self.current_user.user_id, text)
            self._refresh()
        except ValidationError as e:
            show_error(str(e))

    def _export_pdf(self):
        path = self.report_service.generate_single_ticket_pdf(self.ticket_id)
        show_success(f"Ticket exported:\n{path}")

    def _refresh(self):
        self._build_ui()