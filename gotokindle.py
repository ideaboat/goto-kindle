#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gotokindle - 将剪贴板图文一键发送至Kindle（macOS版）
用法：在终端执行 gotokindle [-title 标题]   （用 -help 查看帮助）
"""

import argparse
import os
import sys
import subprocess
import tempfile
import shutil
import time
import random
import string
import base64
from datetime import datetime
from io import BytesIO

try:
    from PIL import Image, ImageGrab
except ImportError:
    print("错误：缺少 Pillow 库，请运行 pip install Pillow")
    sys.exit(1)

try:
    import pyperclip
except ImportError:
    print("错误：缺少 pyperclip 库，请运行 pip install pyperclip")
    sys.exit(1)

# ============ 配置 ============
KINDLE_MOUNT = "/Volumes/Kindle"
KINDLE_DOCS = os.path.join(KINDLE_MOUNT, "documents")
CALIBRE_CONVERT = "/usr/local/bin/ebook-convert"
if not os.path.exists(CALIBRE_CONVERT):
    # Calibre官方安装包的实际路径
    CALIBRE_CONVERT = "/Applications/calibre.app/Contents/MacOS/ebook-convert"

# 文字大小（仅对MOBI生效）
FONT_SIZE = 16  # pt
# 纯文本 vs 电子书的字数阈值（字符数）
TEXT_THRESHOLD = 500

# ============ 辅助函数 ============
def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        prog="gotokindle",
        usage="gotokindle [-title 标题] [-help]",
        description="把剪贴板中的图文发送到Kindle（自动生成TXT或MOBI并拷入documents目录）。",
        add_help=False,
    )
    group = parser.add_argument_group("参数")
    group.add_argument("-title", metavar="标题",
                       help="自定义标题，格式为「标题_4位随机码」（同时用作文件名）")
    group.add_argument("-help", "-h", action="help", help="显示本帮助并退出")
    return parser.parse_args()

def random_suffix(length=4):
    """生成随机数字后缀"""
    return ''.join(random.choices(string.digits, k=length))

def timestamp_str():
    """生成时间戳字符串，如 20260908_123456"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def get_clipboard_content():
    """
    返回 (type, content)
    type: 'text' 或 'image'
    content: 文本字符串 或 PIL.Image 对象
    若无内容，返回 (None, None)
    """
    # 1. 尝试获取图像
    try:
        img = ImageGrab.grabclipboard()
        if img is not None and isinstance(img, Image.Image):
            return ('image', img)
    except Exception:
        pass

    # 2. 尝试获取文本
    try:
        text = pyperclip.paste()
        if text and text.strip():
            return ('text', text.strip())
    except Exception:
        pass

    return (None, None)

def kindle_connected():
    """检查Kindle是否挂载"""
    return os.path.isdir(KINDLE_MOUNT) and os.path.isdir(KINDLE_DOCS)

def generate_unique_filename(ext, prefix="Kindle", title=None):
    """生成文件名：指定title时为 title_随机码，否则为 prefix_时间戳_随机码"""
    suffix = random_suffix(4)
    if title:
        return f"{title}_{suffix}.{ext}"
    return f"{prefix}_{timestamp_str()}_{suffix}.{ext}"

def copy_file_to_kindle(src_path, dest_filename):
    """拷贝文件到Kindle documents目录，返回目标完整路径"""
    if not kindle_connected():
        print(f"错误：未检测到Kindle挂载在 {KINDLE_MOUNT}")
        print("请通过USB连接Kindle，并确认已进入‘传输文件’模式。")
        sys.exit(1)

    dest_path = os.path.join(KINDLE_DOCS, dest_filename)
    try:
        shutil.copy2(src_path, dest_path)
        return dest_path
    except Exception as e:
        print(f"拷贝失败：{e}")
        sys.exit(1)

