"""
login.py
Login screen shown after the person has picked their role on the
RoleSelectScreen. Two-panel design: a decorative illustration panel on the
left, and a rounded card with a blue header on the right containing the
actual username/password form, a show/hide toggle, and a "Forgot
Password?" link.
"""

import tkinter as tk
from services.auth_service import AuthService
from utils.validators import ValidationError
from utils import theme
from ui.widgets import rounded_rect, vertical_gradient, add_placeholder

ROLE_LABELS = {
    "admin": "Admin Login",
    "employee": "Employee Login",
    "staff": "Support Staff Login",
}

HEADER_BLUE = "#2F5FD0"
HEADER_BLUE_DARK = "#24439C"
PANEL_TOP = "#E9F1FE"
PANEL_BOTTOM = "#CBDDF9"
FIELD_BORDER = "#DCE3EC"
PLACEHOLDER_COLOR = "#9AA5B1"
TEXT_DARK = "#22314A"

CARD_W, CARD_H = 340, 440
HEADER_H = 118
RADIUS = 22


class LoginScreen(tk.Frame):
    def __init__(self, master, role, on_login_success, on_back, on_forgot_password):
        super().__init__(master, bg="white")
        self.master = master
        self.role = role
        self.on_login_success = on_login_success
        self.on_back = on_back
        self.on_forgot_password = on_forgot_password
        self.auth_service = AuthService()
        self.password_visible = False
        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self):
        left = tk.Canvas(self, width=280, highlightthickness=0, bd=0)
        left.pack(side="left", fill="y")
        left.bind("<Configure>", lambda e: self._draw_left_panel(left))

        right = tk.Frame(self, bg="white")
        right.pack(side="left", fill="both", expand=True)

        card = tk.Canvas(right, width=CARD_W, height=CARD_H, highlightthickness=0,
                          bd=0, bg="white")
        card.place(relx=0.5, rely=0.5, anchor="center")
        self._draw_card(card)

    # ------------------------------------------------------------------
    def _draw_left_panel(self, canvas):
        canvas.delete("all")
        h = canvas.winfo_height() or 560
        w = 280
        vertical_gradient(canvas, 0, 0, w, h, PANEL_TOP, PANEL_BOTTOM)

        cx, cy = w // 2, h // 2 - 20

        # Simple "laptop with headset" illustration
        canvas.create_rectangle(cx - 70, cy - 55, cx + 70, cy + 45,
                                 fill="#1F2A44", outline="", width=0)
        canvas.create_text(cx, cy - 8, text="🎧", font=("Segoe UI Emoji", 34))
        canvas.create_polygon(cx - 85, cy + 45, cx + 85, cy + 45,
                               cx + 100, cy + 60, cx - 100, cy + 60,
                               fill="#324164", outline="")

        # Floating icon bubbles around the illustration
        bubbles = [
            (cx - 95, cy - 90, "💬", "#FFFFFF"),
            (cx + 85, cy - 95, "⚙️", "#FFFFFF"),
            (cx + 110, cy + 10, "✉️", "#FFFFFF"),
            (cx - 100, cy + 90, "❓", "#FFFFFF"),
        ]
        for bx, by, emoji, fill in bubbles:
            canvas.create_oval(bx - 20, by - 20, bx + 20, by + 20,
                                fill=fill, outline="#D7E3F7", width=1)
            canvas.create_text(bx, by, text=emoji, font=("Segoe UI Emoji", 14))

        canvas.create_text(cx, h - 60, text="IT Help Desk", font=theme.FONT_SUBTITLE,
                            fill=HEADER_BLUE_DARK)
        canvas.create_text(cx, h - 36, text="We're here to help,\nany time you need.",
                            font=theme.FONT_SMALL, fill="#5B6B85", justify="center")

    # ------------------------------------------------------------------
    def _draw_card(self, canvas):
        # Soft drop-shadow illusion (offset grey card behind the white one)
        rounded_rect(canvas, 6, 8, CARD_W + 6, CARD_H + 8, radius=RADIUS,
                     fill="#E7ECF3", outline="")
        # Card body
        rounded_rect(canvas, 0, 0, CARD_W, CARD_H, radius=RADIUS,
                     fill="white", outline="#E7ECF3", width=1)
        # Rounded-top header band
        rounded_rect(canvas, 0, 0, CARD_W, HEADER_H, radius=RADIUS,
                     corners=(True, True, False, False), fill=HEADER_BLUE, outline="")

        # --- Header content (icon + title + subtitle) ---
        header_frame = tk.Frame(canvas, bg=HEADER_BLUE)
        tk.Label(header_frame, text="🎧", font=("Segoe UI Emoji", 22),
                 bg=HEADER_BLUE, fg="white").pack(pady=(10, 2))
        tk.Label(header_frame, text="IT Help Desk", font=theme.FONT_SUBTITLE,
                 bg=HEADER_BLUE, fg="white").pack()
        tk.Label(header_frame, text=ROLE_LABELS.get(self.role, "Login"),
                 font=theme.FONT_SMALL, bg=HEADER_BLUE, fg="#DCE7FB").pack(pady=(2, 8))
        canvas.create_window(CARD_W // 2, HEADER_H // 2, window=header_frame)

        # --- Form content ---
        form = tk.Frame(canvas, bg="white")
        canvas.create_window(CARD_W // 2, HEADER_H + (CARD_H - HEADER_H) // 2 + 4,
                              window=form, width=CARD_W - 56)

        self.username_entry = self._build_field(form, "👤", "Enter your username")
        self.username_get, _ = add_placeholder(self.username_entry, "Enter your username",
                                                color=PLACEHOLDER_COLOR, normal_color=TEXT_DARK)

        pw_frame, pw_entry, eye_lbl = self._build_password_field(form)
        self.password_entry = pw_entry
        self.password_get, self.password_set_mask = add_placeholder(
            pw_entry, "Enter your password", color=PLACEHOLDER_COLOR,
            normal_color=TEXT_DARK, show="•")
        eye_lbl.bind("<Button-1>", lambda e: self._toggle_password_visibility())
        pw_entry.bind("<Return>", lambda e: self._attempt_login())

        forgot_lbl = tk.Label(form, text="Forgot Password?", font=theme.FONT_SMALL,
                               bg="white", fg=HEADER_BLUE, cursor="hand2")
        forgot_lbl.pack(anchor="e", pady=(4, 14))
        forgot_lbl.bind("<Button-1>", lambda e: self._open_forgot_password())

        self._build_login_button(form)

        self.error_label = tk.Label(form, text="", fg=theme.DANGER, bg="white",
                                     font=theme.FONT_SMALL, wraplength=CARD_W - 60, justify="left")
        self.error_label.pack(pady=(10, 0))

        back_lbl = tk.Label(form, text="👤  Choose a different role", font=theme.FONT_SMALL,
                             bg="white", fg="#8A96A8", cursor="hand2")
        back_lbl.pack(pady=(12, 0))
        back_lbl.bind("<Button-1>", lambda e: self.on_back())

    # ------------------------------------------------------------------
    def _build_field(self, parent, icon, placeholder):
        tk.Frame(parent, bg="white", height=6).pack()  # small top spacer
        wrap = tk.Frame(parent, bg="white", highlightbackground=FIELD_BORDER,
                         highlightthickness=1)
        wrap.pack(fill="x", pady=(0, 12))
        tk.Label(wrap, text=icon, bg="white", font=theme.FONT_SMALL,
                 fg="#8A96A8").pack(side="left", padx=(10, 4), pady=8)
        entry = tk.Entry(wrap, font=theme.FONT_BODY, relief="flat", bd=0,
                          bg="white", fg=TEXT_DARK, insertbackground=TEXT_DARK)
        entry.pack(side="left", fill="both", expand=True, ipady=6, padx=(0, 10))
        return entry

    def _build_password_field(self, parent):
        wrap = tk.Frame(parent, bg="white", highlightbackground=FIELD_BORDER,
                         highlightthickness=1)
        wrap.pack(fill="x", pady=(0, 4))
        tk.Label(wrap, text="🔒", bg="white", font=theme.FONT_SMALL,
                 fg="#8A96A8").pack(side="left", padx=(10, 4), pady=8)
        entry = tk.Entry(wrap, font=theme.FONT_BODY, relief="flat", bd=0,
                          bg="white", fg=TEXT_DARK, insertbackground=TEXT_DARK)
        entry.pack(side="left", fill="both", expand=True, ipady=6)
        eye = tk.Label(wrap, text="👁", bg="white", font=theme.FONT_SMALL,
                        fg="#8A96A8", cursor="hand2")
        eye.pack(side="left", padx=(4, 10))
        return wrap, entry, eye

    def _toggle_password_visibility(self):
        self.password_visible = not self.password_visible
        self.password_set_mask("" if self.password_visible else "•")

    def _build_login_button(self, parent):
        btn_h = 42
        btn = tk.Canvas(parent, height=btn_h, highlightthickness=0, bd=0, bg="white")
        btn.pack(fill="x", pady=(4, 0))

        def draw(width):
            btn.delete("all")
            rounded_rect(btn, 0, 0, width, btn_h, radius=btn_h // 2,
                         fill=HEADER_BLUE, outline="")
            btn.create_text(width // 2, btn_h // 2, text="➜  Log In",
                             font=theme.FONT_BODY_BOLD, fill="white")

        btn.bind("<Configure>", lambda e: draw(e.width))
        btn.bind("<Button-1>", lambda e: self._attempt_login())
        btn.config(cursor="hand2")

    # ------------------------------------------------------------------
    def _attempt_login(self):
        username = self.username_get()
        password = self.password_get()
        try:
            user = self.auth_service.login(username, password, expected_role=self.role)
            self.error_label.config(text="")
            self.on_login_success(user)
        except ValidationError as e:
            self.error_label.config(text=str(e))

    def _open_forgot_password(self):
        self.on_forgot_password(self.role)