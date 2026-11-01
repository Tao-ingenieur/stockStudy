"""Desktop translations. Stable keys keep result data independent of language."""

TEXT = {
    "app": ("淘金人股票分析", "Taojinren Stock Analysis"),
    "tagline": ("本地行情 · 策略筛选", "Local market data · Strategy screening"),
    "file": ("文件", "File"), "analysis": ("分析", "Analysis"),
    "language": ("语言", "Language"), "about_menu": ("关于", "About"),
    "help": ("使用帮助", "Help"), "about": ("关于淘金人股票分析", "About Taojinren Stock Analysis"),
    "exit": ("退出", "Exit"), "settings": ("分析设置", "Analysis Settings"),
    "strategy_section": ("分析策略", "Analysis Strategy"), "results": ("分析结果", "Analysis Results"),
    "data": ("行情数据", "Market data"), "zip": ("选择 ZIP", "Choose ZIP"),
    "folder": ("选择目录", "Choose folder"), "date": ("末条日期", "Latest date"),
    "date_hint": ("YYYY-MM-DD，留空使用行情数据中的最新交易日", "YYYY-MM-DD; blank uses the latest trading date in the market data"),
    "strategy": ("策略", "Strategy"), "gain": ("区间涨幅筛选", "Interval Gain"),
    "period": ("比较周期 N", "Period N"), "threshold": ("涨幅阈值 (%)", "Gain threshold (%)"),
    "period_hint": ("按交易记录计数；N=20 需要21条日线。", "Count trading records; N=20 requires 21 daily bars."),
    "rule": ("最新收盘价 ÷ N 条记录前收盘价 − 1 ≥ 阈值；每只股票最多一条结果。", "Latest close / close N records earlier − 1 ≥ threshold; at most one result per stock."),
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
    "result_summary": ("周期 {period}；涨幅 ≥ {threshold}%。历史不足 {short}；日期不符 {dates}；无效收盘价 {invalid}。", "Period {period}; gain ≥ {threshold}%. insufficient history {short}; date mismatch {dates}; invalid close {invalid}."),
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

}


TEXT.update({
    "ma-cross": ("双均线金叉", "MA Crossover"),
    "fast_period": ("短期均线", "Fast MA"), "slow_period": ("长期均线", "Slow MA"),
    "trend_filter": ("收盘价高于趋势均线", "Close above trend MA"),
    "trend_period": ("趋势均线周期", "Trend period"),
    "ma_rule": ("上一条短均线 ≤ 长均线，最新短均线 > 长均线；勾选趋势过滤时还需最新收盘价 > 趋势均线。", "Previous fast MA ≤ slow MA; latest fast MA > slow MA. With the trend filter, latest close must also be above the trend MA."),
    "ma_hint": ("默认5/20金叉，趋势过滤默认120日。放量确认默认关闭；开启时需成交量 ≥ 前M条均量 × 倍数，不含当天。", "Defaults: 5/20 crossover with 120-bar trend filter. Volume confirmation is off by default; enable it to require volume ≥ prior M-bar mean × multiple, excluding today."),
    "ma_volume_filter": ("放量确认（可选）", "Volume confirmation (optional)"),
    "ma_volume_off": ("放量确认：未启用，不检查成交量。", "Volume confirmation: off; volume is not tested."),
    "ma_volume_on": ("放量确认：成交量 ≥ 前{period}条均量 × {multiple}；无效成交量 {invalid}。", "Volume confirmation: volume ≥ prior {period}-bar mean × {multiple}; invalid volume {invalid}."),
    "bad_ma_parameters": ("均线周期须为正整数，短期须小于长期；启用的趋势/均量周期须为正整数，成交量倍数须为正的有限数值。", "MA periods must be positive integers with fast < slow. Enabled trend/volume windows must be positive integers; volume multiple must be finite and positive."),
    "fast_ma": ("MA{period}", "MA{period}"), "slow_ma": ("MA{period}", "MA{period}"),
    "trend_ma": ("趋势MA{period}", "Trend MA{period}"),
    "previous_fast_ma": ("上条MA{period}", "Previous MA{period}"),
    "previous_slow_ma": ("上条MA{period}", "Previous MA{period}"),
    "ma_result": ("MA{fast} 上穿 MA{slow}；{trend}。历史不足 {short}；日期不符 {dates}；无效收盘价 {invalid}。", "MA{fast} crossed above MA{slow}; {trend}. insufficient history {short}; date mismatch {dates}; invalid close {invalid}."),
    "trend_on": ("要求收盘价 > MA{period}", "close > MA{period} required"),
    "trend_off": ("未启用趋势过滤", "trend filter disabled"),
})
TEXT["adjustment"] = ("复权情况：当前数据未提供复权因子，本次按不复权价格分析，分红送转可能影响价格比较和均线信号。", "Adjustment: no adjustment factors are available. Raw prices were used; corporate actions may affect price comparisons and MA signals.")


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


