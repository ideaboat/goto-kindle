# gotokindle

一键将剪贴板内容（文本/图片）发送到 Kindle（通过 USB 直连），基于 Calibre 转换。

## 功能特性
- 自动检测剪贴板文本或图片
- 短文本（≤500字符）直接拷贝为 TXT，长文本生成 16pt 字号的 MOBI 电子书
- 带图片的剪贴板自动生成图文混排的 MOBI
- 自动生成不重名的文件（时间戳+随机数）
- 检测 Kindle 是否挂载，未连接时提示

## 依赖
- Python 3.6+
- `pyperclip`, `Pillow`
- Calibre（需安装，`ebook-convert` 可用）

## 安装
1. 克隆本仓库
2. 安装依赖：`pip3 install pyperclip Pillow`
3. 确保 Calibre 已安装，并设置 `CALIBRE_CONVERT` 路径（默认 macOS 路径为 `/Applications/calibre.app/Contents/MacOS/ebook-convert`）

## 使用
```bash
gotokindle