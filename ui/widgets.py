"""
widgets.py
Reusable, professionally styled Tkinter widgets: buttons, cards, badges,
tables, and dialog helpers. Keeping these in one place avoids duplicating
styling logic across every screen.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from utils import theme


class PrimaryButton(tk.Button):
    def __init__(self, master, text, command=None, bg=theme.ACCENT,
                 fg="white", **kwargs):
        super().__init__(
            master, text=text, command=command, bg=bg, fg=fg,
            activebackground=theme.ACCENT_HOVER, activeforeground="white",
            font=theme.FONT_BODY_BOLD, relief="flat", bd=0,
            padx=16, pady=8, cursor="hand2", **kwargs
        )
        self.bind("<Enter>", lambda e: self.config(bg=theme.ACCENT_HOVER))
        self.bind("<Leave>", lambda e: self.config(bg=bg))


class DangerButton(PrimaryButton):
    def __init__(self, master, text, command=None, **kwargs):
        super().__init__(master, text, command, bg=theme.DANGER, **kwargs)


class SecondaryButton(tk.Button):
    def __init__(self, master, text, command=None, **kwargs):
        super().__init__(
            master, text=text, command=command,
            bg=theme.CARD_BG, fg=theme.TEXT_DARK,
            activebackground=theme.BG_LIGHT,
            font=theme.FONT_BODY_BOLD, relief="solid", bd=1,
            padx=14, pady=7, cursor="hand2",
            highlightbackground=theme.BORDER, **kwargs
        )


class Card(tk.Frame):
    """A simple rounded-looking card container (Tkinter has no native radius,
    so we simulate depth with a border + background contrast)."""

    def __init__(self, master, **kwargs):
        super().__init__(master, bg=theme.CARD_BG, highlightbackground=theme.BORDER,
                          highlightthickness=1, bd=0, **kwargs)


class StatCard(Card):
    def __init__(self, master, label, value, color=theme.ACCENT, icon="●", **kwargs):
        super().__init__(master, **kwargs)
        self.configure(padx=16, pady=16)

        icon_canvas = tk.Canvas(self, width=44, height=44, highlightthickness=0,
                                 bd=0, bg=theme.CARD_BG)
        icon_canvas.pack(side="left", padx=(0, 12))
        icon_canvas.create_oval(2, 2, 42, 42, fill=color, outline="")
        icon_canvas.create_text(22, 22, text=icon, font=("Segoe UI Emoji", 15), fill="white")

        content = tk.Frame(self, bg=theme.CARD_BG)
        content.pack(side="left", fill="both", expand=True)

        self.value_label = tk.Label(content, text=str(value), font=theme.FONT_CARD_NUMBER,
                                     bg=theme.CARD_BG, fg=theme.TEXT_DARK)
        self.value_label.pack(anchor="w")
        tk.Label(content, text=label, font=theme.FONT_SMALL,
                 bg=theme.CARD_BG, fg=theme.TEXT_MUTED).pack(anchor="w")

    def set_value(self, value):
        self.value_label.config(text=str(value))


def priority_badge(master, priority):
    color = theme.PRIORITY_COLORS.get(priority, theme.TEXT_MUTED)
    lbl = tk.Label(master, text=priority, bg=color, fg="white",
                    font=theme.FONT_SMALL, padx=8, pady=2)
    return lbl


def status_badge(master, status):
    color = theme.STATUS_COLORS.get(status, theme.TEXT_MUTED)
    lbl = tk.Label(master, text=status, bg=color, fg="white",
                    font=theme.FONT_SMALL, padx=8, pady=2)
    return lbl


def styled_treeview(master, columns, headings, widths=None):
    """Create a ttk.Treeview with consistent, modern styling."""
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Custom.Treeview",
                     background=theme.CARD_BG,
                     fieldbackground=theme.CARD_BG,
                     foreground=theme.TEXT_DARK,
                     rowheight=30,
                     font=theme.FONT_BODY,
                     borderwidth=0)
    style.configure("Custom.Treeview.Heading",
                     background=theme.PRIMARY,
                     foreground="white",
                     font=theme.FONT_BODY_BOLD,
                     relief="flat")
    style.map("Custom.Treeview",
              background=[("selected", theme.ACCENT)],
              foreground=[("selected", "white")])

    frame = tk.Frame(master, bg=theme.CARD_BG)
    tree = ttk.Treeview(frame, columns=columns, show="headings",
                         style="Custom.Treeview", selectmode="browse")
    for col, head in zip(columns, headings):
        tree.heading(col, text=head)
        w = widths.get(col, 120) if widths else 120
        tree.column(col, width=w, anchor="center")

    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    tree.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")

    # Color-coded row tags — the closest a native ttk.Treeview can get to
    # the colored priority/status "pill" badges in the design mockup
    # (Treeview cells can't host custom-shaped widgets, only styled text).
    for name, color in theme.PRIORITY_COLORS.items():
        tree.tag_configure(f"priority_{name}", foreground=color)
    for name, color in theme.STATUS_COLORS.items():
        tree.tag_configure(f"status_{name}", foreground=color)

    return frame, tree


def row_tags(priority=None, status=None):
    """Build the tag tuple for a Treeview row so its Priority/Status text
    is colored to match the app's palette. Pass whichever of the two the
    row has; if both are given, the priority color takes precedence since
    it's usually the more urgent signal."""
    tags = []
    if status:
        tags.append(f"status_{status}")
    if priority:
        tags.append(f"priority_{priority}")
    return tuple(tags)


