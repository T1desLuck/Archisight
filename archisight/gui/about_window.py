# -*- coding: utf-8 -*-
"""gui/about_window.py — окно "О программе" с описанием и контактом автора."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from . import style as S


class AboutWindow(tk.Toplevel):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        t = self.app.tr.t

        self.withdraw()
        self.title(t("about_title"))
        self.configure(bg=S.BG)
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        outer = ttk.Frame(self, style="App.TFrame", padding=(26, 22, 26, 18))
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text="Archisight", style="Title.TLabel").pack(anchor="w")
        ttk.Frame(outer, style="App.TFrame", height=12).pack()

        card_outer, card = S.card_frame(outer)
        card_outer.pack(fill="both", expand=True)

        text_frame = tk.Frame(card, bg=S.CARD_BG)
        text_frame.pack(fill="both", expand=True, padx=4, pady=4)

        scrollbar = ttk.Scrollbar(text_frame, orient="vertical")
        text = tk.Text(
            text_frame,
            wrap="word",
            bg=S.CARD_BG,
            fg=S.TEXT_PRIMARY,
            font=S.FONT_VALUE,
            relief="flat",
            padx=18,
            pady=16,
            yscrollcommand=scrollbar.set,
            width=54,
            height=18,
            cursor="arrow",
        )
        scrollbar.config(command=text.yview)
        text.insert("1.0", t("about_body"))
        text.configure(state="disabled")
        text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        ttk.Frame(outer, style="App.TFrame", height=14).pack()
        btn_row = tk.Frame(outer, bg=S.BG)
        btn_row.pack(fill="x")
        ttk.Button(btn_row, style="Accent.TButton", text=t("about_close"), command=self.destroy).pack(side="right")

        self.update_idletasks()
        self._center_on_parent(master)
        self.deiconify()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _center_on_parent(self, master):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        px, py = master.winfo_rootx(), master.winfo_rooty()
        pw, ph = master.winfo_width(), master.winfo_height()
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
