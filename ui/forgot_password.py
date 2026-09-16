"""
forgot_password.py
"Forgot Password?" screen — rendered as a normal full-window screen (same
style/size as the login screen), not a popup. Reached from the login
screen's "Forgot Password?" link, with a link back to Login.
"""

import tkinter as tk
from utils import theme
from utils import email_service
from ui.widgets import PrimaryButton, show_error, show_success

ROLE_LABELS = {
    "admin": "Admin",
    "employee": "Employee",
    "staff": "Support Staff",
}


class ForgotPasswordScreen(tk.Frame):
    def __init__(self, master, role, auth_service, on_back):
        super().__init__(master, bg=theme.BG_LIGHT)
        self.role = role
        self.auth_service = auth_service
        self.on_back = on_back
        self._build_ui()

    def _build_ui(self):
        container = tk.Frame(self, bg=theme.BG_LIGHT)
        container.place(relx=0.5, rely=0.5, anchor="center")

        # No boxed "card" — matches the login screen's flush, borderless look.
        card = tk.Frame(container, bg=theme.BG_LIGHT, padx=40, pady=20)
        card.pack()

        header_bar = tk.Frame(card, bg=theme.PRIMARY, height=6, width=320)
        header_bar.pack(pady=(0, 20))
        header_bar.pack_propagate(False)

        tk.Label(card, text="Reset Your Password", font=theme.FONT_TITLE,
                 bg=theme.BG_LIGHT, fg=theme.PRIMARY).pack()
        tk.Label(card, text=f"{ROLE_LABELS.get(self.role, 'Account')} account",
                 font=theme.FONT_BODY, bg=theme.BG_LIGHT, fg=theme.TEXT_MUTED).pack(pady=(0, 24))

        tk.Label(card, text="Username", font=theme.FONT_BODY_BOLD,
                 bg=theme.BG_LIGHT, fg=theme.TEXT_DARK, anchor="w").pack(fill="x")
        self.username_entry = tk.Entry(card, font=theme.FONT_BODY, relief="solid",
                                        bd=1, width=32)
        self.username_entry.pack(pady=(4, 14), ipady=6)

        tk.Label(card, text="Email on file", font=theme.FONT_BODY_BOLD,
                 bg=theme.BG_LIGHT, fg=theme.TEXT_DARK, anchor="w").pack(fill="x")
        self.email_entry = tk.Entry(card, font=theme.FONT_BODY, relief="solid",
                                     bd=1, width=32)
        self.email_entry.pack(pady=(4, 14), ipady=6)

        tk.Label(card, text="We'll email a new temporary password to the "
                             "address on file for this account.",
                 font=theme.FONT_SMALL, bg=theme.BG_LIGHT, fg=theme.TEXT_MUTED,
                 wraplength=280, justify="left").pack(anchor="w", pady=(0, 16))

        PrimaryButton(card, "Send New Password", command=self._reset).pack(fill="x")

        self.status_label = tk.Label(card, text="", font=theme.FONT_SMALL,
                                      bg=theme.BG_LIGHT, fg=theme.DANGER,
                                      wraplength=280, justify="left")
        self.status_label.pack(pady=(12, 0))

        back_lbl = tk.Label(card, text="← Back to Login", font=theme.FONT_SMALL,
                             bg=theme.BG_LIGHT, fg=theme.TEXT_MUTED, cursor="hand2")
        back_lbl.pack(pady=(16, 0))
        back_lbl.bind("<Button-1>", lambda e: self.on_back())

    def _reset(self):
        username = self.username_entry.get().strip()
        email = self.email_entry.get().strip()

        if not username or not email:
            show_error("Please enter both your username and email.")
            return

        user = self.auth_service.find_for_password_reset(username, email, role=self.role)
        if user is None:
            # Deliberately vague — don't reveal whether the username or
            # email was the wrong part, to avoid leaking account details.
            show_error("We couldn't find a matching account with that "
                        "username and email.")
            return

        new_password = self.auth_service.reset_password_and_generate(user.user_id)
        sent, message = email_service.send_password_reset_email(
            user.email, user.full_name, user.username, new_password)

        if sent:
            show_success("A new password has been emailed to you.")
        else:
            # SMTP not configured in this environment — still succeeds
            # functionally, just saved locally instead of delivered.
            show_success("Your password was reset. " + message)

        self.on_back()