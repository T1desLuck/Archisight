# -*- coding: utf-8 -*-
"""
gui/main_window.py — главный (единственный) экран Archisight.

Окно строго информационное: показывает текущее состояние архива и
статус мониторинга. Все настройки живут в отдельном окне настроек
(gui/settings_window.py), которое открывается через верхнее меню.
"""

from __future__ import annotations

import tkinter as tk
from datetime import datetime
from tkinter import ttk

from .. import core
from .. import i18n
from . import style as S


REASON_KEY = {
    "not_a_folder": "main_details_reason_not_a_folder",
    "format_mismatch": "main_details_reason_format_mismatch",
    "invalid_date": "main_details_reason_invalid_date",
}


class MainWindow(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master, style="App.TFrame", padding=(28, 22, 28, 18))
        self.app = app
        self.details_visible = False
        self._build()
        self.refresh()

    # ------------------------------------------------------------------ UI

    def _build(self):
        t = self.app.tr.t

        # --- Заголовок ---
        header = ttk.Frame(self, style="App.TFrame")
        header.pack(fill="x")

        title_row = ttk.Frame(header, style="App.TFrame")
        title_row.pack(fill="x", anchor="w")
        ttk.Label(title_row, text="Archisight", style="Title.TLabel").pack(side="left")

        self.subtitle_label = ttk.Label(header, style="Subtitle.TLabel")
        self.subtitle_label.pack(fill="x", anchor="w", pady=(2, 0))

        ttk.Frame(self, style="App.TFrame", height=16).pack()

        # --- Карточка с основной информацией ---
        card_outer, card = S.card_frame(self)
        card_outer.pack(fill="x")
        card.configure(padx=20, pady=18)
        inner = tk.Frame(card, bg=S.CARD_BG)
        inner.pack(fill="both", expand=True, padx=18, pady=16)
        inner.columnconfigure(0, weight=1)
        inner.columnconfigure(1, weight=0)

        row = 0

        # Текущая дата
        self.lbl_date_caption = ttk.Label(inner, style="Label.TLabel")
        self.lbl_date_caption.grid(row=row, column=0, sticky="w", pady=(0, 10))
        self.lbl_date_value = ttk.Label(inner, style="Value.TLabel")
        self.lbl_date_value.grid(row=row, column=1, sticky="e", pady=(0, 10))
        row += 1

        ttk.Separator(inner, orient="horizontal").grid(row=row, column=0, columnspan=2, sticky="ew", pady=6)
        row += 1

        # Найдено папок / хранится дней (серым, справа)
        self.lbl_found_caption = ttk.Label(inner, style="Label.TLabel")
        self.lbl_found_caption.grid(row=row, column=0, sticky="w", pady=(6, 4))
        self.lbl_found_value = ttk.Label(inner, style="Value.TLabel")
        self.lbl_found_value.grid(row=row, column=1, sticky="e", pady=(6, 4))
        row += 1

        self.lbl_retention_caption = ttk.Label(inner, style="GraySide.TLabel")
        self.lbl_retention_caption.grid(row=row, column=0, sticky="w")
        self.lbl_retention_value = ttk.Label(inner, style="GraySide.TLabel")
        self.lbl_retention_value.grid(row=row, column=1, sticky="e")
        row += 1

        ttk.Separator(inner, orient="horizontal").grid(row=row, column=0, columnspan=2, sticky="ew", pady=10)
        row += 1

        # Путь к архиву
        self.lbl_path_caption = ttk.Label(inner, style="Label.TLabel")
        self.lbl_path_caption.grid(row=row, column=0, sticky="w", columnspan=2, pady=(0, 3))
        row += 1
        self.lbl_path_value = ttk.Label(inner, style="Value.TLabel", wraplength=560, justify="left")
        self.lbl_path_value.grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 10))
        row += 1

        # Диапазон дат в архиве
        self.lbl_range_caption = ttk.Label(inner, style="Label.TLabel")
        self.lbl_range_caption.grid(row=row, column=0, sticky="w", columnspan=2, pady=(0, 3))
        row += 1
        self.lbl_range_value = ttk.Label(inner, style="Value.TLabel")
        self.lbl_range_value.grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 10))
        row += 1

        ttk.Separator(inner, orient="horizontal").grid(row=row, column=0, columnspan=2, sticky="ew", pady=6)
        row += 1

        # Статус + последняя проверка
        status_row = tk.Frame(inner, bg=S.CARD_BG)
        status_row.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        status_row.columnconfigure(1, weight=1)

        self.lbl_status_caption = ttk.Label(status_row, style="Label.TLabel")
        self.lbl_status_caption.grid(row=0, column=0, sticky="w")
        self.status_dot = tk.Label(status_row, text="\u25cf", bg=S.CARD_BG, font=(S.FONT_FAMILY, 11))
        self.status_dot.grid(row=0, column=1, sticky="w", padx=(8, 4))
        self.status_text = ttk.Label(status_row, style="StatusActive.TLabel")
        self.status_text.grid(row=0, column=2, sticky="w")

        self.lbl_last_check = ttk.Label(status_row, style="Muted.TLabel")
        self.lbl_last_check.grid(row=0, column=3, sticky="e")
        status_row.columnconfigure(3, weight=1)
        row += 1

        # Кнопка "Открыть архив" — снизу справа карточки
        btn_row = tk.Frame(inner, bg=S.CARD_BG)
        btn_row.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(16, 0))
        btn_row.columnconfigure(0, weight=1)
        self.btn_open_archive = ttk.Button(
            btn_row, style="Accent.TButton", command=self.app.open_archive_folder
        )
        self.btn_open_archive.grid(row=0, column=1, sticky="e")

        ttk.Frame(self, style="App.TFrame", height=14).pack()

        # --- Переключатель сводки ---
        toggle_row = ttk.Frame(self, style="App.TFrame")
        toggle_row.pack(fill="x")
        self.btn_toggle_details = ttk.Button(
            toggle_row, style="Link.TButton", command=self._toggle_details
        )
        self.btn_toggle_details.pack(side="left")

        self.btn_refresh = ttk.Button(
            toggle_row, style="Link.TButton", command=self.refresh
        )
        self.btn_refresh.pack(side="right")

        # --- Панель сводки (скрыта по умолчанию) ---
        self.details_outer, self.details_card = S.card_frame(self)
        self.details_card.configure(padx=14, pady=12)

        details_header = ttk.Label(self.details_card, style="SectionCard.TLabel")
        details_header.pack(anchor="w", padx=8, pady=(4, 6))
        self.details_header_label = details_header

        list_frame = tk.Frame(self.details_card, bg=S.CARD_BG)
        list_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        self.details_list = tk.Listbox(
            list_frame,
            height=7,
            bg="#FBFCFE",
            fg=S.TEXT_PRIMARY,
            font=S.FONT_SMALL,
            relief="flat",
            highlightthickness=1,
            highlightbackground=S.BORDER,
            selectmode="none",
            activestyle="none",
            yscrollcommand=scrollbar.set,
        )
        scrollbar.config(command=self.details_list.yview)
        self.details_list.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    # ------------------------------------------------------------- actions

    def _toggle_details(self):
        self.details_visible = not self.details_visible
        if self.details_visible:
            self.details_outer.pack(fill="both", expand=True, pady=(2, 0))
        else:
            self.details_outer.pack_forget()
        self._apply_texts()

    # ------------------------------------------------------------ refresh

    def refresh(self):
        """Полностью обновляет отображаемую информацию (без удаления файлов)."""
        self._apply_texts()

        report = self.app.compute_preview()
        cfg = self.app.config
        lang = self.app.tr.language

        self.subtitle_label.configure(
            text="Archive + Oversight" if lang == "en" else "Архив под присмотром"
        )

        self.lbl_date_value.configure(text=i18n.format_long_date(datetime.now().date(), lang))

        if report.error == "path_missing":
            found_text = "\u2014"
            range_text = self.app.tr.t("main_no_path_set")
        else:
            found_text = str(len(report.scan.valid))
            if report.scan.valid:
                dates = [d for d, _, _ in report.scan.valid]
                fmt = cfg.date_format()
                range_text = f"{core.format_date(min(dates), fmt)} \u2014 {core.format_date(max(dates), fmt)}"
            else:
                range_text = self.app.tr.t("main_date_range_none")

        self.lbl_found_value.configure(text=found_text)
        self.lbl_retention_value.configure(text=str(cfg.retention_days))

        path_text = cfg.archive_path if cfg.archive_path else self.app.tr.t("main_no_path_set")
        self.lbl_path_value.configure(text=path_text)
        self.lbl_range_value.configure(text=range_text)

        active = self.app.is_autostart_active()
        if active:
            self.status_dot.configure(fg=S.STATUS_ACTIVE)
            self.status_text.configure(text=self.app.tr.t("main_status_active"), style="StatusActive.TLabel")
        else:
            self.status_dot.configure(fg=S.STATUS_INACTIVE)
            self.status_text.configure(text=self.app.tr.t("main_status_inactive"), style="StatusInactive.TLabel")

        if cfg.last_check:
            try:
                dt = datetime.fromisoformat(cfg.last_check)
                last_check_text = self.app.tr.t(
                    "main_last_check"
                ) + " " + i18n.format_datetime_short(dt, lang)
            except ValueError:
                last_check_text = self.app.tr.t("main_last_check") + " " + self.app.tr.t("main_last_check_never")
        else:
            last_check_text = self.app.tr.t("main_last_check") + " " + self.app.tr.t("main_last_check_never")
        self.lbl_last_check.configure(text=last_check_text)

        self._populate_details(report)

    def _populate_details(self, report: core.CleanupReport):
        self.details_list.delete(0, "end")
        if report.error == "path_missing" or report.scan is None:
            return

        ignored = report.scan.ignored
        if not ignored:
            self.details_list.insert("end", "  " + self.app.tr.t("main_details_ignored_empty"))
        else:
            for item in ignored:
                reason_text = self.app.tr.t(REASON_KEY.get(item.reason, "main_details_reason_format_mismatch"))
                self.details_list.insert("end", f"  \u2022 {item.name}  \u2014  {reason_text}")

        if report.retention and report.retention.delete:
            self.details_list.insert("end", "")
            n = len(report.retention.delete)
            note = (
                f"  \u2192 {n} folder(s) will be removed on the next check"
                if self.app.tr.language == "en"
                else f"  \u2192 при следующей проверке будет удалено папок: {n}"
            )
            self.details_list.insert("end", note)

    def _apply_texts(self):
        t = self.app.tr.t
        self.lbl_date_caption.configure(text=t("main_current_date"))
        self.lbl_found_caption.configure(text=t("main_folders_found"))
        self.lbl_retention_caption.configure(text=t("main_retention_days"))
        self.lbl_path_caption.configure(text=t("main_archive_path"))
        self.lbl_range_caption.configure(text=t("main_date_range"))
        self.lbl_status_caption.configure(text=t("main_status"))
        self.btn_open_archive.configure(text=t("main_open_archive"))
        self.btn_refresh.configure(text=t("main_refresh"))
        self.btn_toggle_details.configure(
            text=t("main_details_hide") if self.details_visible else t("main_details_show")
        )
        self.details_header_label.configure(text=t("main_details_ignored_header"))
