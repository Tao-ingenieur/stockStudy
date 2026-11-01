# 淘金人股票分析使用手册

## 一、基本使用

### 1.1 准备行情

支持通达信 `.day` 日线、ZIP 数据包和解压目录，无需安装通达信客户端或 pytdx。日线完整包可在[通达信个人行情页面](https://www.tdx.com.cn/article/vipdata.html)获取，请自行确认数据更新日期。

默认位置为工作区 `stock_data/tongdaxin/hsjday.zip`，也可放在其他有读取权限的目录。解压目录中应包含 `sh/lday`、`sz/lday` 或 `bj/lday`。同一目录不要混入同一股票的多份文件。

当前支持上海6开头、深圳00/30开头、北京43/83/87/92开头的股票，含科创板、创业板及北京历史代码。指数、基金和可转债不参与筛选。

### 1.2 开始分析

双击 `dist/windows/淘金人股票分析.exe`，选择 ZIP 或目录，从下拉框选策略，在“分析策略”区域设置参数，点击“开始分析”。扫描期间可以取消，取消或失败保留上次完成结果。

每只股票只检查最后一条记录，最多输出一条结果。周期按该股票自身交易记录计数，不是自然日，不补停牌日。

**末条日期留空使用行情数据中的最新交易日。** 填写日期时，股票文件的最后一条记录必须恰为该日；较早或较晚都不参与。这不是截取历史行情进行回放。

顶部菜单提供文件、分析、语言、关于。可切换简体中文 / English，参数、结果和筛选条件会保留。“关于”菜单包含使用帮助及软件名称、版本。

### 1.3 查看、筛选和导出

结果按市场、板块及代码/名称/日期关键词组合过滤，无需重新读取行情。市场支持全部、上海、深圳、北京及沪深；上海细分主板/科创板，深圳细分主板/创业板（含原中小板），北京不再细分。切换市场时不兼容板块自动重置，点击“重置筛选”可恢复全部结果。

表格最多预览2000条，但筛选和导出处理全部结果。默认不保存文件：

- “导出筛选结果”保存当前匹配的全部行。
- “文件 → 导出全部结果”保存原始命中结果，不受结果过滤影响。
- 选择目录后才保存；取消选择不写文件，关闭程序前请导出需要保留的结果。

每次导出创建独立的 `淘金人股票分析_时间_唯一后缀` 目录，不覆盖之前结果，包含：

| 文件 | 内容 |
| --- | --- |
| matches.csv | 带表头的 UTF-8 BOM 表格，含代码、名称、日期和策略指标 |
| matches.json | 同一批命中记录，供程序读取 |
| summary.json | 版本、策略参数、数据路径、实际目标日期、读取统计、跳过原因及导出范围 |

无命中也可导出空表。汇总中的原始分析数量与实际导出数量分开记录。代码是六位文本，Excel 导入时请将代码列设为文本，保留前导零。

### 1.4 价格、单位和证券信息

当前按**不复权价格**分析：行情没有复权因子，分红送转可能影响涨幅、均线和突破。结果摘要会说明这一点。原始收盘价变化也不一定等于除权除息日行情软件显示的涨跌幅。筛选记录不代表买入建议。

价格展示为元，原始模型使用整数分；成交额单位元。放量突破界面用万股展示成交量，CSV / JSON 使用股，成交量倍数没有单位。

证券表为 `resources/security_names.csv`，只有 `market,code,name,status,name_checked_at` 五列。状态为 listed、delisted 或 unknown，仅作参考并保留在导出中，**不影响筛选**，GUI不显示状态列或状态筛选。

缺失名称时仍参与分析，名称留空。name_checked_at 是名称核对日期，不是行情日期。EXE / pyz 优先读取旁边的外置表，没有时使用内置表，每次分析重新读取。

可独立更新证券表：

```powershell
python repo/scripts/update_security_names.py
# 使用已有来源快照离线重建
python repo/scripts/update_security_names.py --offline --cache-dir output/security_metadata/2026-11-01 --checked-at 2026-11-01
# 可导入已核实的北交所名录（code,name,listing_date）
python repo/scripts/update_security_names.py --offline --cache-dir output/security_metadata/2026-11-01 --bse-listed D:/参考资料/bse_listed.csv
```

来源包括上交所、深交所公开证券名录和终止上市资料；北交所名称可以由巨潮资料补充，但名称存在不代表已核实仍上市。不能用 ST 名称或行情过旧推断退市。来源、校验值和覆盖范围保存在 security_metadata.json，下载快照与备份保存在 output/security_metadata；更新工具同步现有 Windows / CLI 发布目录中的外置表。

### 1.5 命令行

源码和 CLI 发布包需要 Python 3.11+，运行只依赖标准库。从工作区根目录运行：

```powershell
python repo/stockstudy.py --help
python repo/stockstudy.py --version
python repo/stockstudy.py sources
python repo/stockstudy.py scan --data D:/行情/hsjday.zip
python dist/cli/淘金人股票分析.pyz scan --data D:/行情/vipdoc
```

`--data` 可指定 ZIP 或目录，`--workspace` 可指定含 stock_data/output 的工作区，`--names` 可替换证券表。只有提供 `--output-dir` 才导出结果，`--quiet` 隐藏进度。相对路径按当前目录解释。

退出码0表示完成，1表示致命参数或输入/输出错误，2表示部分股票读取失败；日期不符不是读取错误。单个股票损坏会记录错误并继续其他股票。

## 二、策略说明

### 2.1 区间涨幅

找最新收盘价相对N条记录前收盘价的涨幅，大于等于阈值即命中。默认N=20、阈值10%，需要21条记录。

```text
涨幅 = (最新收盘价 ÷ N条记录前收盘价 - 1) × 100%
命中条件：涨幅 ≥ 阈值
```

N=1比较相邻两条记录。阈值允许超过100%，恰好达到也命中；按未舍入值判断。历史不足或比较价格不大于零时跳过。

```powershell
python repo/stockstudy.py scan --strategy gain --period 20 --gain-threshold 10
```

周期1、阈值9.9%可粗略筛选单日接近10%涨停的股票，但不是精确涨停判断，不同板块限制、价格取整和除权除息会影响结果。

### 2.2 双均线金叉

只找最新一条刚发生的短均线上穿长均线。均线为包含当天收盘价的简单平均数，默认5/20。

```text
上一条短均线 ≤ 长均线
最新短均线 > 长均线
默认附加条件：最新收盘价 > MA120
```

短周期必须小于长周期。“收盘价高于趋势均线”可取消，趋势周期可改。默认需120条记录，取消趋势条件后需21条；启用放量确认时，还需要至少“均量窗口+1”条记录；通用要求取“长周期+1、启用时的趋势周期、启用时的均量窗口+1”中的最大值。均线相等、收盘价等于趋势均线都不满足对应的严格条件。连续多日短线在长线上方不算新金叉。

```powershell
python repo/stockstudy.py scan --strategy ma-cross
python repo/stockstudy.py scan --strategy ma-cross --no-trend-filter
python repo/stockstudy.py scan --strategy ma-cross --fast-period 10 --slow-period 30 --trend-period 120
```

**可选放量确认默认不勾选。** 勾选后，除金叉条件外，还需满足：

```text
最新成交量 ≥ 此前M条记录平均成交量 × 指定倍数
```

默认M=5、倍数1.5，平均成交量不含当天；恰好达到倍数也满足。它与MA120趋势条件相互独立：只勾趋势就只加趋势要求，只勾放量就只加放量要求，两项都勾选则都必须满足。

```powershell
python repo/stockstudy.py scan --strategy ma-cross --volume-filter --volume-period 5 --volume-multiple 1.5
# 只增加放量确认，不检查MA120
python repo/stockstudy.py scan --strategy ma-cross --volume-filter --no-trend-filter
```

勾选放量时，结果增加成交量、历史均量、成交量倍数；关闭时不检查成交量，也不显示这三列，导出中的未计算字段为空而不是0。摘要明确记录放量是否启用，导出还记录均量窗口、倍数阈值及窗口起止日期。历史均量为零或成交量无效时跳过并计数。与“放量突破”使用相同成交量定义，但各策略界面参数分别保留；金叉不要求突破前期高点。

结果中的“上条MA”是最后一条之前那条记录对应的均线。导出保留上一条日期；趋势条件关闭时趋势均线为空。历史不足或参与计算的收盘价不大于零时跳过。

### 2.3 放量突破

找收盘价突破前期高点、成交量同时放大的股票，默认价格窗口N=20、均量窗口M=5、成交量倍数1.5。

```text
最新收盘价 > 前N条记录中的最高价
最新成交量 ≥ 前M条记录平均成交量 × 倍数
```

两个历史窗口都不含当天，最高价使用每天的盘中最高价，不是最高收盘价。价格相等不算突破，成交量恰好达到倍数算满足。需要 max(N,M)+1 条记录，默认21条。

```powershell
python repo/stockstudy.py scan --strategy breakout
python repo/stockstudy.py scan --strategy breakout --breakout-period 20 --volume-period 5 --volume-multiple 1.5
```

结果解释：

- 前期最高价：本次突破的比较价位。
- 突破幅度：(收盘价÷前期最高价−1)×100%，**不是当日涨幅**。
- 历史均量：前M条记录平均成交量。
- 成交量倍数：最新成交量÷历史均量，**不是盘中量比**。

不要求当天收阳线，也不要求首次突破。每次只检查最新一天；隔天更新数据再次运行时，同一股票可能再次命中。历史不足、无效价格、负成交量或历史均量为零时跳过并计数。

导出还包括前期高点日期、两个历史窗口的起止日期；最高价多次出现时记录最近一次日期。按突破幅度降序排列，同幅度按市场和代码稳定排序。均线、最低成交额等额外条件不在本策略首版范围内。

开发和构建见 [README](../README.md)，扩展设计见 [架构说明](architecture.md) 与 [数据源约定](data-sources.md)。
