"""Desktop translations. Stable keys keep result data independent of language."""

TEXT = {
    "app": ("股票分析", "Stock Analysis"),
    "tagline": ("本地行情 · 策略筛选", "Local market data · Strategy screening"),
    "file": ("文件", "File"), "analysis": ("分析", "Analysis"),
    "language": ("语言", "Language"), "about_menu": ("关于", "About"),
    "help": ("使用帮助", "Help"), "about": ("关于股票分析", "About Stock Analysis"),
    "exit": ("退出", "Exit"), "settings": ("分析设置", "Analysis Settings"),
    "strategy_section": ("分析策略", "Analysis Strategy"), "results": ("分析结果", "Analysis Results"),
    "data": ("行情数据", "Market data"), "zip": ("选择 ZIP", "Choose ZIP"),
    "folder": ("选择目录", "Choose folder"), "date": ("末条日期", "Latest date"),
    "date_hint": ("YYYY-MM-DD，留空使用各股票最新记录", "YYYY-MM-DD; blank uses each stock's latest record"),
    "exclude": ("排除已确认退市", "Exclude confirmed delisted stocks"),
    "strategy": ("策略", "Strategy"), "gain": ("区间涨幅筛选", "Interval Gain"),
    "period": ("比较周期 N", "Period N"), "threshold": ("涨幅超过 (%)", "Gain above (%)"),
    "period_hint": ("按交易记录计数；N=20 需要21条日线。", "Count trading records; N=20 requires 21 daily bars."),
    "rule": ("最新收盘价 ÷ N 条记录前收盘价 − 1 > 阈值；每只股票最多一条结果。", "Latest close / close N records earlier − 1 > threshold; at most one result per stock."),
    "start": ("开始分析", "Start Analysis"), "cancel": ("取消", "Cancel"),
    "export": ("导出分析结果", "Export Results"), "search": ("搜索代码 / 名称 / 日期", "Search code / name / date"),
    "ready": ("就绪", "Ready"), "running": ("正在扫描 {done:,} / {total:,}", "Scanning {done:,} / {total:,}"),
    "starting": ("正在读取行情数据……", "Reading market data…"),
    "done": ("分析完成", "Analysis complete"), "partial": ("分析完成，部分文件读取失败", "Complete; some files could not be read"),
    "cancelled": ("已取消", "Cancelled"), "cancelling": ("正在取消，请稍候……", "Cancelling…"),
    "failed": ("分析失败", "Analysis failed"),
    "stats_empty": ("命中股票  —     读取异常  —", "Matched stocks  —     Read errors  —"),
    "stats": ("命中股票  {matches:,}     已读取  {read:,}     读取异常  {errors:,}", "Matched stocks  {matches:,}     Read  {read:,}     Read errors  {errors:,}"),
    "preview_empty": ("分析后在此查看结果。点击导出后才保存文件。", "Results appear here after analysis. Files are saved only when you export."),
    "preview": ("显示 {shown:,} / {filtered:,} 条，共 {total:,} 条。导出包含完整结果，不受搜索条件影响。", "Showing {shown:,} / {filtered:,} filtered rows; {total:,} total. Export includes all results."),
    "result_summary": ("周期 {period}；涨幅 > {threshold}%。排除退市 {delisted}；历史不足 {short}；日期不符 {dates}；无效收盘价 {invalid}。", "Period {period}; gain > {threshold}%. Delisted excluded {delisted}; insufficient history {short}; date mismatch {dates}; invalid close {invalid}."),
    "adjustment": ("复权情况：当前数据未提供复权因子，本次按不复权价格分析，分红送转可能影响涨幅。", "Adjustment: no adjustment factors are available in this dataset. Raw prices were used; dividends and share changes may affect gains."),
    "not_exported": ("结果仅保留在当前窗口，尚未导出。", "Results are kept in this window and have not been exported."),
    "exported": ("已导出至：{path}", "Exported to: {path}"),
    "cancel_note": ("本次分析已取消。上一次完成的结果仍保留。", "This analysis was cancelled. The last completed result is retained."),
    "error_note": ("请检查行情路径和数据格式。上一次完成的结果仍保留。", "Check the data path and format. The last completed result is retained."),
    "check": ("请检查分析设置", "Check Analysis Settings"),
    "missing_data": ("请选择通达信 ZIP 文件或解压后的数据目录。", "Choose a Tongdaxin ZIP file or extracted data folder."),
    "bad_path": ("行情路径不存在：{path}", "Market data path does not exist: {path}"),
    "bad_parameters": ("比较周期须为正整数，涨幅阈值须为非负有限数值。", "Period must be a positive integer; gain threshold must be finite and nonnegative."),
    "bad_date": ("末条日期请使用 YYYY-MM-DD 格式，或留空。", "Use YYYY-MM-DD for the latest date, or leave it blank."),
    "export_folder": ("选择分析结果导出目录", "Choose an export folder"),
    "export_failed": ("导出失败", "Export failed"),
    "running_close": ("请先取消分析，等待任务停止后再关闭窗口。", "Cancel the analysis and wait for it to stop before closing."),
    "symbol": ("股票代码", "Stock Code"), "name": ("股票名称", "Stock Name"),
    "end_date": ("截止日期", "End Date"), "close": ("收盘价", "Close"),
    "base_date": ("基准日期", "Base Date"), "base_close": ("基准收盘价", "Base Close"),
    "gain_column": ("涨幅", "Gain"),
    "help_body": (
        "1. 在分析设置中选择通达信 ZIP 或日线数据目录，可设置末条日期和退市过滤。\n\n2. 从策略下拉框选择策略，下面的分析策略区域显示该策略的参数。区间涨幅默认比较20条记录前的收盘价，阈值为严格超过10%；N=1比较相邻两条记录。\n\n3. 点击开始分析，结果显示在表格中。搜索只影响预览，最多显示2000条；导出包含全部结果。\n\n4. 分析不会自动保存文件。点击导出筛选结果或文件菜单中的导出全部结果并选择目录，生成 CSV、JSON 和汇总文件。关闭程序后未导出的结果不保留。\n\n5. 末条日期仅要求股票文件的最后一条记录恰为该日期，不是历史回放。留空时不同股票的截止日期可能不同。\n\n6. 复权情况在结果摘要中显示。当前通达信日线未提供复权因子，分红送转可能影响价格比较。筛选结果不代表买入建议。",
        "1. Choose a Tongdaxin ZIP or daily-bar folder in Analysis Settings. Optionally set a latest date and exclude confirmed delisted stocks.\n\n2. Select a strategy from the dropdown. Its parameters appear in Analysis Strategy. Interval Gain defaults to a 20-record period and a gain strictly above 10%. N=1 compares adjacent records.\n\n3. Start analysis to populate the table. Search affects the preview only (up to 2,000 rows); export includes all results.\n\n4. Analysis does not save files automatically. Choose Export Filtered or File > Export All and a folder to create CSV, JSON and summary files. Unexported results are lost when the app closes.\n\n5. Latest date requires the final bar to match that date; it is not a historical replay. Blank allows stocks with different final dates. \n\n6. Adjustment availability appears in the result summary. Current Tongdaxin bars have no adjustment factors; corporate actions may distort price changes. Screening is not a buy recommendation."
    ),
}