def labeled_entry(master, label_text, show=None, width=30):
    frame = tk.Frame(master, bg=master["bg"] if "bg" in master.keys() else theme.CARD_BG)
    tk.Label(frame, text=label_text, font=theme.FONT_BODY_BOLD,
              bg=frame["bg"], fg=theme.TEXT_DARK).pack(anchor="w", pady=(0, 4))
    entry = tk.Entry(frame, font=theme.FONT_BODY, relief="solid", bd=1,
                       highlightbackground=theme.BORDER, width=width, show=show)
    entry.pack(fill="x", ipady=5)
    return frame, entry


def labeled_combobox(master, label_text, values, width=28):
    frame = tk.Frame(master, bg=master["bg"] if "bg" in master.keys() else theme.CARD_BG)
    tk.Label(frame, text=label_text, font=theme.FONT_BODY_BOLD,
              bg=frame["bg"], fg=theme.TEXT_DARK).pack(anchor="w", pady=(0, 4))
    combo = ttk.Combobox(frame, values=values, font=theme.FONT_BODY,
                          width=width, state="readonly")
    combo.pack(fill="x", ipady=3)
    return frame, combo


def show_error(msg):
    messagebox.showerror("Error", msg)


def show_success(msg):
    messagebox.showinfo("Success", msg)


class TopBar(tk.Frame):
    """Persistent header shown above the content area on every dashboard
    view: a search box, a notification bell, and the current user's avatar
    with their name/role. Stays visible while the page below it switches."""

    def __init__(self, master, user, role_label, on_search=None):
        super().__init__(master, bg="white", height=64)
        self.pack_propagate(False)

        border = tk.Frame(self, bg=theme.BORDER, height=1)
        border.pack(side="bottom", fill="x")

        inner = tk.Frame(self, bg="white")
        inner.pack(fill="both", expand=True, padx=24)

        search_wrap = tk.Frame(inner, bg="#F3F5F8")
        search_wrap.pack(side="left", pady=14)
        tk.Label(search_wrap, text="🔍", bg="#F3F5F8", font=("Segoe UI Emoji", 11),
                 fg="#8A96A8").pack(side="left", padx=(12, 4), pady=8)
        self.search_entry = tk.Entry(search_wrap, bg="#F3F5F8", relief="flat", bd=0,
                                      font=theme.FONT_BODY, width=36, fg=theme.TEXT_DARK,
                                      insertbackground=theme.TEXT_DARK)
        self.search_entry.pack(side="left", padx=(0, 12), ipady=6)
        add_placeholder(self.search_entry, "Search tickets, users, or anything...",
                         color="#9AA5B1", normal_color=theme.TEXT_DARK)
        if on_search:
            self.search_entry.bind("<Return>", lambda e: on_search(self.search_entry.get()))

        avatar_frame = tk.Frame(inner, bg="white")
        avatar_frame.pack(side="right", padx=(16, 0))
        initials = "".join([p[0] for p in user.full_name.split()[:2]]).upper() or "?"
        avatar = tk.Canvas(avatar_frame, width=36, height=36, highlightthickness=0, bg="white")
        avatar.pack(side="left")
        avatar.create_oval(2, 2, 36, 36, fill=theme.ACCENT, outline="")
        avatar.create_text(19, 19, text=initials, fill="white", font=theme.FONT_SMALL)

        text_frame = tk.Frame(avatar_frame, bg="white")
        text_frame.pack(side="left", padx=(8, 0))
        tk.Label(text_frame, text=user.full_name, bg="white", font=theme.FONT_BODY_BOLD,
                 fg=theme.TEXT_DARK).pack(anchor="w")
        tk.Label(text_frame, text=role_label, bg="white", font=theme.FONT_SMALL,
                 fg=theme.TEXT_MUTED).pack(anchor="w")

        bell = tk.Label(inner, text="🔔", bg="white", font=("Segoe UI Emoji", 13),
                         fg="#5B6B85")
        bell.pack(side="right", padx=(4, 20))


