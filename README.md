# 股票分析 本地日线筛选工具

股票分析 读取本地股票日线，按区间涨幅或双均线金叉筛选股票。当前已实现通达信 `.day` 文件及官方 ZIP 数据包读取，提供 CLI 和 Windows 图形界面 EXE。策略核心与数据源、界面分离，便于以后增加其他行情来源和客户端。

这是一套规则筛选工具。当前没有回测、实时行情、自动交易或阶段底部确认功能。价格采用文件中的原始、不复权价格。

## 工作区布局

```text
stockStudy/
├── repo/                         GitHub 仓库目录
│   ├── src/                      全部业务源码
│   │   └── readers/              行情文件读取器（当前为通达信）
│   ├── tests/                    单元与集成测试
│   ├── scripts/                  测试和构建入口
│   ├── resources/                股票名称等小型参考资料
│   ├── vendor/pytdx/             上游原版读取器及来源信息，仅供参考
│   ├── apps/                     Web、Android、iOS、微信客户端规划
│   ├── docs/                     架构与数据源接入约定
│   └── pyproject.toml
├── stock_data/                   原始行情数据，不上传 GitHub
│   └── tongdaxin/hsjday.zip
├── output/                       分析结果，不上传 GitHub
└── dist/                         发布产物，不上传 GitHub
    ├── cli/股票分析.pyz
    ├── windows/股票分析.exe
    ├── web/
    ├── android/
    ├── ios/
    └── wechat/
```

GitHub 仅同步 `repo`。该目录的 `.gitignore` 已排除虚拟环境、构建缓存和常见二进制产物。行情、分析结果和发布文件保留在工作区本地。

## 快速开始

需要 Python 3.11 或以上；本项目使用 Python 3.12 测试。运行源码和 CLI 发布包只依赖标准库，**不需要安装 pytdx 或 pandas，不需要修改 site-packages**。

在工作区根目录运行：

```powershell
python repo/stockstudy.py --help
python repo/stockstudy.py -version
python repo/stockstudy.py sources
python repo/stockstudy.py scan
python repo/stockstudy.py scan --period 20 --gain-threshold 10
```

默认使用工作区的 `stock_data/tongdaxin/hsjday.zip`。分析默认只保留结果，不写文件；CLI 明确指定 `--output-dir` 才导出，GUI 使用“导出筛选结果”或“导出全部结果”。从项目或发布目录启动时，程序会向上寻找同时含有 `stock_data` 和 `output` 的工作区；其他位置请显式指定 `--workspace` 或 `--data`、`--output-dir`。

```powershell
python repo/stockstudy.py scan --workspace D:/stockStudy
python repo/stockstudy.py scan --data D:/行情/vipdoc --output-dir D:/分析结果
python repo/stockstudy.py scan --data D:/行情/hsjday.zip --period 20
```

相对路径按终端当前目录解释。数据可以放在任意有读取权限的目录；导出目录需要写入权限。

可选安装成 `stockstudy` 命令，建议使用项目虚拟环境：

```powershell
cd repo
uv venv --python 3.12
uv pip install -e .
.venv/Scripts/股票分析.exe scan
```

激活虚拟环境后也可以直接使用 `stockstudy scan` 或 `python -m stockstudy scan`。

## 数据准备

