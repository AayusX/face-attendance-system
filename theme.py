import tkinter as tk
from tkinter import ttk

BG = "#eef1f6"
PANEL = "#ffffff"
CARD = "#ffffff"
CARD_ALT = "#e9edf4"
BORDER = "#cfd6e4"
TEXT = "#1b2434"
MUTED = "#68738a"
ACCENT = "#2563eb"
ACCENT_HOVER = "#4c7ff0"
ACCENT_DARK = "#1d4ed8"
GREEN = "#16a34a"
RED = "#dc2626"
AMBER = "#b45309"
CYAN = "#0891b2"

FONT = ("Segoe UI", 10)
FONT_SM = ("Segoe UI", 9)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_H1 = ("Segoe UI", 20, "bold")
FONT_H2 = ("Segoe UI", 13, "bold")


def apply_theme(root):
    root.configure(bg=BG)
    root.option_add("*TCombobox*Listbox.background", CARD)
    root.option_add("*TCombobox*Listbox.foreground", TEXT)
    root.option_add("*TCombobox*Listbox.selectBackground", ACCENT_DARK)
    root.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")

    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(".", background=BG, foreground=TEXT, font=FONT, bordercolor=BORDER)
    style.configure("TFrame", background=BG)
    style.configure("Card.TFrame", background=CARD)
    style.configure("Panel.TFrame", background=PANEL)

    style.configure("TLabel", background=BG, foreground=TEXT)
    style.configure("Muted.TLabel", background=BG, foreground=MUTED)
    style.configure("Card.TLabel", background=CARD, foreground=TEXT)
    style.configure("CardMuted.TLabel", background=CARD, foreground=MUTED)
    style.configure("Panel.TLabel", background=PANEL, foreground=TEXT)
    style.configure("H1.TLabel", background=BG, foreground=TEXT, font=FONT_H1)
    style.configure("H2.TLabel", background=BG, foreground=TEXT, font=FONT_H2)
    style.configure("CardH2.TLabel", background=CARD, foreground=TEXT, font=FONT_H2)
    style.configure("Accent.TLabel", background=BG, foreground=ACCENT, font=FONT_BOLD)

    style.configure(
        "TButton",
        background="#e8ecf3",
        foreground=TEXT,
        bordercolor="#d5dbe6",
        borderwidth=1,
        focusthickness=0,
        padding=(14, 8),
    )
    style.map(
        "TButton",
        background=[("active", "#d7deea"), ("disabled", "#f2f4f8")],
        foreground=[("disabled", "#aab2c1")],
    )
    style.configure(
        "Primary.TButton",
        background=ACCENT,
        foreground="#ffffff",
        bordercolor=ACCENT,
        borderwidth=1,
        focusthickness=0,
        padding=(14, 8),
    )
    style.map(
        "Primary.TButton",
        background=[("active", ACCENT_DARK), ("disabled", "#9db8ee")],
        foreground=[("disabled", "#e4ebf7")],
    )
    style.configure(
        "Danger.TButton",
        background="#e05858",
        foreground="#ffffff",
        bordercolor="#e05858",
        borderwidth=1,
        focusthickness=0,
        padding=(14, 8),
    )
    style.map("Danger.TButton", background=[("active", "#c0392b")])

    style.configure(
        "TEntry",
        fieldbackground="#ffffff",
        foreground=TEXT,
        insertcolor=TEXT,
        bordercolor=BORDER,
        lightcolor=BORDER,
        darkcolor=BORDER,
        borderwidth=1,
        padding=(10, 7),
    )
    style.map("TEntry", bordercolor=[("focus", ACCENT)])

    style.configure(
        "TSpinbox",
        fieldbackground="#ffffff",
        foreground=TEXT,
        background="#e8ecf3",
        arrowcolor=TEXT,
        bordercolor=BORDER,
        borderwidth=1,
        padding=(10, 7),
    )
    style.map("TSpinbox", bordercolor=[("focus", ACCENT)])

    style.configure(
        "TCombobox",
        fieldbackground="#ffffff",
        background="#e8ecf3",
        foreground=TEXT,
        arrowcolor=TEXT,
        bordercolor=BORDER,
        borderwidth=1,
        padding=(10, 7),
    )
    style.map("TCombobox", bordercolor=[("focus", ACCENT)])

    style.configure(
        "TNotebook", background=BG, borderwidth=0, tabmargins=(2, 6, 2, 0)
    )
    style.configure(
        "TNotebook.Tab",
        background="#dfe4ee",
        foreground=MUTED,
        bordercolor=BORDER,
        borderwidth=0,
        padding=(20, 10),
        font=FONT_BOLD,
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", ACCENT)],
        foreground=[("selected", "#ffffff")],
    )

    style.configure(
        "Treeview",
        background=CARD,
        fieldbackground=CARD,
        foreground=TEXT,
        borderwidth=0,
        rowheight=28,
        font=FONT,
    )
    style.map(
        "Treeview",
        background=[("selected", ACCENT_DARK)],
        foreground=[("selected", "#ffffff")],
    )
    style.configure(
        "Treeview.Heading",
        background=CARD_ALT,
        foreground=TEXT,
        borderwidth=0,
        padding=(8, 7),
        font=FONT_BOLD,
    )
    style.map("Treeview.Heading", background=[("active", BORDER)])

    style.configure(
        "TProgressbar", background=ACCENT, troughcolor="#dfe4ee", borderwidth=0
    )

    style.configure(
        "Vertical.TScrollbar",
        background="#c3ccdb",
        troughcolor=BG,
        borderwidth=0,
        arrowsize=12,
    )
    style.configure(
        "Horizontal.TScrollbar",
        background="#c3ccdb",
        troughcolor=BG,
        borderwidth=0,
        arrowsize=12,
    )

    style.configure("TSeparator", background=BORDER)

    return style