def convert_html_to_mobi(html_content, output_path, title):
    """
    将HTML字符串转换为MOBI文件，使用Calibre的ebook-convert
    title 会写入电子书元数据（Kindle 书库显示的就是它，而非文件名）
    """
    if not os.path.exists(CALIBRE_CONVERT):
        print(f"错误：找不到 Calibre 转换器 {CALIBRE_CONVERT}")
        print("请确认Calibre已安装，或修改脚本中的 CALIBRE_CONVERT 路径。")
        sys.exit(1)

    # 写入临时HTML文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(html_content)
        temp_html = f.name

    try:
        # 执行转换
        cmd = [CALIBRE_CONVERT, temp_html, output_path,
               "--output-profile=kindle",
               "--base-font-size", str(FONT_SIZE),  # 额外保证
               "--title", title                      # 写入元数据，Kindle 显示它
              ]
        print("正在转换电子书，请稍候...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print("转换失败，错误信息：")
            print(result.stderr)
            sys.exit(1)
        print("转换完成。")
    finally:
        # 删除临时HTML
        if os.path.exists(temp_html):
            os.unlink(temp_html)

    return output_path

# ============ 生成内容（HTML for MOBI） ============
def build_html_from_text(text):
    """将纯文本包装为带字号设置的HTML"""
    # 转义HTML特殊字符
    import html
    escaped = html.escape(text)
    # 保留换行（转换为 <br>）
    lines = escaped.split('\n')
    body = '<br>'.join(lines)
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
body {{
    font-family: sans-serif;
    font-size: {FONT_SIZE}pt;
    line-height: 1.6;
    margin: 20px;
}}
pre {{
    white-space: pre-wrap;
    word-wrap: break-word;
}}
</style>
</head>
<body>
<div style="font-size:{FONT_SIZE}pt;">
{body}
</div>
</body>
</html>"""

def build_html_from_image(img):
    """将PIL图像转为base64嵌入的HTML"""
    buffered = BytesIO()
    # 保存为JPEG以减小体积
    img = img.convert('RGB')  # 确保RGB
    img.save(buffered, format='JPEG', quality=85)
    img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
body {{
    margin: 0;
    padding: 0;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    background: white;
}}
img {{
    max-width: 100%;
    height: auto;
}}
</style>
</head>
<body>
<img src="data:image/jpeg;base64,{img_base64}" />
</body>
</html>"""

# ============ 主流程 ============
def main():
    title = parse_args().title
    print("正在读取剪贴板...")
    ctype, content = get_clipboard_content()

    if ctype is None:
        print("错误：剪贴板为空，请复制内容后再试。")
        sys.exit(1)

    # 决定走哪种方案
    if ctype == 'image':
        print("检测到图像，将生成带图的MOBI电子书（方案二）")
        html_content = build_html_from_image(content)
        ext = "mobi"
        filename = generate_unique_filename(ext, "KindleImage", title)
        # 生成临时MOBI文件
        with tempfile.NamedTemporaryFile(suffix='.mobi', delete=False) as tmp:
            mobi_path = tmp.name
        convert_html_to_mobi(html_content, mobi_path, os.path.splitext(filename)[0])
        # 拷贝
        dest = copy_file_to_kindle(mobi_path, filename)
        os.unlink(mobi_path)  # 清理临时文件

    else:  # text
        text = content
        char_count = len(text)
        print(f"检测到文本，共 {char_count} 个字符。")

        if char_count <= TEXT_THRESHOLD:
            print("字符数较少，采用方案一：直接拷贝为纯文本TXT")
            # 生成TXT文件，注意编码UTF-8
            filename = generate_unique_filename("txt", "KindleText", title)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                f.write(text)
                txt_path = f.name
            dest = copy_file_to_kindle(txt_path, filename)
            os.unlink(txt_path)
        else:
            print("字符数较多，采用方案二：生成MOBI电子书（带字号16）")
            html_content = build_html_from_text(text)
            filename = generate_unique_filename("mobi", "KindleText", title)
            with tempfile.NamedTemporaryFile(suffix='.mobi', delete=False) as tmp:
                mobi_path = tmp.name
            convert_html_to_mobi(html_content, mobi_path, os.path.splitext(filename)[0])
            dest = copy_file_to_kindle(mobi_path, filename)
            os.unlink(mobi_path)

    print("\n✅ 成功！文件已发送至Kindle：")
    print(f"   {dest}")
    print("现在您可以安全弹出Kindle，然后打开该文件阅读。")
    print("（提示：若为TXT，请在Kindle内按AA键将字号调至第4档，即16pt）")

if __name__ == "__main__":
    main()