def confirm(msg):
    return messagebox.askyesno("Confirm", msg)


def rounded_rect(canvas, x1, y1, x2, y2, radius=20, corners=(True, True, True, True), **kwargs):
    """Draw a rectangle with independently controllable rounded corners on a
    Canvas: corners = (top_left, top_right, bottom_right, bottom_left).
    Returns the polygon item id. Used to fake rounded "cards" and headers,
    since plain Tkinter frames can't have rounded corners natively."""
    tl, tr, br, bl = corners
    r = radius
    points = []
    points += [x1, y1 + r, x1, y1] if tl else [x1, y1, x1, y1]
    points += [x1 + r, y1] if tl else []
    points += [x2 - r, y1, x2, y1] if tr else [x2, y1, x2, y1]
    points += [x2, y1 + r] if tr else []
    points += [x2, y2 - r, x2, y2] if br else [x2, y2, x2, y2]
    points += [x2 - r, y2] if br else []
    points += [x1 + r, y2, x1, y2] if bl else [x1, y2, x1, y2]
    points += [x1, y2 - r] if bl else []
    return canvas.create_polygon(points, smooth=True, **kwargs)


def vertical_gradient(canvas, x1, y1, x2, y2, color1, color2, steps=60):
    """Paint a smooth top-to-bottom color gradient on a Canvas by drawing
    many thin rectangles with interpolated colors (Tkinter has no native
    gradient fill)."""
    r1, g1, b1 = canvas.winfo_rgb(color1)
    r2, g2, b2 = canvas.winfo_rgb(color2)
    height = y2 - y1
    for i in range(steps):
        t = i / steps
        r = int(r1 + (r2 - r1) * t) >> 8
        g = int(g1 + (g2 - g1) * t) >> 8
        b = int(b1 + (b2 - b1) * t) >> 8
        color = f"#{r:02x}{g:02x}{b:02x}"
        seg_y1 = y1 + height * i / steps
        seg_y2 = y1 + height * (i + 1) / steps
        canvas.create_rectangle(x1, seg_y1, x2, seg_y2 + 1, fill=color, outline=color)


def add_placeholder(entry, placeholder, color="#9AA5B1", normal_color=None, show=None):
    """Simulates HTML-style placeholder text in a Tkinter Entry (not
    natively supported): shows grey hint text until focused, restores the
    real value (with masking, if `show` is set e.g. for passwords) on
    focus-out. Returns a getter function that always returns the real
    typed value (never the placeholder text)."""
    normal_color = normal_color or entry.cget("fg")
    state = {"showing_placeholder": True}

    def show_placeholder():
        entry.delete(0, "end")
        if show:
            entry.config(show="")
        entry.insert(0, placeholder)
        entry.config(fg=color)
        state["showing_placeholder"] = True

    def on_focus_in(event=None):
        if state["showing_placeholder"]:
            entry.delete(0, "end")
            entry.config(fg=normal_color)
            if show:
                entry.config(show=show)
            state["showing_placeholder"] = False

    def on_focus_out(event=None):
        if not entry.get():
            show_placeholder()

    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)
    show_placeholder()

    def get_value():
        return "" if state["showing_placeholder"] else entry.get()

    def set_mask(char):
        """Change the masking character (e.g. toggle password visibility).
        No-op while the placeholder hint is still showing."""
        if not state["showing_placeholder"]:
            entry.config(show=char)

    return get_value, set_mask