TEXT.update({
    "board_filter": ("板块", "Board"), "board_all": ("全部板块", "All Boards"),
    "board_sh-main": ("上海主板", "Shanghai Main Board"),
    "board_star": ("科创板", "STAR Market"),
    "board_sz-main": ("深圳主板", "Shenzhen Main Board"),
    "board_chinext": ("创业板", "ChiNext"),
    "board_bse": ("北交所", "Beijing Exchange"),
    "board_other": ("其他 / 未识别", "Other / Unclassified"),
    "board_bj_all": ("北交所（不细分）", "Beijing (no subdivision)"),
})


TEXT.update({
    "breakout": ("放量突破", "Volume Breakout"),
    "breakout_period": ("价格窗口 N", "Price window N"),
    "volume_period": ("均量窗口 M", "Volume window M"),
    "volume_multiple": ("成交量倍数 ≥", "Volume multiple ≥"),
    "breakout_rule": ("收盘价 > 前N条最高价，成交量 ≥ 前M条均量 × 倍数；两个窗口均不含当天。", "Close > highest high of prior N bars; volume ≥ mean volume of prior M bars × multiple. Both windows exclude today."),
    "bad_breakout_parameters": ("价格和均量窗口须为正整数，成交量倍数须为正的有限数值。", "Price and volume windows must be positive integers; volume multiple must be finite and positive."),
    "prior_high": ("前期最高价", "Prior high"),
    "breakout_pct": ("突破幅度", "Breakout (%)"),
    "volume": ("成交量（万股）", "Volume (10k shares)"),
    "average_volume": ("历史均量（万股）", "Mean volume (10k shares)"),
    "volume_ratio": ("成交量倍数", "Volume multiple"),
    "breakout_result": ("突破前{price_period}条高点；成交量 ≥ 前{volume_period}条均量 × {multiple}。历史不足 {short}；日期不符 {dates}；无效价格 {invalid}；无效成交量 {volumes}。", "Prior {price_period}-bar high breakout; volume ≥ prior {volume_period}-bar mean × {multiple}. Short history {short}; date mismatch {dates}; invalid price {invalid}; invalid volume {volumes}."),
})