TEXT.update({
    "ma-cross": ("双均线金叉", "MA Crossover"),
    "fast_period": ("短期均线", "Fast MA"), "slow_period": ("长期均线", "Slow MA"),
    "trend_filter": ("收盘价高于趋势均线", "Close above trend MA"),
    "trend_period": ("趋势均线周期", "Trend period"),
    "ma_rule": ("上一条短均线 ≤ 长均线，最新短均线 > 长均线；勾选趋势过滤时还需最新收盘价 > 趋势均线。", "Previous fast MA ≤ slow MA; latest fast MA > slow MA. With the trend filter, latest close must also be above the trend MA."),
    "ma_hint": ("默认5/20日金叉，趋势过滤默认120日；历史不足则跳过。", "Defaults: 5/20 crossover with a 120-bar trend filter. Insufficient history is skipped."),
    "bad_ma_parameters": ("均线周期须为正整数，短期必须小于长期；趋势过滤开启时须提供正整数周期。", "MA periods must be positive integers with fast < slow; an enabled trend filter requires a positive period."),
    "fast_ma": ("MA{period}", "MA{period}"), "slow_ma": ("MA{period}", "MA{period}"),
    "trend_ma": ("趋势MA{period}", "Trend MA{period}"),
    "previous_fast_ma": ("上条MA{period}", "Previous MA{period}"),
    "previous_slow_ma": ("上条MA{period}", "Previous MA{period}"),
    "ma_result": ("MA{fast} 上穿 MA{slow}；{trend}。排除退市 {delisted}；历史不足 {short}；日期不符 {dates}；无效收盘价 {invalid}。", "MA{fast} crossed above MA{slow}; {trend}. Delisted excluded {delisted}; insufficient history {short}; date mismatch {dates}; invalid close {invalid}."),
    "trend_on": ("要求收盘价 > MA{period}", "close > MA{period} required"),
    "trend_off": ("未启用趋势过滤", "trend filter disabled"),
})
TEXT["adjustment"] = ("复权情况：当前数据未提供复权因子，本次按不复权价格分析，分红送转可能影响价格比较和均线信号。", "Adjustment: no adjustment factors are available. Raw prices were used; corporate actions may affect price comparisons and MA signals.")
TEXT["help_body"] = tuple(body + extra for body, extra in zip(TEXT["help_body"], (
    "\n\n双均线金叉：默认5日均线上穿20日均线，上一条短线不高于长线、最新短线严格高于长线。默认勾选收盘价严格高于120日均线；可取消过滤或修改周期。仅金叉发生的最新记录命中，已维持多日的多头排列不算新金叉。开启默认过滤需120条日线，关闭时需21条。",
    "\n\nMA Crossover: defaults to the 5-bar SMA crossing above the 20-bar SMA on the latest record. Previous fast SMA must be at or below slow SMA. Close above the 120-bar trend SMA is enabled by default and can be disabled. A continuing bullish alignment is not a new crossover. Default history required: 120 bars with the filter, 21 without it."
)))


