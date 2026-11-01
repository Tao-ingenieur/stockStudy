"""Windows graphical application. No console is needed."""

import os
import queue
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from . import __version__
from .application import AnalysisOutcome, analyze, make_request
from .cli import find_workspace
from .service import ScanCancelled

class StockStudyApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title(f"StockStudy {__version__} · 股票日线分析")
        root.geometry("1180x800")
        root.minsize(1000, 720)
        root.configure(background="#f4f6fb")
        self.events = queue.Queue()
        self.cancel_event = threading.Event()
        self.running = False
        self.outcome: AnalysisOutcome | None = None
        self.filter_after = None
        workspace = find_workspace()
        self.data = tk.StringVar(value=str(workspace / "stock_data/tongdaxin/hsjday.zip"))
        self.output = tk.StringVar(value=str(workspace / "output"))
        self.period = tk.StringVar(value="20")
        self.threshold = tk.StringVar(value="10")
        self.as_of = tk.StringVar()
        self.exclude_delisted = tk.BooleanVar(value=True)
        self.search = tk.StringVar()
        self.status = tk.StringVar(value="就绪 · 选择数据和策略后，点击开始分析")
        self.detail = tk.StringVar(value="价格使用不复权日线。日期留空时，各股票使用自身最后一条记录。")
        self.counts = tk.StringVar(value="命中记录  —       命中股票  —       读取异常  —")
        self.preview = tk.StringVar(value="分析后将在这里显示结果")
        self.rule = tk.StringVar()
        self._style()
        self._build()
        self.rule.set("规则：最新收盘价相对 N 条交易记录前收盘价，涨幅严格超过阈值；每只股票最多一条结果。")
        self.search.trace_add("write", self._schedule_filter)
        root.protocol("WM_DELETE_WINDOW", self._close)
        self.poll_after = root.after(100, self._poll)
        root.bind("<Destroy>", self._destroyed, add="+")

    def _style(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", font=("Microsoft YaHei UI", 10))
        style.configure("TFrame", background="#f4f6fb")
        style.configure("TLabel", background="#f4f6fb", foreground="#25324b")
        style.configure("Title.TLabel", font=("Microsoft YaHei UI", 24, "bold"), foreground="#172542")
        style.configure("Muted.TLabel", foreground="#63718a")
        style.configure("Stats.TLabel", font=("Microsoft YaHei UI", 12, "bold"), foreground="#224c94")
        style.configure("TLabelframe", background="#f4f6fb", bordercolor="#d5deed")
        style.configure("TLabelframe.Label", background="#f4f6fb", foreground="#25324b", font=("Microsoft YaHei UI", 11, "bold"))
        style.configure("TButton", padding=(12, 7))
        style.configure("Primary.TButton", background="#235dd3", foreground="white", font=("Microsoft YaHei UI", 10, "bold"))
        style.map("Primary.TButton", background=[("active", "#194db7"), ("disabled", "#c6d0e3")])
        style.configure("TEntry", padding=5)
        style.configure("Treeview", rowheight=29, background="white", fieldbackground="white", borderwidth=0)
        style.configure("Treeview.Heading", font=("Microsoft YaHei UI", 10, "bold"), padding=(8, 8))

    def _build(self):
        container = ttk.Frame(self.root, padding=(24, 16, 24, 16))
        container.pack(fill="both", expand=True)
        header = ttk.Frame(container)
        header.pack(fill="x", pady=(0, 16))
        ttk.Label(header, text="StockStudy", style="Title.TLabel").pack(side="left")
        ttk.Label(header, text=f"  本地日线分析  /  {__version__}", style="Muted.TLabel").pack(side="left", padx=10, pady=(10, 0))
        ttk.Button(header, text="关于与帮助", command=self.about).pack(side="right")

        settings = ttk.LabelFrame(container, text="分析设置", padding=(16, 12))
        settings.pack(fill="x")
        settings.columnconfigure(1, weight=1)
        ttk.Label(settings, text="行情数据").grid(row=0, column=0, sticky="w", padx=(0, 12), pady=5)
        self.data_entry = ttk.Entry(settings, textvariable=self.data)
        self.data_entry.grid(row=0, column=1, sticky="ew", pady=5)
        self.zip_button = ttk.Button(settings, text="选择 ZIP", command=self._choose_zip)
        self.zip_button.grid(row=0, column=2, padx=(8, 0))
        self.directory_button = ttk.Button(settings, text="选择目录", command=self._choose_data_dir)
        self.directory_button.grid(row=0, column=3, padx=(8, 0))
        ttk.Label(settings, text="结果保存").grid(row=1, column=0, sticky="w", padx=(0, 12), pady=5)
        self.output_entry = ttk.Entry(settings, textvariable=self.output)
        self.output_entry.grid(row=1, column=1, sticky="ew", pady=5)
        self.output_button = ttk.Button(settings, text="选择目录", command=self._choose_output)
        self.output_button.grid(row=1, column=2, columnspan=2, sticky="e")

        parameters = ttk.Frame(settings)
        parameters.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(12, 5))
        ttk.Label(parameters, text="策略").pack(side="left")
        ttk.Label(parameters, text="区间涨幅筛选").pack(side="left", padx=(8, 20))
        ttk.Label(parameters, text="比较周期 N").pack(side="left")
        self.period_entry = ttk.Entry(parameters, textvariable=self.period, width=7)
        self.period_entry.pack(side="left", padx=(8, 20))
        ttk.Label(parameters, text="末条日期").pack(side="left")
        self.date_entry = ttk.Entry(parameters, textvariable=self.as_of, width=13)
        self.date_entry.pack(side="left", padx=(8, 8))
        ttk.Label(parameters, text="YYYY-MM-DD，可留空", style="Muted.TLabel").pack(side="left")

        advanced = ttk.Frame(settings)
        advanced.grid(row=3, column=0, columnspan=4, sticky="ew", pady=5)
        ttk.Label(advanced, text="涨幅超过 (%)").pack(side="left")
        self.threshold_entry = ttk.Entry(advanced, textvariable=self.threshold, width=7)
        self.threshold_entry.pack(side="left", padx=(8, 20))
        ttk.Label(advanced, text="N=1 比较相邻两条记录；N=20 需21条记录。价格口径：不复权。", style="Muted.TLabel").pack(side="left")
        self.delisted_check = ttk.Checkbutton(advanced, text="排除已确认退市", variable=self.exclude_delisted)
        self.delisted_check.pack(side="right")
        ttk.Label(settings, textvariable=self.rule, style="Muted.TLabel", wraplength=1020).grid(row=4, column=0, columnspan=4, sticky="w", pady=(9, 0))

        actions = ttk.Frame(container)
        actions.pack(fill="x", pady=(14, 10))
        self.start_button = ttk.Button(actions, text="开始分析", style="Primary.TButton", command=self.start)
        self.start_button.pack(side="left")
        self.cancel_button = ttk.Button(actions, text="取消", command=self.cancel, state="disabled")
        self.cancel_button.pack(side="left", padx=8)
        self.progress = ttk.Progressbar(actions, mode="determinate", maximum=100, length=260)
        self.progress.pack(side="left", padx=(12, 16))
        ttk.Label(actions, textvariable=self.status).pack(side="left", fill="x", expand=True)

        ttk.Label(container, textvariable=self.counts, style="Stats.TLabel").pack(anchor="w", pady=(3, 12))
        tools = ttk.Frame(container)
        tools.pack(fill="x", pady=(0, 8))
        ttk.Label(tools, text="筛选结果", font=("Microsoft YaHei UI", 12, "bold")).pack(side="left")
        ttk.Label(tools, text="搜索代码 / 名称 / 日期", style="Muted.TLabel").pack(side="left", padx=(20, 8))
        ttk.Entry(tools, textvariable=self.search, width=24).pack(side="left")
        self.folder_button = ttk.Button(tools, text="打开结果目录", command=self.open_folder, state="disabled")
        self.folder_button.pack(side="right")
        self.csv_button = ttk.Button(tools, text="打开完整 CSV", command=self.open_csv, state="disabled")
        self.csv_button.pack(side="right", padx=8)

        footer = ttk.Frame(container)
        footer.pack(side="bottom", fill="x", pady=(8, 0))
        ttk.Label(footer, textvariable=self.preview, style="Muted.TLabel").pack(anchor="w", pady=(0, 4))
        ttk.Label(footer, textvariable=self.detail, style="Muted.TLabel", wraplength=1080).pack(anchor="w")
        table_frame = ttk.Frame(container)
        table_frame.pack(fill="both", expand=True)
        columns = ("symbol", "name", "date", "close", "base_date", "base_close", "gain")
        self.table = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        headings = ("股票代码", "股票名称", "截止日期", "收盘价", "基准日期", "基准收盘价", "涨幅（不复权）")
        widths = (110, 140, 120, 100, 120, 110, 140)
        for column, heading, width in zip(columns, headings, widths):
            self.table.heading(column, text=heading)
            self.table.column(column, width=width, minwidth=75, anchor="w" if column == "name" else "center")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        self.table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.table.tag_configure("alternate", background="#f2f6fc")
        self.inputs = [self.data_entry, self.output_entry, self.zip_button, self.directory_button,
                       self.output_button, self.period_entry, self.threshold_entry, self.date_entry, self.delisted_check]

    def _choose_zip(self):
        value = filedialog.askopenfilename(parent=self.root, title="选择通达信日线数据包", filetypes=[("ZIP 数据包", "*.zip"), ("全部文件", "*.*")])
        if value:
            self.data.set(value)

    def _choose_data_dir(self):
        value = filedialog.askdirectory(parent=self.root, title="选择含 sh/lday、sz/lday 的数据目录")
        if value:
            self.data.set(value)

    def _choose_output(self):
        value = filedialog.askdirectory(parent=self.root, title="选择分析结果保存目录")
        if value:
            self.output.set(value)

    def _set_running(self, running):
        self.running = running
        self.start_button.configure(state="disabled" if running else "normal")
        self.cancel_button.configure(state="normal" if running else "disabled")
        for widget in self.inputs:
            widget.configure(state="disabled" if running else "normal")

    def start(self):
        if self.running:
            return
        try:
            request = make_request(self.data.get(), self.output.get(), self.period.get(),
                                   self.threshold.get(), self.as_of.get(),
                                   include_delisted=not self.exclude_delisted.get())
        except ValueError as exc:
            messagebox.showerror("请检查分析设置", str(exc), parent=self.root)
            return
        self.cancel_event.clear()
        self._set_running(True)
        self.progress["value"] = 0
        self.status.set("正在读取行情数据……")
        self.detail.set("分析进行中。取消后不会生成本次报告，之前的结果不受影响。")
        threading.Thread(target=self._worker, args=(request,), daemon=True).start()

    def _worker(self, request):
        def progress(done, total):
            if done % 50 == 0 or done == total:
                self.events.put(("progress", (done, total)))
        try:
            outcome = analyze(request, progress=progress, cancelled=self.cancel_event.is_set)
            self.events.put(("done", outcome))
        except ScanCancelled:
            self.events.put(("cancelled", None))
        except Exception as exc:
            self.events.put(("error", str(exc)))

    def _poll(self):
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == "progress":
                    done, total = value
                    self.progress["value"] = 100 * done / total if total else 0
                    self.status.set(f"正在扫描 {done:,} / {total:,}")
                else:
                    self._set_running(False)
                    if kind == "done":
                        self.outcome = value
                        summary = value.summary
                        self.progress["value"] = 100
                        self.status.set("分析完成" if not summary["read_errors"] else "已完成，部分文件读取失败")
                        self.counts.set(f"命中记录  {summary['matches']:,}       命中股票  {summary['matched_securities']:,}       读取异常  {summary['read_errors']:,}")
                        self.detail.set(f"已保存到 {value.directory}。排除退市 {summary['delisted_excluded_count']}；状态未知 {summary['unknown_listing_status_count']}；历史不足 {summary['insufficient_history_count']}；无效收盘价 {summary['invalid_close_count']}。不复权涨幅可能受分红送转影响。")
                        self.folder_button.configure(state="normal")
                        self.csv_button.configure(state="normal")
                        self._render_rows()
                    elif kind == "cancelled":
                        self.status.set("已取消")
                        self.detail.set("本次分析已取消，未生成新报告。之前的结果仍可查看。")
                    elif kind == "error":
                        self.status.set("分析失败，请检查数据")
                        self.detail.set("本次分析未完成。请检查行情数据路径、数据格式和保存目录的写入权限。")
                        messagebox.showerror("分析失败", value, parent=self.root)
        except queue.Empty:
            pass
        self.poll_after = self.root.after(100, self._poll)

    def cancel(self):
        self.cancel_event.set()
        self.cancel_button.configure(state="disabled")
        self.status.set("正在取消，请稍候……")

    def _schedule_filter(self, *_args):
        if self.filter_after is not None:
            self.root.after_cancel(self.filter_after)
        self.filter_after = self.root.after(180, self._render_rows)

    def _render_rows(self):
        if self.filter_after is not None:
            self.root.after_cancel(self.filter_after)
        self.filter_after = None
        self.table.delete(*self.table.get_children())
        if self.outcome is None:
            return
        term = self.search.get().strip().lower()
        rows = [row for row in self.outcome.rows if not term or term in " ".join(
            str(row[key]) for key in ("market", "code", "name", "date")).lower()]
        for i, row in enumerate(rows[:2000]):
            gain = f"{row['gain_pct']:.4f}%"
            self.table.insert("", "end", values=(row["market"] + row["code"], row["name"] or "—", row["date"],
                row["close"], row["base_date"], row["base_close"], gain),
                tags=("alternate",) if i % 2 else ())
        self.preview.set(f"显示 {min(len(rows), 2000):,} / {len(rows):,} 条匹配记录 · 完整结果已保存为 CSV 和 JSON")

    def _open(self, path):
        try:
            os.startfile(str(path))
        except OSError as exc:
            messagebox.showerror("无法打开", f"{path}\n\n{exc}", parent=self.root)

    def open_folder(self):
        if self.outcome:
            self._open(self.outcome.directory)

    def open_csv(self):
        if self.outcome:
            self._open(self.outcome.directory / "matches.csv")

    def about(self):
        messagebox.showinfo("关于 StockStudy", f"StockStudy {__version__}\n\n选择通达信 ZIP 或数据目录，设置策略后开始分析。\n比较周期按各股票交易记录计数，N=20需21条日线。\n末条日期留空时不统一各股票的数据日期。\n\n价格不复权；分红送转可能影响涨幅。\n涨幅为收盘价比值，除权除息日可能不同于行情软件公布的单日涨幅。\n分析结果保存在指定目录，支持 CSV 和 JSON。", parent=self.root)

    def _close(self):
        if self.running:
            messagebox.showinfo("分析进行中", "请先取消分析，等待任务停止后再关闭窗口。", parent=self.root)
            return
        self.root.destroy()

    def _destroyed(self, event):
        if event.widget is self.root:
            for timer in (self.poll_after, self.filter_after):
                if timer is not None:
                    self.root.after_cancel(timer)


def main(argv=None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if arguments and sys.stdout is not None:
        from .cli import main as cli_main
        return cli_main(arguments)
    root = tk.Tk()
    if arguments and arguments[0] in {"--version", "-version", "-V", "--help", "-h"}:
        root.withdraw()
        messagebox.showinfo("StockStudy", f"StockStudy {__version__}\n\n双击程序打开图形界面。\n命令行分析请使用 dist/cli/stockstudy.pyz。", parent=root)
        root.destroy()
        return 0
    StockStudyApp(root)
    root.mainloop()
    return 0
