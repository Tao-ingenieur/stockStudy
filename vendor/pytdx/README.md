# pytdx 上游原版参考

`daily_bar_reader.py` 由 `scripts/fetch_upstream.py` 从 rainx/pytdx 下载，保持字节原样。精确提交号、原始地址和 SHA-256 见 `provenance.json`；如上游提供独立许可证文件，一并保存为 `LICENSE.upstream`。

该文件仅供对照来源和日线格式，**不是项目的运行依赖**，不要用它覆盖任何 `site-packages`。它自身导入 pandas 和 pytdx，直接运行它仍需要这些库；StockStudy 的运行入口不导入该文件。

原作者及许可声明以[上游项目](https://github.com/rainx/pytdx)为准。参考文件不包含在 StockStudy 的 CLI 和 Windows 发布包中。
