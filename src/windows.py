"""Bilingual desktop frontend with in-memory analysis and explicit export."""

import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from . import __version__
from .application import analyze, export_analysis, filter_results, make_request, MARKET_FILTERS
from .cli import find_workspace
from .i18n import translate
from .boards import BOARDS_BY_MARKET
from .service import ScanCancelled

STRATEGIES = {"gain": "gain", "ma-cross": "ma-cross", "breakout": "breakout"}


class StockStudyApp:
    def __init__(self, root):
        self.root = root
        root.geometry("1180x840")
        root.minsize(1000, 760)
        root.configure(background="#f4f6fb")
        self.language = tk.StringVar(value="zh")
        self.events = queue.Queue()
        self.cancel_event = threading.Event()
        self.running = False
        self.outcome = None
        self.exported_path = None
        self.exported_info = None
        self.help_window = None
        self.filter_after = None
        self.phase = "ready"
        self.done_count = self.total_count = 0
        self.progress_value = 0
        self.strategy_id = "gain"
        self.workspace = find_workspace()
        self.data = tk.StringVar(value=str(self.workspace / "stock_data/tongdaxin/hsjday.zip"))
        self.period = tk.StringVar(value="20")
        self.threshold = tk.StringVar(value="10")
        self.fast_period = tk.StringVar(value="5")
        self.slow_period = tk.StringVar(value="20")
        self.trend_period = tk.StringVar(value="120")
        self.trend_filter = tk.BooleanVar(value=True)
        self.breakout_period = tk.StringVar(value="20")
        self.volume_period = tk.StringVar(value="5")
        self.volume_multiple = tk.StringVar(value="1.5")
        self.as_of = tk.StringVar()
        self.result_market = tk.StringVar(value="all")
        self.result_board = tk.StringVar(value="all")
        self.search = tk.StringVar()
        self.status = tk.StringVar()
        self.counts = tk.StringVar()
        self.preview = tk.StringVar()
        self.detail = tk.StringVar()
        self._style()
        self._icon()
        self._build_view()
        self.search.trace_add("write", self._schedule_filter)
        root.protocol("WM_DELETE_WINDOW", self._close)
        self.poll_after = root.after(100, self._poll)
        root.bind("<Destroy>", self._destroyed, add="+")

    def t(self, key, **values):
        return translate(self.language.get(), key, **values)

    def _icon(self):
        bundled = Path(__file__).resolve().parent / "resources" / "candlestick.png"
        checkout = Path(__file__).resolve().parents[1] / "resources" / "candlestick.png"
        path = bundled if bundled.is_file() else checkout
        if path.is_file():
            self.icon = tk.PhotoImage(file=str(path))
            self.root.iconphoto(True, self.icon)

    def _style(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", font=("Microsoft YaHei UI", 10))
        style.configure("TFrame", background="#f4f6fb")
        style.configure("TLabel", background="#f4f6fb", foreground="#25324b")
        style.configure("Title.TLabel", font=("Microsoft YaHei UI", 22, "bold"), foreground="#172542")
        style.configure("Muted.TLabel", foreground="#63718a")
        style.configure("Stats.TLabel", font=("Microsoft YaHei UI", 11, "bold"), foreground="#224c94")
        style.configure("TLabelframe", background="#f4f6fb", bordercolor="#d5deed")
        style.configure("TLabelframe.Label", background="#f4f6fb", foreground="#25324b", font=("Microsoft YaHei UI", 11, "bold"))
        style.configure("TButton", padding=(10, 6))
        style.configure("Primary.TButton", background="#235dd3", foreground="white")
        style.map("Primary.TButton", background=[("active", "#194db7"), ("disabled", "#c6d0e3")])
        style.configure("TEntry", padding=5)
        style.configure("Treeview", rowheight=28, background="white", fieldbackground="white")
        style.configure("Treeview.Heading", font=("Microsoft YaHei UI", 10, "bold"), padding=(6, 7))

    def _menus(self):
        menu = tk.Menu(self.root)
        file = tk.Menu(menu, tearoff=False)
        file.add_command(label=self.t("zip"), command=self._choose_zip)
        file.add_command(label=self.t("folder"), command=self._choose_data_dir)
        file.add_separator()
        file.add_command(label=self.t("export"), command=self.export_results,
                         state="normal" if self.outcome and not self.running else "disabled")
        file.add_command(label=self.t("export_all"), command=lambda: self.export_results(all_results=True),
                         state="normal" if self.outcome and not self.running else "disabled")
        self.export_menu = file
        file.add_separator()
        file.add_command(label=self.t("exit"), command=self._close)
        menu.add_cascade(label=self.t("file"), menu=file)
        analysis = tk.Menu(menu, tearoff=False)
        analysis.add_command(label=self.t("start"), command=self.start, state="disabled" if self.running else "normal")
        analysis.add_command(label=self.t("cancel"), command=self.cancel, state="normal" if self.running else "disabled")
        menu.add_cascade(label=self.t("analysis"), menu=analysis)
        language = tk.Menu(menu, tearoff=False)
        for label, code in (("简体中文", "zh"), ("English", "en")):
            language.add_radiobutton(label=label, variable=self.language, value=code, command=self.switch_language)
        menu.add_cascade(label=self.t("language"), menu=language)
        about = tk.Menu(menu, tearoff=False)
        about.add_command(label=self.t("help"), command=self.show_help)
        about.add_separator()
        about.add_command(label=self.t("about"), command=self.about)
        menu.add_cascade(label=self.t("about_menu"), menu=about)
        self.root.configure(menu=menu)
        old = getattr(self, "menubar", None)
        self.menubar = menu
        if old is not None:
            old.destroy()

    def _build_view(self):
        self.root.title(f"{self.t('app')} {__version__}")
        if hasattr(self, "container"):
            self.container.destroy()
        self.container = container = ttk.Frame(self.root, padding=(20, 12))
        container.pack(fill="both", expand=True)
        header = ttk.Frame(container)
        header.pack(fill="x", pady=(0, 12))
        ttk.Label(header, text=self.t("app"), style="Title.TLabel").pack(side="left")
        ttk.Label(header, text=self.t("tagline"), style="Muted.TLabel").pack(side="left", padx=18, pady=(7, 0))

        self.settings_frame = settings = ttk.LabelFrame(container, text=self.t("settings"), padding=(12, 8))
        settings.pack(fill="x", pady=(0, 10))
        settings.columnconfigure(1, weight=1)
        ttk.Label(settings, text=self.t("data")).grid(row=0, column=0, padx=(0, 10), sticky="w")
        self.data_entry = ttk.Entry(settings, textvariable=self.data)
        self.data_entry.grid(row=0, column=1, sticky="ew", pady=4)
        self.zip_button = ttk.Button(settings, text=self.t("zip"), command=self._choose_zip)
        self.zip_button.grid(row=0, column=2, padx=(8, 0))
        self.directory_button = ttk.Button(settings, text=self.t("folder"), command=self._choose_data_dir)
        self.directory_button.grid(row=0, column=3, padx=(8, 0))
        options = ttk.Frame(settings)
        options.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(6, 4))
        ttk.Label(options, text=self.t("strategy")).pack(side="left")
        self.strategy_label = tk.StringVar(value=self.t(STRATEGIES[self.strategy_id]))
        self.strategy_box = ttk.Combobox(options, state="readonly", width=18, textvariable=self.strategy_label,
                                         values=[self.t(label) for label in STRATEGIES.values()])
        self.strategy_box.pack(side="left", padx=(8, 16))
        self.strategy_box.bind("<<ComboboxSelected>>", self._strategy_changed)
        ttk.Label(options, text=self.t("date")).pack(side="left")
        self.date_entry = ttk.Entry(options, textvariable=self.as_of, width=12)
        self.date_entry.pack(side="left", padx=8)
        ttk.Label(options, text=self.t("date_hint"), style="Muted.TLabel").pack(side="left")

        self.strategy_frame = ttk.LabelFrame(container, text=self.t("strategy_section"), padding=(12, 8))
        self.strategy_frame.pack(fill="x", pady=(0, 10))
        self._build_strategy()
        actions = ttk.Frame(container)
        actions.pack(fill="x", pady=(0, 10))
        self.start_button = ttk.Button(actions, text=self.t("start"), style="Primary.TButton", command=self.start)
        self.start_button.pack(side="left")
        self.cancel_button = ttk.Button(actions, text=self.t("cancel"), command=self.cancel)
        self.cancel_button.pack(side="left", padx=8)
        self.progress = ttk.Progressbar(actions, maximum=100, value=self.progress_value, length=210)
        self.progress.pack(side="left", padx=(8, 14))
        ttk.Label(actions, textvariable=self.status).pack(side="left")

        self.results_frame = results = ttk.LabelFrame(container, text=self.t("results"), padding=(12, 10))
        results.pack(fill="both", expand=True)
        tools = ttk.Frame(results)
        tools.pack(fill="x", pady=(0, 8))
        ttk.Label(tools, textvariable=self.counts, style="Stats.TLabel").pack(side="left")
        self.export_button = ttk.Button(tools, text=self.t("export"), command=self.export_results)
        self.export_button.pack(side="right")
        search = ttk.Frame(results)
        search.pack(fill="x", pady=(0, 8))
        ttk.Label(search, text=self.t("search"), style="Muted.TLabel").pack(side="left")
        ttk.Entry(search, textvariable=self.search, width=26).pack(side="left", padx=8)
        filters = ttk.Frame(results)
        filters.pack(fill="x", pady=(0, 8))
        ttk.Label(filters, text=self.t("market_filter")).pack(side="left")
        self.market_label = tk.StringVar(value=self.t("market_" + self.result_market.get()))
        self.market_box = ttk.Combobox(filters, textvariable=self.market_label, state="readonly", width=21,
                                       values=[self.t("market_" + key) for key in MARKET_FILTERS])
        self.market_box.pack(side="left", padx=(8, 18))
        self.market_box.bind("<<ComboboxSelected>>", self._filters_changed)
        ttk.Label(filters, text=self.t("board_filter")).pack(side="left")
        self.board_label = tk.StringVar()
        self.board_box = ttk.Combobox(filters, textvariable=self.board_label, state="readonly", width=22)
        self.board_box.pack(side="left", padx=(8, 18))
        self.board_box.bind("<<ComboboxSelected>>", self._board_changed)
        self._sync_boards()
        ttk.Button(filters, text=self.t("reset_filters"), command=self.reset_filters).pack(side="left")
        footer = ttk.Frame(results)
        footer.pack(side="bottom", fill="x", pady=(8, 0))
        ttk.Label(footer, textvariable=self.preview, style="Muted.TLabel", wraplength=1080).pack(anchor="w")
        self.detail_label = ttk.Label(footer, textvariable=self.detail, style="Muted.TLabel", wraplength=1080, justify="left")
        self.detail_label.pack(anchor="w", pady=(5, 0), fill="x")
        footer.bind("<Configure>", lambda e: self.detail_label.configure(wraplength=max(300, e.width - 5)))
        table_frame = ttk.Frame(results)
        table_frame.pack(fill="both", expand=True)
        self.table = ttk.Treeview(table_frame, show="headings", selectmode="browse")
        vertical = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        horizontal = ttk.Scrollbar(table_frame, orient="horizontal", command=self.table.xview)
        self.table.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        self.table.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        self.table.tag_configure("alternate", background="#f2f6fc")
        self.inputs = [self.data_entry, self.zip_button, self.directory_button,
                       self.date_entry] + self.strategy_inputs
        self._set_running(self.running)
        self._refresh_text()
        self._render_rows()

    def _build_strategy(self):
        for child in self.strategy_frame.winfo_children():
            child.destroy()
        # Each registered strategy owns its own parameter builder.
        {"gain": self._build_gain_parameters, "ma-cross": self._build_ma_parameters, "breakout": self._build_breakout_parameters}[self.strategy_id]()

    def _build_gain_parameters(self):
        row = ttk.Frame(self.strategy_frame)
        row.pack(fill="x")
        ttk.Label(row, text=self.t("period")).pack(side="left")
        self.period_entry = ttk.Entry(row, textvariable=self.period, width=7)
        self.period_entry.pack(side="left", padx=(8, 20))
        ttk.Label(row, text=self.t("threshold")).pack(side="left")
        self.threshold_entry = ttk.Entry(row, textvariable=self.threshold, width=7)
        self.threshold_entry.pack(side="left", padx=(8, 20))
        self.strategy_inputs = [self.period_entry, self.threshold_entry]
        ttk.Label(row, text=self.t("period_hint"), style="Muted.TLabel").pack(side="left")
        ttk.Label(self.strategy_frame, text=self.t("rule"), style="Muted.TLabel", wraplength=1000).pack(anchor="w", pady=(7, 0))

    def _build_breakout_parameters(self):
        row = ttk.Frame(self.strategy_frame)
        row.pack(fill="x")
        self.strategy_inputs = []
        for key, variable in (("breakout_period", self.breakout_period), ("volume_period", self.volume_period),
                              ("volume_multiple", self.volume_multiple)):
            ttk.Label(row, text=self.t(key)).pack(side="left")
            entry = ttk.Entry(row, textvariable=variable, width=7)
            entry.pack(side="left", padx=(8, 18))
            self.strategy_inputs.append(entry)
        ttk.Label(self.strategy_frame, text=self.t("breakout_rule"), style="Muted.TLabel", wraplength=1000).pack(anchor="w", pady=(7, 0))

    def _build_ma_parameters(self):
        row = ttk.Frame(self.strategy_frame)
        row.pack(fill="x")
        self.strategy_inputs = []
        for key, variable in (("fast_period", self.fast_period), ("slow_period", self.slow_period)):
            ttk.Label(row, text=self.t(key)).pack(side="left")
            entry = ttk.Entry(row, textvariable=variable, width=6)
            entry.pack(side="left", padx=(8, 18))
            self.strategy_inputs.append(entry)
        self.trend_check = ttk.Checkbutton(row, text=self.t("trend_filter"), variable=self.trend_filter,
                                           command=self._trend_changed)
        self.trend_check.pack(side="left", padx=(0, 12))
        self.strategy_inputs.append(self.trend_check)
        ttk.Label(row, text=self.t("trend_period")).pack(side="left")
        self.trend_entry = ttk.Entry(row, textvariable=self.trend_period, width=6)
        self.trend_entry.pack(side="left", padx=8)
        self.strategy_inputs.append(self.trend_entry)
        ttk.Label(self.strategy_frame, text=self.t("ma_hint"), style="Muted.TLabel").pack(anchor="w", pady=(6, 0))
        ttk.Label(self.strategy_frame, text=self.t("ma_rule"), style="Muted.TLabel", wraplength=1000).pack(anchor="w", pady=(4, 0))

    def _trend_changed(self):
        self.trend_entry.configure(state="normal" if self.trend_filter.get() and not self.running else "disabled")

    def _result_columns(self):
        s = self.outcome.summary if self.outcome else {}
        mode = s.get("strategy", self.strategy_id)
        columns = ["symbol", "name", "end_date", "close"]
        columns += {
            "ma-cross": ["fast_ma", "slow_ma", "trend_ma", "previous_fast_ma", "previous_slow_ma"],
            "breakout": ["prior_high", "breakout_pct", "volume", "average_volume", "volume_ratio"],
        }.get(mode, ["base_date", "base_close", "gain_column"])
        self.table.configure(columns=columns)
        for column in columns:
            if column in {"fast_ma", "previous_fast_ma"}:
                period = s.get("fast_period", self.fast_period.get())
            elif column in {"slow_ma", "previous_slow_ma"}:
                period = s.get("slow_period", self.slow_period.get())
            else:
                period = s.get("trend_period", self.trend_period.get())
            self.table.heading(column, text=self.t(column, period=period))
            self.table.column(column, width=140 if column == "name" else 120, minwidth=85,
                              anchor="w" if column == "name" else "center")

    def _strategy_changed(self, _event=None):
        labels = [self.t(label) for label in STRATEGIES.values()]
        self.strategy_id = list(STRATEGIES)[labels.index(self.strategy_label.get())]
        self._build_view()

    def switch_language(self):
        if self.help_window is not None and self.help_window.winfo_exists():
            self.help_window.destroy()
            self.help_window = None
        self._build_view()

    def _refresh_text(self):
        self.status.set(self.t(self.phase, done=self.done_count, total=self.total_count))
        if self.outcome is None:
            self.counts.set(self.t("stats_empty"))
            self.detail.set("")
            return
        s = self.outcome.summary
        self.counts.set(self.t("stats", matches=s["matched_securities"], read=s["securities_read"], errors=s["read_errors"]))
        common = dict(short=s["insufficient_history_count"], dates=s["date_mismatches"], invalid=s["invalid_close_count"])
        if s.get("strategy") == "ma-cross":
            trend = self.t("trend_on", period=s["trend_period"]) if s["trend_filter"] else self.t("trend_off")
            detail = self.t("ma_result", fast=s["fast_period"], slow=s["slow_period"], trend=trend, **common)
        elif s.get("strategy") == "breakout":
            detail = self.t("breakout_result", price_period=s["breakout_period"], volume_period=s["volume_period"],
                            multiple=s["volume_multiple"], volumes=s["invalid_volume_count"], **common)
        else:
            detail = self.t("result_summary", period=s["period"], threshold=s["gain_threshold_pct"], **common)
        detail += "\n" + self.t("adjustment")
        detail += "\n" + (self.t("exported_scope", path=self.exported_path,
                                       scope=self.t("scope_" + self.exported_info[0]), count=self.exported_info[1])
                           if self.exported_path else self.t("not_exported"))
        if self.phase == "cancelled":
            detail += "\n" + self.t("cancel_note")
        elif self.phase == "failed":
            detail += "\n" + self.t("error_note")
        self.detail.set(detail)

    def _choose_zip(self):
        if self.running:
            return
        value = filedialog.askopenfilename(parent=self.root, title=self.t("zip"), filetypes=[("ZIP", "*.zip"), ("All files", "*.*")])
        if value:
            self.data.set(value)

    def _choose_data_dir(self):
        if self.running:
            return
        value = filedialog.askdirectory(parent=self.root, title=self.t("folder"))
        if value:
            self.data.set(value)

    def _set_running(self, running):
        self.running = running
        self.start_button.configure(state="disabled" if running else "normal")
        self.cancel_button.configure(state="normal" if running else "disabled")
        self.export_button.configure(state="normal" if self.outcome and not running else "disabled")
        for widget in self.inputs:
            widget.configure(state="disabled" if running else "normal")
        if self.strategy_id == "ma-cross":
            self._trend_changed()
        self.strategy_box.configure(state="disabled" if running else "readonly")
        self._menus()

    def start(self):
        if self.running:
            return
        try:
            request = make_request(self.data.get(), self.period.get(), self.threshold.get(), self.as_of.get(),
                                   language=self.language.get(),
                                   strategy_name=self.strategy_id, fast_period=self.fast_period.get(),
                                   slow_period=self.slow_period.get(), trend_filter=self.trend_filter.get(),
                                   trend_period=self.trend_period.get(), breakout_period=self.breakout_period.get(),
                                   volume_period=self.volume_period.get(), volume_multiple=self.volume_multiple.get())
        except ValueError as exc:
            messagebox.showerror(self.t("check"), str(exc), parent=self.root)
            return
        self.cancel_event.clear()
        self.phase = "starting"
        self.progress_value = 0
        self.progress["value"] = 0
        self._set_running(True)
        self._refresh_text()
        threading.Thread(target=self._worker, args=(request,), daemon=True).start()

    def _worker(self, request):
        def progress(done, total):
            if done % 50 == 0 or done == total:
                self.events.put(("progress", (done, total)))
        try:
            self.events.put(("done", analyze(request, progress=progress, cancelled=self.cancel_event.is_set)))
        except ScanCancelled:
            self.events.put(("cancelled", None))
        except Exception as exc:
            self.events.put(("failed", str(exc)))

    def _poll(self):
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == "progress":
                    self.done_count, self.total_count = value
                    self.progress_value = 100 * self.done_count / self.total_count if self.total_count else 0
                    self.progress["value"] = self.progress_value
                    if self.phase != "cancelling":
                        self.phase = "running"
                else:
                    self.phase = kind
                    if kind == "done":
                        self.outcome = value
                        self.exported_path = None
                        self.exported_info = None
                        self.phase = "partial" if value.summary["read_errors"] else "done"
                        self.progress_value = 100
                        self.progress["value"] = 100
                        self._render_rows()
                    self._set_running(False)
                    if kind == "failed":
                        messagebox.showerror(self.t("failed"), value, parent=self.root)
                self._refresh_text()
        except queue.Empty:
            pass
        self.poll_after = self.root.after(100, self._poll)

    def cancel(self):
        if self.running:
            self.cancel_event.set()
            self.phase = "cancelling"
            self.cancel_button.configure(state="disabled")
            self._refresh_text()

    def _filter_values(self):
        return dict(market=self.result_market.get(), board=self.result_board.get(),
                    query=self.search.get().strip())

    def _filtered_rows(self):
        return filter_results(self.outcome.rows, **self._filter_values()) if self.outcome else []

    def _filters_changed(self, _event=None):
        markets = list(MARKET_FILTERS)
        self.result_market.set(markets[[self.t("market_" + key) for key in markets].index(self.market_label.get())])
        self._sync_boards()
        self._render_rows()

    def _board_text(self, key):
        if self.result_market.get() == "bj" and key == "all":
            return self.t("board_bj_all")
        return self.t("board_" + key)

    def _sync_boards(self):
        choices = BOARDS_BY_MARKET[self.result_market.get()]
        if self.result_board.get() not in choices:
            self.result_board.set("all")
        self.board_box.configure(values=[self._board_text(key) for key in choices],
                                 state="disabled" if len(choices) == 1 else "readonly")
        self.board_label.set(self._board_text(self.result_board.get()))

    def _board_changed(self, _event=None):
        choices = BOARDS_BY_MARKET[self.result_market.get()]
        self.result_board.set(choices[[self._board_text(key) for key in choices].index(self.board_label.get())])
        self._render_rows()

    def reset_filters(self):
        self.result_market.set("all")
        self.result_board.set("all")
        self._sync_boards()
        self.market_label.set(self.t("market_all"))
        self.search.set("")
        self._render_rows()

    def _schedule_filter(self, *_args):
        if self.filter_after is not None:
            self.root.after_cancel(self.filter_after)
        self.filter_after = self.root.after(180, self._render_rows)

    def _render_rows(self):
        if self.filter_after is not None:
            self.root.after_cancel(self.filter_after)
        self.filter_after = None
        self.table.delete(*self.table.get_children())
        self._result_columns()
        if self.outcome is None:
            self.preview.set(self.t("preview_empty"))
            return
        rows = self._filtered_rows()
        for i, row in enumerate(rows[:2000]):
            values = [row["market"] + row["code"], row["name"] or "—", row["date"], row["close"]]
            if self.outcome.summary.get("strategy") == "ma-cross":
                values += [row[key] or "—" for key in ("fast_ma", "slow_ma", "trend_ma", "previous_fast_ma", "previous_slow_ma")]
            elif self.outcome.summary.get("strategy") == "breakout":
                values += [row["prior_high"], f"{row['breakout_pct']:.4f}%", f"{row['volume'] / 10000:.2f}",
                           f"{row['average_volume'] / 10000:.2f}", f"{row['volume_ratio']:.4f}"]
            else:
                values += [row["base_date"], row["base_close"], f"{row['gain_pct']:.4f}%"]
            self.table.insert("", "end", values=values, tags=("alternate",) if i % 2 else ())
        self.preview.set(self.t("preview", shown=min(len(rows), 2000), filtered=len(rows), total=len(self.outcome.rows)))

    def export_results(self, *, all_results=False):
        if self.outcome is None or self.running:
            return
        folder = filedialog.askdirectory(parent=self.root, title=self.t("export_folder"),
                                         initialdir=str(self.workspace / "output") if (self.workspace / "output").exists() else str(self.workspace))
        if not folder:
            return
        try:
            path = export_analysis(self.outcome, Path(folder), filters=None if all_results else self._filter_values())
            self.exported_path = path
            self.exported_info = ("all", len(self.outcome.rows)) if all_results else ("filtered", len(self._filtered_rows()))
        except (OSError, ValueError) as exc:
            messagebox.showerror(self.t("export_failed"), str(exc), parent=self.root)
        self._refresh_text()

    def about(self):
        messagebox.showinfo(self.t("about"), f"{self.t('app')}\n{__version__}", parent=self.root)

    def show_help(self):
        if self.help_window is not None and self.help_window.winfo_exists():
            self.help_window.lift()
            return
        self.help_window = window = tk.Toplevel(self.root)
        window.title(self.t("help"))
        window.geometry("760x570")
        window.transient(self.root)
        body = ttk.Frame(window, padding=18)
        body.pack(fill="both", expand=True)
        scrollbar = ttk.Scrollbar(body)
        scrollbar.pack(side="right", fill="y")
        text = tk.Text(body, wrap="word", font=("Microsoft YaHei UI", 11), relief="flat", padx=12, pady=12,
                       yscrollcommand=scrollbar.set)
        text.pack(fill="both", expand=True)
        scrollbar.configure(command=text.yview)
        text.insert("1.0", self.t("help_body"))
        text.configure(state="disabled")

    def _close(self):
        if self.running:
            messagebox.showinfo(self.t("analysis"), self.t("running_close"), parent=self.root)
            return
        self.root.destroy()

    def _destroyed(self, event):
        if event.widget is self.root:
            for timer in (self.poll_after, self.filter_after):
                if timer is not None:
                    self.root.after_cancel(timer)


def main(argv=None):
    arguments = sys.argv[1:] if argv is None else argv
    if arguments and sys.stdout is not None:
        from .cli import main as cli_main
        return cli_main(arguments)
    root = tk.Tk()
    if arguments and arguments[0] in {"--version", "-version", "-V", "--help", "-h"}:
        root.withdraw()
        messagebox.showinfo("股票分析", f"股票分析 {__version__}\n\n双击打开程序；使用帮助位于“关于”菜单。", parent=root)
        root.destroy()
        return 0
    StockStudyApp(root)
    root.mainloop()
    return 0