TEXT.update({
    "market_filter": ("市场", "Market"),
    "market_all": ("全部市场", "All Markets"), "market_sh": ("上海 (sh)", "Shanghai (sh)"),
    "market_sz": ("深圳 (sz)", "Shenzhen (sz)"), "market_bj": ("北京 (bj)", "Beijing (bj)"),
    "market_shsz": ("沪深 (sh+sz)", "Shanghai + Shenzhen"),
    "status_filter": ("上市状态", "Listing Status"), "status_all": ("全部状态", "All Statuses"),
    "status_listed": ("仍上市", "Listed"), "status_delisted": ("已退市", "Delisted"),
    "status_unknown": ("未知", "Unknown"), "listing_status": ("上市状态", "Listing Status"),
    "reset_filters": ("重置筛选", "Reset Filters"),
    "export": ("导出筛选结果", "Export Filtered"),
    "export_all": ("导出全部结果", "Export All"),
    "preview": ("筛选结果 {filtered:,} 条，显示 {shown:,} 条；原始结果 {total:,} 条。导出筛选结果包含全部匹配行，不限预览条数。", "Filtered: {filtered:,}; showing {shown:,} of {total:,} original rows. Filtered export includes every match, beyond the preview limit."),
    "exported_scope": ("最近导出：{scope}，{count:,} 条。目录：{path}", "Last export: {scope}, {count:,} rows. Folder: {path}"),
    "scope_filtered": ("筛选结果", "Filtered results"), "scope_all": ("全部结果", "All results"),
})
TEXT["help_body"] = tuple(body.replace(old, new) + extra for body, old, new, extra in zip(TEXT["help_body"],
    ("搜索只影响预览，最多显示2000条；导出包含全部结果。", "Search affects the preview only (up to 2,000 rows); export includes all results."),
    ("结果可按市场和关键词组合筛选，最多预览2000条。", "Combine market and keyword filters; the preview shows up to 2,000 rows."),
    ("\n\n结果筛选不会重新扫描或修改原始结果。市场支持上海、深圳、北京及沪深。上市状态保留在导出文件中，界面暂不展示。重置筛选恢复全部结果。导出筛选结果保存所有符合条件的行；文件菜单中的导出全部结果不受筛选影响。汇总保留原始分析统计，并单独记录导出范围、导出条数和筛选条件。",
     "\n\nResult filters do not rescan or modify the original results. Reset Filters restores all rows. Export Filtered saves all matching rows; File > Export All ignores result filters. Summaries retain original analysis statistics and separately record export scope, row count and filter criteria.")
))


def translate(language, key, **values):
    return TEXT[key][language == "en"].format(**values)
