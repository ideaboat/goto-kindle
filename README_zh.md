# gotokindle

一键将剪贴板内容（文本/图片）发送到 Kindle（通过 USB 直连），基于 Calibre 转换。

## 功能特性
- 自动检测剪贴板文本或图片
- 短文本（≤500字符）直接拷贝为 TXT，长文本生成 16pt 字号的 MOBI 电子书
- 带图片的剪贴板自动生成图文混排的 MOBI
- 自动生成不重名的文件（时间戳+随机数）；`-title` 可自定义标题与文件名
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
gotokindle                   # 读取剪贴板，自动命名后发送
gotokindle -title 财经周刊    # 标题与文件名变为 财经周刊_1234.txt / .mobi
gotokindle -help             # 查看功能与参数说明
```

`-title` 指定的标题同时用于两处：文件名的前半部分（后半部分是 4 位随机码，避免重名）、以及电子书元数据标题（Kindle 书库里显示的就是它）。不加该参数时文件名仍为「前缀_时间戳_随机码」。

建议配置 alias 或直接软链接到 PATH：
```bash
alias gotokindle='python3 /path/to/gotokindle.py'
```
