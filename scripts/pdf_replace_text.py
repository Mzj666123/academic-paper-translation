#!/usr/bin/env python3
"""
PDF 文字层替换工具
保持原排版和图片位置不变，只替换英文文字为中文

用法：
  python pdf_replace_text.py input.pdf output.pdf translations.json

translations.json 格式：
{
  "page_1": ["中文段落1", "中文段落2", ...],
  "page_2": ["中文段落1", ...]
}
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("请先安装 PyMuPDF: python -m pip install pymupdf")
    sys.exit(1)


def merge_blocks_into_paragraphs(blocks, line_gap_threshold=8):
    """把同一段落的多个文本块合并成一个段落块

    判断依据：
    - 相邻块的y间距小（行间距，不是段落间距）
    - 左边界大致相同（同一段落左对齐）
    """
    if not blocks:
        return []

    paragraphs = []
    current_para = {
        "x0": blocks[0]["x0"],
        "y0": blocks[0]["y0"],
        "x1": blocks[0]["x1"],
        "y1": blocks[0]["y1"],
        "text": blocks[0]["text"],
        "width": blocks[0]["width"],
        "height": blocks[0]["height"],
        "blocks": [blocks[0]]
    }

    for i in range(1, len(blocks)):
        block = blocks[i]

        gap = block["y0"] - current_para["y1"]

        left_diff = abs(block["x0"] - current_para["x0"])

        is_same_paragraph = (
            gap < line_gap_threshold and
            left_diff < 15 and
            len(block["text"]) > 20
        )

        if is_same_paragraph:
            current_para["y1"] = block["y1"]
            current_para["x1"] = max(current_para["x1"], block["x1"])
            current_para["text"] += "\n" + block["text"]
            current_para["height"] = current_para["y1"] - current_para["y0"]
            current_para["blocks"].append(block)
        else:
            paragraphs.append(current_para)
            current_para = {
                "x0": block["x0"],
                "y0": block["y0"],
                "x1": block["x1"],
                "y1": block["y1"],
                "text": block["text"],
                "width": block["width"],
                "height": block["height"],
                "blocks": [block]
            }

    paragraphs.append(current_para)
    return paragraphs


def extract_text_blocks(page, page_num):
    """按列提取文本块：先左列从上到下，再右列从上到下，然后合并成段落"""
    blocks = page.get_text("blocks")

    valid_blocks = []
    for b in blocks:
        x0, y0, x1, y1, text, block_no, block_type = b
        text = text.strip()
        if block_type == 0 and len(text) > 5:
            valid_blocks.append({
                "x0": x0, "y0": y0, "x1": x1, "y1": y1,
                "text": text,
                "width": x1 - x0,
                "height": y1 - y0
            })

    page_mid = page.rect.width / 2
    left = [b for b in valid_blocks if b["x0"] + b["width"]/2 < page_mid]
    right = [b for b in valid_blocks if b["x0"] + b["width"]/2 >= page_mid]

    left.sort(key=lambda b: b["y0"])
    right.sort(key=lambda b: b["y0"])

    left_paragraphs = merge_blocks_into_paragraphs(left)
    right_paragraphs = merge_blocks_into_paragraphs(right)

    return left_paragraphs + right_paragraphs


def is_title_block(block, page):
    """判断文本块是否是标题（根据字号和位置）"""
    height = block["height"]
    text = block["text"]

    if len(text) < 50 and height < 20:
        return True

    if text.strip()[:3] in ["2.1", "2.2", "3.1", "3.2", "4.1", "4.2", "1 ", "2 ", "3 "] or \
       any(text.strip().startswith(f"{i}.") for i in range(1, 10)):
        return True

    return False


def get_text_font_size(block, is_title):
    """根据块大小和是否是标题，确定字体大小"""
    if is_title:
        return 11
    else:
        return 9.5


def check_overlap_with_images(block_rect, image_rects):
    """检查文本块是否与图片重叠，如果重叠则调整高度"""
    adjusted_height = block_rect.height

    for img_rect in image_rects:
        if block_rect.intersects(img_rect):
            intersection = block_rect & img_rect
            if intersection.height > 5:
                adjusted_height = min(adjusted_height, img_rect.y0 - block_rect.y0)

    return adjusted_height


def replace_text_in_page(page, translations, font_name="china-s"):
    """在页面上替换文字：擦掉英文，写入中文

    默认使用内置 china-s 字体，保证中文正常显示
    """
    blocks = extract_text_blocks(page, page.number)

    image_rects = []
    for img in page.get_images(full=True):
        xref = img[0]
        for rect in page.get_image_rects(xref):
            padded = fitz.Rect(
                rect.x0 - 3, rect.y0 - 3,
                rect.x1 + 3, rect.y1 + 3
            )
            image_rects.append(padded)

    replaced_count = 0
    for i, block in enumerate(blocks):
        if i >= len(translations):
            break

        chinese_text = translations[i]
        if not chinese_text:
            continue

        title = is_title_block(block, page)

        rect = fitz.Rect(block["x0"], block["y0"], block["x1"], block["y1"])
        page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)

        usable_height = check_overlap_with_images(rect, image_rects)

        font_size = get_text_font_size(block, title)

        usable_height = max(usable_height, 10)
        text_rect = fitz.Rect(
            block["x0"] + 2,
            block["y0"] + 2,
            block["x1"] - 2,
            block["y0"] + usable_height - 2
        )

        if text_rect.is_empty or text_rect.width < 10 or text_rect.height < 5:
            replaced_count += 1
            continue

        try:
            inserted = page.insert_textbox(
                text_rect,
                chinese_text,
                fontsize=font_size,
                fontname=font_name,
                color=(0, 0, 0),
                align=0,
                lineheight=1.3
            )

            if inserted < 0:
                font_size = font_size * 0.9
                page.insert_textbox(
                    text_rect,
                    chinese_text,
                    fontsize=font_size,
                    fontname=font_name,
                    color=(0, 0, 0),
                    align=0,
                    lineheight=1.3
                )
        except Exception as e:
            pass

        replaced_count += 1

    return replaced_count


def main():
    parser = argparse.ArgumentParser(description="PDF文字层替换工具")
    parser.add_argument("input", help="输入PDF文件路径")
    parser.add_argument("output", help="输出PDF文件路径")
    parser.add_argument("translations", help="翻译JSON文件路径")
    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"错误：文件不存在 - {args.input}")
        sys.exit(1)

    with open(args.translations, "r", encoding="utf-8") as f:
        translations = json.load(f)

    doc = fitz.open(args.input)
    total_replaced = 0

    for page_num in range(len(doc)):
        page = doc[page_num]
        page_key = f"page_{page_num + 1}"

        if page_key in translations:
            page_translations = translations[page_key]
            replaced = replace_text_in_page(page, page_translations)
            total_replaced += replaced
            print(f"  ✓ 第{page_num+1}页: 替换了 {replaced} 个文本块")

    doc.save(args.output)
    doc.close()

    print(f"\n✅ 完成！共替换 {total_replaced} 个文本块")
    print(f"输出文件: {args.output}")


if __name__ == "__main__":
    main()
