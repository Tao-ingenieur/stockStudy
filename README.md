# StockStudy 本地日线筛选工具

StockStudy 读取本地股票日线，按最低价数字形态筛选记录，支持附加历史价格跌幅条件。当前已实现通达信 `.day` 文件及官方 ZIP 数据包读取，提供 CLI 和 Windows 图形界面 EXE。策略核心与数据源、界面分离，便于以后增加其他行情来源和客户端。

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
    ├── cli/stockstudy.pyz
    ├── windows/stockstudy.exe
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
python repo/stockstudy.py scan --strategy pattern-drop
```

默认使用工作区的 `stock_data/tongdaxin/hsjday.zip`，默认写入 `output`。从项目或发布目录启动时，程序会向上寻找同时含有 `stock_data` 和 `output` 的工作区；其他位置请显式指定 `--workspace` 或 `--data`、`--output-dir`。

```powershell
python repo/stockstudy.py scan --workspace D:/stockStudy
python repo/stockstudy.py scan --data D:/行情/vipdoc --output-dir D:/分析结果
python repo/stockstudy.py scan --data D:/行情/hsjday.zip --lookback 20
```

相对路径按终端当前目录解释。数据可以放在任意有读取权限的目录；结果目录需要写入权限。

可选安装成 `stockstudy` 命令，建议使用项目虚拟环境：

```powershell
cd repo
uv venv --python 3.12
uv pip install -e .
.venv/Scripts/stockstudy.exe scan
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

当前股票范围：上海 `6` 开头，深圳 `00`、`30` 开头，包含科创板。即使 ZIP 含北交所、指数、基金等数据，当前筛选也不包含这些品种。没有 ST 过滤。成交量内部单位为股，价格内部单位为整数分，成交额为元。

股票名称来自 `resources/security_names.csv`，是随项目提供的本地参考表，**不是联网更新的最新证券名录**。缺失名称不妨碍筛选，报告中名称留空，并在汇总中记录缺失数量。自定义名称表需 UTF-8 编码，列名为 `market,code,name`，代码必须保留六位：

```csv
market,code,name
sz,000001,平安银行
sh,688001,示例名称
```

```powershell
python repo/stockstudy.py scan --names D:/参考资料/security_names.csv
```

## 两种筛选策略

### pattern 价格形态筛选

默认检查每只股票最近 1 条交易记录。最低价满足以下任意规则即命中：

1. 整数个位与两位小数相同：`3.33`、`13.33`、`8.88`。
2. 两位整数与两位小数相同或倒序：`12.12`、`12.21`。

```powershell
python repo/stockstudy.py scan --strategy pattern --lookback 5
```

### pattern-drop 价格形态与跌幅筛选

默认检查每只股票最近 100 条交易记录。第一类价格规则放宽为两位小数相同，如 `13.88`；第二类规则相同。同时要求当前候选日最低价，相比之前第 40、20、10、5 条交易记录中任意一条的最高价，下降幅度严格大于 40%。

```text
(参考日最高价 - 候选日最低价) / 参考日最高价 > 0.4
```

参考日按 `40,20,10,5` 的顺序检查，记录第一个满足的参考日。比较的是指定日期的最高价，不是整个区间的最高价，也不确认候选日为阶段最低点。除权除息可能影响不复权价格的比较。

```powershell
python repo/stockstudy.py scan --strategy pattern-drop --lookback 100
python repo/stockstudy.py scan --strategy pattern-drop --drop-threshold 0.3 --reference-days 60,40,20,10
```

`lookback` 是每只股票末尾的记录条数，不是自然日。程序会额外读取跌幅比较所需的历史记录；历史不足时只检查存在的参考日。

### 数据日期和边界

默认采用各股票文件自身的最新记录，停牌股票的最后记录可能更早。`summary.json` 会记录最新日期分布。

```powershell
python repo/stockstudy.py scan --as-of 2026-10-30
```

`--as-of` 是“最后一条记录必须恰为该日”的过滤条件，不是历史回放截止日期。较早或较晚的文件都会被排除并记入汇总。

## 分析输出

每次运行创建独立的 `output/<时间>_<策略>_<唯一后缀>/`，不会覆盖上次结果。

| 文件 | 内容 |
| --- | --- |
| `matches.csv` | UTF-8 BOM，股票、日期、最低价、形态、参考日和跌幅 |
| `matches.json` | 同样的命中记录，供后续 Web/API/移动客户端消费 |
| `summary.json` | 参数、版本、数据路径、扫描数量、日期分布、缺失名称和错误明细 |

单个损坏文件会记录错误并继续其他股票。退出码：`0` 扫描完成；`1` 参数、输入或输出发生致命错误；`2` 有股票文件读取失败，结果不完整。指定日期导致的正常排除不会产生退出码 2。无命中时仍输出带表头的 CSV 和空 JSON 列表。

结果中的代码按文本保存。使用 Excel 导入 CSV 时，请将代码列设置为文本，以免丢失前导零。

## 发布和不同客户端

Windows 版提供独立图形界面，双击 `dist/windows/stockstudy.exe` 即可使用，不会打开命令行窗口。

1. 选择通达信 ZIP 数据包或解压后的行情目录，设置结果保存目录。
2. 选择“价格形态”或“价格形态 + 跌幅”，设置最近记录数；跌幅模式可设置百分比阈值及历史参考位置。
3. 可填写末条日期 `YYYY-MM-DD`；留空时采用每只股票自身最后一条记录。
4. 点击“开始分析”。进度条显示扫描进度，可以取消；取消不会生成本次报告。
5. 在表格中查看结果，按代码、名称或日期搜索，或点击“打开完整 CSV”“打开结果目录”。表格预览最多 2000 条，CSV / JSON 包含完整结果。

窗口标题和“关于与帮助”显示版本。命令行任务使用 `dist/cli/stockstudy.pyz`。

发布包不携带大体积行情数据，名称表内置。发布目录不包含版本号；CLI 的 `--help`、`--version`、`-version`、`-V` 可以显示软件版本。

```powershell
python repo/scripts/build.py --target cli
python dist/cli/stockstudy.pyz scan
```

构建 Windows EXE 时，在 Windows 上创建独立构建环境：

```powershell
uv venv repo/.venv --python 3.12
uv pip install --python repo/.venv/Scripts/python.exe -r repo/requirements-build.txt
repo/.venv/Scripts/python.exe repo/scripts/build.py --target all
dist/windows/stockstudy.exe
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

测试覆盖 GUI 参数校验、后台扫描、取消、结果表格及搜索、价格形态、精度、跌幅阈值、历史边界、科创板、ZIP/目录一致性、坏文件隔离、日期排除、报告和 CLI。真实行情扫描结果放在工作区 `output`，不纳入源码测试或 Git。

## 后续数据源

当前仅 `tdx` 已实现并测试。标准 CSV、AKShare、Tushare、BaoStock 是后续适配候选，不代表已经可以调用；其接口、可用性、许可与费用需要接入时分别核对。适配规范见 `docs/data-sources.md`。
