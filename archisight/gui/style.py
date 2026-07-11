# -*- coding: utf-8 -*-
"""
style.py — единая палитра и настройка ttk-темы для всего приложения.

Дизайн: светлый минимализм, мягкие серо-голубые тона, один синий акцент.
Согласовано с иконкой приложения (archisight/assets/icon.png).
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

BG = "#F5F7FA"
CARD_BG = "#FFFFFF"
BORDER = "#E2E8F0"
TEXT_PRIMARY = "#1E293B"
TEXT_SECONDARY = "#64748B"
TEXT_MUTED = "#94A3B8"
ACCENT = "#2563EB"
ACCENT_HOVER = "#1D4ED8"
ACCENT_SOFT = "#EFF4FF"
STATUS_ACTIVE = "#16A34A"
STATUS_INACTIVE = "#94A3B8"
DANGER = "#DC2626"

FONT_FAMILY = "Segoe UI"

FONT_TITLE = (FONT_FAMILY, 21, "bold")
FONT_SUBTITLE = (FONT_FAMILY, 10)
FONT_LABEL = (FONT_FAMILY, 10)
FONT_LABEL_BOLD = (FONT_FAMILY, 10, "bold")
FONT_VALUE = (FONT_FAMILY, 11)
FONT_VALUE_BOLD = (FONT_FAMILY, 11, "bold")
FONT_SMALL = (FONT_FAMILY, 9)
FONT_SECTION = (FONT_FAMILY, 12, "bold")
FONT_MONO = ("Consolas", 11)


def apply_style(root: tk.Misc) -> ttk.Style:
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    root.configure(bg=BG)

    style.configure("App.TFrame", background=BG)
    style.configure("Card.TFrame", background=CARD_BG)
    style.configure("Card.TLabel", background=CARD_BG, foreground=TEXT_PRIMARY, font=FONT_LABEL)

    style.configure("Title.TLabel", background=BG, foreground=TEXT_PRIMARY, font=FONT_TITLE)
    style.configure("Subtitle.TLabel", background=BG, foreground=TEXT_SECONDARY, font=FONT_SUBTITLE)

    style.configure("Label.TLabel", background=CARD_BG, foreground=TEXT_SECONDARY, font=FONT_LABEL)
    style.configure("Value.TLabel", background=CARD_BG, foreground=TEXT_PRIMARY, font=FONT_VALUE_BOLD)
    style.configure("Muted.TLabel", background=CARD_BG, foreground=TEXT_MUTED, font=FONT_SMALL)
    style.configure("GraySide.TLabel", background=CARD_BG, foreground=TEXT_SECONDARY, font=FONT_LABEL)

    style.configure("StatusActive.TLabel", background=CARD_BG, foreground=STATUS_ACTIVE, font=FONT_VALUE_BOLD)
    style.configure("StatusInactive.TLabel", background=CARD_BG, foreground=STATUS_INACTIVE, font=FONT_VALUE_BOLD)

    style.configure("Section.TLabel", background=BG, foreground=TEXT_PRIMARY, font=FONT_SECTION)
    style.configure("SectionCard.TLabel", background=CARD_BG, foreground=TEXT_PRIMARY, font=FONT_SECTION)

    style.configure(
        "Accent.TButton",
        background=ACCENT,
        foreground="#FFFFFF",
        font=FONT_LABEL_BOLD,
        padding=(14, 8),
        borderwidth=0,
        focusthickness=0,
    )
    style.map(
        "Accent.TButton",
        background=[("active", ACCENT_HOVER), ("pressed", ACCENT_HOVER)],
    )

    style.configure(
        "Secondary.TButton",
        background=CARD_BG,
        foreground=TEXT_PRIMARY,
        font=FONT_LABEL,
        padding=(12, 7),
        borderwidth=1,
        relief="solid",
        bordercolor=BORDER,
    )
    style.map(
        "Secondary.TButton",
        background=[("active", ACCENT_SOFT)],
        bordercolor=[("active", ACCENT)],
    )

    style.configure(
        "Link.TButton",
        background=BG,
        foreground=ACCENT,
        font=FONT_LABEL,
        padding=(4, 2),
        borderwidth=0,
    )
    style.map("Link.TButton", foreground=[("active", ACCENT_HOVER)])

    style.configure(
        "Danger.TButton",
        background=CARD_BG,
        foreground=DANGER,
        font=FONT_LABEL,
        padding=(12, 7),
        borderwidth=1,
        relief="solid",
        bordercolor="#FCA5A5",
    )
    style.map("Danger.TButton", background=[("active", "#FEF2F2")])

    style.configure(
        "TSeparator",
        background=BORDER,
    )

    style.configure(
        "TCheckbutton",
        background=CARD_BG,
        foreground=TEXT_PRIMARY,
        font=FONT_LABEL,
    )
    style.map("TCheckbutton", background=[("active", CARD_BG)])

    style.configure(
        "TRadiobutton",
        background=CARD_BG,
        foreground=TEXT_PRIMARY,
        font=FONT_LABEL,
    )
    style.map("TRadiobutton", background=[("active", CARD_BG)])

    style.configure(
        "TEntry",
        fieldbackground="#FFFFFF",
        foreground=TEXT_PRIMARY,
        bordercolor=BORDER,
        lightcolor=BORDER,
        darkcolor=BORDER,
        padding=6,
    )

    style.configure(
        "TCombobox",
        fieldbackground="#FFFFFF",
        foreground=TEXT_PRIMARY,
        background="#FFFFFF",
        bordercolor=BORDER,
        padding=6,
    )

    style.configure(
        "TSpinbox",
        fieldbackground="#FFFFFF",
        foreground=TEXT_PRIMARY,
        bordercolor=BORDER,
        padding=6,
    )

    style.configure("Card.TLabelframe", background=CARD_BG, bordercolor=BORDER, relief="solid")
    style.configure("Card.TLabelframe.Label", background=CARD_BG, foreground=TEXT_PRIMARY, font=FONT_LABEL_BOLD)

    return style


def card_frame(parent, **kwargs):
    """Создаёт 'карточку' — белую панель с тонкой рамкой на светлом фоне."""
    outer = tk.Frame(parent, bg=BORDER, **kwargs)
    inner = tk.Frame(outer, bg=CARD_BG)
    inner.pack(fill="both", expand=True, padx=1, pady=1)
    return outer, inner