通达信官方提供[个人行情日线完整包](https://www.tdx.com.cn/article/vipdata.html)。如需当天数据，先确认页面更新日期已经变为当天；官方页面未承诺具体更新时间。

可以直接把完整包保存为 `stock_data/tongdaxin/hsjday.zip`，无需安装或运行通达信客户端，也无需手动解压。也支持解压后的目录：

```text
任意数据目录/
├── sh/lday/sh600000.day
├── sh/lday/sh688001.day
└── sz/lday/sz000001.day
```

`--data` 可指向该目录、其外层含 `vipdoc` 的目录或 ZIP。不要将多个日期的数据副本混在同一个扫描目录中；重复股票文件会报错，避免静默选错数据。

当前股票范围：上海 `6` 开头，深圳 `00`、`30` 开头，北京 `92` 开头及历史 `43`、`83`、`87` 开头，包含科创板、创业板。指数、基金和可转债不纳入筛选。默认排除已确认退市股票，未知状态仍参与分析并记录数量；没有 ST 过滤。成交量内部单位为股，价格内部单位为整数分，成交额为元。

股票名称来自 `resources/security_names.csv`，是有来源和核对日期的本地证券信息快照。扫描时不联网查询，快照可能滞后于实际上市状态。缺失名称不妨碍筛选，报告中名称留空，并在汇总中记录缺失数量。自定义名称表需 UTF-8 编码，列名为 `market,code,name,status,name_checked_at`，代码必须保留六位：

```csv
market,code,name,status,name_checked_at
sz,000001,平安银行,listed,2026-11-01
sh,688001,示例名称,unknown,
```

```powershell
python repo/stockstudy.py scan --names D:/参考资料/security_names.csv
```

## 上市状态和名录更新

`security_names.csv` 仅包含以下五列：

| 列 | 含义 |
| --- | --- |
| `market` | `sh` 上海、`sz` 深圳、`bj` 北京 |
| `code` | 六位股票代码，保留前导零 |
| `name` | 股票名称 |
| `status` | `listed` 官方名录确认仍上市；`delisted` 已确认摘牌；`unknown` 未确认 |
| `name_checked_at` | 名称核对日期，格式 `YYYY-MM-DD`；未核对时留空，不代表行情日期或状态核对日期 |

来源、上市和摘牌生效日期、状态核对日期保存在单独的 `resources/security_metadata.json`，分析程序只读取五列 CSV。

不能用 ST 名称、行情过旧或未出现在某个名录中推断退市。三列名称 CSV 仍兼容，但所有状态视为未知。名称列表中的历史代码可能因代码切换而保留，不能全部计为当前上市公司。

来源：

- 上交所：[股票列表](https://www.sse.com.cn/assortment/stock/list/share/)、[暂停/终止上市公司](https://www.sse.com.cn/assortment/stock/list/delisting/)。
- 深交所：[股票列表](https://www.szse.cn/market/product/stock/list/index.html)、[暂停/终止上市公司](https://www.szse.cn/market/stock/suspend/index.html)。
- 北交所：[上市公司名录](https://www.bse.cn/nq/listedcompany.html)、正式摘牌公告；北交所接口未能访问时，使用[巨潮代码名称资料](https://www.cninfo.com.cn/new/data/bj_stock.json)补名称，不据此声明仍上市。

2026-11-01 的快照共 6165 条：上海 2318 条确认未退市、148 条确认退市；深圳 2905 条确认未退市、189 条确认退市；北京 605 条代码名称（含历史代码），其中 2 条依据摘牌公告确认退市、603 条状态未知。北交所状态尚未全量核实，不能宣称退市过滤完整。原始下载快照留在工作区 `output/security_metadata`，校验值和覆盖情况见 `resources/security_metadata.json`。

```powershell
python repo/scripts/update_security_names.py
# 使用已下载的快照离线重建，不访问网络
python repo/scripts/update_security_names.py --offline --cache-dir output/security_metadata/2026-11-01 --checked-at 2026-11-01
# 若已有核实的北交所官方上市名录 CSV（code,name,listing_date），可另行导入
python repo/scripts/update_security_names.py --offline --cache-dir output/security_metadata/2026-11-01 --bse-listed D:/参考资料/bse_listed.csv
```

更新脚本保留下载快照，校验来源完整性后再替换名称表，并同步现有 `dist/windows`、`dist/cli` 中的外置 CSV。EXE 和 CLI 发布包优先读取各自旁边的 `security_names.csv`，不存在时使用内置快照。更新 CSV 不需要重装 Python；已打开的 GUI 在下一次分析时读取更新后的表。

GUI 可取消勾选“排除已确认退市”；CLI 对应：

```powershell
python repo/stockstudy.py scan --include-delisted
```

这个选项用于历史研究时保留退市文件，不代表完整历史回测功能；`--as-of` 仍然只检查文件末条日期。未知状态不会被默认为正常或退市，数量和代码写入 `summary.json`；命中 CSV / JSON 包含 `status`。

## 区间涨幅筛选

默认找出最新收盘价相对 20 条交易记录前的收盘价，涨幅**大于等于 10%**的股票。每只股票最多一条结果。N=20 需要 21 条记录；N=1 比较相邻两条记录的收盘价。周期按该股票文件中的交易记录计数，不是自然日，也不补齐停牌日。

```text
区间涨幅 = (最新收盘价 / N 条记录前的收盘价 - 1) × 100%
命中条件：区间涨幅 ≥ 阈值
```

```powershell
python repo/stockstudy.py scan --period 20 --gain-threshold 10
python repo/stockstudy.py scan --period 1 --gain-threshold 10
python repo/stockstudy.py scan --period 5 --gain-threshold 3
```

`--gain-threshold 10` 表示 10%，恰好 10% 也命中，比较方式固定为大于等于。比较使用原始整数分和精确十进制阈值，不依赖显示四舍五入。阈值可以超过 100%。如需粗略筛选单日接近 10% 涨停的股票，可设置周期为 1、涨幅阈值为 9.9%（CLI：`scan --period 1 --gain-threshold 9.9`）。这只是涨幅筛选，并非精确涨停认定；不同板块的涨跌幅限制、价格取整及除权除息可能影响结果。结果按截止日期由近到远、同日涨幅由高到低排序。

历史不足 N+1 条、基准或最新收盘价不大于零时不计算，代码与数量写入 `summary.json`。上市首日没有前一个收盘价时不会计算单日涨幅。当前证券范围由证券表的当前状态决定，不用于重建历史上市范围。

### 价格口径与复权

当前使用通达信 `.day` 中的**不复权成交价格**。分红、送股、转增或配股会使不同日期的原始股价不能直接比较。例如每股 10 元派现金 1 元后，9 元股价加 1 元现金不能简单视为损失 10%。复权通过调整价格，使权益变化前后的价格具有可比性。

跨多日分析涨幅、走势和回测建议使用复权数据。即使 N=1，在除权除息日也不能把两天原始收盘价比值当作行情软件公布的单日涨幅：交易所使用除权除息参考价作为该日涨跌幅基准。参见[深交所的参考价说明](https://investor.szse.cn/knowledge/t20181017_555757.html)。

当前读取的 `.day` 记录不包含复权因子和分红送配信息，程序尚未提供复权计算。要实现前复权或后复权，需要另外接入可靠的累计复权因子或权益事件数据；不能仅根据价格跳空猜测。界面、报告和汇总均明确标识不复权口径。本筛选器输出的是价格变化条件，不代表买入建议或已经验证的盈利策略。

## 双均线金叉筛选

在“分析设置”的策略下拉框中选择“双均线金叉”。短期均线默认5条记录，长期均线默认20条；均线为收盘价的简单算术平均数（SMA），包含对应当天。仅筛选最新一条记录刚刚发生的向上交叉：

```text
上一条记录：MA5 ≤ MA20
最新一条记录：MA5 > MA20
默认附加条件：最新收盘价 > MA120
```

“收盘价高于趋势均线”是可选条件，默认勾选，趋势周期默认120，均可修改。该条件用于过滤价格仍低于长期平均水平的金叉，会减少候选，也可能错过较早的反弹；120不是必须或保证盈利的参数。未要求MA120本身上升，未附加成交量条件。长期均线确认趋势的背景可参考[TradingView 均线说明](https://www.tradingview.com/support/solutions/43000502589-moving-averages/)。

均线比较和趋势过滤都在四舍五入前计算。收盘价恰好等于趋势均线不命中；已维持多日的短均线高于长均线不属于新金叉。所有周期按股票自身的交易记录计数，不是自然日。

默认需要至少120条日线；关闭趋势过滤后需要21条。通用读取长度为 `max(长期均线周期+1, 启用时的趋势均线周期)`。历史不足的股票跳过并计数，不缩短均线窗口。均线涉及的任何收盘价不大于零时也跳过。

```powershell
python repo/stockstudy.py scan --strategy ma-cross
python repo/stockstudy.py scan --strategy ma-cross --no-trend-filter
python repo/stockstudy.py scan --strategy ma-cross --fast-period 10 --slow-period 30 --trend-period 120
```

金叉结果展示最新及上一条记录的短、长均线和趋势均线；导出还包括上一条记录的日期，方便核对交叉。未启用趋势过滤时趋势均线为空。当前数据未提供复权因子，分红送转可能影响均线信号，复权情况统一放在结果摘要中说明。

### 数据日期和边界

末条日期留空使用行情数据中的最新交易日。末条记录早于该日的股票（例如停牌后未更新的股票）不参与筛选。`summary.json` 记录实际采用的日期及各股票末条日期分布。

```powershell
python repo/stockstudy.py scan --as-of 2026-10-30
```

`--as-of` 是“最后一条记录必须恰为该日”的过滤条件，不是历史回放截止日期。较早或较晚的文件都会被排除并记入汇总。

## 分析输出

`gain_ratio` 为比例（0.12 表示 12%），`gain_pct` 为百分数（12 表示 12%）。报告中的基准和最新收盘价均为原始成交价。

分析不会自动写入磁盘。GUI 完成后在表格中查看，点击“导出筛选结果”或“文件 → 导出全部结果”并选择目录才保存。未导出的结果关闭窗口后不保留；重新分析成功后替换窗口中的结果，取消或失败会保留上一次完成的结果。

每次导出创建独立的 `<所选目录>/股票分析_<时间>_<唯一后缀>/`，不会覆盖之前的导出。结果区的“导出筛选结果”保存所有符合当前市场、板块和搜索条件的行，不受2000条预览上限影响；“文件 → 导出全部结果”保存原始分析结果，不受筛选影响。CLI 使用 `--output-dir` 明确导出：

```powershell
python repo/stockstudy.py scan --output-dir D:/分析结果
```

| 文件 | 内容 |
| --- | --- |
| `matches.csv` | UTF-8 BOM，股票、日期、收盘价、价格口径，以及所选策略的涨幅或均线字段 |
| `matches.json` | 同样的命中记录，供后续 Web/API/移动客户端消费 |
| `summary.json` | 参数、版本、数据路径、扫描数量、日期分布、缺失名称和错误明细 |

单个损坏文件会记录错误并继续其他股票。退出码：`0` 扫描完成；`1` 参数、输入或输出发生致命错误；`2` 有股票文件读取失败，结果不完整。指定日期导致的正常排除不会产生退出码 2。选择导出时，即使无命中也生成带表头的 CSV 和空 JSON 列表。

结果中的代码按文本保存。使用 Excel 导入 CSV 时，请将代码列设置为文本，以免丢失前导零。

### 结果过滤与导出范围

市场旁的“板块”框随市场联动：上海可选主板/科创板，深圳可选主板/创业板；北京显示“北交所（不细分）”。全部市场或沪深范围下可直接选择具体板块。切换市场时，不兼容的板块自动重置为全部；重置筛选恢复市场、板块及搜索条件。

深圳原中小板已于2021年并入主板，本程序不再单列。参考[深交所说明](https://www.szse.cn/aboutus/trends/news/t20210406_585442.html)。分类按当前支持的市场及代码推导：沪市600/601/603/605为主板，688及科创板存托凭证689归入科创板；深市00开头为主板（含原中小板），30开头为创业板；北交所支持的现行及历史代码统一归入北交所。无法识别的代码保留为“其他/未识别”，不擅自归到主板。该分类不判断当前是否上市，也不回溯历史板块变更。

导出新增 `board` 列：`sh-main`、`star`、`sz-main`、`chinext`、`bse` 或 `other`。证券名称表仍为原来的五列，不增加字段。筛选导出的 `result_filters.board` 记录所选板块，导出全部结果不受该条件影响。

市场可选全部、上海（sh）、深圳（sz）、北京（bj）、沪深（sh+sz）。上市状态不在 GUI 表格或筛选栏中显示，仍保留在导出 CSV / JSON 的 `status` 列中。多个条件同时满足才显示，关键词支持代码（包括 `sz000001` 形式）、名称和日期，忽略英文大小写。重置筛选恢复全部结果，无需重新读取行情。

结果过滤只作用于本次已经命中的记录。分析时排除的退市股票或不满足策略的股票，不能通过结果过滤恢复。上市状态未知不会自动视为仍上市，特别是北交所尚未全量核实的状态仍按 unknown 处理。

“导出筛选结果”保存完整筛选子集；“导出全部结果”忽略结果过滤。零条结果也可导出带表头的空 CSV / JSON。导出汇总保留原始扫描统计，另用 `export_scope`、`export_record_count` 和（筛选导出时的）`result_filters` 记录此次导出范围、实际条数与条件，原始分析结果不被修改。

## 发布和不同客户端

Windows 版提供独立图形界面，双击 `dist/windows/股票分析.exe` 即可使用，不会打开命令行窗口。

界面分为“分析设置、分析策略、分析结果”三个区域：

1. 在“分析设置”选择行情 ZIP 或目录，填写可选的末条日期，并设置是否排除已确认退市股票。
2. 从策略下拉框选择策略。“分析策略”区域显示所选策略的参数；可选区间涨幅或双均线金叉；金叉默认5/20，并勾选收盘价高于120日均线。
3. 点击“开始分析”，后台扫描时可取消。在“分析结果”中查看股票、比较日期、收盘价和策略指标，可组合市场、板块与关键词筛选。
4. 下方结果摘要说明复权情况、排除退市、状态未知、历史不足等。当前数据未提供复权因子时，简要提示本次采用不复权价格。
5. 需要保存时，点击“导出筛选结果”，或使用“文件 → 导出全部结果”。默认不保存文件。

顶部菜单为“文件、分析、语言、关于”，可在“语言”中切换简体中文 / English，参数、已完成的结果与市场/板块/搜索条件会保留。“关于”菜单下包含独立的使用帮助，以及仅显示软件名称与版本的关于窗口。程序文件为 `股票分析.exe`，使用原创 K 线图标。

窗口标题和关于窗口显示版本。CLI 发布文件为 `dist/cli/股票分析.pyz`。

发布包不携带大体积行情数据，名称表内置。发布目录不包含版本号；CLI 的 `--help`、`--version`、`-version`、`-V` 可以显示软件版本。

```powershell
python repo/scripts/build.py --target cli
python dist/cli/股票分析.pyz scan
```

构建 Windows EXE 时，在 Windows 上创建独立构建环境：

```powershell
uv venv repo/.venv --python 3.12
uv pip install --python repo/.venv/Scripts/python.exe -r repo/requirements-build.txt
repo/.venv/Scripts/python.exe repo/scripts/build.py --target all
dist/windows/股票分析.exe
```

已存在 `.venv` 时跳过创建命令。构建依赖与项目运行依赖分离。

| 平台 | 发布目录 | 状态与要求 |
| --- | --- | --- |
| CLI | `dist/cli/` | Python zipapp，需 Python 3.11+ |
| Windows EXE | `dist/windows/` | 图形界面，目标机器无需另装 Python |
| Web | `dist/web/` | 规划，需 Web UI 和服务端接口 |
| Android APK | `dist/android/` | 规划，需 Android 客户端、SDK、签名 |
| iOS IPA | `dist/ios/` | 规划，需 macOS、Xcode 和签名 |
| 微信小程序 | `dist/wechat/` | 规划，需小程序 UI、AppID 和上传构建流程 |

不同平台需要各自实现界面、存储和权限处理，不是把 Python 文件简单转换成不同后缀。建议 Web/移动端通过服务端接口调用同一分析核心，避免手机端直接处理大型行情 ZIP。后续设计见 `docs/architecture.md`。

## 测试

```powershell
python repo/scripts/test.py
```

测试覆盖北交所识别、退市三态标识与过滤、名录导入、GUI 参数校验、后台扫描、取消、结果表格及组合筛选、筛选/全部导出、中英文切换、分析不写文件与显式导出、区间涨幅、均线金叉与趋势过滤、精确阈值、历史不足与无效收盘价、科创板、ZIP/目录一致性、坏文件隔离、日期排除、报告和 CLI。真实行情扫描结果放在工作区 `output`，不纳入源码测试或 Git。

## 后续数据源

当前仅 `tdx` 已实现并测试。标准 CSV、AKShare、Tushare、BaoStock 是后续适配候选，不代表已经可以调用；其接口、可用性、许可与费用需要接入时分别核对。适配规范见 `docs/data-sources.md`。
