"""
main.py
Application entry point for the IT Help Desk / IT Support Ticket Management
System. Wires together the login screen and the role-specific dashboards.

Run with:
    python main.py
"""

import tkinter as tk

from database.database import get_db
from utils.seed_data import seed
from services.auth_service import AuthService
from ui.role_select import RoleSelectScreen
from ui.login import LoginScreen
from ui.forgot_password import ForgotPasswordScreen
from ui.admin_dashboard import AdminDashboard
from ui.user_dashboard import UserDashboard
from ui.staff_dashboard import StaffDashboard
from utils import theme


LOGIN_SIZE = (760, 580)
DASHBOARD_SIZE = (1200, 750)


class HelpDeskApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("IT Help Desk — Support Ticket Management System")
        self.minsize(760, 560)
        self.configure(bg=theme.BG_LIGHT)

        # Initialize database + demo data on first run
        get_db()
        seed()

        self.current_screen = None
        self._set_window_size(*LOGIN_SIZE)
        self.show_role_select()

    def _set_window_size(self, width, height):
        """Resize and re-center the window on screen. Used to keep the
        login/role-select screens compact (instead of a tiny card floating
        in a huge mostly-empty window) while dashboards get a full-size
        window for the sidebar, tables, and charts."""
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height) // 3)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _clear(self):
        if self.current_screen is not None:
            self.current_screen.destroy()
            self.current_screen = None

    def show_role_select(self):
        self._clear()
        self._set_window_size(*LOGIN_SIZE)
        self.current_screen = RoleSelectScreen(self, on_role_selected=self.show_login)
        self.current_screen.pack(fill="both", expand=True)

    def show_login(self, role):
        self._clear()
        self._set_window_size(*LOGIN_SIZE)
        self.current_screen = LoginScreen(
            self, role=role, on_login_success=self.route_user,
            on_back=self.show_role_select, on_forgot_password=self.show_forgot_password)
        self.current_screen.pack(fill="both", expand=True)

    def show_forgot_password(self, role):
        self._clear()
        self._set_window_size(*LOGIN_SIZE)
        self.current_screen = ForgotPasswordScreen(
            self, role=role, auth_service=AuthService(),
            on_back=lambda: self.show_login(role))
        self.current_screen.pack(fill="both", expand=True)

    def route_user(self, user):
        self._clear()
        self._set_window_size(*DASHBOARD_SIZE)
        if user.role == "admin":
            self.current_screen = AdminDashboard(self, user, on_logout=self.show_role_select)
        elif user.role == "staff":
            self.current_screen = StaffDashboard(self, user, on_logout=self.show_role_select)
        else:
            self.current_screen = UserDashboard(self, user, on_logout=self.show_role_select)
        self.current_screen.pack(fill="both", expand=True)


if __name__ == "__main__":
    app = HelpDeskApp()
    app.mainloop()