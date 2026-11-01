# 股票分析

读取本地股票日线，按**区间涨幅**或**双均线金叉**筛选股票，提供 Windows GUI 和 CLI。当前支持通达信 `.day` 文件、ZIP 数据包及解压目录，覆盖支持代码范围内的沪深北股票。

- 区间涨幅：默认比较 20 条交易记录前的收盘价，涨幅 **≥ 10%**。
- 双均线金叉：默认 MA5 上穿 MA20，可选收盘价高于 MA120，默认开启。
- 末条日期留空使用行情数据中的最新交易日；上市状态仅作参考，不参与筛选。
- 中英文界面，支持市场、板块、关键词过滤；仅用户导出时保存 CSV / JSON。

当前按不复权价格分析；尚未提供复权、历史回测、实时行情或交易功能。

## 快速开始

Windows 用户双击工作区中的 `dist/windows/股票分析.exe`，选择行情数据后开始分析。

源码和 CLI 需要 Python 3.11+，运行只依赖标准库，无需安装 pytdx。从工作区根目录运行：

```powershell
python repo/stockstudy.py --help
python repo/stockstudy.py scan --data stock_data/tongdaxin/hsjday.zip
# 只有明确指定输出目录才保存结果
python repo/stockstudy.py scan --period 20 --gain-threshold 10 --output-dir output
```

数据可放在任意有读取权限的目录。默认路径为 `stock_data/tongdaxin/hsjday.zip`。

## 工作区

```text
stockStudy/
├── repo/          源码、测试、文档和证券参考表，只有此目录同步 GitHub
├── stock_data/    原始行情
├── output/        显式导出结果和证券来源快照
└── dist/          发布文件：windows、cli；其他平台待实现
```

业务源码直接放在 `repo/src/`，测试放在 `repo/tests/`。发布目录及程序文件名不包含版本号；程序内和 CLI 版本参数显示版本。

## 开发与构建

```powershell
python repo/scripts/test.py
uv venv repo/.venv --python 3.12
uv pip install --python repo/.venv/Scripts/python.exe -r repo/requirements-build.txt
repo/.venv/Scripts/python.exe repo/scripts/build.py --target all
```

Windows EXE 必须在 Windows 构建。已有虚拟环境时跳过创建步骤。CLI 输出为 `dist/cli/股票分析.pyz`，Windows 输出为 `dist/windows/股票分析.exe`。

## 文档

- [完整使用手册](docs/user-guide.md)：数据准备、策略、过滤、导出、证券表更新及发布说明。
- [重建项目 Prompt](docs/REBUILD_PROMPT.md)：可直接交给其他大模型的完整功能要求与验收标准。
- [版本更新记录](CHANGELOG.md)：从 0.9.3 开始独立维护。
- [架构说明](docs/architecture.md) · [数据源约定](docs/data-sources.md) · [验证记录](docs/validation.md)