TEXT["help_body"] = (
    "一、基本使用\n\n淘金人股票分析：读取本地日线，按所选条件筛选股票。\n\n"
    "选择通达信 ZIP 或日线目录，选择策略、填写参数后开始分析；扫描可取消。每只股票只检查最新一条记录，最多命中一条。\n\n"
    "末条日期留空使用行情数据中的最新交易日；填写日期时，股票文件的末条记录必须恰为该日，不是历史回放。上市状态不参与筛选。\n\n"
    "结果可按市场、板块和代码/名称/日期搜索；最多预览2000条，导出不受此限制。点击“导出筛选结果”保存匹配行；文件菜单的“导出全部结果”保存原始结果。取消选择不保存，关闭窗口前请导出需要保留的结果。\n\n"
    "当前按不复权价格分析，分红送转可能影响结果。筛选结果不代表买入建议。\n\n"
    "二、策略说明\n\n"
    "2.1 区间涨幅\n"
    "最新收盘价相对N条记录前的收盘价，涨幅大于等于阈值即命中。默认N=20、阈值10%，需21条记录。周期1、阈值9.9%可粗筛单日接近10%涨停的股票，不是精确涨停判断。\n\n"
    "2.2 双均线金叉\n"
    "上一条短均线≤长均线，最新短均线>长均线。默认5/20，且要求收盘价>120日均线；可取消趋势条件。默认需120条记录，取消后需21条。连续多日短线在长线上方不算新金叉。\n"
    "可选“放量确认”默认关闭：开启后还需成交量≥此前M条均量×倍数，默认M=5、倍数1.5，均量不含当天。它与MA120条件独立，两者勾选哪个就检查哪个；关闭放量时不检查或展示成交量指标。\n\n"
    "2.3 放量突破\n"
    "最新收盘价>此前N条记录的最高价，且成交量≥此前M条记录均量×倍数。默认N=20、M=5、倍数1.5，需21条记录；两个历史窗口均不含当天。\n"
    "突破幅度是收盘价超过前期最高价的百分比，不是当日涨幅。成交量倍数不是盘中量比。不要求当天收阳线，也不要求首次突破。历史不足或均量为零时跳过。\n\n"
    "所有周期按股票自身交易记录计数，不是自然日。",
    "1. BASIC USE\n\nTaojinren Stock Analysis screens local daily bars using your chosen conditions.\n\n"
    "Choose a Tongdaxin ZIP or daily-bar folder, select a strategy, set its parameters and start. Scans can be cancelled. Only each stock's latest bar is tested, with at most one match.\n\n"
    "A blank latest date uses the latest trading date in the market data. A specified date must match the stock file's final bar; it is not a historical replay. Listing status does not affect screening.\n\n"
    "Filter by market, board or code/name/date. The preview shows up to 2,000 rows; exports include every matching row. Export Filtered saves the subset; File > Export All saves original results. Cancelling the picker saves nothing. Export before closing to keep results.\n\n"
    "Current data has no adjustment factors. Raw prices are used; corporate actions may affect results. Screening is not a buy recommendation.\n\n"
    "2. STRATEGIES\n\n"
    "2.1 Interval Gain\n"
    "Latest close versus the close N records earlier must gain at least the threshold. Defaults: N=20, threshold=10%, requiring 21 bars. Period 1 and 9.9% roughly screen one-day gains near a 10% limit, not exact limit-up status.\n\n"
    "2.2 MA Crossover\n"
    "Previous fast SMA≤slow SMA and latest fast SMA>slow SMA. Defaults: 5/20 with close>120-bar SMA. Disable the optional trend filter to require 21 bars instead of 120. A continuing bullish alignment is not a new crossover.\n"
    "Optional volume confirmation is off by default. When enabled, volume must also be ≥ the prior M-bar mean × multiple (defaults: M=5, multiple=1.5, excluding today). This is independent of MA120; each enabled condition must pass. When off, volume is neither tested nor shown.\n\n"
    "2.3 Volume Breakout\n"
    "Latest close>highest high of the prior N bars, and volume≥mean volume of the prior M bars×multiple. Defaults: N=20, M=5, multiple=1.5, requiring 21 bars. Both history windows exclude today.\n"
    "Breakout percentage measures close versus the prior high, not the one-day gain. Volume multiple is not an intraday volume ratio. A bullish candle or first breakout is not required. Short history or zero mean volume is skipped.\n\n"
    "All periods count each stock's trading records, not calendar days."
)


def translate(language, key, **values):
    return TEXT[key][language == "en"].format(**values)
