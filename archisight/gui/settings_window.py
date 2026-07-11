# -*- coding: utf-8 -*-
"""
gui/settings_window.py — окно настроек Archisight.

Важное правило: ничего не применяется и не сохраняется, пока пользователь
не нажмёт "Сохранить". Закрытие окна (крестиком или "Отмена") отменяет
все несохранённые изменения. Исключение — кнопка "Применить сейчас":
она выполняет реальную разовую проверку с текущими значениями полей
формы, но НЕ сохраняет их как настройки по умолчанию.
"""

from __future__ import annotations

import os
import tkinter as tk
from datetime import date
from tkinter import filedialog, messagebox, ttk

from .. import autostart
from .. import core
from ..config import AppConfig
from . import style as S

SEPARATOR_KEYS = {
    ".": "settings_sep_dot",
    "-": "settings_sep_dash",
    ",": "settings_sep_comma",
}


class SettingsWindow(tk.Toplevel):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.withdraw()  # прячем пока не построено окно, чтобы не мигало

        t = self.app.tr.t
        self.title(t("settings_title"))
        self.configure(bg=S.BG)
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        cfg = self.app.config

        # --- состояние формы (в памяти, до нажатия "Сохранить") ---
        self._language_touched = False
        self.language_var = tk.StringVar(value=cfg.effective_language())
        self.retention_var = tk.StringVar(value=str(cfg.retention_days))
        self.path_var = tk.StringVar(value=cfg.archive_path or "")

        hh, mm = ("", "")
        if cfg.run_time:
            try:
                hh, mm = cfg.run_time.split(":")
            except ValueError:
                hh, mm = "", ""
        self.hour_var = tk.StringVar(value=hh)
        self.minute_var = tk.StringVar(value=mm)

        self.order_var = tk.StringVar(value=cfg.date_order)
        self.separator_var = tk.StringVar(value=cfg.date_separator)
        self.year_format_var = tk.StringVar(value=cfg.date_year_format)
        self.autostart_var = tk.BooleanVar(value=cfg.autostart_enabled)

        self._build()
        self._update_preview()

        self.update_idletasks()
        self._center_on_parent(master)
        self.deiconify()
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    # ------------------------------------------------------------------ UI

    def _center_on_parent(self, master):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        px, py = master.winfo_rootx(), master.winfo_rooty()
        pw, ph = master.winfo_width(), master.winfo_height()
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def _build(self):
        t = self.app.tr.t
        outer = ttk.Frame(self, style="App.TFrame", padding=(24, 20, 24, 16))
        outer.pack(fill="both", expand=True)

        # ============================================================ Язык
        self._section(outer, "settings_language")
        lang_row = tk.Frame(outer, bg=S.BG)
        lang_row.pack(fill="x", pady=(0, 14))
        ttk.Radiobutton(
            lang_row, text=t("settings_language_en"), value="en",
            variable=self.language_var, command=self._on_language_touched,
            style="TRadiobutton",
        ).pack(side="left", padx=(0, 20))
        ttk.Radiobutton(
            lang_row, text=t("settings_language_ru"), value="ru",
            variable=self.language_var, command=self._on_language_touched,
            style="TRadiobutton",
        ).pack(side="left")

        # ===================================================== Дни хранения
        self._section(outer, "settings_retention_days")
        ret_row = tk.Frame(outer, bg=S.BG)
        ret_row.pack(fill="x", pady=(0, 14))
        self.retention_spin = ttk.Spinbox(
            ret_row, from_=core.MIN_RETENTION_DAYS, to=core.MAX_RETENTION_DAYS,
            textvariable=self.retention_var, width=8, justify="center",
        )
        self.retention_spin.pack(side="left")
        self.retention_hint_label = ttk.Label(ret_row, style="Subtitle.TLabel")
        self.retention_hint_label.pack(side="left", padx=(12, 0))

        # ======================================================== Путь
        self._section(outer, "settings_archive_path")
        path_row = tk.Frame(outer, bg=S.BG)
        path_row.pack(fill="x", pady=(0, 4))
        path_entry = ttk.Entry(path_row, textvariable=self.path_var, state="readonly", width=46)
        path_entry.pack(side="left", fill="x", expand=True)

        path_btn_row = tk.Frame(outer, bg=S.BG)
        path_btn_row.pack(fill="x", pady=(6, 14))
        self.btn_browse = ttk.Button(path_btn_row, style="Secondary.TButton", command=self._browse_path)
        self.btn_browse.pack(side="left")
        self.btn_clear_path = ttk.Button(path_btn_row, style="Link.TButton", command=self._clear_path)
        self.btn_clear_path.pack(side="left", padx=(10, 0))

        # ==================================================== Время проверки
        self._section(outer, "settings_run_time")
        time_row = tk.Frame(outer, bg=S.BG)
        time_row.pack(fill="x", pady=(0, 2))
        vcmd_h = (self.register(self._validate_hour), "%P")
        vcmd_m = (self.register(self._validate_minute), "%P")
        self.hour_spin = ttk.Spinbox(
            time_row, from_=0, to=23, textvariable=self.hour_var, width=4, justify="center",
            format="%02.0f", validate="key", validatecommand=vcmd_h,
        )
        self.hour_spin.pack(side="left")
        tk.Label(time_row, text=":", bg=S.BG, fg=S.TEXT_PRIMARY, font=S.FONT_VALUE_BOLD).pack(side="left", padx=6)
        self.minute_spin = ttk.Spinbox(
            time_row, from_=0, to=59, textvariable=self.minute_var, width=4, justify="center",
            format="%02.0f", validate="key", validatecommand=vcmd_m,
        )
        self.minute_spin.pack(side="left")
        self.btn_clear_time = ttk.Button(time_row, style="Link.TButton", command=self._clear_time)
        self.btn_clear_time.pack(side="left", padx=(14, 0))

        self.run_time_hint_label = ttk.Label(outer, style="Subtitle.TLabel", wraplength=540, justify="left")
        self.run_time_hint_label.pack(fill="x", pady=(4, 14))

        # =============================================== Формат названий дат
        self._section(outer, "settings_date_format_header")

        fmt_grid = tk.Frame(outer, bg=S.BG)
        fmt_grid.pack(fill="x", pady=(0, 6))

        self.order_label = ttk.Label(fmt_grid, style="Subtitle.TLabel")
        self.order_label.grid(row=0, column=0, sticky="w", pady=4)
        self.order_combo = ttk.Combobox(
            fmt_grid, state="readonly", width=22
        )
        self.order_combo.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=4)
        self.order_combo.bind("<<ComboboxSelected>>", lambda e: self._on_format_changed())

        self.sep_label = ttk.Label(fmt_grid, style="Subtitle.TLabel")
        self.sep_label.grid(row=1, column=0, sticky="w", pady=4)
        self.sep_combo = ttk.Combobox(
            fmt_grid, state="readonly", width=22
        )
        self.sep_combo.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=4)
        self.sep_combo.bind("<<ComboboxSelected>>", lambda e: self._on_format_changed())

        self.year_label = ttk.Label(fmt_grid, style="Subtitle.TLabel")
        self.year_label.grid(row=2, column=0, sticky="w", pady=4)
        year_row = tk.Frame(fmt_grid, bg=S.BG)
        year_row.grid(row=2, column=1, sticky="w", padx=(10, 0), pady=4)
        self.year_short_radio = ttk.Radiobutton(
            year_row, value="short", variable=self.year_format_var,
            command=self._on_format_changed, style="TRadiobutton",
        )
        self.year_short_radio.pack(side="left", padx=(0, 16))
        self.year_full_radio = ttk.Radiobutton(
            year_row, value="full", variable=self.year_format_var,
            command=self._on_format_changed, style="TRadiobutton",
        )
        self.year_full_radio.pack(side="left")

        preview_row = tk.Frame(outer, bg=S.BG)
        preview_row.pack(fill="x", pady=(6, 16))
        self.preview_caption = ttk.Label(preview_row, style="Subtitle.TLabel")
        self.preview_caption.pack(side="left")
        self.preview_value = tk.Label(
            preview_row, bg=S.BG, fg=S.ACCENT, font=S.FONT_MONO,
        )
        self.preview_value.pack(side="left", padx=(8, 0))

        self.preview_hint_label = ttk.Label(outer, style="Subtitle.TLabel", wraplength=540, justify="left")
        self.preview_hint_label.pack(fill="x", pady=(0, 14))

        ttk.Separator(outer, orient="horizontal").pack(fill="x", pady=(0, 12))

        # ======================================================= Автозапуск
        self.autostart_check = ttk.Checkbutton(
            outer, variable=self.autostart_var, style="TCheckbutton",
        )
        self.autostart_check.pack(anchor="w", pady=(0, 16))

        # ======================================================= Кнопки
        btn_bar = tk.Frame(outer, bg=S.BG)
        btn_bar.pack(fill="x", side="bottom", pady=(6, 0))

        self.btn_apply_now = ttk.Button(btn_bar, style="Secondary.TButton", command=self._apply_now)
        self.btn_apply_now.pack(side="left")

        right_btns = tk.Frame(btn_bar, bg=S.BG)
        right_btns.pack(side="right")
        self.btn_cancel = ttk.Button(right_btns, style="Secondary.TButton", command=self._on_cancel)
        self.btn_cancel.pack(side="right", padx=(8, 0))
        self.btn_save = ttk.Button(right_btns, style="Accent.TButton", command=self._on_save)
        self.btn_save.pack(side="right", padx=(8, 0))
        self.btn_reset = ttk.Button(right_btns, style="Danger.TButton", command=self._on_reset)
        self.btn_reset.pack(side="right", padx=(0, 0))

        self._apply_texts()

    def _section(self, parent, key):
        ttk.Label(parent, style="Section.TLabel", text=self.app.tr.t(key)).pack(anchor="w", pady=(0, 6))

    def _apply_texts(self):
        t = self.app.tr.t
        self.title(t("settings_title"))
        self.retention_hint_label.configure(
            text=t("settings_retention_hint", min=core.MIN_RETENTION_DAYS, max=core.MAX_RETENTION_DAYS)
        )
        self.btn_browse.configure(text=t("settings_browse"))
        self.btn_clear_path.configure(text=t("settings_clear_path"))
        self.btn_clear_time.configure(text=t("settings_clear_time"))
        self.run_time_hint_label.configure(text=t("settings_run_time_hint"))

        self.order_label.configure(text=t("settings_date_order"))
        self.order_combo.configure(values=[
            t("settings_date_order_dmy"), t("settings_date_order_mdy"), t("settings_date_order_ymd"),
        ])
        order_map = {"DMY": 0, "MDY": 1, "YMD": 2}
        self.order_combo.current(order_map[self.order_var.get()])
        self._order_display_to_code = {
            t("settings_date_order_dmy"): "DMY",
            t("settings_date_order_mdy"): "MDY",
            t("settings_date_order_ymd"): "YMD",
        }

        self.sep_label.configure(text=t("settings_separator"))
        self.sep_combo.configure(values=[
            t("settings_sep_dot"), t("settings_sep_dash"), t("settings_sep_comma"),
        ])
        sep_map = {".": 0, "-": 1, ",": 2}
        self.sep_combo.current(sep_map[self.separator_var.get()])
        self._sep_display_to_code = {
            t("settings_sep_dot"): ".",
            t("settings_sep_dash"): "-",
            t("settings_sep_comma"): ",",
        }

        self.year_label.configure(text=t("settings_year_format"))
        self.year_short_radio.configure(text=t("settings_year_short"))
        self.year_full_radio.configure(text=t("settings_year_full"))

        self.preview_caption.configure(text=t("settings_preview"))
        self.preview_hint_label.configure(text=t("settings_preview_hint"))

        self.autostart_check.configure(text=t("settings_autostart"))

        self.btn_apply_now.configure(text=t("settings_apply_now"))
        self.btn_cancel.configure(text=t("settings_cancel"))
        self.btn_save.configure(text=t("settings_save"))
        self.btn_reset.configure(text=t("settings_reset"))

    # -------------------------------------------------------------- events

    def _on_language_touched(self):
        self._language_touched = True

    def _validate_hour(self, proposed: str) -> bool:
        if proposed == "":
            return True
        if not proposed.isdigit():
            return False
        return 0 <= int(proposed) <= 23 and len(proposed) <= 2

    def _validate_minute(self, proposed: str) -> bool:
        if proposed == "":
            return True
        if not proposed.isdigit():
            return False
        return 0 <= int(proposed) <= 59 and len(proposed) <= 2

    def _browse_path(self):
        initial = self.path_var.get() or os.path.expanduser("~")
        chosen = filedialog.askdirectory(parent=self, initialdir=initial if os.path.isdir(initial) else None)
        if chosen:
            self.path_var.set(chosen)

    def _clear_path(self):
        self.path_var.set("")

    def _clear_time(self):
        self.hour_var.set("")
        self.minute_var.set("")

    def _on_format_changed(self):
        display = self.order_combo.get()
        if display in getattr(self, "_order_display_to_code", {}):
            self.order_var.set(self._order_display_to_code[display])
        sep_display = self.sep_combo.get()
        if sep_display in getattr(self, "_sep_display_to_code", {}):
            self.separator_var.set(self._sep_display_to_code[sep_display])
        self._update_preview()

    def _current_date_format(self) -> core.DateFormatSettings:
        return core.DateFormatSettings(
            order=self.order_var.get(),
            separator=self.separator_var.get(),
            year_format=self.year_format_var.get(),
        )

    def _update_preview(self):
        try:
            fmt = self._current_date_format()
            example = core.format_date(date.today(), fmt)
        except ValueError:
            example = "\u2014"
        self.preview_value.configure(text=example)

    # ------------------------------------------------------------ validate

    def _read_retention_days(self):
        raw = self.retention_var.get().strip()
        if not raw.isdigit():
            return None
        value = int(raw)
        if core.MIN_RETENTION_DAYS <= value <= core.MAX_RETENTION_DAYS:
            return value
        return None

    def _read_run_time(self):
        """Возвращает ("HH:MM" | None, ok: bool)."""
        h, m = self.hour_var.get().strip(), self.minute_var.get().strip()
        if h == "" and m == "":
            return None, True
        if h == "" or m == "":
            return None, False
        try:
            hi, mi = int(h), int(m)
        except ValueError:
            return None, False
        if not (0 <= hi <= 23 and 0 <= mi <= 59):
            return None, False
        return f"{hi:02d}:{mi:02d}", True

    # ------------------------------------------------------------- actions

    def _build_config_from_form(self, base: AppConfig) -> AppConfig | None:
        """Возвращает новый AppConfig на основе текущего состояния формы,
        либо None (и показывает ошибку), если форма невалидна."""
        t = self.app.tr.t

        retention_days = self._read_retention_days()
        if retention_days is None:
            messagebox.showerror(
                t("error_title"),
                t("settings_invalid_days", min=core.MIN_RETENTION_DAYS, max=core.MAX_RETENTION_DAYS),
                parent=self,
            )
            return None

        run_time, ok = self._read_run_time()
        if not ok:
            messagebox.showerror(t("error_title"), t("settings_run_time_hint"), parent=self)
            return None

        new_cfg = AppConfig(**base.to_dict())
        new_cfg.retention_days = retention_days
        new_cfg.archive_path = self.path_var.get().strip() or None
        new_cfg.run_time = run_time
        new_cfg.date_order = self.order_var.get()
        new_cfg.date_separator = self.separator_var.get()
        new_cfg.date_year_format = self.year_format_var.get()

        if self._language_touched:
            new_cfg.language = self.language_var.get()

        return new_cfg

    def _apply_now(self):
        t = self.app.tr.t
        path = self.path_var.get().strip()
        if not path:
            messagebox.showinfo(t("settings_apply_now"), t("settings_apply_now_no_path"), parent=self)
            return

        retention_days = self._read_retention_days()
        if retention_days is None:
            messagebox.showerror(
                t("error_title"),
                t("settings_invalid_days", min=core.MIN_RETENTION_DAYS, max=core.MAX_RETENTION_DAYS),
                parent=self,
            )
            return

        if not messagebox.askyesno(
            t("settings_apply_now_confirm_title"), t("settings_apply_now_confirm_text"), parent=self
        ):
            return

        fmt = self._current_date_format()
        report = core.perform_cleanup(path, fmt, retention_days, dry_run=False)

        if report.error == "path_missing":
            messagebox.showerror(t("error_title"), t("settings_path_invalid"), parent=self)
            return

        self.app.record_manual_check_timestamp()

        lines = []
        if report.retention and report.retention.reference_note != "normal":
            lines.append(t("settings_apply_now_result_no_reference"))
        else:
            lines.append(t("settings_apply_now_result_deleted", n=len(report.deleted_names)))
            lines.append(t("settings_apply_now_result_kept", n=len(report.retention.keep) if report.retention else 0))
        lines.append(t("settings_apply_now_result_ignored", n=len(report.scan.ignored)))
        if report.delete_errors:
            lines.append(t("settings_apply_now_result_errors", n=len(report.delete_errors)))

        messagebox.showinfo(t("settings_apply_now_result_title"), "\n".join(lines), parent=self)
        self.app.refresh_main_window()

    def _on_save(self):
        new_cfg = self._build_config_from_form(self.app.config)
        if new_cfg is None:
            return

        # Синхронизируем автозапуск с реальным состоянием реестра Windows.
        desired_autostart = self.autostart_var.get()
        ok = autostart.set_autostart(desired_autostart)
        if ok:
            new_cfg.autostart_enabled = desired_autostart
        else:
            # На Windows это означает сбой реестра; в среде разработки (не Windows)
            # автозапуск всегда возвращает False — сохраняем намерение пользователя
            # в конфиге, но реального переключения не происходит.
            new_cfg.autostart_enabled = self.app.config.autostart_enabled

        self.app.apply_new_config(new_cfg)
        self.destroy()

    def _on_reset(self):
        t = self.app.tr.t
        if not messagebox.askyesno(
            t("settings_reset_confirm_title"), t("settings_reset_confirm_text"), parent=self
        ):
            return

        defaults = AppConfig.defaults()
        self.language_var.set(defaults.effective_language())
        self._language_touched = False
        self.retention_var.set(str(defaults.retention_days))
        self.path_var.set("")
        self.hour_var.set("")
        self.minute_var.set("")
        self.order_var.set(defaults.date_order)
        self.separator_var.set(defaults.date_separator)
        self.year_format_var.set(defaults.date_year_format)
        self.autostart_var.set(False)
        self._apply_texts()
        self._update_preview()

    def _on_cancel(self):
        self.destroy()
